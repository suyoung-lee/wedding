"""imgs/ 원본 -> assets/ 웹용 이미지 생성.

    python build_assets.py

원본(imgs/, 45MB PNG)은 레포에 올리지 않습니다. assets/ 결과물만 커밋합니다.
사진을 교체하려면 아래 ORDER 목록만 고치고 다시 실행하세요.
"""

import os
import numpy as np
from PIL import Image
from scipy import ndimage
import pypdfium2 as pdfium

SRC = "imgs"
OUT = "assets"
os.makedirs(OUT, exist_ok=True)

A = lambda n: os.path.join(SRC, f"KakaoTalk_20260909_203020487{n}.png")
B = lambda n: os.path.join(SRC, f"KakaoTalk_20260909_204922384{n}.png")
SOLO = os.path.join(SRC, "KakaoTalk_20260909_203158458.png")

# 촬영 세트별로 묶은 갤러리 순서. (파일, 설명)
# 슬라이드형이라 순서만 의미가 있고, 가로 사진은 object-fit:contain 으로 처리됩니다.
ORDER = [
    # 검정 배경 스튜디오
    (A("_16"), "검정 배경 스튜디오 - 신부 정면"),
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

# ── 약도 ────────────────────────────────────────────────────────────
# 업체 PDF의 아래쪽 교통편 텍스트 블록은 잘라냅니다. 폰에서 축소되면 못 읽고,
# 같은 내용을 index.html 에 HTML 텍스트로 넣어두었습니다.
#   map-full.png : 다이어그램 고해상도. 탭하면 새 탭에서 크게.
#   map.png      : 같은 그림 축소본. 페이지에 인라인 표시.
page = pdfium.PdfDocument(MAP_PDF)[0]
w_pt, h_pt = page.get_size()
full = Image.fromarray(page.render(scale=3000 / w_pt).to_numpy()).convert("RGB")

# 다이어그램 영역 (원본 대비 비율 — PDF가 바뀌면 여기만 조정)
cl, ct, cr, cb = 0.072, 0.163, 0.928, 0.628
crop = full.crop((int(cl * full.width), int(ct * full.height),
                  int(cr * full.width), int(cb * full.height)))

# 신분당선을 실제 노선색(빨강)으로 정정.
# 업체 약도는 신분당선을 남색으로 그렸는데, 그 남색은 도보 경로선·핀·
# "세인트 메리엘" 글자에도 함께 쓰입니다. 그래서 색으로만 고르면 지도가 통째로
# 빨개집니다. 남색 영역을 연결 요소로 나눈 뒤 "가장 큰 덩어리"(= 역 막대 + ④번
# 출구 표시)만 칠합니다.
SHINBUNDANG = (165, 17, 47)      # #A5112F — 후보 4종을 비교해 고른 값
NAVY_R = 51                      # 원본 남색 #3331b7 의 R 채널

ca = np.array(crop).astype(int)
navy = ((ca[:, :, 2] > ca[:, :, 0] + 25) &
        (ca[:, :, 2] > ca[:, :, 1] + 25) &
        (ca[:, :, 2] > 90))
lab, ncomp = ndimage.label(navy, structure=np.ones((3, 3)))
sizes = ndimage.sum(navy, lab, range(1, ncomp + 1))
main = int(np.argmax(sizes)) + 1
bar = (lab == main)

# 엉뚱한 덩어리를 칠하지 않도록 검증 — 세로로 길고 왼쪽에 있어야 합니다.
ys, xs = np.nonzero(bar)
h, w = bar.shape
assert bar.sum() > navy.sum() * 0.5,        "신분당선 막대를 못 찾았습니다"
assert (ys.max() - ys.min()) > h * 0.4,     "찾은 덩어리가 세로로 길지 않습니다"
assert xs.max() < w * 0.3,                  "찾은 덩어리가 지도 왼쪽에 있지 않습니다"

# ④ 원 안의 숫자처럼 링에 닿지 않아 따로 떨어진 조각도 같이 칠합니다.
# (안 하면 링만 빨갛고 숫자는 남색으로 남습니다)
y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
for cid, sl in enumerate(ndimage.find_objects(lab), start=1):
    if cid == main or sl is None:
        continue
    if sl[0].start >= y0 and sl[0].stop <= y1 + 1 and sl[1].start >= x0 and sl[1].stop <= x1 + 1:
        bar |= (lab == cid)

# 안티에일리어싱 보존: 흰 배경 위 남색의 투명도를 구해 같은 투명도로 빨강을 올림
alpha = np.clip((255 - ca[:, :, 0]) / (255 - NAVY_R), 0, 1)[..., None]
recolored = np.array(crop).astype(float)
recolored[bar] = ((1 - alpha) * 255 + alpha * np.array(SHINBUNDANG))[bar]
crop = Image.fromarray(recolored.round().astype(np.uint8))

crop.save(os.path.join(OUT, "map-full.png"), "PNG", optimize=True)
small = crop.resize((1540, round(crop.height * 1540 / crop.width)), Image.LANCZOS)
small.save(os.path.join(OUT, "map.png"), "PNG", optimize=True)
print("  신분당선 정정: {}px -> #{:02X}{:02X}{:02X}".format(int(bar.sum()), *SHINBUNDANG))

for n in ("map.png", "map-full.png"):
    sz = os.path.getsize(os.path.join(OUT, n))
    total += sz
    im = Image.open(os.path.join(OUT, n))
    print(f"{n:14} {im.width}x{im.height}  {sz/1024:.0f}KB")

print(f"\n합계 {total/1e6:.2f} MB")
print("\n-- index.html 슬라이드용 (처음 2장은 즉시, 나머지는 data-src 지연 로딩) --")
for i, (name, alt, wide) in enumerate(manifest):
    cls = "slide contain" if wide else "slide"
    src = f'src="assets/{name}"' if i < 2 else f'data-src="assets/{name}"'
    print(f'<div class="{cls}"><img {src} alt="{alt}" draggable="false"></div>')
