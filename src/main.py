import sys
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QMessageBox,
)
from PyQt6.QtCore import QTimer, Qt

from db import Database


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TimeLimiter - 컴퓨터 사용 시간 관리")
        self.db = Database("timelimiter.db")
        self.running = False
        self.current_session_id = None
        self.session_start = None
        self.current_date = date.today()

        # resume open session if exists
        open_s = self.db.get_open_session()
        if open_s:
            try:
                self.current_session_id = open_s.get("id")
                self.session_start = datetime.fromisoformat(open_s.get("start_ts"))
                self.running = True
            except Exception:
                self.running = False

        central = QWidget()
        layout = QVBoxLayout()

        self.time_label = QLabel("오늘 사용: 00:00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

        self.stop_btn = QPushButton("사용 중지")
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        self.log_table = QTableWidget(0, 3)
        self.log_table.setHorizontalHeaderLabels(["시작 시간", "종료 시간", "사용 시간"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.log_table)

        central.setLayout(layout)
        self.setCentralWidget(central)

        self.stop_btn.clicked.connect(self.on_stop)

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_timer)

        # PIN이 없으면 최초 실행 시 설정 (부모가 설정)
        if self.db.get_setting("pin_sha256") is None:
            self._prompt_set_pin()

        # 세션 시작 (복구된 세션이 없으면 새로 시작)
        if not self.running:
            self.on_start()
        else:
            self.stop_btn.setEnabled(True)
            self.timer.start()

        self.refresh_ui()

    def on_start(self):
        if self.running:
            return
        now = datetime.now()
        self.session_start = now
        session_id = self.db.start_session(now.isoformat())
        self.current_session_id = session_id
        self.running = True
        self.stop_btn.setEnabled(True)
        self.timer.start()
        self.refresh_ui()

    def on_stop(self):
        if not self.running:
            return
        now = datetime.now()
        self.db.end_session(self.current_session_id, now.isoformat())
        self.running = False
        self.current_session_id = None
        self.session_start = None
        self.stop_btn.setEnabled(False)
        self.timer.stop()
        self.refresh_ui()

        # 잠금 화면 표시
        self.kiosk = KioskWindow(on_unlock=self.on_start)
        self.kiosk.show()

    def update_timer(self):
        today = date.today()
        if today != self.current_date:
            if self.running and self.current_session_id:
                midnight = datetime.combine(today, datetime.min.time())
                self.db.end_session(self.current_session_id, midnight.isoformat())
                new_id = self.db.start_session(midnight.isoformat())
                self.current_session_id = new_id
                self.session_start = midnight
            self.current_date = today
        total = self.db.get_total_seconds_for_date(self.current_date)
        if self.running and self.session_start:
            total += int((datetime.now() - self.session_start).total_seconds())
        hrs = total // 3600
        mins = (total % 3600) // 60
        secs = total % 60
        self.time_label.setText(f"오늘 사용: {hrs:02d}:{mins:02d}:{secs:02d}")
        self.refresh_logs()

    @staticmethod
    def _format_ts(iso_str: str) -> str:
        if not iso_str:
            return ""
        try:
            return datetime.fromisoformat(iso_str).strftime("%H:%M:%S")
        except Exception:
            return iso_str

    @staticmethod
    def _format_duration(seconds) -> str:
        if seconds is None:
            return "진행 중"
        s = int(seconds)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"

    def refresh_logs(self):
        sessions = self.db.get_sessions_for_date(self.current_date)
        self.log_table.setRowCount(0)
        for s in sessions:
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)
            start = self._format_ts(s.get("start_ts") or "")
            end = self._format_ts(s.get("end_ts") or "")
            dur = self._format_duration(s.get("duration_seconds"))
            self.log_table.setItem(row, 0, QTableWidgetItem(start))
            self.log_table.setItem(row, 1, QTableWidgetItem(end))
            self.log_table.setItem(row, 2, QTableWidgetItem(dur))

    def refresh_ui(self):
        self.update_timer()
        self.refresh_logs()

    def closeEvent(self, event):
        # PIN이 설정되어 있으면 PIN 입력 없이 종료 불가
        pin_exists = self.db.get_setting("pin_sha256") is not None
        if pin_exists:
            pin, ok = QInputDialog.getText(
                self, "종료 인증", "앱을 종료하려면 PIN을 입력하세요:",
                QLineEdit.EchoMode.Password
            )
            if not ok or not self.db.verify_pin(pin):
                event.ignore()
                return
        if self.running and self.current_session_id:
            now = datetime.now()
            self.db.end_session(self.current_session_id, now.isoformat())
        event.accept()

    def _prompt_set_pin(self) -> bool:
        p1, ok1 = QInputDialog.getText(self, "PIN 생성", "새 PIN 입력:", QLineEdit.EchoMode.Password)
        if not ok1 or not p1:
            return False
        p2, ok2 = QInputDialog.getText(self, "PIN 확인", "PIN 다시 입력:", QLineEdit.EchoMode.Password)
        if not ok2 or p1 != p2:
            QMessageBox.warning(self, "오류", "PIN이 일치하지 않거나 입력이 취소되었습니다.")
            return False
        self.db.set_pin(p1)
        QMessageBox.information(self, "완료", "PIN이 설정되었습니다.")
        return True


class KioskWindow(QMainWindow):
    def __init__(self, on_unlock=None):
        super().__init__()
        self._on_unlock = on_unlock
        self._unlocked = False
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setWindowTitle("Locked")
        self._init_ui()
        self.showFullScreen()
        # 주기적으로 최상위 유지
        self._stay_on_top_timer = QTimer()
        self._stay_on_top_timer.setInterval(1000)
        self._stay_on_top_timer.timeout.connect(self._ensure_on_top)
        self._stay_on_top_timer.start()

    def _ensure_on_top(self):
        self.raise_()
        self.activateWindow()

    def _init_ui(self):
        label = QLabel("컴퓨터 사용이 중지되었습니다.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: white;")
        btn = QPushButton("사용 시작")
        btn.setStyleSheet("font-size: 18px; padding: 10px 30px;")
        btn.clicked.connect(self._unlock)
        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(label)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        w = QWidget()
        w.setLayout(layout)
        w.setStyleSheet("background-color: #1a1a2e;")
        self.setCentralWidget(w)

    def _unlock(self):
        self._unlocked = True
        self._stay_on_top_timer.stop()
        self.close()
        if self._on_unlock:
            self._on_unlock()

    def keyPressEvent(self, event):
        event.accept()

    def closeEvent(self, event):
        if self._unlocked:
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(600, 400)
    win.show()
    sys.exit(app.exec())
