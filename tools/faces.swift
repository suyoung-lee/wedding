import Foundation
import Vision
import ImageIO
import CoreGraphics

for path in CommandLine.arguments.dropFirst() {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
          let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
        print("\(path)\tERROR"); continue
    }
    let w = CGFloat(img.width), h = CGFloat(img.height)
    let req = VNDetectFaceRectanglesRequest()
    try? VNImageRequestHandler(cgImage: img, options: [:]).perform([req])
    let faces = (req.results ?? [])
    var parts: [String] = []
    for f in faces {
        let b = f.boundingBox            // normalized, origin bottom-left
        let x = b.minX * w
        let y = (1 - b.maxY) * h         // top-left origin
        parts.append(String(format: "%.0f,%.0f,%.0f,%.0f", x, y, b.width * w, b.height * h))
    }
    print("\(path)\t\(Int(w))x\(Int(h))\t\(faces.count)\t\(parts.joined(separator: " "))")
}

// build_assets.py 의 FACE 표를 다시 뽑을 때 씁니다.
//   swift tools/faces.swift assets/g*.jpg
// 출력: 파일  너비x높이  얼굴수  x,y,w,h ...   (좌상단 기준 픽셀)
