# Codex-to-Bitrig-Bridge

Create Bitrig agent files from Codex using Codex skills and agents.

This repository documents a bridge workflow for creating iPhone-first Codex projects that become visible in Bitrig Remote as native Bitrig Agent projects.

## Create a New iPhone Project and Register It

```bash
python3 tools/codex_iphone_to_bitrig.py automate --new "My App" --summary "A concise description of the app" --refresh-bitrig
```

The command creates a small local Codex seed project under `GeneratedProjects/`, creates native Bitrig Agent project state under `~/Library/Bitrig/Projects/`, restarts Bitrig, rewrites state after launch-time cleanup, updates Bitrig's Agent index, and runs verification.

## Register an Existing Codex iOS Project

```bash
python3 tools/codex_iphone_to_bitrig.py automate --project /absolute/path/to/ExistingProject --refresh-bitrig
```

## Manual Prompt Fallback

`prepare` still exists for cases where you intentionally want a prompt for Bitrig's Agent New Project composer:

```bash
python3 tools/codex_iphone_to_bitrig.py prepare --new "My App" --summary "A concise description of the app"
```

## Verify Existing Agent State

```bash
python3 tools/codex_iphone_to_bitrig.py verify --name "MyAppAgent"
```

Verification checks Bitrig's native project catalog, Agent index entry, iPhone support, project folder, `Project.json`, and `BitrigAgent.json`.

## Important

Bitrig Remote needs a native Bitrig Agent project. A Classic import or a manual project-index row is not enough.

## Full Documentation

See [docs/README.md](docs/README.md) for the complete setup, skill creation, native Agent adoption, and troubleshooting workflow.
