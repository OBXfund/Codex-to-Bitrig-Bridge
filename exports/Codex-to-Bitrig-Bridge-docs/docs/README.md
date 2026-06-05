# Bitrig Remote Bridge Documentation

These files describe the complete workflow for creating iPhone-first Codex projects that appear in Bitrig Remote as native Bitrig Agent projects.

Read in this order:

1. [Bitrig Remote Bridge Overview](bitrig-remote-bridge-overview.md)
2. [How The Bridge Works](how-the-bridge-works.md)
3. [Create The Codex Skill And Agent Bridge](create-codex-skill-and-agent.md)
4. [Native Bitrig Agent Flow](native-bitrig-agent-flow.md)
5. [Troubleshooting Bitrig Remote Agent Visibility](troubleshooting-bitrig-remote.md)

## Short Version

The reliable workflow is:

1. Create or identify a local Codex iOS project.
2. Use Bitrig desktop's native `Agent -> New Project...` flow when Remote visibility matters.
3. Let Bitrig create the project ID.
4. Adopt that Bitrig-created ID with:

```bash
python3 tools/codex_iphone_to_bitrig.py automate \
  --project /absolute/path/to/project \
  --agent-name ProjectNameAgent \
  --project-id <bitr-created-project-id> \
  --overwrite
```

5. Verify:

```bash
python3 tools/codex_iphone_to_bitrig.py verify \
  --name "ProjectNameAgent" \
  --source-path /absolute/path/to/project
```

6. Confirm the project appears in both Bitrig desktop's Agent list and Bitrig Remote's Agent list.

## Key Rule

Do not rely on file-only insertion when the deliverable is Bitrig Remote visibility. A project can pass local file checks and still be absent from Bitrig Remote. Native Bitrig Agent creation plus adoption is the reliable path.
