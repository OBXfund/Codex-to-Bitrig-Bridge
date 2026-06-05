# Codex iPhone to Bitrig Remote

This workspace is a bridge for creating iPhone-first Codex projects that become visible in Bitrig Remote.

When the user asks from Codex on iPhone to create a project for Bitrig Remote:

1. Use `tools/codex_iphone_to_bitrig.py automate`.
2. Prefer `--new "<Project Name>"` when the user is starting from an idea rather than an existing checkout.
3. Prefer `--project /absolute/path/to/project` when the user points at an existing Codex iOS project.
4. Do not create Classic Bitrig imports.
5. Do not use generic names like `New Project`, `App`, or `Untitled`; ask for or derive a specific visible project name.
6. Use the generated Agent name everywhere Bitrig indexes the project.
7. The `automate` command must create native Bitrig Agent project state, update Bitrig's Agent index, and run verification.

The durable path is:

```bash
python3 tools/codex_iphone_to_bitrig.py automate --new "Project Name" --summary "Short app idea" --refresh-bitrig
```

Bitrig Remote should show the project under Agent after the command passes verification. Use `prepare` only when you deliberately want a manual Bitrig Agent prompt fallback.
