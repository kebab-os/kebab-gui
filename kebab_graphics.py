"""kebab_graphics runtime facade.

This module provides a pygame-compatible API surface while allowing the
underlying renderer/input backend to be swapped in the future.
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType
from typing import Dict


_BACKEND_ENV_VAR = "KEBAB_GRAPHICS_BACKEND"
_DEFAULT_BACKEND = "pygame"
_KNOWN_BACKENDS: Dict[str, str] = {
    "pygame": "pygame",
}

_backend_name: str | None = None
_backend_module: ModuleType | None = None


def register_backend(name: str, module_path: str) -> None:
    """Register a backend import path.

    Example:
        register_backend("mygpu", "kebab_graphics_backends.mygpu")
    """
    clean_name = str(name).strip().lower()
    if not clean_name:
        raise ValueError("Backend name cannot be empty")
    _KNOWN_BACKENDS[clean_name] = str(module_path).strip()


def _resolve_backend_module_path(name: str) -> str:
    key = str(name).strip().lower()
    if key in _KNOWN_BACKENDS:
        return _KNOWN_BACKENDS[key]
    # Allow direct module paths so experimental backends can be tested
    # without changing this file.
    return name


def _load_backend(name: str) -> ModuleType:
    module_path = _resolve_backend_module_path(name)
    try:
        return importlib.import_module(module_path)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load kebab_graphics backend '{name}' via '{module_path}': {exc}"
        ) from exc


def set_backend(name: str) -> ModuleType:
    """Set the active backend module by logical name or module path."""
    global _backend_name, _backend_module
    selected = str(name or "").strip() or _DEFAULT_BACKEND
    module = _load_backend(selected)
    _backend_name = selected
    _backend_module = module
    return module


def get_backend_name() -> str:
    """Return the currently active backend identifier."""
    if _backend_name is None:
        _bootstrap_backend()
    return str(_backend_name)


def get_backend_module() -> ModuleType:
    """Return the currently active backend module object."""
    if _backend_module is None:
        _bootstrap_backend()
    return _backend_module


def _bootstrap_backend() -> None:
    requested = os.environ.get(_BACKEND_ENV_VAR, _DEFAULT_BACKEND)
    set_backend(requested)


def __getattr__(name: str):
    # Forward everything not defined in this module to the active backend
    # so existing pygame-style code keeps working unchanged.
    backend = get_backend_module()
    return getattr(backend, name)


def __dir__():
    backend = get_backend_module()
    return sorted(set(globals()) | set(dir(backend)))


_bootstrap_backend()
