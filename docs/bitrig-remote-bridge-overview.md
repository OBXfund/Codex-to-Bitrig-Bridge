# Bitrig Remote Bridge Overview

This guide explains how to create iPhone-first Codex projects that become visible in Bitrig Remote as native Bitrig Agent projects.

The important lesson is simple: Bitrig Remote does not reliably show projects created only by editing local catalog files. The reliable path is to let Bitrig create a native Agent project through its own Agent New Project flow, then use the bridge tooling to rename, populate, index, and verify that Bitrig-created project.

## What The Bridge Does

The bridge has three jobs:

1. Create or identify a local Codex iOS project.
2. Create or adopt a native Bitrig Agent project.
3. Verify the Bitrig Agent project is visible to Bitrig Remote.

The bridge script is:

```bash
python3 tools/codex_iphone_to_bitrig.py
```

It supports:

```bash
python3 tools/codex_iphone_to_bitrig.py prepare
python3 tools/codex_iphone_to_bitrig.py automate
python3 tools/codex_iphone_to_bitrig.py verify
```

## Directory Model

Use a bridge workspace with this structure:

```text
<bridge-workspace>/
  AGENTS.md
  README.md
  tools/
    codex_iphone_to_bitrig.py
  codex-iphone-bitrig-remote/
    SKILL.md
    agents/
      openai.yaml
    scripts/
      iphone_bitrig_remote.py
  GeneratedProjects/
  .bitrig-bridge/
```

Generated Codex seed projects go under:

```text
<bridge-workspace>/GeneratedProjects/<ProjectName>/
```

Bitrig native Agent projects live under:

```text
~/Library/Bitrig/Projects/<project-id>/
```

Bitrig metadata lives under:

```text
~/Library/Bitrig/Metadata/<project-id>/
```

The Bitrig project catalog is:

```text
~/Library/Bitrig/Projects.json
```

The App Intents project index is stored in:

```text
~/Library/Preferences/app.bitrig.bitrigapp.plist
```

## Why Native Agent Creation Matters

Bitrig Remote lists native Agent projects. A project must have more than a folder and a `Project.json` file.

A working Agent project needs:

- an entry in `~/Library/Bitrig/Projects.json`
- a project folder in `~/Library/Bitrig/Projects/<project-id>/`
- `Project.json`
- `BitrigAgent.json`
- `App/App.swift`
- `App/ContentView.swift`
- an iPhone application target in `Project.json`
- an Agent entry in the App Intents project index
- Bitrig-created project state when Bitrig Remote refuses manually inserted entries

The last point is the practical one. If Bitrig launches and removes your project from `Projects.json`, the project was not accepted as a native Bitrig project. Use the native Agent New Project composer, then adopt the Bitrig-created project ID.

## Recommended Flow

For a new project from an idea:

```bash
python3 tools/codex_iphone_to_bitrig.py automate \
  --new "Project Name" \
  --summary "Short app idea" \
  --refresh-bitrig
```

For an existing Codex iOS project:

```bash
python3 tools/codex_iphone_to_bitrig.py automate \
  --project /absolute/path/to/ExistingProject \
  --agent-name ExistingProjectAgent \
  --refresh-bitrig
```

If Bitrig Remote still does not show the project, use the native adoption flow:

1. Open Bitrig.
2. Choose `Agent`.
3. Click `+`.
4. Choose `New Project...`.
5. Select iPhone.
6. Paste a prompt that tells Bitrig to create the desired Agent project.
7. Let Bitrig create the project.
8. Find the new Bitrig project ID in `~/Library/Bitrig/Projects.json`.
9. Adopt that project ID:

```bash
python3 tools/codex_iphone_to_bitrig.py automate \
  --project /absolute/path/to/ExistingProject \
  --agent-name ExistingProjectAgent \
  --project-id <bitr-created-project-id> \
  --overwrite
```

10. Verify:

```bash
python3 tools/codex_iphone_to_bitrig.py verify \
  --name ExistingProjectAgent \
  --source-path /absolute/path/to/ExistingProject
```

## Verification Checks

The verifier must pass:

- `projectsJsonEntry`
- `iPhoneEnabled`
- `projectFolderExists`
- `projectJsonExists`
- `projectJsonHasIosApp`
- `bitrigAgentJsonExists`
- `indexHasAgentEntry`
- `sourcePathMatches` when a source path is provided

Passing these checks is necessary. The final acceptance test is still visual: the project must appear in Bitrig's Agent list and Bitrig Remote's Agent list.

## Naming Rules

Never use generic names:

- `New Project`
- `Project`
- `App`
- `Agent`
- `Untitled`

Use a specific visible name and keep it consistent everywhere:

```text
Source project: NeonByteRush
Agent project: NeonByteRushAgent
Bundle id: app.bitrig.agent.neonbyterushagent
Target name: NeonByteRushAgent
```

## What Not To Do

Do not create a Classic import when the goal is Bitrig Remote Agent visibility.

Do not rely only on editing:

- `Projects.json`
- App Intents project index
- project folders under `~/Library/Bitrig/Projects`

Those edits can pass a local file verifier and still fail in Bitrig Remote if Bitrig itself did not create or accept the project.

Do not call the task complete until:

1. Bitrig's desktop Agent list shows the project.
2. Bitrig Remote's Agent list shows the project.
3. The Bitrig preview builds or opens the expected app.
