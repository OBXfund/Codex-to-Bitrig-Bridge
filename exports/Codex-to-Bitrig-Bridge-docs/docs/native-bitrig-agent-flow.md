# Native Bitrig Agent Flow

This is the reliable path when Bitrig Remote does not show a project created only through file automation.

The goal is to let Bitrig create the native Agent project ID, then use the bridge script to populate that accepted project with the correct app, metadata, name, and index entry.

## When To Use This

Use this flow when:

- `verify` passes but Bitrig Remote does not show the project
- Bitrig desktop does not show the project in the Agent list
- Bitrig deletes the project row from `Projects.json` after launch
- the project was created by manually writing files under `~/Library/Bitrig`
- Bitrig created a project named `New Project` instead of the intended Agent name

## Step 1: Prepare Or Build The Local Codex Project

For a new project:

```bash
python3 tools/codex_iphone_to_bitrig.py prepare \
  --new "Project Name" \
  --summary "Short app idea" \
  --agent-name ProjectNameAgent \
  --json
```

For an existing local iOS project:

```bash
python3 tools/codex_iphone_to_bitrig.py prepare \
  --project /absolute/path/to/project \
  --agent-name ProjectNameAgent \
  --json
```

This creates a prompt under:

```text
<bridge-workspace>/.bitrig-bridge/ProjectNameAgent.bitrig-agent-prompt.txt
```

## Step 2: Open Bitrig's Native Agent Composer

In Bitrig desktop:

1. Open the project list.
2. Select `Agent`.
3. Click the `+` button.
4. Choose `New Project...`.
5. Select iPhone as the target platform.
6. Paste the generated Agent prompt.
7. Submit the prompt.

Bitrig should create a real native Agent project. It may initially display as `New Project`; that is acceptable because the adoption step renames it.

## Step 3: Wait For Bitrig To Create A Project ID

After submitting the prompt, wait until Bitrig creates a new project row.

Find the newest project:

```bash
python3 - <<'PY'
import json
from pathlib import Path

projects = json.loads((Path.home() / "Library/Bitrig/Projects.json").read_text())
rows = sorted(
    projects.items(),
    key=lambda item: item[1].get("updatedAt") or item[1].get("createdAt") or "",
    reverse=True,
)
for project_id, project in rows[:10]:
    print(project_id, project.get("name"), project.get("updatedAt"))
PY
```

Look for a new row with a current timestamp. It may be named `New Project`.

Save its ID:

```text
<bitr-created-project-id>
```

## Step 4: Adopt The Bitrig-Created Project ID

Run:

```bash
python3 tools/codex_iphone_to_bitrig.py automate \
  --project /absolute/path/to/project \
  --agent-name ProjectNameAgent \
  --project-id <bitr-created-project-id> \
  --overwrite \
  --json
```

This rewrites the Bitrig-created project with:

- the correct project name
- the correct iPhone application target
- the correct bundle identifier
- `App/App.swift`
- `App/ContentView.swift`
- `BitrigAgent.json`
- `Project.json`
- Bitrig metadata
- the App Intents Agent index row

If the source project has:

```text
Sources/<SourceProjectName>/ContentView.swift
```

the bridge copies that file into:

```text
~/Library/Bitrig/Projects/<bitr-created-project-id>/App/ContentView.swift
```

If the source project does not have a compatible `ContentView.swift`, the bridge creates a small SwiftUI shell showing the source project name and path.

## Step 5: Let Bitrig Build

If Bitrig is still open in the newly created project, it should notice or retain the rewritten files. If needed, ask Bitrig's Agent chat to build:

```text
Build the project and fix any Swift or project-generation errors.
```

A successful result should say the build succeeded with no diagnostics.

The preview should show the expected app, not an empty starter shell.

## Step 6: Return To The Agent List

Close or back out of the project window so Bitrig returns to the Agent project list.

This matters because Bitrig flushes and refreshes project index state when returning to the list.

## Step 7: Verify Locally

Run:

```bash
python3 tools/codex_iphone_to_bitrig.py verify \
  --name "ProjectNameAgent" \
  --source-path /absolute/path/to/project \
  --json
```

Expected checks:

```text
projectsJsonEntry: OK
iPhoneEnabled: OK
projectFolderExists: OK
projectJsonExists: OK
projectJsonHasIosApp: OK
bitrigAgentJsonExists: OK
indexHasAgentEntry: OK
sourcePathMatches: OK
```

## Step 8: Verify In Bitrig Desktop

Bitrig desktop must show the project in the Agent list.

Confirm:

- the name is `ProjectNameAgent`
- the platform is iPhone
- it appears above older projects if recently updated
- opening it shows the expected preview

## Step 9: Verify In Bitrig Remote

On iPhone:

1. Open Bitrig Remote.
2. Refresh the Agent list.
3. Confirm `ProjectNameAgent` appears.
4. Open it.
5. Confirm the expected app preview or conversation is available.

Do not call the workflow complete until the project appears in Bitrig Remote.

## Example: Existing SwiftUI Game

Assume:

```text
Source project: /absolute/path/to/GeneratedProjects/NeonByteRush
Agent name: NeonByteRushAgent
Bitrig-created project ID: 22f02a83-1fe3-40aa-98cf-ccb3a2f8eb16
```

Adopt it:

```bash
python3 tools/codex_iphone_to_bitrig.py automate \
  --project /absolute/path/to/GeneratedProjects/NeonByteRush \
  --agent-name NeonByteRushAgent \
  --project-id 22f02a83-1fe3-40aa-98cf-ccb3a2f8eb16 \
  --overwrite \
  --json
```

Verify:

```bash
python3 tools/codex_iphone_to_bitrig.py verify \
  --name "NeonByteRushAgent" \
  --source-path /absolute/path/to/GeneratedProjects/NeonByteRush \
  --json
```

Expected final state:

- Bitrig desktop Agent list shows `NeonByteRushAgent`
- Bitrig Remote Agent list shows `NeonByteRushAgent`
- the Bitrig preview shows the playable SwiftUI app
- build succeeds with no diagnostics
