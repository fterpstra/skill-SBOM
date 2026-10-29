#!/usr/bin/env python3
"""Genereer de manifesten per assistent uit het neutrale .plugin/plugin.json.

.plugin/plugin.json is de enige bron. Dit script maakt daaruit de varianten in
de mappen per assistent; die bestanden bewerk je nooit met de hand.

Gebruik:
    python3 scripts/generate_plugin.py          # alle manifesten genereren
    python3 scripts/generate_plugin.py --check  # alleen controleren (voor CI)
"""

import copy
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SOURCE_PATH = ROOT_DIR / ".plugin" / "plugin.json"
CLAUDE_PATH = ROOT_DIR / ".claude-plugin" / "plugin.json"
CURSOR_PATH = ROOT_DIR / ".cursor-plugin" / "plugin.json"


def load_source() -> dict:
    """Lees het neutrale .plugin/plugin.json."""
    with open(SOURCE_PATH) as f:
        return json.load(f)


def generate_claude(data: dict) -> dict:
    """Manifest voor .claude-plugin: de bron zonder displayName (dat veld hoort alleen in .cursor-plugin)."""
    result = copy.deepcopy(data)
    result.pop("displayName", None)
    return result


def _display_name(name: str) -> str:
    """Maak van een kebab-case pluginnaam een leesbare weergavenaam.

    Voorbeeld: "geonovum-sbom" -> "Geonovum Sbom". Alleen gebruikt als de
    bron geen displayName heeft.
    """
    return name.replace("-", " ").title()


def generate_cursor(data: dict) -> dict:
    """Manifest voor .cursor-plugin: de bron met displayName direct na name."""
    result = copy.deepcopy(data)
    ordered = {"name": result.pop("name")}
    ordered["displayName"] = result.pop("displayName", None) or _display_name(ordered["name"])
    ordered.update(result)
    return ordered


PLATFORMS: dict[str, tuple[Path, callable]] = {
    "claude": (CLAUDE_PATH, generate_claude),
    "cursor": (CURSOR_PATH, generate_cursor),
}


def write_json(path: Path, data: dict) -> None:
    """Schrijf JSON met vaste opmaak."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def generate_all(source_data: dict) -> None:
    """Genereer alle manifesten."""
    for _name, (path, generator) in PLATFORMS.items():
        generated = generator(source_data)
        write_json(path, generated)
        print(f"Gegenereerd: {path.relative_to(ROOT_DIR)}")


def check_sync(source_data: dict) -> bool:
    """Controleer of de manifesten gelijk zijn aan wat de bron oplevert."""
    all_synced = True
    for _name, (path, generator) in PLATFORMS.items():
        expected = generator(source_data)
        if not path.exists():
            print(f"FOUT: {path.relative_to(ROOT_DIR)} bestaat niet")
            all_synced = False
            continue
        with open(path) as f:
            actual = json.load(f)
        if actual != expected:
            print(f"FOUT: {path.relative_to(ROOT_DIR)} is niet in sync")
            all_synced = False
        else:
            print(f"OK: {path.relative_to(ROOT_DIR)}")
    return all_synced


def main() -> None:
    if not SOURCE_PATH.exists():
        print(f"FOUT: {SOURCE_PATH} niet gevonden")
        sys.exit(1)

    source_data = load_source()

    if "--check" in sys.argv:
        if check_sync(source_data):
            print("\nAlle platform-bestanden zijn in sync")
            sys.exit(0)
        else:
            print("\nNiet in sync. Draai: python3 scripts/generate_plugin.py")
            sys.exit(1)
    else:
        generate_all(source_data)
        print("\nAlle platform-bestanden gegenereerd")


if __name__ == "__main__":
    main()
