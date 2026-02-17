import sys
import os
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QDateEdit,
)
from PyQt6.QtCore import QTimer, Qt, QDate

# DB 경로: exe로 패키징된 경우 exe 위치 기준, 스크립트 실행 시 스크립트 위치 기준
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DB_PATH = os.path.join(_BASE_DIR, "timelimiter.db")

from db import Database


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TimeLimiter - 컴퓨터 사용 시간 관리")
        self.db = Database(_DB_PATH)
        self.running = False
        self.current_session_id = None
        self.session_start = None
        self.current_date = date.today()
        self.selected_date = date.today()

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

        # 날짜 탐색 UI
        date_nav = QHBoxLayout()
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedWidth(40)
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMaximumDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedWidth(40)
        date_nav.addWidget(self.prev_btn)
        date_nav.addWidget(self.date_edit)
        date_nav.addWidget(self.next_btn)
        layout.addLayout(date_nav)

        self.stop_btn = QPushButton("사용 중지")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFixedHeight(48)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                color: white;
                background-color: #c0392b;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
            QPushButton:disabled {
                background-color: #888888;
                color: #cccccc;
            }
        """)
        layout.addWidget(self.stop_btn)

        self.log_table = QTableWidget(0, 3)
        self.log_table.setHorizontalHeaderLabels(["시작 시간", "종료 시간", "사용 시간"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.log_table)

        central.setLayout(layout)
        self.setCentralWidget(central)

        self.stop_btn.clicked.connect(self.on_stop)
        self.prev_btn.clicked.connect(self.on_prev_date)
        self.next_btn.clicked.connect(self.on_next_date)
        self.date_edit.dateChanged.connect(self.on_date_changed)

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
            self.date_edit.setMaximumDate(QDate.currentDate())
        total = self.db.get_total_seconds_for_date(self.selected_date)
        if self.running and self.session_start and self.selected_date == self.current_date:
            total += int((datetime.now() - self.session_start).total_seconds())
        hrs = total // 3600
        mins = (total % 3600) // 60
        secs = total % 60
        if self.selected_date == today:
            prefix = "오늘 사용"
        else:
            prefix = f"{self.selected_date.strftime('%m/%d')} 사용"
        self.time_label.setText(f"{prefix}: {hrs:02d}:{mins:02d}:{secs:02d}")
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
        sessions = self.db.get_sessions_for_date(self.selected_date)
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

    def on_prev_date(self):
        new_date = self.selected_date - timedelta(days=1)
        self.date_edit.setDate(QDate(new_date.year, new_date.month, new_date.day))

    def on_next_date(self):
        new_date = self.selected_date + timedelta(days=1)
        if new_date <= date.today():
            self.date_edit.setDate(QDate(new_date.year, new_date.month, new_date.day))

    def on_date_changed(self, qdate: QDate):
        self.selected_date = date(qdate.year(), qdate.month(), qdate.day())
        self.next_btn.setEnabled(self.selected_date < date.today())
        self.update_timer()

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
        # Windows: 작업 표시줄 숨기기
        if sys.platform == "win32":
            self._set_taskbar_visible(False)
        # 주기적으로 최상위 유지
        self._stay_on_top_timer = QTimer()
        self._stay_on_top_timer.setInterval(500)
        self._stay_on_top_timer.timeout.connect(self._ensure_on_top)
        self._stay_on_top_timer.start()

    def _ensure_on_top(self):
        self.raise_()
        self.activateWindow()
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(self.winId())
                # HWND_TOPMOST(-1), SWP_NOMOVE|SWP_NOSIZE
                ctypes.windll.user32.SetWindowPos(
                    hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002
                )
                # 포커스 강제 획득
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass

    @staticmethod
    def _set_taskbar_visible(visible: bool):
        """Windows 작업 표시줄 표시/숨기기"""
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
            if hwnd:
                # SW_SHOW=5, SW_HIDE=0
                ctypes.windll.user32.ShowWindow(hwnd, 5 if visible else 0)
        except Exception:
            pass

    def _init_ui(self):
        label = QLabel("컴퓨터 사용이 중지되었습니다.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: white;")
        btn = QPushButton("사용 시작")
        btn.setStyleSheet("font-size: 18px; padding: 10px 30px; color: white; border: 2px solid white; border-radius: 6px;")
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
        if sys.platform == "win32":
            self._set_taskbar_visible(True)
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
    app.setStyle("Fusion")  # Mac/Windows 동일한 스타일 렌더링
    win = MainWindow()
    win.resize(600, 400)
    win.show()
    sys.exit(app.exec())
