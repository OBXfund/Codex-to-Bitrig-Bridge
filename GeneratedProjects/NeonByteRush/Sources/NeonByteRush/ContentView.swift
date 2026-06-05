import SwiftUI

public struct ContentView: View {
    @StateObject private var game = ByteRushGame()

    public init() {}

    public var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color(red: 0.02, green: 0.02, blue: 0.08), .black],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                HudView(game: game)
                    .padding(.horizontal, 18)
                    .padding(.top, 12)
                    .padding(.bottom, 8)

                GameField(game: game)
                    .padding(.horizontal, 12)
                    .padding(.bottom, 10)

                ArcadeControls(game: game)
                    .padding(.horizontal, 18)
                    .padding(.bottom, 18)
            }

            if game.phase != .running {
                StartOverlay(game: game)
            }
        }
        .preferredColorScheme(.dark)
        .onReceive(game.clock) { date in
            game.tick(at: date)
        }
    }
}

private struct HudView: View {
    @ObservedObject var game: ByteRushGame

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("NEON BYTE RUSH")
                    .font(.system(size: 17, weight: .black, design: .monospaced))
                    .foregroundStyle(.cyan)
                Text("WAVE \(game.wave)")
                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.72))
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 2) {
                Text(game.score.formatted())
                    .font(.system(size: 24, weight: .black, design: .monospaced))
                    .foregroundStyle(.white)
                    .contentTransition(.numericText())
                HStack(spacing: 6) {
                    ForEach(0..<3, id: \.self) { index in
                        RoundedRectangle(cornerRadius: 2)
                            .fill(index < game.shields ? Color.mint : Color.white.opacity(0.18))
                            .frame(width: 18, height: 7)
                    }
                }
            }
        }
    }
}

private struct GameField: View {
    @ObservedObject var game: ByteRushGame

    var body: some View {
        GeometryReader { proxy in
            let size = proxy.size

            ZStack {
                PixelGrid()

                ForEach(game.shards) { shard in
                    Diamond()
                        .fill(Color.yellow)
                        .shadow(color: .yellow, radius: 8)
                        .frame(width: shard.size * size.width, height: shard.size * size.width)
                        .position(x: shard.x * size.width, y: shard.y * size.height)
                }

                ForEach(game.blocks) { block in
                    BlockView(block: block)
                        .frame(width: block.size * size.width, height: block.size * size.width)
                        .position(x: block.x * size.width, y: block.y * size.height)
                }

                ByteRunner(isBoosting: game.isBoosting)
                    .frame(width: 46, height: 38)
                    .position(x: game.playerX * size.width, y: size.height * 0.84)
                    .shadow(color: .cyan, radius: game.isBoosting ? 18 : 10)
            }
            .clipShape(RoundedRectangle(cornerRadius: 6))
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color.cyan.opacity(0.45), lineWidth: 2)
            )
            .contentShape(Rectangle())
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { value in
                        game.setPlayerX(value.location.x / max(size.width, 1))
                    }
            )
        }
        .aspectRatio(0.62, contentMode: .fit)
    }
}

private struct PixelGrid: View {
    var body: some View {
        Canvas { context, size in
            context.fill(Path(CGRect(origin: .zero, size: size)), with: .color(.black.opacity(0.8)))

            var path = Path()
            let cell: CGFloat = 24
            var x: CGFloat = 0
            while x <= size.width {
                path.move(to: CGPoint(x: x, y: 0))
                path.addLine(to: CGPoint(x: x, y: size.height))
                x += cell
            }

            var y: CGFloat = 0
            while y <= size.height {
                path.move(to: CGPoint(x: 0, y: y))
                path.addLine(to: CGPoint(x: size.width, y: y))
                y += cell
            }

            context.stroke(path, with: .color(.cyan.opacity(0.14)), lineWidth: 1)

            var centerLine = Path()
            centerLine.move(to: CGPoint(x: size.width * 0.5, y: 0))
            centerLine.addLine(to: CGPoint(x: size.width * 0.5, y: size.height))
            context.stroke(centerLine, with: .color(.pink.opacity(0.26)), lineWidth: 2)
        }
    }
}

private struct BlockView: View {
    let block: ByteRushGame.Block

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 4)
                .fill(block.kind.color.opacity(0.9))
            RoundedRectangle(cornerRadius: 2)
                .stroke(.white.opacity(0.55), lineWidth: 2)
                .padding(5)
            if block.kind == .splitter {
                Rectangle()
                    .fill(.black.opacity(0.55))
                    .frame(width: 5)
            }
        }
        .shadow(color: block.kind.color, radius: 8)
    }
}

private struct ByteRunner: View {
    let isBoosting: Bool

    var body: some View {
        ZStack {
            Capsule()
                .fill(Color.cyan)
                .frame(width: 42, height: 22)
            Rectangle()
                .fill(Color.black)
                .frame(width: 12, height: 8)
                .offset(x: 7)
            Rectangle()
                .fill(isBoosting ? Color.orange : Color.mint)
                .frame(width: 10, height: 26)
                .offset(x: -20)
            Rectangle()
                .fill(Color.white)
                .frame(width: 4, height: 4)
                .offset(x: 16, y: -2)
        }
    }
}

private struct Diamond: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: rect.midX, y: rect.minY))
        path.addLine(to: CGPoint(x: rect.maxX, y: rect.midY))
        path.addLine(to: CGPoint(x: rect.midX, y: rect.maxY))
        path.addLine(to: CGPoint(x: rect.minX, y: rect.midY))
        path.closeSubpath()
        return path
    }
}

private struct ArcadeControls: View {
    @ObservedObject var game: ByteRushGame

    var body: some View {
        HStack(spacing: 14) {
            ControlButton(symbol: "◀") {
                game.nudge(-0.11)
            }

            Button {
                game.toggleBoost()
            } label: {
                Circle()
                    .fill(game.isBoosting ? Color.orange : Color.pink)
                    .frame(width: 66, height: 66)
                    .overlay(
                        Circle()
                            .stroke(.white.opacity(0.65), lineWidth: 3)
                            .padding(7)
                    )
                    .shadow(color: game.isBoosting ? .orange : .pink, radius: 12)
            }
            .buttonStyle(.plain)
            .disabled(game.phase != .running)

            ControlButton(symbol: "▶") {
                game.nudge(0.11)
            }
        }
    }
}

private struct ControlButton: View {
    let symbol: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(symbol)
                .font(.system(size: 28, weight: .black, design: .monospaced))
                .foregroundStyle(.white)
                .frame(width: 72, height: 58)
                .background(Color.white.opacity(0.09), in: RoundedRectangle(cornerRadius: 6))
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.cyan.opacity(0.5), lineWidth: 2)
                )
        }
        .buttonStyle(.plain)
    }
}

private struct StartOverlay: View {
    @ObservedObject var game: ByteRushGame

    var body: some View {
        ZStack {
            Color.black.opacity(0.72)
                .ignoresSafeArea()

            VStack(spacing: 18) {
                Text("NEON\nBYTE\nRUSH")
                    .font(.system(size: 52, weight: .black, design: .monospaced))
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.white)
                    .shadow(color: .cyan, radius: 12)

                if game.phase == .gameOver {
                    Text("SCORE \(game.score.formatted())")
                        .font(.system(size: 20, weight: .bold, design: .monospaced))
                        .foregroundStyle(.yellow)
                }

                Button {
                    game.start()
                } label: {
                    Text(game.phase == .ready ? "PLAY" : "RETRY")
                        .font(.system(size: 22, weight: .black, design: .monospaced))
                        .foregroundStyle(.black)
                        .frame(width: 168, height: 54)
                        .background(Color.mint, in: RoundedRectangle(cornerRadius: 6))
                        .shadow(color: .mint, radius: 14)
                }
                .buttonStyle(.plain)
            }
        }
    }
}

@MainActor
private final class ByteRushGame: ObservableObject {
    enum Phase {
        case ready
        case running
        case gameOver
    }

    enum BlockKind: CaseIterable {
        case blocker
        case splitter
        case surge

        var color: Color {
            switch self {
            case .blocker:
                return .pink
            case .splitter:
                return .purple
            case .surge:
                return .orange
            }
        }
    }

    struct Block: Identifiable {
        let id = UUID()
        var x: CGFloat
        var y: CGFloat
        var size: CGFloat
        var speed: CGFloat
        var kind: BlockKind
    }

    struct Shard: Identifiable {
        let id = UUID()
        var x: CGFloat
        var y: CGFloat
        var size: CGFloat
        var speed: CGFloat
    }

    let clock = Timer.publish(every: 1.0 / 60.0, on: .main, in: .common).autoconnect()

    @Published var phase: Phase = .ready
    @Published var score = 0
    @Published var wave = 1
    @Published var shields = 2
    @Published var playerX: CGFloat = 0.5
    @Published var isBoosting = false
    @Published var blocks: [Block] = []
    @Published var shards: [Shard] = []

    private var lastTick: Date?
    private var blockSpawn: TimeInterval = 0
    private var shardSpawn: TimeInterval = 0
    private var elapsed: TimeInterval = 0

    func start() {
        phase = .running
        score = 0
        wave = 1
        shields = 2
        playerX = 0.5
        isBoosting = false
        blocks.removeAll()
        shards.removeAll()
        elapsed = 0
        blockSpawn = 0.2
        shardSpawn = 0.8
        lastTick = nil
    }

    func tick(at date: Date) {
        guard phase == .running else {
            lastTick = date
            return
        }

        let delta = min(date.timeIntervalSince(lastTick ?? date), 0.05)
        lastTick = date
        elapsed += delta
        wave = max(1, Int(elapsed / 18) + 1)
        score += isBoosting ? 2 : 1

        spawn(delta: delta)
        move(delta: delta)
        resolveCollisions()
    }

    func setPlayerX(_ value: CGFloat) {
        playerX = min(max(value, 0.08), 0.92)
    }

    func nudge(_ amount: CGFloat) {
        guard phase == .running else { return }
        setPlayerX(playerX + amount)
    }

    func toggleBoost() {
        guard phase == .running else { return }
        isBoosting.toggle()
    }

    private func spawn(delta: TimeInterval) {
        blockSpawn -= delta
        shardSpawn -= delta

        if blockSpawn <= 0 {
            let lane = CGFloat(Int.random(in: 0...4)) / 4.0
            let kind = BlockKind.allCases.randomElement() ?? .blocker
            let speed = CGFloat(0.20 + Double(wave) * 0.025 + Double.random(in: 0...0.08))
            blocks.append(Block(x: 0.1 + lane * 0.8, y: -0.08, size: kind == .splitter ? 0.14 : 0.11, speed: speed, kind: kind))
            blockSpawn = max(0.32, 0.9 - Double(wave) * 0.06)
        }

        if shardSpawn <= 0 {
            shards.append(Shard(x: CGFloat.random(in: 0.12...0.88), y: -0.06, size: 0.055, speed: CGFloat(0.18 + Double(wave) * 0.015)))
            shardSpawn = Double.random(in: 0.55...1.15)
        }
    }

    private func move(delta: TimeInterval) {
        let boostMultiplier: CGFloat = isBoosting ? 1.35 : 1.0
        for index in blocks.indices {
            blocks[index].y += blocks[index].speed * CGFloat(delta) * boostMultiplier
            if blocks[index].kind == .surge {
                blocks[index].x += sin(CGFloat(elapsed * 4) + blocks[index].y * 8) * 0.002
            }
        }
        for index in shards.indices {
            shards[index].y += shards[index].speed * CGFloat(delta) * boostMultiplier
        }

        blocks.removeAll { $0.y > 1.12 }
        shards.removeAll { $0.y > 1.12 }
    }

    private func resolveCollisions() {
        let playerY: CGFloat = 0.84
        let hitRadius: CGFloat = 0.072

        var collected: Set<UUID> = []
        for shard in shards {
            if hypot(shard.x - playerX, shard.y - playerY) < hitRadius {
                score += 150
                collected.insert(shard.id)
                if score.isMultiple(of: 900) {
                    shields = min(3, shields + 1)
                }
            }
        }
        shards.removeAll { collected.contains($0.id) }

        var hits: Set<UUID> = []
        for block in blocks {
            let radius = hitRadius + block.size * 0.34
            if hypot(block.x - playerX, block.y - playerY) < radius {
                hits.insert(block.id)
                if shields > 0 {
                    shields -= 1
                    isBoosting = false
                    score = max(0, score - 100)
                } else {
                    phase = .gameOver
                }
            }
        }
        blocks.removeAll { hits.contains($0.id) }
    }
}
