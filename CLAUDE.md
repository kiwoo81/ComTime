# TimeLimiter - CLAUDE.md

## 프로젝트 개요
아이 컴퓨터 사용 시간을 관리하는 부모 통제 애플리케이션.
- 개발 언어: 한국어 UI
- 최초 개발 환경: macOS
- 현재 작업: Windows 이식 및 호환성 확인

## 기술 스택
- **언어**: Python 3.x
- **GUI**: PyQt6
- **DB**: SQLite3 (내장 모듈)
- **보안**: hashlib (PIN SHA256 해싱)

## 프로젝트 구조
```
TimeLimiter/
├── CLAUDE.md              # 이 파일
├── requirements.txt       # PyQt6
├── .gitignore
└── src/
    ├── main.py            # 메인 GUI 앱 (MainWindow, KioskWindow)
    └── db.py              # SQLite 데이터베이스 레이어
```

## 핵심 컴포넌트

### MainWindow (src/main.py)
- 하루 컴퓨터 사용 시간 표시 (HH:MM:SS)
- 세션 시작/종료 기록
- 오늘 세션 목록 테이블 표시
- PIN 인증으로 앱 종료 보호
- 앱 시작 시 중단된 세션 자동 복구
- 자정 기준 일별 리셋

### KioskWindow (src/main.py)
- 사용 종료 후 표시되는 전체화면 잠금 화면
- Windows 작업 표시줄 숨김
- 키 입력 무시 (탈출 불가)
- Windows API (ctypes)로 항상 위에 표시 및 포커스 강제
- "사용 시작" 버튼으로 재개

### db.py
- `sessions` 테이블: 세션 start/end 타임스탬프, 소요 시간
- `settings` 테이블: PIN(SHA256), 기타 설정값
- DB 파일 경로: 고정 경로 사용 (Windows 호환성 적용됨)

## 실행 방법
```bash
# 가상환경 생성 및 활성화
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 앱 실행
python src/main.py
```

## Windows 이식 현황

### 완료된 작업 (커밋: 0980647)
- DB 파일 경로 고정 (macOS 경로 문제 수정)
- 키오스크 잠금 강화 (Windows API ctypes 적용)

### 확인 필요 사항 (완료)
- [x] Windows에서 정상 실행 여부
- [x] 키오스크 모드 잠금 동작 확인
- [x] 작업 표시줄 숨김/복원 동작 확인
- [x] DB 경로 정상 작동 확인
- [x] PIN 설정 및 인증 동작 확인
- [x] 세션 시작/종료 및 시간 기록 확인
- [x] 앱 종료 후 재시작 시 세션 복구 확인

## 개발 진행 노트
<!-- 개발 중 발견한 이슈, 결정사항, 메모를 여기에 추가 -->

### 2026-02-17
- GitHub에서 Windows PC로 클론 완료
- Windows 호환성 테스트 전 항목 통과 (실행, 키오스크, 작업표시줄, DB, PIN, 세션, 세션 복구)
- 키오스크 화면 "사용 시작" 버튼 글자색/테두리색 흰색으로 수정 (어두운 배경에서 가시성 개선)
- 날짜 선택 기능 추가 (◀ ▶ 버튼 + 달력 팝업으로 과거 날짜 이력 및 총 사용시간 조회)
- "사용 중지" 버튼 스타일 강화 (빨간 배경, 굵은 글씨, 호버 효과)
- Fusion 스타일 적용으로 Mac/Windows UI 통일
- exe 패키징 지원: PyInstaller --onefile, frozen 환경에서 DB 경로 sys.executable 기준으로 수정

## exe 빌드 방법
```bash
pyinstaller --onefile --windowed --name TimeLimiter --add-data "src/db.py;." src/main.py
```
- 결과물: `dist/TimeLimiter.exe` (약 36MB)
- DB 파일은 exe와 같은 폴더에 생성됨
- `dist/`, `build/`, `*.spec`은 .gitignore에 제외됨
