// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "CodexPhoneSketch",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "CodexPhoneSketch", targets: ["CodexPhoneSketch"])
    ],
    targets: [
        .target(name: "CodexPhoneSketch")
    ]
)
