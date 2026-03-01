# ComTime - CLAUDE.md

## 프로젝트 개요
아이 컴퓨터 사용 시간을 관리하는 부모 통제 애플리케이션.
- 한국어 UI
- 지원 OS: macOS, Windows

## 개발 규칙

### 크로스플랫폼 호환성
기능 추가 또는 소스 코드 변경 시 반드시 macOS와 Windows 양쪽에서 정상 동작하는지 호환성 체크를 수행할 것.
- `sys.platform` 분기가 필요한지 확인 (예: ctypes, subprocess, 파일 경로)
- macOS 전용 API (osascript, AppKit 등) 사용 시 Windows 대체 구현 필수
- Windows 전용 API (ctypes.windll 등) 사용 시 `sys.platform == "win32"` 가드 필수
- 파일 경로 구분자는 `os.path.join()` 사용 (하드코딩 금지)
- 새 외부 의존성 추가 시 양쪽 OS에서 설치 가능한지 확인

## 기술 스택
- **언어**: Python 3.x
- **GUI**: PyQt6 (Fusion 스타일)
- **DB**: SQLite3
- **보안**: hashlib (PIN SHA256 해싱)
- **패키징**: PyInstaller

## 프로젝트 구조
```
ComTime/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── .gitignore
├── generate_icon.py         # 아이콘 생성 스크립트
├── comtime_icon.png         # 앱 아이콘 (512x512)
├── comtime_icon.ico         # Windows용 아이콘
├── comtime_icon.icns        # macOS용 아이콘
└── src/
    ├── main.py              # 메인 GUI (MainWindow, KioskWindow)
    └── db.py                # SQLite 데이터베이스 레이어
```

## 핵심 컴포넌트

### MainWindow (src/main.py)
- 하루 컴퓨터 사용 시간 표시 (HH:MM:SS)
- 세션 시작/종료 기록 및 목록 테이블
- 프로그램 사용 내역 추적 (5초 간격 포그라운드 앱 감지)
- 날짜별 이력 조회 (◀ ▶ 버튼 + 달력 팝업)
- 세션 우클릭 삭제
- PIN 인증으로 앱 종료 보호 / PIN 변경 메뉴
- 세션 자동 복구 및 자정 리셋
- 하트비트(30초 간격) 기반 비정상 종료 감지 → 재시작 시 꺼져 있던 시간 제외
- 잠금 유예: 1분 이내 잠금 해제 시 세션 유지 (새 세션 생성 없이 재개)
- 테이블 스크롤 위치 유지 (1초 갱신 시에도 스크롤 위치 보존)

### KioskWindow (src/main.py)
- 사용 종료 후 전체화면 잠금 (탈출 불가)
- Windows: 작업 표시줄 숨김, ctypes SetWindowPos(HWND_TOPMOST)로 항상 위 표시
- macOS/Windows 공통: `activateWindow()` / `SetForegroundWindow` 미호출 → 절전 모드 진입 허용
- "사용 시작" 버튼으로 재개

### db.py
- `sessions` 테이블: 세션 start/end 타임스탬프, 소요 시간
- `settings` 테이블: PIN(SHA256), `last_heartbeat`(비정상 종료 감지), 기타 설정값
- `app_usage` 테이블: 세션별 프로그램 사용 기록 (앱명, 사용 시간)

## 실행 방법
```bash
python -m venv .venv
source .venv/bin/activate        # macOS
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
python src/main.py
```

## 실행 파일 빌드

### Windows (.exe)
```bash
pyinstaller --onefile --windowed --name ComTime --icon=comtime_icon.ico --add-data "src/db.py;." --add-data "comtime_icon.png;." src/main.py
```

### macOS (.app)
```bash
pyinstaller --onedir --windowed --name ComTime --icon=comtime_icon.icns --add-data "src/db.py:." --add-data "comtime_icon.png:." src/main.py
```

### 공통
- 구분자 차이: Windows는 `;`, macOS는 `:`
- DB 파일은 실행 파일과 같은 폴더에 생성됨
- `dist/`, `build/`, `*.spec`은 .gitignore에 제외됨
