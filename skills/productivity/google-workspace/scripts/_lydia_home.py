"""Resolve LYDIA_HOME for standalone skill scripts.

Skill scripts may run outside the Lydia process (e.g. system Python,
nix env, CI) where ``lydia_constants`` is not importable.  This module
provides the same ``get_lydia_home()`` and ``display_lydia_home()``
contracts as ``lydia_constants`` without requiring it on ``sys.path``.

When ``lydia_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``lydia_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``LYDIA_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from lydia_constants import display_lydia_home as display_lydia_home
    from lydia_constants import get_lydia_home as get_lydia_home
except (ModuleNotFoundError, ImportError):

    def get_lydia_home() -> Path:
        """Return the Lydia home directory (default: ~/.lydia).

        Mirrors ``lydia_constants.get_lydia_home()``."""
        val = os.environ.get("LYDIA_HOME", "").strip()
        return Path(val) if val else Path.home() / ".lydia"

    def display_lydia_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``lydia_constants.display_lydia_home()``."""
        home = get_lydia_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
