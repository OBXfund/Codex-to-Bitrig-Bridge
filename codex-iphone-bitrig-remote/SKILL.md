---
name: codex-iphone-bitrig-remote
description: Use when the user wants to start an iPhone app project from Codex on iPhone or ChatGPT mobile and make it visible in Bitrig Remote on iPhone as a native Bitrig Agent project. Covers creating a new lightweight Codex iOS seed project, bridging an existing local Codex iOS project, avoiding Classic imports, directly creating native Agent state, and verifying Bitrig Remote-ready indexing.
---

# Codex iPhone Bitrig Remote

Use this skill when the user wants to start projects on Codex for iPhone and see them in Bitrig Remote on the same iPhone.

## Rule

Bitrig Remote needs a native Bitrig **Agent** project. Do not use Classic imports. The automated path must create a project folder, `Project.json`, `BitrigAgent.json`, a `Projects.json` entry, and an Agent index entry, then verify them.

## Default Workspace

Use the verified bridge workspace:

`/Users/lonniejordan/Documents/Bitrig Test`

The main wrapper is:

`/Users/lonniejordan/Documents/Bitrig Test/tools/codex_iphone_to_bitrig.py`

## Workflow

1. Get a specific visible project name. Reject generic names like `New Project`, `App`, `Untitled`, or `Agent`.
2. For a new phone-started idea, run:

```bash
python3 /Users/lonniejordan/Documents/Bitrig\ Test/tools/codex_iphone_to_bitrig.py automate --new "Project Name" --summary "Short app idea" --refresh-bitrig
```

3. For an existing local Codex iOS project, run:

```bash
python3 /Users/lonniejordan/Documents/Bitrig\ Test/tools/codex_iphone_to_bitrig.py automate --project /absolute/path/to/project --refresh-bitrig
```

4. `automate` runs verification internally. To re-check a project manually:

```bash
python3 /Users/lonniejordan/Documents/Bitrig\ Test/tools/codex_iphone_to_bitrig.py verify --name "AgentName"
```

Only call it complete when verification passes:

- `projectsJsonEntry`
- `iPhoneEnabled`
- `projectFolderExists`
- `projectJsonExists`
- `projectJsonHasIosApp`
- `bitrigAgentJsonExists`
- `indexHasAgentEntry`
- `sourcePathMatches` when a source path was provided

## Known Good Result

`CodexPhoneSketchAgent` was created and verified as a native Bitrig Agent project with iPhone support and a `source=agent` index row.

`NeonByteRushAgent` was created by `automate`, copied the playable SwiftUI `ContentView.swift` into native Bitrig Agent state, and verified with source-path matching.
