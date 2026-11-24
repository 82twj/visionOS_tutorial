// Prepares a raw screenshot for the tutorial: optional crop, transparent rounded
// window corners, and an Apple-style dimming layer that leaves the regions a step
// talks about at full brightness.
//
//   swift Scripts/process_capture.swift <input.png> <output.png> \
//       [--crop x,y,w,h] [--radius r] [--dim 0.5] [--spot x,y,w,h[,r]]... [--scale-to width]
//
// All coordinates are pixels with the origin at the top-left corner. --spot is
// relative to the cropped image.

import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

func numbers(_ text: String) -> [CGFloat] {
    text.split(separator: ",").map { part in
        guard let value = Double(part) else { fail("not a number: \(part)") }
        return CGFloat(value)
    }
}

var arguments = Array(CommandLine.arguments.dropFirst())
guard arguments.count >= 2 else { fail("usage: process_capture.swift input output [options]") }
let inputPath = arguments.removeFirst()
let outputPath = arguments.removeFirst()

var crop: CGRect?
var radius: CGFloat = 0
var dim: CGFloat = 0.5
var spots: [(CGRect, CGFloat)] = []
var scaleToWidth: CGFloat?

while !arguments.isEmpty {
    let option = arguments.removeFirst()
    guard !arguments.isEmpty else { fail("missing value for \(option)") }
    let value = arguments.removeFirst()
    switch option {
    case "--crop":
        let n = numbers(value)
        guard n.count == 4 else { fail("--crop needs x,y,w,h") }
        crop = CGRect(x: n[0], y: n[1], width: n[2], height: n[3])
    case "--radius":
        radius = numbers(value)[0]
    case "--dim":
        dim = numbers(value)[0]
    case "--spot":
        let n = numbers(value)
        guard n.count == 4 || n.count == 5 else { fail("--spot needs x,y,w,h[,r]") }
        spots.append((CGRect(x: n[0], y: n[1], width: n[2], height: n[3]), n.count == 5 ? n[4] : 12))
    case "--scale-to":
        scaleToWidth = numbers(value)[0]
    default:
        fail("unknown option \(option)")
    }
}

guard let source = CGImageSourceCreateWithURL(URL(fileURLWithPath: inputPath) as CFURL, nil),
      var image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
    fail("cannot read \(inputPath)")
}

if let crop {
    guard let cropped = image.cropping(to: crop) else { fail("crop is outside the image") }
    image = cropped
}

let sourceSize = CGSize(width: image.width, height: image.height)
let factor = scaleToWidth.map { $0 / sourceSize.width } ?? 1
let size = CGSize(
    width: (sourceSize.width * factor).rounded(),
    height: (sourceSize.height * factor).rounded()
)

guard let context = CGContext(
    data: nil,
    width: Int(size.width),
    height: Int(size.height),
    bitsPerComponent: 8,
    bytesPerRow: 0,
    space: CGColorSpace(name: CGColorSpace.sRGB)!,
    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
) else {
    fail("cannot create a drawing context")
}

// Work in top-left pixel coordinates of the cropped source.
context.translateBy(x: 0, y: size.height)
context.scaleBy(x: factor, y: -factor)
context.interpolationQuality = .high

let bounds = CGRect(origin: .zero, size: sourceSize)
if radius > 0 {
    context.addPath(CGPath(roundedRect: bounds, cornerWidth: radius, cornerHeight: radius, transform: nil))
    context.clip()
}

context.saveGState()
context.translateBy(x: 0, y: sourceSize.height)
context.scaleBy(x: 1, y: -1)
context.draw(image, in: bounds)
context.restoreGState()

if !spots.isEmpty {
    let overlay = CGMutablePath()
    overlay.addRect(bounds)
    for (rect, corner) in spots {
        let clamped = rect.intersection(bounds)
        let limit = min(corner, min(clamped.width, clamped.height) / 2)
        overlay.addPath(CGPath(roundedRect: clamped, cornerWidth: limit, cornerHeight: limit, transform: nil))
    }
    context.addPath(overlay)
    context.setFillColor(CGColor(red: 0, green: 0, blue: 0, alpha: dim))
    context.fillPath(using: .evenOdd)
}

guard let result = context.makeImage(),
      let destination = CGImageDestinationCreateWithURL(
          URL(fileURLWithPath: outputPath) as CFURL,
          UTType.png.identifier as CFString,
          1,
          nil
      ) else {
    fail("cannot write \(outputPath)")
}
CGImageDestinationAddImage(destination, result, nil)
guard CGImageDestinationFinalize(destination) else { fail("cannot write \(outputPath)") }
print("\(outputPath): \(result.width)x\(result.height)")
