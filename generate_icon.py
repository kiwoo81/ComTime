"""ComTime 앱 아이콘 생성 스크립트"""
from PIL import Image, ImageDraw, ImageFont
import math
import os

SIZE = 512
CENTER = SIZE // 2
BG_COLOR = (52, 152, 219)       # 밝은 파란색 (아이 친화적)
MONITOR_COLOR = (44, 62, 80)     # 진한 남색 (모니터)
SCREEN_COLOR = (236, 240, 241)   # 밝은 회색 (화면)
CLOCK_COLOR = (241, 196, 15)     # 노란색 (시계)
CLOCK_RING = (243, 156, 18)      # 주황 (시계 테두리)
HAND_COLOR = (44, 62, 80)        # 시계 바늘
WHITE = (255, 255, 255)

img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 1. 둥근 배경
margin = 10
draw.rounded_rectangle(
    [margin, margin, SIZE - margin, SIZE - margin],
    radius=90,
    fill=BG_COLOR,
)

# 2. 모니터 본체
mon_left, mon_top = 80, 100
mon_right, mon_bot = 370, 330
draw.rounded_rectangle(
    [mon_left, mon_top, mon_right, mon_bot],
    radius=18,
    fill=MONITOR_COLOR,
)

# 3. 화면
scr_margin = 18
draw.rounded_rectangle(
    [mon_left + scr_margin, mon_top + scr_margin,
     mon_right - scr_margin, mon_bot - scr_margin],
    radius=8,
    fill=SCREEN_COLOR,
)

# 4. 모니터 스탠드
stand_cx = (mon_left + mon_right) // 2
draw.polygon([
    (stand_cx - 40, mon_bot),
    (stand_cx + 40, mon_bot),
    (stand_cx + 30, mon_bot + 35),
    (stand_cx - 30, mon_bot + 35),
], fill=MONITOR_COLOR)

# 스탠드 받침
draw.rounded_rectangle(
    [stand_cx - 60, mon_bot + 30, stand_cx + 60, mon_bot + 45],
    radius=5,
    fill=MONITOR_COLOR,
)

# 5. 화면 안에 재생 버튼 (아이 느낌)
# 작은 삼각형
tri_cx, tri_cy = (mon_left + mon_right) // 2 - 10, (mon_top + mon_bot) // 2
tri_size = 25
draw.polygon([
    (tri_cx - tri_size // 2, tri_cy - tri_size),
    (tri_cx - tri_size // 2, tri_cy + tri_size),
    (tri_cx + tri_size, tri_cy),
], fill=(46, 204, 113))  # 초록색 재생 버튼

# 6. 시계 (우하단에 오버레이)
clock_cx, clock_cy = 380, 370
clock_r = 90

# 시계 배경 (흰 테두리 + 노란 배경)
draw.ellipse(
    [clock_cx - clock_r - 6, clock_cy - clock_r - 6,
     clock_cx + clock_r + 6, clock_cy + clock_r + 6],
    fill=WHITE,
)
draw.ellipse(
    [clock_cx - clock_r, clock_cy - clock_r,
     clock_cx + clock_r, clock_cy + clock_r],
    fill=CLOCK_COLOR,
)

# 시계 눈금 (12개)
for i in range(12):
    angle = math.radians(i * 30 - 90)
    inner = clock_r - 15
    outer = clock_r - 5
    x1 = clock_cx + inner * math.cos(angle)
    y1 = clock_cy + inner * math.sin(angle)
    x2 = clock_cx + outer * math.cos(angle)
    y2 = clock_cy + outer * math.sin(angle)
    width = 4 if i % 3 == 0 else 2
    draw.line([(x1, y1), (x2, y2)], fill=HAND_COLOR, width=width)

# 시침 (10시 방향)
hour_angle = math.radians(10 * 30 - 90)
hour_len = clock_r * 0.5
draw.line(
    [(clock_cx, clock_cy),
     (clock_cx + hour_len * math.cos(hour_angle),
      clock_cy + hour_len * math.sin(hour_angle))],
    fill=HAND_COLOR, width=6,
)

# 분침 (2시 방향)
min_angle = math.radians(2 * 30 - 90)
min_len = clock_r * 0.7
draw.line(
    [(clock_cx, clock_cy),
     (clock_cx + min_len * math.cos(min_angle),
      clock_cy + min_len * math.sin(min_angle))],
    fill=HAND_COLOR, width=4,
)

# 시계 중심점
draw.ellipse(
    [clock_cx - 5, clock_cy - 5, clock_cx + 5, clock_cy + 5],
    fill=HAND_COLOR,
)

# 저장
out_dir = os.path.dirname(os.path.abspath(__file__))

# PNG (원본)
png_path = os.path.join(out_dir, "comtime_icon.png")
img.save(png_path, "PNG")
print(f"PNG saved: {png_path}")

# ICO (Windows용 - 여러 크기 포함)
ico_path = os.path.join(out_dir, "comtime_icon.ico")
icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save(ico_path, "ICO", sizes=icon_sizes)
print(f"ICO saved: {ico_path}")

# ICNS (macOS용) - iconutil 사용
import subprocess, tempfile, shutil

iconset_dir = os.path.join(out_dir, "comtime_icon.iconset")
os.makedirs(iconset_dir, exist_ok=True)

icns_sizes = [16, 32, 64, 128, 256, 512]
for s in icns_sizes:
    resized = img.resize((s, s), Image.LANCZOS)
    resized.save(os.path.join(iconset_dir, f"icon_{s}x{s}.png"))
    # @2x 버전
    if s <= 256:
        resized2x = img.resize((s * 2, s * 2), Image.LANCZOS)
        resized2x.save(os.path.join(iconset_dir, f"icon_{s}x{s}@2x.png"))

icns_path = os.path.join(out_dir, "comtime_icon.icns")
result = subprocess.run(
    ["iconutil", "-c", "icns", iconset_dir, "-o", icns_path],
    capture_output=True, text=True,
)
if result.returncode == 0:
    print(f"ICNS saved: {icns_path}")
else:
    print(f"ICNS failed: {result.stderr}")

# 정리
shutil.rmtree(iconset_dir, ignore_errors=True)
print("Done!")
