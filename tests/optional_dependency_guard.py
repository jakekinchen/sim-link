"""Static collection-time guards for tests with optional heavy dependencies."""

from __future__ import annotations

import ast
import importlib.util

from pathlib import Path


OPTIONAL_IMPORT_ROOTS = frozenset(
    {
        "bpy",
        "drake",
        "hy3dgen",
        "manifold3d",
        "pydrake",
        "pyrender",
        "requests",
        "scipy",
        "trimesh",
    }
)


def missing_top_level_optional_dependency(path: Path) -> str | None:
    """Return the first missing optional import in a local import graph.

    The graph is inspected before pytest imports a test module.  This avoids
    turning an unavailable optional package into a collection error while
    leaving tests with no missing dependency fully collectible.
    """

    pending = [Path(path)]
    visited: set[Path] = set()
    while pending:
        current = pending.pop()
        if current in visited or not current.is_file():
            continue
        visited.add(current)
        try:
            tree = ast.parse(current.read_text(encoding="utf-8"), filename=str(current))
        except (OSError, SyntaxError):
            continue
        for module in _top_level_imports(tree):
            root = module.split(".", 1)[0]
            if root in OPTIONAL_IMPORT_ROOTS:
                try:
                    present = importlib.util.find_spec(root) is not None
                except (ImportError, ModuleNotFoundError, ValueError):
                    present = False
                if not present:
                    return root
            repo_root = next(
                (parent for parent in current.parents if (parent / "scenesmith").is_dir()),
                current.parent,
            )
            local = _local_module_path(module, repo_root=repo_root)
            if local is not None:
                pending.append(local)
    return None


def _top_level_imports(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.append(node.module)
    return tuple(modules)


def _local_module_path(module: str, *, repo_root: Path) -> Path | None:
    if not (module == "scenesmith" or module.startswith("scenesmith.") or module == "tests" or module.startswith("tests.")):
        return None
    relative = Path(*module.split("."))
    package_path = repo_root / relative / "__init__.py"
    if package_path.is_file():
        return package_path
    module_path = repo_root / relative.with_suffix(".py")
    return module_path if module_path.is_file() else None
