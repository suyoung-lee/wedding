"""인쇄용 QR코드 생성기.

    python qr/generate_qr.py

URL을 바꾸면 이미 인쇄된 종이 청첩장이 전부 무효가 되므로 URL은 고정입니다.
의존성: pip install segno
"""

import segno

# 종이 청첩장에 인쇄되는 값. 절대 변경 금지.
URL = "https://suyoung-lee.github.io/wedding/"

# 종이 위 QR 목표 크기(quiet zone 포함). 업체 요청에 따라 조정.
TARGET_MM = 30.0
BORDER = 4  # quiet zone, 모듈 단위. QR 규격 최소값이 4 — 줄이지 말 것.

qr = segno.make(URL, error="h", micro=False)

modules = qr.symbol_size(scale=1, border=BORDER)[0]  # quiet zone 포함 모듈 수
mm_per_module = TARGET_MM / modules

print(f"URL          : {URL}")
print(f"version      : {qr.version}  (error correction: H / 30%)")
print(f"modules      : {modules} x {modules}  (quiet zone {BORDER} 포함)")
print(f"target size  : {TARGET_MM}mm  ->  module {mm_per_module:.3f}mm")
if mm_per_module < 0.4:
    print("  ⚠ 모듈이 0.4mm 미만입니다. 인쇄 후 스캔이 불안정할 수 있으니 크기를 키우세요.")

# ── 벡터: 인쇄업체에 보낼 파일 ──
qr.save("qr/wedding-qr.svg", border=BORDER, scale=mm_per_module, unit="mm")
qr.save("qr/wedding-qr.pdf", border=BORDER, scale=mm_per_module * 72 / 25.4)  # pt
qr.save("qr/wedding-qr.eps", border=BORDER, scale=mm_per_module * 72 / 25.4)  # pt

# ── 래스터: 미리보기 / 벡터를 못 받는 업체용 ──
for dpi in (600, 1200):
    px_per_module = mm_per_module / 25.4 * dpi
    qr.save(f"qr/wedding-qr-{dpi}dpi.png", border=BORDER,
            scale=max(1, round(px_per_module)), dpi=dpi)

# 화면/웹 공유용
qr.save("qr/wedding-qr-web.png", border=BORDER, scale=12)

print("\n생성 완료: qr/*.svg .pdf .eps .png")
