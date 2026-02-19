# ComTime

아이 컴퓨터 사용 시간을 관리하는 부모 통제 애플리케이션입니다.

## 주요 기능

- **사용 시간 추적** - 세션별 시작/종료 시간 및 누적 사용시간 표시 (HH:MM:SS)
- **프로그램 사용 기록** - 포그라운드 앱 자동 감지 및 사용 시간 기록
- **키오스크 잠금** - 사용 중지 시 전체화면 잠금 ("사용 시작" 버튼으로 해제)
- **PIN 보호** - 숫자 4자리 PIN으로 앱 종료, 기록 삭제, PIN 변경 시 인증
- **날짜별 이력 조회** - 과거 날짜의 사용시간 및 프로그램 내역 확인
- **세션 자동 복구** - 비정상 종료 후 재시작 시 중단된 세션 복구
- **자정 자동 리셋** - 자정에 새 세션 시작
- **자동 시작 등록** - 컴퓨터 부팅 시 자동 실행 등록/해제 (PIN 보호)
- **단일 인스턴스** - 중복 실행 방지

## 기술 스택

Python 3.x | PyQt6 (Fusion) | SQLite3 | macOS & Windows

## 빠른 시작

```bash
python -m venv .venv
source .venv/bin/activate        # macOS
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
python src/main.py
```

## 실행 파일 빌드

```bash
# Windows
pyinstaller --onefile --windowed --name ComTime --icon=comtime_icon.ico \
  --add-data "src/db.py;." --add-data "comtime_icon.png;." src/main.py

# macOS
pyinstaller --onefile --windowed --name ComTime --icon=comtime_icon.icns \
  --add-data "src/db.py:." --add-data "comtime_icon.png:." src/main.py
```

## 프로젝트 구조

```
ComTime/
├── requirements.txt
├── comtime_icon.*           # 앱 아이콘 (png, ico, icns)
├── generate_icon.py         # 아이콘 생성 스크립트
└── src/
    ├── main.py              # 메인 GUI (MainWindow, KioskWindow)
    └── db.py                # SQLite 데이터베이스 레이어
```
