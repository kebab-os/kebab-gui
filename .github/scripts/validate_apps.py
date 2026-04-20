"""
Validates every app.py found in src/applications/<AppName>/app.py.

Each app must satisfy:
  1. `import pygame` (directly or as part of a multi-import)
  2. A module-level `config` dict literal that contains both "width" and "height" keys
  3. A function named `init_data` with no required parameters
  4. A function named `draw_content` with exactly 4 parameters
"""

import ast
import sys
from pathlib import Path


def has_pygame_import(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "pygame" or alias.name.startswith("pygame.") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "pygame" or (node.module and node.module.startswith("pygame.")):
                return True
    return False


def get_config_keys(tree: ast.Module) -> set:
    """Return the string keys present in the top-level `config = {...}` assignment, or empty set."""
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "config"
            and isinstance(node.value, ast.Dict)
        ):
            keys = set()
            for k in node.value.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    keys.add(k.value)
            return keys
    return set()


def get_function_param_count(tree: ast.Module, func_name: str):
    """Return the number of parameters of the first top-level function with func_name, or None."""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            args = node.args
            return len(args.args)
    return None


def validate_app(app_path: Path) -> list[str]:
    errors = []
    try:
        source = app_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Cannot read file: {exc}"]

    try:
        tree = ast.parse(source, filename=str(app_path))
    except SyntaxError as exc:
        return [f"Syntax error: {exc}"]

    # Rule 1 – pygame import
    if not has_pygame_import(tree):
        errors.append("Missing `import pygame`")

    # Rule 2 – config dict with width and height
    config_keys = get_config_keys(tree)
    if not config_keys:
        errors.append("Missing module-level `config` dict assignment")
    else:
        for required in ("width", "height"):
            if required not in config_keys:
                errors.append(f"`config` dict is missing the \"{required}\" key")

    # Rule 3 – init_data()
    init_params = get_function_param_count(tree, "init_data")
    if init_params is None:
        errors.append("Missing `init_data` function")
    elif init_params != 0:
        errors.append(f"`init_data` must take 0 parameters, found {init_params}")

    # Rule 4 – draw_content(surface, rect, data, is_active)
    draw_params = get_function_param_count(tree, "draw_content")
    if draw_params is None:
        errors.append("Missing `draw_content` function")
    elif draw_params != 4:
        errors.append(f"`draw_content` must take 4 parameters, found {draw_params}")

    return errors


def main() -> int:
    apps_dir = Path("src/applications")
    if not apps_dir.is_dir():
        print(f"ERROR: {apps_dir} directory not found", file=sys.stderr)
        return 1

    app_dirs = sorted(p for p in apps_dir.iterdir() if p.is_dir())
    if not app_dirs:
        print("No application folders found in src/applications.")
        return 0

    overall_ok = True
    for app_dir in app_dirs:
        app_py = app_dir / "app.py"
        if not app_py.exists():
            print(f"[FAIL] {app_dir.name}: missing app.py")
            overall_ok = False
            continue

        errors = validate_app(app_py)
        if errors:
            overall_ok = False
            print(f"[FAIL] {app_dir.name}/app.py:")
            for err in errors:
                print(f"       - {err}")
        else:
            print(f"[ OK ] {app_dir.name}/app.py")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
