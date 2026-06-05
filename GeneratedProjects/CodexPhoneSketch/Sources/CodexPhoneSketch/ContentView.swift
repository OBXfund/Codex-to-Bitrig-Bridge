import SwiftUI

public struct ContentView: View {
    public init() {}

    public var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 16) {
                Text("Codex Phone Sketch")
                    .font(.largeTitle.weight(.bold))
                Text("A small sketchpad app started from Codex on iPhone for Bitrig Remote.")
                    .font(.body)
                    .foregroundStyle(.secondary)
                Spacer()
            }
            .padding()
            .navigationTitle("Codex Phone Sketch")
        }
    }
}
