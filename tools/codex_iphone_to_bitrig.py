#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import plistlib
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = ROOT / "GeneratedProjects"
BRIDGE_ROOT = ROOT / ".bitrig-bridge"
BITRIG_ROOT = Path.home() / "Library" / "Bitrig"
BITRIG_PROJECTS = BITRIG_ROOT / "Projects"
BITRIG_METADATA = BITRIG_ROOT / "Metadata"
BITRIG_PROJECTS_JSON = BITRIG_ROOT / "Projects.json"
BITRIG_PREFS = Path.home() / "Library" / "Preferences" / "app.bitrig.bitrigapp.plist"
PROJECT_INDEX_KEY = "app.bitrig.AppIntents.ProjectIndex"
HELPER = Path.home() / "plugins" / "bitrig-codex-agent-creator" / "skills" / "bitrig-codex-agent-creator" / "scripts" / "prepare_bitrig_codex_agent_prompt.py"
VERIFIER = Path.home() / ".codex" / "skills" / "bitrig-agent-project-bridge" / "scripts" / "verify_bitrig_agent_project.py"
GENERIC_NAMES = {"newproject", "new-project", "project", "app", "agent", "untitled", "new"}


def sanitize_name(value: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", value)
    if not parts:
        raise SystemExit("Project name must contain at least one letter or number.")
    return "".join(part[:1].upper() + part[1:] for part in parts)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def reject_generic_name(name: str) -> None:
    if slug(name) in GENERIC_NAMES:
        raise SystemExit("Use a specific project name. Generic names like New Project or App get mixed together in Bitrig.")


def normalize_agent_name(name: str) -> str:
    reject_generic_name(name)
    value = sanitize_name(name)
    if not value.endswith("Agent"):
        value = f"{value}Agent"
    return value


def swift_string(value: str) -> str:
    return json.dumps(value)


def ensure_helper(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def cf_absolute_now() -> float:
    apple_epoch = dt.datetime(2001, 1, 1, tzinfo=dt.timezone.utc)
    return round((dt.datetime.now(dt.timezone.utc) - apple_epoch).total_seconds(), 3)


def load_json_file(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_agent_metadata(path: Path) -> dict:
    try:
        return load_json_file(path / "BitrigAgent.json", {})
    except Exception:
        return {}


def write_json_file(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def backup_if_exists(path: Path, label: str) -> None:
    if path.exists():
        backup = path.with_name(f"{path.name}.{label}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(path, backup)


def existing_agent_project_id(agent_name: str):
    if not BITRIG_PROJECTS.exists():
        return None
    for project_dir in sorted(BITRIG_PROJECTS.iterdir()):
        if not project_dir.is_dir():
            continue
        agent_json = load_agent_metadata(project_dir)
        if agent_json.get("name") == agent_name:
            return project_dir.name
        project_json = load_json_file(project_dir / "Project.json", {})
        if project_json.get("name") == agent_name:
            return project_dir.name
    return None


def create_seed_project(name: str, summary: str) -> Path:
    reject_generic_name(name)
    project_name = sanitize_name(name)
    project_dir = GENERATED_ROOT / project_name
    source_dir = project_dir / "Sources" / project_name
    source_dir.mkdir(parents=True, exist_ok=True)

    package = f"""// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "{project_name}",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "{project_name}", targets: ["{project_name}"])
    ],
    targets: [
        .target(name: "{project_name}")
    ]
)
"""
    app_swift = f"""import SwiftUI

@main
struct {project_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}
"""
    content_swift = f"""import SwiftUI

public struct ContentView: View {{
    public init() {{}}

    public var body: some View {{
        NavigationStack {{
            VStack(alignment: .leading, spacing: 16) {{
                Text({swift_string(name)})
                    .font(.largeTitle.weight(.bold))
                Text({swift_string(summary or "Created from Codex on iPhone for Bitrig Remote.")})
                    .font(.body)
                    .foregroundStyle(.secondary)
                Spacer()
            }}
            .padding()
            .navigationTitle({swift_string(name)})
        }}
    }}
}}
"""
    metadata = {
        "kind": "codex-iphone-seed",
        "name": project_name,
        "requestedName": name,
        "summary": summary or "Created from Codex on iPhone for Bitrig Remote.",
        "target": "Bitrig native Agent, iPhone",
    }

    (project_dir / "Package.swift").write_text(package, encoding="utf-8")
    (source_dir / f"{project_name}App.swift").write_text(app_swift, encoding="utf-8")
    (source_dir / "ContentView.swift").write_text(content_swift, encoding="utf-8")
    (project_dir / "CodexIPhoneProject.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return project_dir


def bridge_result(args: argparse.Namespace, allow_existing_agent_name: bool = False) -> dict:
    ensure_helper(HELPER, "Bitrig Codex Agent prompt helper")
    identity_count = sum(bool(value) for value in [args.new, args.project, args.name])
    if identity_count != 1:
        raise SystemExit("Provide exactly one of --new, --project, or --name.")

    project_path = None
    if args.new:
        project_path = create_seed_project(args.new, args.summary or "")
    elif args.project:
        project_path = Path(args.project).expanduser().resolve()
        if not project_path.is_dir():
            raise SystemExit(f"Project path is not a directory: {project_path}")

    helper_cmd = [sys.executable, str(HELPER), "--json"]
    if project_path:
        helper_cmd.extend(["--project", str(project_path)])
    else:
        reject_generic_name(args.name)
        helper_cmd.extend(["--name", args.name])
    if args.agent_name:
        reject_generic_name(args.agent_name)
        helper_cmd.extend(["--agent-name", args.agent_name])

    result = run_json(helper_cmd)
    if result.get("needsUserConfirmation"):
        return result

    BRIDGE_ROOT.mkdir(parents=True, exist_ok=True)
    if allow_existing_agent_name and args.agent_name:
        helper_agent_name = result["agentName"]
        agent_name = normalize_agent_name(args.agent_name)
        result["agentName"] = agent_name
        if result.get("prompt"):
            result["prompt"] = result["prompt"].replace(helper_agent_name, agent_name)
            result["prompt"] = result["prompt"].replace(slug(helper_agent_name), slug(agent_name))
    else:
        agent_name = result["agentName"]
    prompt_path = BRIDGE_ROOT / f"{agent_name}.bitrig-agent-prompt.txt"
    result_path = BRIDGE_ROOT / f"{agent_name}.json"
    prompt_path.write_text(result["prompt"] + "\n", encoding="utf-8")
    result["promptPath"] = str(prompt_path)
    result["resultPath"] = str(result_path)
    result["nextSteps"] = [
        "Open Bitrig on the host Mac.",
        "Choose Agent, then New Project. Do not choose Classic.",
        f"Paste the prompt from {prompt_path}.",
        f"After Bitrig finishes, run: python3 tools/codex_iphone_to_bitrig.py verify --name {json.dumps(agent_name)}",
        "Refresh Bitrig Remote on iPhone and check Agent.",
    ]
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def run_json(command: list[str]) -> dict:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        raise SystemExit(completed.returncode)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        sys.stderr.write(completed.stdout)
        raise SystemExit(f"Expected JSON output from helper: {error}")


def prepare(args: argparse.Namespace) -> int:
    result = bridge_result(args)
    if result.get("needsUserConfirmation"):
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    if args.copy:
        subprocess.run(["pbcopy"], input=result["prompt"], text=True, check=True)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        agent_name = result["agentName"]
        print(f"Agent name: {agent_name}")
        print(f"Source project: {result.get('sourceProjectPath')}")
        print(f"Prompt: {result.get('promptPath')}")
        print()
        print(result["prompt"])
        print()
        print("Next:")
        for step in result["nextSteps"]:
            print(f"- {step}")
    return 0


def swift_shell(agent_name: str, source_name: str, source_path: str, summary: str) -> str:
    return f"""import SwiftUI

struct ContentView: View {{
  var body: some View {{
    NavigationStack {{
      ScrollView {{
        VStack(alignment: .leading, spacing: 24) {{
          VStack(alignment: .leading, spacing: 10) {{
            Image(systemName: "terminal.fill")
              .font(.system(size: 42, weight: .semibold))
              .foregroundStyle(.tint)
              .accessibilityHidden(true)
            Text({swift_string(agent_name)})
              .font(.largeTitle.bold())
            Text({swift_string(summary or "Native Bitrig Agent shell for a local Codex iOS project.")})
              .font(.body)
              .foregroundStyle(.secondary)
          }}
          VStack(alignment: .leading, spacing: 14) {{
            Label("Source Project", systemImage: "shippingbox")
              .font(.headline)
            detailRow(title: "Name", value: {swift_string(source_name)})
            detailRow(title: "Path", value: {swift_string(source_path)})
          }}
          .padding(18)
          .frame(maxWidth: .infinity, alignment: .leading)
          .background(.background, in: RoundedRectangle(cornerRadius: 8))
        }}
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
      }}
      .background(Color(.systemGroupedBackground))
      .navigationTitle("Agent Project")
    }}
  }}

  private func detailRow(title: String, value: String) -> some View {{
    VStack(alignment: .leading, spacing: 4) {{
      Text(title)
        .font(.caption)
        .foregroundStyle(.secondary)
      Text(value)
        .font(.callout.monospaced())
        .textSelection(.enabled)
        .lineLimit(nil)
    }}
    .frame(maxWidth: .infinity, alignment: .leading)
  }}
}}
"""


def app_swift(agent_name: str) -> str:
    return f"""import SwiftUI

@main
struct {sanitize_name(agent_name)}App: App {{
  var body: some Scene {{
    WindowGroup {{
      ContentView()
    }}
  }}
}}
"""


def project_json(agent_name: str) -> dict:
    bundle = f"app.bitrig.agent.{slug(agent_name)}"
    return {
        "configs": {"Debug": "debug", "Release": "release"},
        "name": agent_name,
        "options": {
            "groupSortPosition": "bottom",
            "transitivelyLinkDependencies": False,
        },
        "settings": {"CODE_SIGN_IDENTITY": "-"},
        "targets": {
            agent_name: {
                "deploymentTarget": "26.0",
                "info": {
                    "path": "App/Info.plist",
                    "properties": {
                        "CFBundleDisplayName": agent_name,
                        "CFBundleShortVersionString": "1.0",
                        "CFBundleVersion": "1",
                        "ITSAppUsesNonExemptEncryption": False,
                        "UILaunchScreen": {},
                        "UISupportedInterfaceOrientations": [
                            "UIInterfaceOrientationPortrait",
                            "UIInterfaceOrientationPortraitUpsideDown",
                            "UIInterfaceOrientationLandscapeLeft",
                            "UIInterfaceOrientationLandscapeRight",
                        ],
                    },
                },
                "platform": "iOS",
                "settings": {
                    "ASSETCATALOG_COMPILER_APPICON_NAME": "AppIcon",
                    "ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME": "AccentColor",
                    "CURRENT_PROJECT_VERSION": "1",
                    "MARKETING_VERSION": "1.0",
                    "PRODUCT_BUNDLE_IDENTIFIER": bundle,
                    "PRODUCT_NAME": "$(TARGET_NAME)",
                    "SWIFT_VERSION": "5.0",
                    "TARGETED_DEVICE_FAMILY": "1",
                },
                "sources": [{"path": "App"}],
                "type": "application",
            }
        },
    }


def copy_or_make_content_view(source_path: Path, app_dir: Path, agent_name: str, source_name: str, summary: str) -> str:
    direct = source_path / "Sources" / source_name / "ContentView.swift"
    fallback = source_path / "ContentView.swift"
    if direct.exists():
        shutil.copy2(direct, app_dir / "ContentView.swift")
        return str(direct)
    if fallback.exists():
        shutil.copy2(fallback, app_dir / "ContentView.swift")
        return str(fallback)
    (app_dir / "ContentView.swift").write_text(swift_shell(agent_name, source_name, str(source_path), summary), encoding="utf-8")
    return "generated-shell"


def load_project_index() -> list[dict]:
    if not BITRIG_PREFS.exists():
        return []
    with BITRIG_PREFS.open("rb") as fh:
        prefs = plistlib.load(fh)
    raw = prefs.get(PROJECT_INDEX_KEY, b"[]")
    if isinstance(raw, bytes):
        return json.loads(raw.decode("utf-8"))
    if isinstance(raw, str):
        return json.loads(raw)
    return raw if isinstance(raw, list) else []


def write_project_index(index: list[dict]) -> None:
    prefs = {}
    if BITRIG_PREFS.exists():
        with BITRIG_PREFS.open("rb") as fh:
            prefs = plistlib.load(fh)
    prefs[PROJECT_INDEX_KEY] = json.dumps(index, separators=(",", ":")).encode("utf-8")
    BITRIG_PREFS.parent.mkdir(parents=True, exist_ok=True)
    with BITRIG_PREFS.open("wb") as fh:
        plistlib.dump(prefs, fh)


def write_bitrig_metadata(project_id: str, conversation_id: str, agent_session_id: str, agent_name: str, now_iso: str) -> None:
    metadata_root = BITRIG_METADATA / project_id
    sessions_dir = metadata_root / "sessions"
    conversations_dir = metadata_root / "conversations"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    conversations_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "activeConversationId": conversation_id,
        "conversations": [
            {
                "createdAt": now_iso,
                "family": "codex",
                "id": conversation_id,
                "lastMessageAt": now_iso,
                "name": f"Create {agent_name}",
            }
        ],
    }
    session = {
        "agentSessionId": agent_session_id,
        "contextWindow": 258400,
        "conversationName": f"Create {agent_name}",
        "createdAt": now_iso,
        "lastMessageAt": now_iso,
        "sessionId": conversation_id,
        "tokenUsage": {
            "cacheCreationInputTokens": 0,
            "cacheReadInputTokens": 0,
            "inputTokens": 0,
            "outputTokens": 0,
        },
    }
    conversation_event = {
        "timestamp": now_iso.replace("Z", ".000Z"),
        "type": "session_meta",
        "payload": {
            "id": agent_session_id,
            "timestamp": now_iso.replace("Z", ".000Z"),
            "cwd": str(BITRIG_PROJECTS / project_id),
            "originator": "Codex automation",
            "source": "codex-iphone-to-bitrig",
        },
    }

    write_json_file(metadata_root / "manifest.json", manifest)
    write_json_file(sessions_dir / f"{conversation_id}.json", session)
    (conversations_dir / f"{conversation_id}.jsonl").write_text(json.dumps(conversation_event, sort_keys=True) + "\n", encoding="utf-8")
    (metadata_root / ".metadata_never_index").write_text("", encoding="utf-8")


def create_native_agent_project(result: dict, overwrite: bool = False, project_id_override=None) -> dict:
    agent_name = result["agentName"]
    source_name = result["sourceProjectName"]
    source_path = Path(result["sourceProjectPath"]).expanduser().resolve()
    summary = f"Automated native Bitrig Agent project for {source_name}."

    projects = load_json_file(BITRIG_PROJECTS_JSON, {})
    existing = [(pid, data) for pid, data in projects.items() if data.get("name") == agent_name]
    folder_project_id = existing_agent_project_id(agent_name)
    if existing and not overwrite and not project_id_override:
        existing.sort(key=lambda item: item[1].get("updatedAt") or item[1].get("createdAt") or "", reverse=True)
        project_id = existing[0][0]
        if (BITRIG_METADATA / project_id / "manifest.json").exists():
            return {
                "agentName": agent_name,
                "projectId": project_id,
                "projectRoot": str(BITRIG_PROJECTS / project_id),
                "sourceProjectPath": str(source_path),
                "created": False,
                "reason": "Existing Bitrig Agent project reused. Pass --overwrite to replace local files.",
            }

    project_id = project_id_override or (existing[0][0] if existing else (folder_project_id or str(uuid.uuid4())))
    conversation_id = str(uuid.uuid4())
    agent_session_id = str(uuid.uuid4())
    now_iso = iso_now()
    project_root = BITRIG_PROJECTS / project_id
    app_dir = project_root / "App"
    assets_dir = app_dir / "Assets.xcassets"

    if project_root.exists() and overwrite:
        backup = project_root.with_name(f"{project_root.name}.automate-backup-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}")
        shutil.copytree(project_root, backup)

    app_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    copied_content = copy_or_make_content_view(source_path, app_dir, agent_name, source_name, summary)
    (app_dir / "App.swift").write_text(app_swift(agent_name), encoding="utf-8")
    write_json_file(assets_dir / "Contents.json", {"info": {"author": "xcode", "version": 1}})
    write_json_file(project_root / "Project.json", project_json(agent_name))
    agent_metadata = {
        "kind": "agent-project",
        "name": agent_name,
        "sourceProjectName": source_name,
        "sourceProjectPath": str(source_path),
        "platforms": ["iPhone"],
        "projectSummary": summary,
        "automation": {
            "createdBy": "tools/codex_iphone_to_bitrig.py automate",
            "copiedContentView": copied_content,
            "createdAt": now_iso,
        },
    }
    write_json_file(project_root / "BitrigAgent.json", agent_metadata)

    projects[project_id] = {
        "accentColor": "blue",
        "conversationID": conversation_id,
        "conversations": [
            {
                "agentSessionID": agent_session_id,
                "createdAt": now_iso,
                "id": conversation_id,
                "lastMessageAt": now_iso,
                "model": "codex",
                "name": f"Create {agent_name}",
            }
        ],
        "createdAt": projects.get(project_id, {}).get("createdAt", now_iso),
        "isRemix": False,
        "name": agent_name,
        "supportedPlatforms": {
            "iPad": False,
            "iPhone": True,
            "macOS": False,
            "watchOS": False,
        },
        "updatedAt": now_iso,
    }

    backup_if_exists(BITRIG_PROJECTS_JSON, "automate-backup")
    write_json_file(BITRIG_PROJECTS_JSON, projects)
    write_bitrig_metadata(project_id, conversation_id, agent_session_id, agent_name, now_iso)

    index = [entry for entry in load_project_index() if entry.get("id") != project_id and entry.get("name") != agent_name]
    index.insert(0, {"id": project_id, "name": agent_name, "updatedAt": cf_absolute_now(), "source": "agent"})
    backup_if_exists(BITRIG_PREFS, "automate-backup")
    write_project_index(index)

    return {
        "agentName": agent_name,
        "projectId": project_id,
        "projectRoot": str(project_root),
        "sourceProjectPath": str(source_path),
        "created": True,
        "copiedContentView": copied_content,
    }


def automate(args: argparse.Namespace) -> int:
    result = bridge_result(args, allow_existing_agent_name=True)
    if result.get("needsUserConfirmation"):
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    automation = create_native_agent_project(result, overwrite=args.overwrite, project_id_override=args.project_id)
    if args.refresh_bitrig:
        subprocess.run(["killall", "Bitrig"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        subprocess.run(["open", "-a", "Bitrig"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        time.sleep(args.refresh_delay)
        automation = create_native_agent_project(result, overwrite=True, project_id_override=args.project_id)

    verify_command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "verify",
        "--name",
        result["agentName"],
        "--source-path",
        result["sourceProjectPath"],
        "--json",
    ]
    verified = subprocess.run(verify_command, text=True, capture_output=True, check=False)
    try:
        verify_result = json.loads(verified.stdout) if verified.stdout else {}
    except json.JSONDecodeError:
        verify_result = {"stdout": verified.stdout, "stderr": verified.stderr}

    output = {
        "prepare": result,
        "automation": automation,
        "verification": verify_result,
        "verificationExitCode": verified.returncode,
        "remoteInstruction": "Refresh Bitrig Remote on iPhone and open Agent. The project should appear as " + result["agentName"] + ".",
    }
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(f"Agent name: {result['agentName']}")
        print(f"Source project: {result.get('sourceProjectPath')}")
        print(f"Bitrig project: {automation['projectRoot']}")
        print(f"Project id: {automation['projectId']}")
        print(f"Created: {automation['created']}")
        print(f"Verification: {'OK' if verified.returncode == 0 else 'FAILED'}")
        if verified.stdout:
            print(verified.stdout.strip())
        if verified.stderr:
            print(verified.stderr.strip(), file=sys.stderr)
        print(f"Refresh Bitrig Remote on iPhone and open Agent -> {result['agentName']}.")
    return verified.returncode


def verify(args: argparse.Namespace) -> int:
    ensure_helper(VERIFIER, "Bitrig Agent verifier")
    command = [sys.executable, str(VERIFIER), "--name", args.name]
    if args.source_path:
        command.extend(["--source-path", args.source_path])
    if args.json:
        command.append("--json")
    return subprocess.run(command, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Codex iPhone projects for Bitrig Remote native Agent creation.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="Create or resolve a Codex iOS project and generate a Bitrig Agent prompt.")
    prepare_parser.add_argument("--new", help="Create a new lightweight Codex iOS seed project with this visible name.")
    prepare_parser.add_argument("--summary", help="Short app idea to show in the seed project and Bitrig prompt.")
    prepare_parser.add_argument("--project", help="Existing Codex iOS project path.")
    prepare_parser.add_argument("--name", help="Existing project name to resolve from common local roots.")
    prepare_parser.add_argument("--agent-name", help="Override the visible Bitrig Agent project name.")
    prepare_parser.add_argument("--copy", action="store_true", help="Copy the generated Bitrig prompt to the clipboard.")
    prepare_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    prepare_parser.set_defaults(func=prepare)

    automate_parser = subparsers.add_parser("automate", help="Prepare, create native Bitrig Agent state, and verify Remote-ready indexing.")
    automate_parser.add_argument("--new", help="Create a new lightweight Codex iOS seed project with this visible name.")
    automate_parser.add_argument("--summary", help="Short app idea to show in the seed project and Bitrig prompt.")
    automate_parser.add_argument("--project", help="Existing Codex iOS project path.")
    automate_parser.add_argument("--name", help="Existing project name to resolve from common local roots.")
    automate_parser.add_argument("--agent-name", help="Override the visible Bitrig Agent project name.")
    automate_parser.add_argument("--project-id", help="Adopt an existing Bitrig-created project id instead of creating a new id.")
    automate_parser.add_argument("--overwrite", action="store_true", help="Replace local files for an existing Bitrig project with the same Agent name after making a backup.")
    automate_parser.add_argument("--refresh-bitrig", action="store_true", help="Quit/open Bitrig, wait for launch-time cleanup, then rewrite and verify Agent state for Bitrig Remote.")
    automate_parser.add_argument("--refresh-delay", type=float, default=5.0, help="Seconds to wait after opening Bitrig before the final Agent-state rewrite.")
    automate_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    automate_parser.set_defaults(func=automate)

    verify_parser = subparsers.add_parser("verify", help="Verify Bitrig native Agent state after Bitrig creates the project.")
    verify_parser.add_argument("--name", required=True, help="Visible Bitrig Agent project name.")
    verify_parser.add_argument("--source-path", help="Expected Codex seed/source project path.")
    verify_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    verify_parser.set_defaults(func=verify)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
