#!/usr/bin/env python3
"""Zet de versie uit package.json door naar .plugin/plugin.json en publiccode.yml.

package.json is de bron van de versie (Changesets verhoogt hem). Dit script zet
dezelfde versie in .plugin/plugin.json en in publiccode.yml, en zet in
publiccode.yml de releasedatum op vandaag zodra de versie verandert.

De releaseworkflow draait dit in de versie-PR en werkt die PR bij na elke push
naar main. De releasedatum is dus de dag van de laatste bijwerking van de
versie-PR; merge hem op die dag, dan valt hij samen met de GitHub-release.

Gebruik:
    python3 scripts/sync_version.py          # doorzetten
    python3 scripts/sync_version.py --check  # alleen controleren (voor CI)
"""

import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "package.json"
PLUGIN = ROOT / ".plugin" / "plugin.json"
PUBLICCODE = ROOT / "publiccode.yml"

VERSION_RE = re.compile(r'^softwareVersion: "(?P<v>[^"]*)"$', re.M)
DATE_RE = re.compile(r'^releaseDate: "(?P<d>[^"]*)"$', re.M)


def read_version() -> str:
    with open(PACKAGE) as f:
        return json.load(f)["version"]


def plugin_version() -> str:
    with open(PLUGIN) as f:
        return json.load(f)["version"]


def publiccode_version(text: str) -> str:
    match = VERSION_RE.search(text)
    if not match:
        sys.exit("FOUT: publiccode.yml heeft geen regel softwareVersion: \"...\"")
    return match.group("v")


def check(version: str) -> bool:
    ok = True
    if plugin_version() != version:
        print(f"FOUT: .plugin/plugin.json heeft {plugin_version()}, package.json {version}")
        ok = False
    text = PUBLICCODE.read_text()
    if publiccode_version(text) != version:
        print(f"FOUT: publiccode.yml heeft {publiccode_version(text)}, package.json {version}")
        ok = False
    if not DATE_RE.search(text):
        print("FOUT: publiccode.yml heeft geen regel releaseDate: \"...\"")
        ok = False
    if ok:
        print(f"OK: versie {version} in package.json, .plugin/plugin.json en publiccode.yml")
    return ok


def sync(version: str) -> None:
    with open(PLUGIN) as f:
        plugin = json.load(f)
    if plugin["version"] != version:
        plugin["version"] = version
        with open(PLUGIN, "w") as f:
            json.dump(plugin, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Bijgewerkt: .plugin/plugin.json -> {version}")

    text = PUBLICCODE.read_text()
    if publiccode_version(text) != version:
        today = datetime.date.today().isoformat()
        text = VERSION_RE.sub(f'softwareVersion: "{version}"', text)
        text = DATE_RE.sub(f'releaseDate: "{today}"', text)
        PUBLICCODE.write_text(text)
        print(f"Bijgewerkt: publiccode.yml -> {version}, releaseDate {today}")


def main() -> None:
    version = read_version()
    if "--check" in sys.argv:
        sys.exit(0 if check(version) else 1)
    sync(version)
    check(version)


if __name__ == "__main__":
    main()
