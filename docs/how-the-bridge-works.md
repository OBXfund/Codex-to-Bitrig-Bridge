# How The Bridge Works

This document explains the moving parts behind the Codex-to-Bitrig Remote workflow.

## The Actors

There are four separate systems involved:

1. Codex creates or edits a local iOS project.
2. The bridge script prepares Bitrig-compatible Agent metadata.
3. Bitrig desktop creates and builds native Agent projects.
4. Bitrig Remote lists native Agent projects exposed by Bitrig desktop.

The reliable workflow uses all four. Skipping Bitrig desktop's native Agent creation can leave a project invisible to Bitrig Remote.

## Local Codex Project

A Codex-created seed project is a small Swift package:

```text
GeneratedProjects/<ProjectName>/
  Package.swift
  CodexIPhoneProject.json
  Sources/
    <ProjectName>/
      <ProjectName>App.swift
      ContentView.swift
```

This project is useful because:

- it gives Codex a stable local source tree
- it can compile independently with SwiftPM
- it has a simple `ContentView.swift` that can be copied into Bitrig
- it records the requested project name and summary

For existing apps, the bridge uses the existing project path instead of creating a seed project.

## The Bridge Script

The main script is:

```text
tools/codex_iphone_to_bitrig.py
```

It has three commands:

```bash
prepare
automate
verify
```

### `prepare`

`prepare` resolves a source project and generates a Bitrig Agent prompt.

It writes:

```text
.bitrig-bridge/<AgentName>.bitrig-agent-prompt.txt
.bitrig-bridge/<AgentName>.json
```

Use `prepare` when you want to paste a prompt into Bitrig's Agent New Project composer.

### `automate`

`automate` creates or rewrites Bitrig Agent project state.

It can:

- create a new Codex seed project with `--new`
- use an existing source project with `--project`
- enforce a visible Agent name with `--agent-name`
- adopt a Bitrig-created project ID with `--project-id`
- replace local Bitrig project files with `--overwrite`
- restart Bitrig and rewrite after launch cleanup with `--refresh-bitrig`

The most important flag is:

```bash
--project-id <bitr-created-project-id>
```

Use it when Bitrig created the project through its native UI. That makes the bridge populate an accepted Bitrig project instead of inventing a project ID that Bitrig Remote may ignore.

### `verify`

`verify` checks whether the project looks like a native Bitrig Agent project.

It checks:

- Bitrig project catalog
- iPhone platform support
- project folder existence
- `Project.json`
- iOS application target
- `BitrigAgent.json`
- App Intents Agent index
- source path match

Verification is necessary but not sufficient. The project also must appear in Bitrig desktop and Bitrig Remote.

## Bitrig Project Files

A Bitrig Agent project lives under:

```text
~/Library/Bitrig/Projects/<project-id>/
```

The bridge writes:

```text
Project.json
BitrigAgent.json
App/App.swift
App/ContentView.swift
App/Assets.xcassets/Contents.json
```

### `Project.json`

`Project.json` describes the Bitrig project and target.

The bridge sets:

- project name
- iOS application target
- deployment target
- display name
- bundle identifier
- source folder
- iPhone-only device family

### `BitrigAgent.json`

`BitrigAgent.json` marks the project as an Agent project and records the source project.

Example:

```json
{
  "kind": "agent-project",
  "name": "ProjectNameAgent",
  "sourceProjectName": "ProjectName",
  "sourceProjectPath": "/absolute/path/to/project",
  "platforms": ["iPhone"],
  "projectSummary": "Native Bitrig Agent project for ProjectName."
}
```

### `App/ContentView.swift`

If the source project has:

```text
Sources/<SourceProjectName>/ContentView.swift
```

the bridge copies it into:

```text
App/ContentView.swift
```

Otherwise, the bridge writes a small SwiftUI shell that identifies the source project.

## Bitrig Metadata

Bitrig metadata lives under:

```text
~/Library/Bitrig/Metadata/<project-id>/
```

The bridge writes:

```text
manifest.json
sessions/<conversation-id>.json
conversations/<conversation-id>.jsonl
.metadata_never_index
```

This gives Bitrig enough project conversation metadata to show a recognizable Agent project history.

## Project Catalog

Bitrig's project catalog is:

```text
~/Library/Bitrig/Projects.json
```

The bridge adds or updates a row with:

- project ID
- project name
- active conversation ID
- supported platforms
- creation and update times

Bitrig can rewrite this file on launch. If it removes your project, use native Bitrig Agent creation and adoption.

## App Intents Agent Index

Bitrig Remote and App Intents depend on an index in:

```text
~/Library/Preferences/app.bitrig.bitrigapp.plist
```

The key is:

```text
app.bitrig.AppIntents.ProjectIndex
```

The bridge inserts:

```json
{
  "id": "<project-id>",
  "name": "ProjectNameAgent",
  "updatedAt": 802348296.871888,
  "source": "agent"
}
```

If this index does not contain the project with `source: agent`, Bitrig Remote may not show it.

## Why File-Only Automation Can Fail

File-only automation can create a project that passes local checks but is invisible to Bitrig Remote.

Reasons:

- Bitrig may rebuild `Projects.json` during launch.
- Bitrig may reject project IDs it did not create.
- Bitrig Remote may rely on an in-memory or App Intents index.
- Bitrig Agent state may require conversation metadata.
- Bitrig may need to build the project before it treats it as valid.

The reliable fix is:

1. Create the project through Bitrig desktop's native Agent New Project UI.
2. Capture the Bitrig-created project ID.
3. Adopt that ID with the bridge script.
4. Build in Bitrig.
5. Return to the Agent list.
6. Confirm visibility in Bitrig Remote.

## Why Playwright Is Usually Not The Right Tool Here

Playwright automates browser surfaces. Bitrig desktop is a native macOS app.

Playwright can help only if:

- Bitrig exposes a browser debug endpoint
- the target UI is HTML or Electron with accessible browser automation
- Node/npm and Playwright are installed

For native Bitrig desktop flows, use:

- Bitrig's own Agent New Project UI
- macOS UI automation when needed
- the bridge script for file and metadata adoption

## The End-To-End Success Condition

The workflow is complete only when:

- the Bitrig-created project ID is adopted
- `verify` passes
- Bitrig desktop Agent list shows the project
- Bitrig preview builds successfully
- Bitrig Remote Agent list shows the project

Anything less is partial.
