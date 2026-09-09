"""imgs/ 원본 -> assets/ 웹용 이미지 생성.

    python build_assets.py

원본(imgs/, 45MB PNG)은 레포에 올리지 않습니다. assets/ 결과물만 커밋합니다.
사진을 교체하려면 아래 ORDER 목록만 고치고 다시 실행하세요.
"""

import os
from PIL import Image
import pypdfium2 as pdfium

SRC = "imgs"
OUT = "assets"
os.makedirs(OUT, exist_ok=True)

A = lambda n: os.path.join(SRC, f"KakaoTalk_20260909_203020487{n}.png")
B = lambda n: os.path.join(SRC, f"KakaoTalk_20260909_204922384{n}.png")
SOLO = os.path.join(SRC, "KakaoTalk_20260909_203158458.png")

# 촬영 세트별로 묶은 갤러리 순서. (파일, 설명)
#
# 가로 사진의 위치 주의: 2열 격자에서 가로 사진은 2칸을 차지하므로,
# 앞에 오는 세로 사진 개수가 짝수여야 빈칸 없이 채워집니다.
# 지금은 6장 뒤(7번)에 두어 정확히 맞습니다. 순서를 바꾸면 이 조건을 다시 확인하세요.
ORDER = [
    # 검정 배경 스튜디오
    (A("_16"), "검정 배경 스튜디오 - 신부 정면"),
    (A(""),    "검정 배경 스튜디오 - 신부 측면"),
    (A("_15"), "검정 배경 스튜디오 - 신랑"),
    # 화이트 스튜디오 (거울 / 케이크)
    (A("_04"), "화이트 스튜디오 - 거울 앞 신부"),
    (A("_05"), "화이트 스튜디오 - 거울 앞 두 사람"),
    (A("_03"), "화이트 스튜디오 - 케이크와 함께"),
    # 화이트 스튜디오 (레드 부케)
    (A("_12"), "화이트 스튜디오 - 드레스 전신"),          # ← 가로 사진
    (A("_13"), "화이트 스튜디오 - 레드 부케"),
    (A("_14"), "화이트 홀 - 머메이드 드레스"),
    # 아이보리 수트 + 옐로 드레스
    (B("_02"), "아이보리 수트 - 두 사람"),
    (B("_01"), "아이보리 수트 - 두 사람"),
    (B(""),    "아이보리 수트 - 신부"),
    (SOLO,     "아이보리 수트 - 신랑"),
    # 옐로 플라워
    (A("_02"), "옐로 플라워 - 두 사람"),
    (A("_11"), "옐로 플라워 - 신랑"),
    # 가든
    (A("_07"), "가든 - 두 사람"),
    (A("_01"), "가든 - 두 사람"),
    (A("_06"), "가든 - 잎사귀 배경"),
    (A("_10"), "가든 - 신부"),
    (A("_09"), "가든 - 신부"),
    (A("_08"), "가든 - 신부"),
]

COVER = A("_02")          # 표지
MAP_PDF = os.path.join(SRC, "[세인트 메리엘] 청첩장 약도 (1).pdf")


def save_jpg(im, path, max_w, quality=82):
    im = im.convert("RGB")
    if im.width > max_w:
        h = round(im.height * max_w / im.width)
        im = im.resize((max_w, h), Image.LANCZOS)
    im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    return im.size, os.path.getsize(path)


total = 0
manifest = []
for i, (f, alt) in enumerate(ORDER, 1):
    name = f"g{i:02d}.jpg"
    size, nbytes = save_jpg(Image.open(f), os.path.join(OUT, name), 900)
    total += nbytes
    wide = size[0] > size[1]
    manifest.append((name, alt, wide))
    print(f"{name}  {size[0]}x{size[1]:<5} {nbytes/1024:6.0f}KB  {'[가로]' if wide else ''}  {alt}")

# 표지
size, nbytes = save_jpg(Image.open(COVER), os.path.join(OUT, "cover.jpg"), 1000, 86)
total += nbytes
print(f"cover.jpg  {size[0]}x{size[1]}  {nbytes/1024:.0f}KB")

# 카카오톡 공유 미리보기 (1200x630, 사진을 크림색 배경에 레터박스)
og = Image.new("RGB", (1200, 630), "#fbfaf7")
c = Image.open(COVER).convert("RGB")
c.thumbnail((630, 630), Image.LANCZOS)
og.paste(c, ((1200 - c.width) // 2, (630 - c.height) // 2))
og.save(os.path.join(OUT, "og.jpg"), "JPEG", quality=86, optimize=True)
total += os.path.getsize(os.path.join(OUT, "og.jpg"))
print(f"og.jpg     1200x630  {os.path.getsize(os.path.join(OUT,'og.jpg'))/1024:.0f}KB")

# 약도 PDF -> PNG (선이 얇아서 JPEG보다 PNG가 깔끔)
#   map-full.png : 약도 전체. 페이지에서 탭하면 새 탭으로 열려 확대해 볼 수 있음.
#   map.png      : 지도 다이어그램만 크롭. 페이지에 인라인으로 보여주는 용도.
#                  (아래 교통편 텍스트는 이미지 대신 HTML로 넣어야 폰에서 읽힘)
page = pdfium.PdfDocument(MAP_PDF)[0]
w_pt, h_pt = page.get_size()
full = Image.fromarray(page.render(scale=1800 / w_pt).to_numpy()).convert("RGB")
full.save(os.path.join(OUT, "map-full.png"), "PNG", optimize=True)

# 다이어그램 영역 (원본 대비 비율로 지정 — PDF가 바뀌면 여기만 조정)
cl, ct, cr, cb = 0.072, 0.163, 0.928, 0.628
crop = full.crop((int(cl * full.width), int(ct * full.height),
                  int(cr * full.width), int(cb * full.height)))
crop.save(os.path.join(OUT, "map.png"), "PNG", optimize=True)

for n in ("map.png", "map-full.png"):
    sz = os.path.getsize(os.path.join(OUT, n))
    total += sz
    im = Image.open(os.path.join(OUT, n))
    print(f"{n:14} {im.width}x{im.height}  {sz/1024:.0f}KB")

print(f"\n합계 {total/1e6:.2f} MB")
print("\n-- index.html 갤러리용 --")
for name, alt, wide in manifest:
    print(f'<div class="{"cell wide" if wide else "cell"}"><img src="assets/{name}" alt="{alt}" loading="lazy" draggable="false"></div>')
