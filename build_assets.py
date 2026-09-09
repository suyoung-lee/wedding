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
# 그리드형: 첫 장은 4:3 대표, 나머지는 정사각 썸네일. 순서 = 그리드 순서 = 뷰어 순서.
ORDER = [
    # 첫 장 = 그리드 대표 (가로 4:3 전폭). 유일한 가로 컷.
    (A("_12"), "화이트 스튜디오 - 드레스 전신"),          # ← 가로 사진
    # 검정 배경 스튜디오
    (A("_16"), "검정 배경 스튜디오 - 신부 정면"),
    (A("_15"), "검정 배경 스튜디오 - 신랑"),
    # 화이트 스튜디오 (거울 / 케이크)
    (A("_04"), "화이트 스튜디오 - 거울 앞 신부"),
    (A("_05"), "화이트 스튜디오 - 거울 앞 두 사람"),
    (A("_03"), "화이트 스튜디오 - 케이크와 함께"),
    # 화이트 스튜디오 (레드 부케)
    (os.path.join(SRC, "KakaoTalk_20260909_213739064.png"), "화이트 스튜디오 - 레드 부케"),   # _13 교체본 (상단 검은 줄 제거)
    (A("_14"), "화이트 홀 - 머메이드 드레스"),
    # 아이보리 수트 + 옐로 드레스
    (B("_02"), "아이보리 수트 - 두 사람"),
    (B("_01"), "아이보리 수트 - 두 사람"),
    (B(""),    "아이보리 수트 - 신부"),
    (SOLO,     "아이보리 수트 - 신랑"),
    # 옐로 플라워
    # ※ assets/g13.jpg 는 지금 이 파일이 아니라 따로 받은 보정본으로 교체돼 있습니다.
    #    (앉은 컷). 다시 돌리면 아래 원본으로 되돌아가니 주의.
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

# 크롭 기준점 — 각 사진에서 얼굴(들)의 중심. 원본 대비 비율이라 해상도와 무관.
# macOS Vision 얼굴 인식으로 뽑은 값입니다. 이게 없으면 가운데를 그냥 잘라서
# 전신컷의 머리가 잘려 나갑니다. 사진을 바꾸면 이 값도 같이 고치세요.
#
# ※ 반드시 ORDER 의 원본(imgs/) 기준으로 재세요. assets/gNN.jpg 는 이미 2:3 으로
#    잘린 뒤라 좌표가 다릅니다. 아래 to_portrait 가 정규화 후 좌표로 알아서 바꿉니다.
#   재측정: swift tools/faces.swift imgs/*.png
FACE = [
    (0.569, 0.213), (0.508, 0.210), (0.435, 0.136), (0.259, 0.236), (0.342, 0.223),
    (0.482, 0.212), (0.750, 0.188), (0.678, 0.360), (0.553, 0.299), (0.491, 0.243),
    (0.479, 0.400), (0.495, 0.193), (0.520, 0.319), (0.423, 0.176), (0.511, 0.180),
    (0.569, 0.187), (0.514, 0.513), (0.504, 0.280), (0.402, 0.352), (0.559, 0.192),
]
assert len(FACE) == len(ORDER), "FACE 와 ORDER 개수가 다릅니다"

# 얼굴 무리의 중심이 크롭 위에서 이 지점에 오게 합니다. 0.5 면 얼굴이 정가운데라
# 머리 위 여백이 답답해 보여서, 위쪽 1/3 즈음에 둡니다.
HEADROOM = 0.36

# 세로 사진은 전부 이 비율로 맞춥니다. 원본이 2:3 부터 0.72:1 까지 제각각이라
# 뷰어에서 좌우로 넘길 때 사진 틀이 들쭉날쭉했습니다. 정수배(2k x 3k)로 잘라서
# 반올림 오차 없이 정확히 같은 비율로 떨어지게 합니다. 가로 사진(g01)은 제외.
PORTRAIT = (2, 3)

# 폭이 남아 잘라낼 때는 인물이 가운데 오도록 위치를 잡는데, 아래 두 장은
# 예외입니다. 거울 컷이라 왼쪽 거울 + 오른쪽 아웃포커스 인물로 일부러 비대칭
# 구도를 잡은 사진이어서, 가운데로 옮기면 구도가 무너집니다. (1부터 세는 번호)
NO_RECENTER = {4, 5}

COVER = os.path.join(SRC, "KakaoTalk_20260909_232050635.png")   # 표지 — 아치 컷 보정본 (신부측 추천)
COVER_CROP = (0.08, 0.0, 0.92, 1.0)          # (좌, 상, 우, 하) 비율. 보정본은 이미 타이트해서 좌우만 살짝
MAP_PDF = os.path.join(SRC, "[세인트 메리엘] 청첩장 약도 (1).pdf")


def save_jpg(im, path, max_w, quality=82):
    im = im.convert("RGB")
    if im.width > max_w:
        h = round(im.height * max_w / im.width)
        im = im.resize((max_w, h), Image.LANCZOS)
    # optimize+progressive: 화질은 그대로 두고 파일만 줄이는 무손실 재포장.
    # (assets/ 를 직접 손볼 때는 jpegtran -optimize -progressive 가 같은 일을 합니다)
    im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    return im.size, os.path.getsize(path)


def to_portrait(im, fx, fy, recenter):
    """세로 사진을 정확히 PORTRAIT 비율로 잘라내고, 새 사진 기준 얼굴 위치도 같이 돌려줍니다.
       폭이 남으면 인물을 가운데로(recenter), 높이가 남으면 머리가 잘리지 않게 위쪽으로."""
    num, den = PORTRAIT
    w, h = im.size
    k = min(w // num, h // den)
    cw, ch = num * k, den * k
    x = min(max(fx * w - cw / 2, 0), w - cw) if recenter else (w - cw) / 2
    y = min(max(fy * h - ch * HEADROOM, 0), h - ch)
    x, y = round(x), round(y)
    return im.crop((x, y, x + cw, y + ch)), ((fx * w - x) / cw, (fy * h - y) / ch)


total = 0
manifest = []
for i, (f, alt) in enumerate(ORDER, 1):
    name = f"g{i:02d}.jpg"
    src = Image.open(f).convert("RGB")
    fx, fy = FACE[i - 1]
    if src.height > src.width:                      # 세로 사진만 비율을 맞춥니다
        src, (fx, fy) = to_portrait(src, fx, fy, recenter=i not in NO_RECENTER)
    size, nbytes = save_jpg(src, os.path.join(OUT, name), 900)
    total += nbytes
    wide = size[0] > size[1]
    manifest.append((name, alt, wide))
    # 그리드 썸네일: 정사각 400px (레퍼런스와 동일). 첫 장은 4:3 대표 1200x900 도 추가
    # (fx, fy 는 위에서 정규화 후 좌표로 갱신된 값)
    def _crop(im, ratio):
        """얼굴이 가운데(세로는 위 1/3) 오도록 ratio 비율로 잘라냅니다."""
        w, h = im.size
        cw, ch = (w, w / ratio) if w / h <= ratio else (h * ratio, h)
        x = min(max(fx * w - cw / 2, 0), w - cw)
        y = min(max(fy * h - ch * HEADROOM, 0), h - ch)
        return im.crop((round(x), round(y), round(x + cw), round(y + ch)))
    _crop(src, 1).resize((400, 400), Image.LANCZOS).save(os.path.join(OUT, f"t{i:02d}.jpg"), "JPEG", quality=82, optimize=True)
    total += os.path.getsize(os.path.join(OUT, f"t{i:02d}.jpg"))
    if i == 1:
        _crop(src, 4 / 3).resize((1200, 900), Image.LANCZOS).save(os.path.join(OUT, "wide.jpg"), "JPEG", quality=84, optimize=True)
        total += os.path.getsize(os.path.join(OUT, "wide.jpg"))
    print(f"{name}  {size[0]}x{size[1]:<5} {nbytes/1024:6.0f}KB  {'[가로]' if wide else ''}  {alt}")

# 표지 (EXIF 회전 반영 후 크롭)
from PIL import ImageOps
_c = ImageOps.exif_transpose(Image.open(COVER))
_l, _t, _r, _b = COVER_CROP
_c = _c.crop((int(_l*_c.width), int(_t*_c.height), int(_r*_c.width), int(_b*_c.height)))
size, nbytes = save_jpg(_c, os.path.join(OUT, "cover.jpg"), 1100, 86)
total += nbytes
print(f"cover.jpg  {size[0]}x{size[1]}  {nbytes/1024:.0f}KB")

# 카카오톡 공유 미리보기 (1200x630, 사진을 크림색 배경에 레터박스)
og = Image.new("RGB", (1200, 630), "#fbfaf7")
c = _c.convert("RGB")
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
print("-- index.html #grid 안에 (그리드 순서 = ORDER 순서) --")
for i, (name, alt, wide) in enumerate(manifest):
    cls = "ph wide" if i == 0 else "ph"
    src = "assets/wide.jpg" if i == 0 else f"assets/t{i+1:02d}.jpg"
    print(f'<button class="{cls}" type="button" data-full="assets/{name}" aria-label="웨딩 사진 {i+1}번, 크게 보기"><img src="{src}" alt="" loading="lazy"></button>')
