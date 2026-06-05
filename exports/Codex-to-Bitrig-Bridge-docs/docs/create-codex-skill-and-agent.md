# Create The Codex Skill And Agent Bridge

This guide describes how to create the Codex skill and Agent-facing bridge files used to create iPhone-first projects for Bitrig Remote.

Use this when setting up the workflow on another Mac or in another Codex workspace.

## Prerequisites

Install or confirm:

- macOS
- Bitrig desktop app
- Bitrig Remote on iPhone
- Codex with local filesystem access to the bridge workspace
- Python 3
- Swift and Xcode command line tools

Confirm Python:

```bash
python3 --version
```

Confirm Swift:

```bash
swift --version
```

## Create The Bridge Workspace

Create a workspace:

```bash
mkdir -p <bridge-workspace>/tools
mkdir -p <bridge-workspace>/GeneratedProjects
mkdir -p <bridge-workspace>/.bitrig-bridge
mkdir -p <bridge-workspace>/codex-iphone-bitrig-remote/agents
mkdir -p <bridge-workspace>/codex-iphone-bitrig-remote/scripts
```

The workspace should contain:

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

## Create `AGENTS.md`

Add workspace instructions:

````markdown
# Codex iPhone to Bitrig Remote

This workspace is a bridge for creating iPhone-first Codex projects that become visible in Bitrig Remote.

When the user asks from Codex on iPhone to create a project for Bitrig Remote:

1. Use `tools/codex_iphone_to_bitrig.py automate`.
2. Prefer `--new "<Project Name>"` when starting from an idea.
3. Prefer `--project /absolute/path/to/project` when using an existing Codex iOS project.
4. Do not create Classic Bitrig imports.
5. Do not use generic names like `New Project`, `App`, or `Untitled`.
6. Use the generated Agent name everywhere Bitrig indexes the project.
7. If file automation does not make the project visible in Bitrig Remote, create the project through Bitrig's native Agent New Project UI and adopt the Bitrig-created project ID.

The durable command for a new project is:

```bash
python3 tools/codex_iphone_to_bitrig.py automate --new "Project Name" --summary "Short app idea" --refresh-bitrig
```
````

## Create The Skill

Create:

```text
<bridge-workspace>/codex-iphone-bitrig-remote/SKILL.md
```

Use this structure:

````markdown
---
name: codex-iphone-bitrig-remote
description: Use when the user wants to start an iPhone app project from Codex on iPhone or mobile remote control and make it visible in Bitrig Remote as a native Bitrig Agent project.
---

# Codex iPhone Bitrig Remote

Use this skill when the user wants to start projects from Codex and see them in Bitrig Remote on iPhone.

## Rule

Bitrig Remote needs a native Bitrig Agent project. Do not use Classic imports.

## Default Workspace

Use the bridge workspace:

`<bridge-workspace>`

The main wrapper is:

`<bridge-workspace>/tools/codex_iphone_to_bitrig.py`

## Workflow

1. Get a specific visible project name.
2. Reject generic names like `New Project`, `App`, `Untitled`, or `Agent`.
3. For a new idea, run:

```bash
python3 <bridge-workspace>/tools/codex_iphone_to_bitrig.py automate --new "Project Name" --summary "Short app idea" --refresh-bitrig
```

4. For an existing local Codex iOS project, run:

```bash
python3 <bridge-workspace>/tools/codex_iphone_to_bitrig.py automate --project /absolute/path/to/project --refresh-bitrig
```

5. If Bitrig Remote does not show the project, use Bitrig's native Agent New Project UI and then adopt the Bitrig-created project ID:

```bash
python3 <bridge-workspace>/tools/codex_iphone_to_bitrig.py automate --project /absolute/path/to/project --agent-name ProjectNameAgent --project-id <bitr-created-project-id> --overwrite
```

6. Verify:

```bash
python3 <bridge-workspace>/tools/codex_iphone_to_bitrig.py verify --name "ProjectNameAgent" --source-path /absolute/path/to/project
```
````

## Create The Agent Metadata

Create:

```text
<bridge-workspace>/codex-iphone-bitrig-remote/agents/openai.yaml
```

Use:

```yaml
interface:
  display_name: "Codex iPhone to Bitrig Remote"
  short_description: "Start iPhone projects and bridge to Bitrig Remote"
  default_prompt: "Use $codex-iphone-bitrig-remote to create a new iPhone app project from this prompt and make it visible in Bitrig Remote."
policy:
  allow_implicit_invocation: true
```

## Create The Skill Wrapper Script

Create:

```text
<bridge-workspace>/codex-iphone-bitrig-remote/scripts/iphone_bitrig_remote.py
```

Use:

```python
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


BRIDGE = Path("<bridge-workspace>/tools/codex_iphone_to_bitrig.py")


def main() -> int:
    if not BRIDGE.exists():
        sys.stderr.write(f"Missing bridge script: {BRIDGE}\n")
        return 1
    command = [sys.executable, str(BRIDGE), *sys.argv[1:]]
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
```

Make it executable if desired:

```bash
chmod +x <bridge-workspace>/codex-iphone-bitrig-remote/scripts/iphone_bitrig_remote.py
```

## Install Or Expose The Skill

If Codex loads skills from a user skill directory, copy the skill folder there:

```bash
mkdir -p ~/.codex/skills
rsync -a <bridge-workspace>/codex-iphone-bitrig-remote/ ~/.codex/skills/codex-iphone-bitrig-remote/
```

If your Codex setup uses a plugin or marketplace mechanism, package the same folder as the skill payload and keep the relative layout:

```text
skills/
  codex-iphone-bitrig-remote/
    SKILL.md
    agents/openai.yaml
    scripts/iphone_bitrig_remote.py
```

## Create The Bridge Script

Place the bridge implementation at:

```text
<bridge-workspace>/tools/codex_iphone_to_bitrig.py
```

The bridge script must implement:

- `prepare`
- `automate`
- `verify`

It must be able to:

- create a Swift package seed project
- reject generic names
- generate a Bitrig Agent prompt
- write `Project.json`
- write `BitrigAgent.json`
- write Bitrig metadata
- update Bitrig's project catalog
- update the App Intents Agent index
- adopt a Bitrig-created project ID with `--project-id`
- verify the result

## Minimal Commands To Test The Skill

Prepare only:

```bash
python3 tools/codex_iphone_to_bitrig.py prepare --new "Test Arcade" --summary "A small iPhone arcade game" --json
```

Create local state:

```bash
python3 tools/codex_iphone_to_bitrig.py automate --new "Test Arcade" --summary "A small iPhone arcade game" --refresh-bitrig --json
```

Verify:

```bash
python3 tools/codex_iphone_to_bitrig.py verify --name "TestArcadeAgent" --json
```

If Bitrig Remote does not show the project, use native creation plus adoption as described in `native-bitrig-agent-flow.md`.
