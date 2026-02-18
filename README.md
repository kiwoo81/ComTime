# ComTime

아이 컴퓨터 사용 시간을 관리하는 부모 통제 애플리케이션입니다.

## 주요 기능

- **사용 시간 추적**: 세션별 시작/종료 시간 및 누적 사용시간 표시 (HH:MM:SS)
- **프로그램 사용 기록**: 세션 중 어떤 프로그램을 사용했는지 자동 감지 및 기록
- **키오스크 잠금**: 사용 중지 시 전체화면 잠금 화면 표시 (탈출 불가)
- **PIN 보호**: 앱 종료 시 PIN 인증 필요 (부모만 종료 가능)
- **날짜별 이력 조회**: 과거 날짜의 사용시간 및 프로그램 사용 내역 확인
- **세션 자동 복구**: 비정상 종료 후 재시작 시 중단된 세션 자동 복구
- **자정 기준 리셋**: 자정에 자동으로 새 세션 시작

## 기술 스택

- **언어**: Python 3.x
- **GUI**: PyQt6 (Fusion 스타일)
- **DB**: SQLite3
- **지원 OS**: macOS, Windows

## 빠른 시작

```bash
# 가상환경 생성 및 활성화
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 앱 실행
python src/main.py
```

## 실행 파일 빌드

### Windows
```bash
pyinstaller --onefile --windowed --name ComTime --add-data "src/db.py;." src/main.py
```

### macOS
```bash
pyinstaller --onefile --windowed --name ComTime --add-data "src/db.py:." src/main.py
```

## 프로젝트 구조

```
ComTime/
├── README.md
├── CLAUDE.md
├── requirements.txt
├── .gitignore
└── src/
    ├── main.py    # 메인 GUI (MainWindow, KioskWindow)
    └── db.py      # SQLite 데이터베이스 레이어
```
