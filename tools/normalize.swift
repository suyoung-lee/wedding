import Foundation
import Vision
import ImageIO
import CoreGraphics
import UniformTypeIdentifiers

// 세로 사진을 정확히 같은 비율(2:3)로 잘라 맞춥니다.
//   normalize <src> <dst> <ratio> <maxW> <quality> [--no-recenter]
// 가로로 남는 폭을 잘라낼 때는 인물(얼굴 무리)이 가운데 오게 위치를 잡고,
// 세로로 잘라낼 때는 머리가 잘리지 않게 얼굴을 위 36% 지점에 둡니다.
// --no-recenter: 가로 위치를 옮기지 않고 가운데에서 자릅니다 (거울 컷처럼
//                일부러 비대칭으로 잡은 구도를 지킬 때).

let a = CommandLine.arguments
let src = a[1], dst = a[2]
// 비율은 정수 두 개(2:3)로 받습니다. 반올림 오차 없이 정확히 같은 비율로
// 떨어뜨리려면 크롭 크기가 num/den 의 정수배여야 합니다.
let num = Double(a[3])!, den = Double(a[4])!
let maxW = Double(a[5])!, q = Double(a[6])!
let ratio = num / den
let recenter = !a.contains("--no-recenter")
let HEADROOM = 0.36

guard let isrc = CGImageSourceCreateWithURL(URL(fileURLWithPath: src) as CFURL, nil),
      let img = CGImageSourceCreateImageAtIndex(isrc, 0, nil) else { fatalError("read \(src)") }
let W = Double(img.width), H = Double(img.height)

// 원본 안에 들어가는 최대 num:den 사각형 — 정수배로 딱 떨어지게 잡습니다.
let k = min((W / num).rounded(.down), (H / den).rounded(.down))
let cw = num * k, ch = den * k

let req = VNDetectFaceRectanglesRequest()
try? VNImageRequestHandler(cgImage: img, options: [:]).perform([req])
let faces = req.results ?? []

var x0 = (W - cw) / 2, y0 = (H - ch) / 2
var note = "얼굴없음-가운데"
if !faces.isEmpty {
    var minX = W, maxX = 0.0, minY = H, maxY = 0.0
    for f in faces {
        let b = f.boundingBox
        minX = min(minX, b.minX * W);        maxX = max(maxX, b.maxX * W)
        minY = min(minY, (1 - b.maxY) * H);  maxY = max(maxY, (1 - b.minY) * H)
    }
    let fx = (minX + maxX) / 2, fy = (minY + maxY) / 2
    if recenter { x0 = min(max(fx - cw / 2, 0), W - cw) }
    y0 = min(max(fy - ch * HEADROOM, 0), H - ch)
    note = "얼굴\(faces.count)개" + (recenter ? "" : " (가로 고정)")
}

let rect = CGRect(x: x0.rounded(), y: y0.rounded(), width: cw.rounded(), height: ch.rounded())
guard let cropped = img.cropping(to: rect) else { fatalError("crop \(src)") }

// 확대는 하지 않습니다 (없는 해상도를 만들어내지 않음).
// 줄일 때도 정수배를 유지해 비율이 흐트러지지 않게 합니다.
var ok = k
if cw > maxW { ok = (maxW / num).rounded(.down) }
let outW = num * ok, outH = den * ok

let cs = CGColorSpaceCreateDeviceRGB()
guard let ctx = CGContext(data: nil, width: Int(outW), height: Int(outH), bitsPerComponent: 8,
                          bytesPerRow: 0, space: cs,
                          bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue) else { fatalError("ctx") }
ctx.interpolationQuality = .high
ctx.draw(cropped, in: CGRect(x: 0, y: 0, width: outW, height: outH))
guard let out = ctx.makeImage(),
      let d = CGImageDestinationCreateWithURL(URL(fileURLWithPath: dst) as CFURL,
                                              UTType.jpeg.identifier as CFString, 1, nil)
else { fatalError("write \(dst)") }
CGImageDestinationAddImage(d, out, [kCGImageDestinationLossyCompressionQuality: q] as CFDictionary)
CGImageDestinationFinalize(d)

let name = (dst as NSString).lastPathComponent
print(String(format: "%@  %.0fx%.0f (%.4f) -> 크롭 %.0f,%.0f %.0fx%.0f -> %.0fx%.0f (%.4f)  [%@]",
             name, W, H, W/H, rect.origin.x, rect.origin.y, cw, ch, outW, outH, outW/outH, note))

// imgs/ 원본 없이 assets/ 만으로 세로 사진 비율을 다시 맞출 때 씁니다.
// (원본이 있으면 build_assets.py 의 to_portrait 가 같은 일을 합니다 — 같은 계산식)
//   swift tools/normalize.swift assets/g09.jpg out.jpg 2 3 900 0.85
