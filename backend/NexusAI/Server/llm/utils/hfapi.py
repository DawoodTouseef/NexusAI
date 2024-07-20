from __future__ import annotations

from importlib.metadata import version

from packaging.version import parse

def is_huggingface_v1() -> bool:
    """Return whether OpenAI API is v1 or more."""
    _version = parse(version("huggingface_hub"))
    return _version.major >= 0

