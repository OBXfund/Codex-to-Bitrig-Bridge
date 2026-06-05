#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


BRIDGE = Path("/Users/lonniejordan/Documents/Bitrig Test/tools/codex_iphone_to_bitrig.py")


def main() -> int:
    if not BRIDGE.exists():
        sys.stderr.write(f"Missing bridge script: {BRIDGE}\n")
        return 1
    command = [sys.executable, str(BRIDGE), *sys.argv[1:]]
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
