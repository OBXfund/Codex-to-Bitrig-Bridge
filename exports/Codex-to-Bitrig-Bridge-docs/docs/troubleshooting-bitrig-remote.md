# Troubleshooting Bitrig Remote Agent Visibility

Use this guide when a Codex-created iPhone project does not appear in Bitrig Remote.

## Fast Diagnosis

Run local verification:

```bash
python3 tools/codex_iphone_to_bitrig.py verify \
  --name "ProjectNameAgent" \
  --source-path /absolute/path/to/project \
  --json
```

Then check the Bitrig desktop Agent list.

The meaningful states are:

| Local verification | Bitrig desktop Agent list | Bitrig Remote Agent list | Meaning |
| --- | --- | --- | --- |
| Fails | Missing | Missing | Local project state is incomplete. |
| Passes | Missing | Missing | File state exists, but Bitrig did not accept the project. |
| Passes | Visible | Missing | Bitrig Remote needs refresh or Bitrig has not flushed its Agent index. |
| Passes | Visible | Visible | Done. |

## Problem: `verify` Passes But Bitrig Remote Does Not Show The Project

This means local files are not enough.

Bitrig Remote may ignore a manually inserted project even if these are present:

- `~/Library/Bitrig/Projects.json`
- `~/Library/Bitrig/Projects/<project-id>/Project.json`
- `~/Library/Bitrig/Projects/<project-id>/BitrigAgent.json`
- App Intents project index row

Fix:

1. Create the project through Bitrig desktop's native `Agent -> New Project...` flow.
2. Let Bitrig create a real project ID.
3. Adopt that project ID:

```bash
python3 tools/codex_iphone_to_bitrig.py automate \
  --project /absolute/path/to/project \
  --agent-name ProjectNameAgent \
  --project-id <bitr-created-project-id> \
  --overwrite
```

4. Return to the Bitrig Agent list.
5. Refresh Bitrig Remote.

## Problem: Bitrig Deletes The Project From `Projects.json`

If the project appears in `Projects.json`, then disappears after Bitrig launches, Bitrig rejected the manually inserted project.

Confirm:

```bash
python3 - <<'PY'
import json
from pathlib import Path

projects = json.loads((Path.home() / "Library/Bitrig/Projects.json").read_text())
print([item for item in projects.items() if item[1].get("name") == "ProjectNameAgent"])
PY
```

Fix:

Use native creation plus adoption. Do not keep trying to patch only `Projects.json`.

## Problem: Bitrig Creates `New Project`

Bitrig's native New Project flow may initially create a project named `New Project`.

That is acceptable if it is a newly created native Agent project. Adopt its ID:

```bash
python3 tools/codex_iphone_to_bitrig.py automate \
  --project /absolute/path/to/project \
  --agent-name ProjectNameAgent \
  --project-id <new-project-id> \
  --overwrite
```

This renames the project, target, display name, bundle identifier, metadata, and Agent index row.

## Problem: Bitrig Cannot Read The Source Project Path

Bitrig's Agent may report that an external source path is blocked by macOS privacy.

This can happen even when Codex can read the file.

Fix:

Use the bridge script from Codex to copy the source files into the Bitrig-created project:

```bash
python3 tools/codex_iphone_to_bitrig.py automate \
  --project /absolute/path/to/project \
  --agent-name ProjectNameAgent \
  --project-id <bitr-created-project-id> \
  --overwrite
```

The bridge copies:

```text
/absolute/path/to/project/Sources/<SourceProjectName>/ContentView.swift
```

to:

```text
~/Library/Bitrig/Projects/<bitr-created-project-id>/App/ContentView.swift
```

## Problem: App Preview Shows An Empty Shell

Inspect:

```bash
sed -n '1,160p' ~/Library/Bitrig/Projects/<project-id>/App/ContentView.swift
```

If it contains:

```swift
EmptyView()
```

the Bitrig starter shell was not replaced.

Fix:

```bash
python3 tools/codex_iphone_to_bitrig.py automate \
  --project /absolute/path/to/project \
  --agent-name ProjectNameAgent \
  --project-id <project-id> \
  --overwrite
```

Then ask Bitrig to build again.

## Problem: Project Is In Desktop Agent List But Not In Bitrig Remote

Try:

1. Back out to the Bitrig desktop Agent list.
2. Wait a few seconds.
3. Refresh Bitrig Remote on iPhone.
4. Quit and reopen Bitrig Remote.
5. Confirm both devices are connected to the same Bitrig Remote session/account.

Then re-check the App Intents Agent index:

```bash
python3 - <<'PY'
import json
import plistlib
from pathlib import Path

prefs = Path.home() / "Library/Preferences/app.bitrig.bitrigapp.plist"
raw = plistlib.load(prefs.open("rb")).get("app.bitrig.AppIntents.ProjectIndex", b"[]")
index = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
print([entry for entry in index if entry.get("name") == "ProjectNameAgent"])
PY
```

If the index is missing the project, rerun adoption with the Bitrig-created project ID.

## Problem: Playwright Does Not Work

Playwright can only automate browser-like surfaces or Electron/browser debug targets.

For this workflow, Playwright is not sufficient when:

- Node/npm or `npx` is not installed
- Bitrig exposes no browser debug port
- the required UI is native macOS, not HTML

Use macOS UI automation or Bitrig's own native Agent New Project flow instead.

Native UI automation can use:

```bash
osascript -e 'tell application "System Events" to click at {x, y}'
```

Use screenshots to confirm coordinates before clicking.

## Problem: Generic Names Get Mixed Together

Avoid:

```text
New Project
Project
App
Agent
Untitled
```

Use a unique visible name:

```text
ProjectNameAgent
```

If there are already generic `New Project` rows, sort by `updatedAt` and use the newest ID created by the native Bitrig flow.

## Useful Inspection Commands

List recent Bitrig projects:

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
for project_id, project in rows[:20]:
    print(project_id, project.get("name"), project.get("updatedAt"))
PY
```

Find Agent metadata:

```bash
find ~/Library/Bitrig/Projects -maxdepth 2 -name BitrigAgent.json -print
```

Inspect a project:

```bash
sed -n '1,220p' ~/Library/Bitrig/Projects/<project-id>/Project.json
sed -n '1,120p' ~/Library/Bitrig/Projects/<project-id>/BitrigAgent.json
```

Check the App Intents project index:

```bash
python3 - <<'PY'
import json
import plistlib
from pathlib import Path

prefs = Path.home() / "Library/Preferences/app.bitrig.bitrigapp.plist"
raw = plistlib.load(prefs.open("rb")).get("app.bitrig.AppIntents.ProjectIndex", b"[]")
index = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
for entry in index[:20]:
    print(entry)
PY
```

## Completion Checklist

Only call the project complete when all are true:

- Bitrig desktop Agent list shows the project.
- Bitrig Remote Agent list shows the project.
- The project name is specific, not generic.
- The app is iPhone-enabled.
- The Bitrig preview builds.
- The preview shows the intended app.
- `verify` passes.
