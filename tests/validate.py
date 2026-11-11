"""Offline packaging checks; never imports SDKs or calls the Cortecs API."""

import ast
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


def check_script(path, code, suffix):
    """Syntax-check a JS/TS block with Bun (JS and TS) or Node (JS only); skip if neither exists."""
    if shutil.which("bun"):
        command = ["bun", "build", "--no-bundle"]
    elif shutil.which("node") and suffix == ".mjs":
        command = ["node", "--check"]
    else:
        return
    with tempfile.NamedTemporaryFile("w", suffix=suffix) as script:
        script.write(code)
        script.flush()
        result = subprocess.run([*command, script.name], text=True, capture_output=True)
    assert result.returncode == 0, f"{path}: {result.stderr}"


def validate_markdown(path):
    text = path.read_text()
    blocks = re.findall(r"^```([^\n]*)\n(.*?)^```\s*$", text, re.M | re.S)
    assert len(re.findall(r"^```", text, re.M)) == len(blocks) * 2, f"Unclosed fence: {path}"
    for language, code in blocks:
        if language == "json":
            json.loads(code)
        elif language == "python":
            ast.parse(code, filename=str(path))
        elif language in {"bash", "sh"}:
            result = subprocess.run(["bash", "-n"], input=code, text=True, capture_output=True)
            assert result.returncode == 0, f"{path}: {result.stderr}"
        elif language == "toml":
            tomllib.loads(code)
        elif language in {"javascript", "typescript"}:
            check_script(path, code, ".mjs" if language == "javascript" else ".ts")

    prose = re.sub(r"^```[^\n]*\n.*?^```\s*$", "", text, flags=re.M | re.S)
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", prose):
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith("#"):
            continue
        destination = (path.parent / unquote(parsed.path)).resolve()
        assert destination.is_relative_to(ROOT), f"Link leaves package: {path}: {target}"
        assert destination.is_file(), f"Missing link: {path}: {target}"
    return len(blocks)


def main():
    claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    cursor = json.loads((ROOT / ".cursor-plugin/plugin.json").read_text())
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    for manifest in [claude, cursor]:
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", manifest["name"]), "Invalid plugin name"
        assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"]), "Invalid plugin version"
        assert manifest["description"] and manifest["author"]["name"], "Missing plugin metadata"
    assert claude == cursor, "Claude and Cursor plugin manifests differ"
    assert claude.get("license") and (ROOT / "LICENSE").is_file(), "Missing license"
    assert marketplace["name"] and marketplace["owner"]["name"], "Missing marketplace metadata"
    for plugin in marketplace["plugins"]:
        source = (ROOT / plugin["source"]).resolve()
        assert source.is_relative_to(ROOT), "Marketplace source leaves package"
        manifest = json.loads((source / ".claude-plugin/plugin.json").read_text())
        assert plugin["name"] == manifest["name"], "Marketplace plugin name differs"
        assert list((source / "skills").glob("*/SKILL.md")), "Plugin has no discoverable skills"
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    assert skills, "No discoverable skills"
    for path in skills:
        text = path.read_text()
        assert text.startswith("---\n"), f"Missing frontmatter: {path}"
        frontmatter = text.split("---", 2)[1]
        name = re.search(r"^name: ([a-z0-9-]+)$", frontmatter, re.M)
        description = re.search(r"^description: (.+)$", frontmatter, re.M)
        assert name and name[1] == path.parent.name, f"Invalid skill name: {path}"
        assert description and len(description[1]) <= 1024, f"Invalid description: {path}"
    files = [ROOT / "README.md", *sorted((ROOT / "skills").rglob("*.md"))]
    blocks = sum(validate_markdown(path) for path in files)
    print(f"Validated {len(skills)} skill(s), {len(files)} Markdown files, {blocks} code blocks")


if __name__ == "__main__":
    main()
