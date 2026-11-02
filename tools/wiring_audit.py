#!/usr/bin/env python3
"""
Static wiring audit — "is everything actually connected?" in about a second.

    python tools/wiring_audit.py

Checks (exit code 1 if any ERROR):
  1. IMPORTS    every `from src.X import name` / `import src.X` points at a real
                module AND (for `from`) a name that module really defines.
                Catches renamed/deleted functions and typos before runtime.
  2. ORPHANS    every src/*.py module is reachable from at least one entry point
                (main_story.py, src/story_analytics_sync.py). A module nothing imports is dead weight —
                or, worse, a feature that was built but never connected.
  3. SECRETS    every secret the story bot needs is passed to the story workflow
                (.github/workflows/run-story-bot.yml) — a missing line there means
                a platform silently never publishes.
  4. WORKFLOWS  each workflow's `python ...` entry point exists.

Set WIRING_AUDIT_IGNORE_MODULES=a,b to skip modules that genuinely are not
present in a partial checkout (used only by the build sandbox).
"""
import ast
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ENTRY_POINTS = ["main_story.py", "src/story_analytics_sync.py"]
ALLOWED_ORPHANS: set[str] = set()   # module names (no .py) you consciously keep unconnected
REQUIRED_STORY_SECRETS = [
    "GEMINI_API_KEY", "YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN",
    "PIXABAY_API_KEY", "PEXELS_API_KEY", "POLLINATIONS_API_KEY", "FREESOUND_API_KEY",
    "FB_PAGE_ID", "FB_ACCESS_TOKEN", "IG_USER_ID",
]
IGNORE = {m for m in os.environ.get("WIRING_AUDIT_IGNORE_MODULES", "").split(",") if m}

errors: list[str] = []
warnings: list[str] = []


def top_level_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        names.add(n.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                names.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, (ast.If, ast.Try)):  # conditional definitions
            for sub in ast.walk(node):
                if isinstance(sub, (ast.FunctionDef, ast.ClassDef)):
                    names.add(sub.name)
                elif isinstance(sub, ast.Assign):
                    for t in sub.targets:
                        for n in ast.walk(t):
                            if isinstance(n, ast.Name):
                                names.add(n.id)
    return names


def parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as e:
        errors.append(f"SYNTAX  {path.relative_to(ROOT)}: {e}")
        return None


def module_file(mod: str) -> Path | None:
    p = ROOT / (mod.replace(".", "/") + ".py")
    return p if p.exists() else None


def main() -> int:
    py_files = sorted(SRC.glob("*.py")) + [ROOT / n for n in ("main_story.py",) if (ROOT / n).exists()]
    trees = {f: parse(f) for f in py_files}
    defined = {f: top_level_names(t) for f, t in trees.items() if t}
    edges: dict[str, set[str]] = {}   # module -> src modules it imports

    # 1) imports resolve to real names
    for f, tree in trees.items():
        if tree is None:
            continue
        rel = f.relative_to(ROOT).as_posix()
        key = rel[:-3].replace("/", ".")
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "src":
                target = node.module
                edges.setdefault(key, set()).add(target)
                if node.module == "src":  # `from src import a, b` -> submodules
                    for a in node.names:
                        edges[key].add(f"src.{a.name}")
                        if module_file(f"src.{a.name}") is None and a.name not in IGNORE:
                            errors.append(f"IMPORT  {rel}:{node.lineno}  src.{a.name} does not exist")
                    continue
                tf = module_file(target)
                if tf is None:
                    if target.split(".")[-1] not in IGNORE:
                        errors.append(f"IMPORT  {rel}:{node.lineno}  module {target} does not exist")
                    continue
                avail = defined.get(tf) or (top_level_names(parse(tf)) if parse(tf) else set())
                for a in node.names:
                    if a.name != "*" and a.name not in avail:
                        errors.append(f"IMPORT  {rel}:{node.lineno}  {target} has no top-level name '{a.name}'")
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] == "src":
                        edges.setdefault(key, set()).add(a.name)
                        if module_file(a.name) is None and a.name.split(".")[-1] not in IGNORE:
                            errors.append(f"IMPORT  {rel}:{node.lineno}  module {a.name} does not exist")

    # 2) orphan modules
    reachable: set[str] = set()
    stack = [e[:-3].replace("/", ".") for e in ENTRY_POINTS if (ROOT / e).exists()]
    while stack:
        m = stack.pop()
        if m in reachable:
            continue
        reachable.add(m)
        stack.extend(edges.get(m, ()))
    for f in SRC.glob("*.py"):
        name = f.stem
        if name == "__init__" or name in ALLOWED_ORPHANS or name in IGNORE:
            continue
        if f"src.{name}" not in reachable:
            errors.append(f"ORPHAN  src/{name}.py is imported by nothing reachable from {', '.join(ENTRY_POINTS)}")

    # 3) secrets wired into the story workflow
    wf_dir = ROOT / ".github" / "workflows"
    story_wf = wf_dir / "run-story-bot.yml"
    if story_wf.exists():
        provided = set(re.findall(r"^\s+([A-Z][A-Z0-9_]+):\s*\$\{\{\s*secrets\.", story_wf.read_text(), re.M))
        for secret in REQUIRED_STORY_SECRETS:
            if secret not in provided:
                errors.append(f"SECRET  {secret} is not passed to run-story-bot.yml (that platform would silently never work)")
    else:
        warnings.append("run-story-bot.yml not found — secret wiring not checked")

    # 4) workflows point at real entry points
    for wf in sorted(wf_dir.glob("*.yml")) if wf_dir.exists() else []:
        text = wf.read_text()
        for cmd in re.findall(r"run:\s*python3?\s+(?:-m\s+)?([\w./]+)", text):
            target = ROOT / cmd if cmd.endswith(".py") else ROOT / (cmd.replace(".", "/") + ".py")
            if not target.exists():
                errors.append(f"WORKFLOW {wf.name} runs `{cmd}` but {target.relative_to(ROOT)} does not exist")

    n_mods = len(list(SRC.glob("*.py"))) - 1
    for w in warnings:
        print("WARN  ", w)
    for e in errors:
        print("ERROR ", e)
    if errors:
        print(f"\nWIRING AUDIT FAILED: {len(errors)} problem(s)")
        return 1
    print(f"WIRING AUDIT OK: {n_mods} src modules, every import resolves, none orphaned, "
          f"all {len(REQUIRED_STORY_SECRETS)} story secrets wired into the workflow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
