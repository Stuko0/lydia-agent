"""Lydia CLI skin/theme engine.

A data-driven skin system that lets users customize the CLI's visual appearance.
Skins are defined as YAML files in ~/.lydia/skins/ or as built-in presets.
No code changes are needed to add a new skin.

SKIN YAML SCHEMA
================

All fields are optional. Missing values inherit from the ``default`` skin.

.. code-block:: yaml

    # Required: skin identity
    name: mytheme                         # Unique skin name (lowercase, hyphens ok)
    description: Short description        # Shown in /skin listing

    # Colors: hex values for Rich markup (banner, UI, response box)
    colors:
      banner_border: "#56526e"            # Panel border color
      banner_title: "#c4a7e7"             # Panel title text color
      banner_accent: "#ea9a97"            # Section headers (Available Tools, etc.)
      banner_dim: "#6e6a86"               # Dim/muted text (separators, labels)
      banner_text: "#e0def4"              # Body text (tool names, skill names)
      ui_accent: "#ea9a97"               # General UI accent
      ui_label: "#908caa"                # UI labels
      ui_ok: "#9ccfd8"                   # Success indicators
      ui_error: "#eb6f92"                # Error indicators
      ui_warn: "#f6c177"                 # Warning indicators
      prompt: "#e0def4"                  # Prompt text color
      input_rule: "#56526e"              # Input area horizontal rule
      response_border: "#c4a7e7"         # Response box border (ANSI)
      status_bar_bg: "#2a273f"           # Status bar background
      status_bar_text: "#e0def4"         # Status bar default text
      status_bar_strong: "#c4a7e7"       # Status bar highlighted text
      status_bar_dim: "#6e6a86"          # Status bar separators/muted text
      status_bar_good: "#9ccfd8"         # Healthy context usage
      status_bar_warn: "#f6c177"         # Warning context usage
      status_bar_bad: "#eb6f92"          # High context usage
      status_bar_critical: "#eb6f92"     # Critical context usage
      session_label: "#908caa"           # Session label color
      session_border: "#6e6a86"          # Session ID dim color
      status_bar_bg: "#2a273f"          # TUI status/usage bar background
      voice_status_bg: "#2a273f"        # TUI voice status background
      selection_bg: "#393552"           # TUI mouse-selection highlight background
      completion_menu_bg: "#2a273f"      # Completion menu background
      completion_menu_current_bg: "#393552"  # Active completion row background
      completion_menu_meta_bg: "#2a273f"     # Completion meta column background
      completion_menu_meta_current_bg: "#393552"  # Active completion meta background

    # Spinner: customize the animated spinner during API calls
    spinner:
      waiting_faces:                      # Faces shown while waiting for API
        - "(⚔)"
        - "(⛨)"
      thinking_faces:                     # Faces shown during reasoning
        - "(⌁)"
        - "(<>)"
      thinking_verbs:                     # Verbs for spinner messages
        - "forging"
        - "plotting"
      wings:                              # Optional left/right spinner decorations
        - ["⟪⚔", "⚔⟫"]                  # Each entry is [left, right] pair
        - ["⟪▲", "▲⟫"]

    # Branding: text strings used throughout the CLI
    branding:
      agent_name: "Lydia Agent"          # Banner title, status display
      welcome: "Welcome message"          # Shown at CLI startup
      goodbye: "Goodbye! ✦"              # Shown on exit
      response_label: " ✦ Lydia "       # Response box header label
      prompt_symbol: "❯"                 # Input prompt symbol (bare token; renderers add trailing space)
      help_header: "(^_^)? Commands"      # /help header text

    # Status symbols: override the default text symbols for status indicators
    status_symbols:
      success: "✓"          # Success indicator (instead of ✅)
      error: "✗"            # Error indicator (instead of ❌)
      warning: "⚠"          # Warning indicator
      info: "◆"             # Info marker
      brand: "✦"            # Branding marker (instead of 🌹)
      celebration: "★"      # Celebration marker (instead of 🎉)
      bullet: "•"           # Bullet point

    # Tool prefix: character for tool output lines (default: ┊)
    tool_prefix: "┊"

    # Tool emojis: override the default emoji for any tool (used in spinners & progress)
    tool_emojis:
      terminal: "⚔"           # Override terminal tool emoji
      web_search: "🔮"        # Override web_search tool emoji
      # Any tool not listed here uses its registry default

USAGE
=====

.. code-block:: python

    from lydia_cli.skin_engine import get_active_skin, list_skins, set_active_skin

    skin = get_active_skin()
    print(skin.colors["banner_title"])    # "#c4a7e7"
    print(skin.get_branding("agent_name"))  # "Lydia Agent"

    set_active_skin("ares")               # Switch to built-in ares skin
    set_active_skin("mytheme")            # Switch to user skin from ~/.lydia/skins/

BUILT-IN SKINS
==============

- ``default`` — Classic Lydia gold/kawaii (the current look)
- ``mono``    — Clean grayscale monochrome
- ``slate``   — Cool blue developer-focused theme
- ``daylight`` — Light background theme with dark text and blue accents
- ``warm-lightmode`` — Warm brown/gold text for light terminal backgrounds

USER SKINS
==========

Drop a YAML file in ``~/.lydia/skins/<name>.yaml`` following the schema above.
Activate with ``/skin <name>`` in the CLI or ``display.skin: <name>`` in config.yaml.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lydia_constants import get_lydia_home

logger = logging.getLogger(__name__)


# =============================================================================
# Skin data structure
# =============================================================================

@dataclass
class SkinConfig:
    """Complete skin configuration."""
    name: str
    description: str = ""
    colors: Dict[str, str] = field(default_factory=dict)
    spinner: Dict[str, Any] = field(default_factory=dict)
    branding: Dict[str, str] = field(default_factory=dict)
    tool_prefix: str = "┊"
    tool_emojis: Dict[str, str] = field(default_factory=dict)  # per-tool emoji overrides
    status_symbols: Dict[str, str] = field(default_factory=dict)  # status symbol overrides
    banner_logo: str = ""    # Rich-markup ASCII art logo (replaces LYDIA_AGENT_LOGO)
    banner_hero: str = ""    # Rich-markup hero art (replaces LYDIA_CADUCEUS)

    def get_color(self, key: str, fallback: str = "") -> str:
        """Get a color value with fallback."""
        return self.colors.get(key, fallback)

    def get_spinner_wings(self) -> List[Tuple[str, str]]:
        """Get spinner wing pairs, or empty list if none."""
        raw = self.spinner.get("wings", [])
        result = []
        for pair in raw:
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                result.append((str(pair[0]), str(pair[1])))
        return result

    def get_branding(self, key: str, fallback: str = "") -> str:
        """Get a branding value with fallback."""
        return self.branding.get(key, fallback)

    def get_status_symbol(self, key: str, fallback: str = "") -> str:
        """Get a status symbol (success/error/warning/etc) with fallback.

        Falls back to the default StatusSymbols value if the skin doesn't
        override this particular key.
        """
        if key in self.status_symbols:
            return self.status_symbols[key]
        return getattr(_DEFAULT_STATUS_SYMBOLS, key, fallback)


# Default status symbols (used when a skin doesn't override)
@dataclass
class _StatusSymbolsDefaults:
    success: str = "✓"
    error: str = "✗"
    warning: str = "⚠"
    info: str = "◆"
    brand: str = "✦"
    celebration: str = "★"
    bullet: str = "•"


_DEFAULT_STATUS_SYMBOLS = _StatusSymbolsDefaults()


# =============================================================================
# Built-in skin definitions
# =============================================================================

_BUILTIN_SKINS: Dict[str, Dict[str, Any]] = {
    "default": {
        "name": "default",
        "description": "Rose Pine Moon — iris, rose, and foam",
        "colors": {
            "banner_border": "#56526e",
            "banner_title": "#c4a7e7",
            "banner_accent": "#ea9a97",
            "banner_dim": "#6e6a86",
            "banner_text": "#e0def4",
            "ui_accent": "#ea9a97",
            "ui_label": "#908caa",
            "ui_ok": "#9ccfd8",
            "ui_error": "#eb6f92",
            "ui_warn": "#f6c177",
            "prompt": "#e0def4",
            "input_rule": "#56526e",
            "response_border": "#c4a7e7",
            "status_bar_bg": "#2a273f",
            "session_label": "#908caa",
            "session_border": "#6e6a86",
        },
        "spinner": {
            # Empty = use hardcoded defaults in display.py
        },
        "branding": {
            "agent_name": "Lydia Agent",
            "welcome": "Welcome to Lydia Agent! Type your message or /help for commands.",
            "goodbye": "Goodbye! ✦",
            "response_label": " ✦ Lydia ",
            "prompt_symbol": "❯",
            "help_header": "(^_^)? Available Commands",
        },
        "tool_prefix": "┊",
    },
    "mono": {
        "name": "mono",
        "description": "Monochrome — clean grayscale",
        "colors": {
            "banner_border": "#555555",
            "banner_title": "#e6edf3",
            "banner_accent": "#aaaaaa",
            "banner_dim": "#444444",
            "banner_text": "#c9d1d9",
            "ui_accent": "#aaaaaa",
            "ui_label": "#888888",
            "ui_ok": "#888888",
            "ui_error": "#cccccc",
            "ui_warn": "#999999",
            "prompt": "#c9d1d9",
            "input_rule": "#444444",
            "response_border": "#aaaaaa",
            "status_bar_bg": "#1F1F1F",
            "status_bar_text": "#C9D1D9",
            "status_bar_strong": "#E6EDF3",
            "status_bar_dim": "#777777",
            "status_bar_good": "#B5B5B5",
            "status_bar_warn": "#AAAAAA",
            "status_bar_bad": "#D0D0D0",
            "status_bar_critical": "#F0F0F0",
            "session_label": "#888888",
            "session_border": "#555555",
        },
        "spinner": {},
        "branding": {
            "agent_name": "Lydia Agent",
            "welcome": "Welcome to Lydia Agent! Type your message or /help for commands.",
            "goodbye": "Goodbye! ✦",
            "response_label": " ✦ Lydia ",
            "prompt_symbol": "❯",
            "help_header": "[?] Available Commands",
        },
        "tool_prefix": "┊",
    },
    "slate": {
        "name": "slate",
        "description": "Cool blue — developer-focused",
        "colors": {
            "banner_border": "#4169e1",
            "banner_title": "#7eb8f6",
            "banner_accent": "#8EA8FF",
            "banner_dim": "#4b5563",
            "banner_text": "#c9d1d9",
            "ui_accent": "#7eb8f6",
            "ui_label": "#8EA8FF",
            "ui_ok": "#7eb8f6",
            "ui_error": "#ef5350",
            "ui_warn": "#ffa726",
            "prompt": "#e0def4",
            "input_rule": "#4169e1",
            "response_border": "#7eb8f6",
            "status_bar_bg": "#0d1117",
            "status_bar_text": "#c9d1d9",
            "status_bar_strong": "#7eb8f6",
            "status_bar_dim": "#484f58",
            "status_bar_good": "#7eb8f6",
            "status_bar_warn": "#ffa726",
            "status_bar_bad": "#ef5350",
            "status_bar_critical": "#ef5350",
            "session_label": "#8EA8FF",
            "session_border": "#4169e1",
        },
        "spinner": {},
        "branding": {
            "agent_name": "Lydia Agent",
            "welcome": "Welcome to Lydia Agent! Type your message or /help for commands.",
            "goodbye": "Goodbye! ✦",
            "response_label": " ✦ Lydia ",
            "prompt_symbol": "❯",
            "help_header": "(^-^) Available Commands",
        },
        "tool_prefix": "┊",
    },
    "daylight": {
        "name": "daylight",
        "description": "Light theme — dark text, blue accents",
        "colors": {
            "banner_border": "#d0d0d0",
            "banner_title": "#2c2c2c",
            "banner_accent": "#3b82f6",
            "banner_dim": "#888888",
            "banner_text": "#1a1a1a",
            "ui_accent": "#3b82f6",
            "ui_label": "#6b7280",
            "ui_ok": "#16a34a",
            "ui_error": "#dc2626",
            "ui_warn": "#d97706",
            "prompt": "#1a1a1a",
            "input_rule": "#d0d0d0",
            "response_border": "#3b82f6",
            "status_bar_bg": "#f3f4f6",
            "status_bar_text": "#1a1a1a",
            "status_bar_strong": "#3b82f6",
            "status_bar_dim": "#9ca3af",
            "status_bar_good": "#16a34a",
            "status_bar_warn": "#d97706",
            "status_bar_bad": "#dc2626",
            "status_bar_critical": "#dc2626",
            "session_label": "#6b7280",
            "session_border": "#d0d0d0",
        },
        "spinner": {},
        "branding": {
            "agent_name": "Lydia Agent",
            "welcome": "Welcome to Lydia Agent! Type your message or /help for commands.",
            "goodbye": "Goodbye! ✦",
            "response_label": " ✦ Lydia ",
            "prompt_symbol": "❯",
            "help_header": "(^-^) Available Commands",
        },
        "tool_prefix": "┊",
    },
    "warm-lightmode": {
        "name": "warm-lightmode",
        "description": "Warm brown/gold — light terminal backgrounds",
        "colors": {
            "banner_border": "#d4c5a9",
            "banner_title": "#3d3228",
            "banner_accent": "#c45a6b",
            "banner_dim": "#8b7d6b",
            "banner_text": "#3d3228",
            "ui_accent": "#c45a6b",
            "ui_label": "#7d6e5a",
            "ui_ok": "#5a8a7a",
            "ui_error": "#a8213a",
            "ui_warn": "#b8864e",
            "prompt": "#3d3228",
            "input_rule": "#d4c5a9",
            "response_border": "#b8864e",
            "status_bar_bg": "#f5f0e8",
            "status_bar_text": "#3d3228",
            "status_bar_strong": "#c45a6b",
            "status_bar_dim": "#8b7d6b",
            "status_bar_good": "#5a8a7a",
            "status_bar_warn": "#b8864e",
            "status_bar_bad": "#a8213a",
            "status_bar_critical": "#a8213a",
            "session_label": "#7d6e5a",
            "session_border": "#d4c5a9",
        },
        "spinner": {},
        "branding": {
            "agent_name": "Lydia Agent",
            "welcome": "Welcome to Lydia Agent! Type your message or /help for commands.",
            "goodbye": "Goodbye! ✦",
            "response_label": " ✦ Lydia ",
            "prompt_symbol": "❯",
            "help_header": "(^-^) Available Commands",
        },
        "tool_prefix": "┊",
    },
    "dragon": {
        "name": "dragon",
        "description": "Draconic breath — flame-forged embers",
        "colors": {
            "banner_border": "#6B3A2A",
            "banner_title": "#FFF0D4",
            "banner_accent": "#F29C38",
            "banner_dim": "#7A3511",
            "banner_text": "#FFD39A",
            "ui_accent": "#F29C38",
            "ui_label": "#E2832B",
            "ui_ok": "#4CAF50",
            "ui_error": "#EF5350",
            "ui_warn": "#FFA726",
            "prompt": "#FFD39A",
            "input_rule": "#6B3A2A",
            "response_border": "#F29C38",
            "status_bar_bg": "#1A0F0A",
            "status_bar_text": "#FFD39A",
            "status_bar_strong": "#FFF0D4",
            "status_bar_dim": "#7A3511",
            "status_bar_good": "#7BC96F",
            "status_bar_warn": "#F29C38",
            "status_bar_bad": "#E2832B",
            "status_bar_critical": "#EF5350",
            "session_label": "#E2832B",
            "session_border": "#6B3A2A",
        },
        "spinner": {
            "waiting_faces": ["(✦)", "(▲)", "(◇)", "(<>)", "(🔥)"],
            "thinking_faces": ["(✦)", "(▲)", "(◇)", "(⌁)", "(🔥)"],
            "thinking_verbs": [
                "banking into the draft", "measuring burn", "reading the updraft",
                "tracking ember fall", "setting wing angle", "holding the flame core",
                "plotting a hot landing", "coiling for lift",
            ],
            "wings": [
                ["⟪✦", "✦⟫"],
                ["⟪▲", "▲⟫"],
                ["⟪◌", "◌⟫"],
                ["⟪◇", "◇⟫"],
            ],
        },
        "branding": {
            "agent_name": "Lydia Agent",
            "welcome": "Welcome to Lydia Agent! Type your message or /help for commands.",
            "goodbye": "Flame out! ✦",
            "response_label": " ✦ Lydia ",
            "prompt_symbol": "✦",
            "help_header": "(✦) Available Commands",
        },
        "tool_prefix": "│",
        "banner_logo": """[bold #FFF0D4] ██████╗██╗  ██╗ █████╗ ██████╗ ██╗███████╗ █████╗ ██████╗ ██████╗        █████╗  ██████╗ ███████╗███╗   ██╗████████╗[/]
[bold #FFD39A]██╔════╝██║  ██║██╔══██╗██╔══██╗██║╚══███╔╝██╔══██╗██╔══██╗██╔══██╗      ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝[/]
[#F29C38]██║     ███████║███████║██████╔╝██║  ███╔╝ ███████║██████╔╝██║  ██║█████╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║[/]
[#E2832B]██║     ██╔══██║██╔══██║██╔══██╗██║ ███╔╝  ██╔══██║██╔══██╗██║  ██║╚════╝██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║[/]
[#C75B1D]╚██████╗██║  ██║██║  ██║██║  ██║██║███████╗██║  ██║██║  ██║██████╔╝      ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║[/]
[#7A3511] ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝       ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝[/]""",
        "banner_hero": """[#FFD39A]⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⠶⠶⠶⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#F29C38]⠀⠀⠀⠀⠀⠀⣴⠟⠁⠀⠀⠀⠀⠈⠻⣦⠀⠀⠀⠀⠀⠀[/]
[#F29C38]⠀⠀⠀⠀⠀⣼⠏⠀⠀⠀✦⠀⠀⠀⠀⠹⣧⠀⠀⠀⠀⠀[/]
[#E2832B]⠀⠀⠀⠀⢰⡟⠀⠀⣀⣤⣤⣤⣀⠀⠀⠀⢻⡆⠀⠀⠀⠀[/]
[#E2832B]⠀⠀⣠⡾⠛⠁⣠⣾⠟⠉⠀⠉⠻⣷⣄⠀⠈⠛⢷⣄⠀⠀[/]
[#C75B1D]⠀⣼⠟⠀⢀⣾⠟⠁⠀⠀⠀⠀⠀⠈⠻⣷⡀⠀⠻⣧⠀[/]
[#C75B1D]⢸⡟⠀⠀⣿⡟⠀⠀⠀🔥⠀⠀⠀⠀⢻⣿⠀⠀⢻⡇[/]
[#7A3511]⠀⠻⣦⡀⠘⢿⣧⡀⠀⠀⠀⠀⠀⢀⣼⡿⠃⢀⣴⠟⠀[/]
[#7A3511]⠀⠀⠈⠻⣦⣀⠙⢿⣷⣤⣤⣤⣾⡿⠋⣀⣴⠟⠁⠀⠀[/]
[#C75B1D]⠀⠀⠀⠀⠈⠙⠛⠶⠤⠭⠭⠤⠶⠛⠋⠁⠀⠀⠀⠀[/]
[#F29C38]⠀⠀⠀⠀⠀⠀⠀⠀⣰⡿⢿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#F29C38]⠀⠀⠀⠀⠀⠀⠀⣼⡟⠀⠀⢻⣧⠀⠀⠀⠀⠀⠀⠀⠀[/]
[dim #7A3511]⠀⠀⠀⠀⠀⠀tail flame lit⠀⠀⠀⠀⠀⠀⠀⠀[/]""",
    },
    "alice": {
        "name": "alice",
        "description": "Alice's Descent — Victorian card-deck gothic dark ♠♥♦♣",
        "colors": {
            "banner_border": "#413d57",
            "banner_title": "#d4cfc7",
            "banner_accent": "#c45a6b",
            "banner_dim": "#6e687c",
            "banner_text": "#d4cfc7",
            "ui_accent": "#c45a6b",
            "ui_label": "#958da5",
            "ui_ok": "#4fa8a8",
            "ui_error": "#a8213a",
            "ui_warn": "#b8864e",
            "prompt": "#d4cfc7",
            "input_rule": "#413d57",
            "response_border": "#7848a0",
            "status_bar_bg": "#16131f",
            "status_bar_text": "#d4cfc7",
            "status_bar_strong": "#c45a6b",
            "status_bar_dim": "#6e687c",
            "status_bar_good": "#4fa8a8",
            "status_bar_warn": "#b8864e",
            "status_bar_bad": "#a8213a",
            "status_bar_critical": "#a8213a",
            "session_label": "#958da5",
            "session_border": "#6e687c",
            "selection_bg": "#2d2940",
            "voice_status_bg": "#221e30",
            "completion_menu_bg": "#221e30",
            "completion_menu_current_bg": "#2d2940",
            "completion_menu_meta_bg": "#191622",
            "completion_menu_meta_current_bg": "#2d2940",
        },
        "spinner": {
            "waiting_faces": ["(♠)", "(♥)", "(♦)", "(♣)"],
            "thinking_faces": ["(♠)", "(♥)", "(♦)", "(♣)"],
            "thinking_verbs": [
                "dealing", "shuffling", "cutting the deck", "drawing a card",
                "falling down the hole", "reading the spread", "weaving fate", "consulting the oracles",
            ],
            "wings": [
                ["♠", "♣"],
                ["♥", "♦"],
                ["♠", "♦"],
                ["♣", "♥"],
            ],
        },
        "branding": {
            "agent_name": "Alice Agent",
            "welcome": "Curiouser and curiouser! — Down the rabbit hole we go. ♠♥♦♣",
            "goodbye": "We're all mad here. ♠♥♦♣",
            "response_label": " ♥ Alice ♥ ",
            "prompt_symbol": "♠",
            "help_header": "(♠♥♦♣) Available Commands",
        },
        "tool_prefix": "♧",
        "status_symbols": {
            "success": "♠",
            "error": "♣",
            "warning": "♦",
            "info": "❧",
            "brand": "♠",
            "celebration": "✦",
            "bullet": "•",
        },
        "tool_emojis": {
            "terminal": "♠",
            "web_search": "❧",
            "read_file": "✢",
            "write_file": "✒",
            "patch": "✂",
            "browser_navigate": "○",
            "delegate_task": "♛",
            "memory": "∞",
            "cronjob": "♦",
            "todo": "☐",
            "clarify": "❦",
            "execute_code": "⚘",
            "web_extract": "✦",
            "text_to_speech": "♫",
            "computer_use": "◆",
            "skills_list": "♣",
            "skill_manage": "♣",
            "skill_view": "♣",
        },
        "banner_logo": """\
[bold #d4cfc7]██╗     ██╗   ██╗██████╗ ██╗ █████╗      █████╗  ██████╗ ███████╗███╗   ██║████████╗
██║     ╚██╗ ██╔╝██╔══██╗██║██╔══██╗    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
██║      ╚████╔╝ ██║  ██║██║███████║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
██║       ╚██╔╝  ██║  ██║██║██╔══██║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
███████╗   ██║   ██████╔╝██║██║  ██║    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
╚══════╝   ╚═╝   ╚═════╝ ╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝[/]""",
        "banner_hero": """\
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣤⣄⣀⣠⣤⠾⢿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣧⡈⠉⠉⠀⢠⣾⣣⣤⣶⣾⣿⣿⣿⣷⣶⣶⣤⡀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣼⡿⠂⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣶⣿⣿⣿⣿⡟⠁⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣶⣿⣿⣿⣿⣿⣿⡟⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡀⠀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠄⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠁⠀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠿⣿⣿⣿⣿⠿⠃⠀⠀⠀[/]
[#d4cfc7]⠀⠀⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#d4cfc7]⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#d4cfc7]⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀[/]
[#d4cfc7]⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠿⠿⠟⠛⠛⠛⠛⠛⠛⠿⣿⣿⣿⡿⠙⣷⣄⠀⠀⠀⠀⠀⠀[/]
[#d4cfc7]⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⢀⣴⣾⣿⣦⣄⠀⠀⠀⠀⠀⠈⠋⠁⠀⠀⠈⢻⣆⠀⠀⠀⠀⠀[/]
[#d4cfc7]⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣆⠀⠀⠀⠀[/]
[#d4cfc7]⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣆⠀⠀⠀[/]
[#d4cfc7]⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠹⡄⠀⠀[/]
[#d4cfc7]⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⢻⡀⠀[/]
[#d4cfc7]⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣄⠀⠀⠀⠀⠀⠘⣧⠀[/]
[#d4cfc7]⠀⠀⠙⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⢹⡄[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠋⠙⠻⡿⠛⠉⠙⠻⣿⣿⣆⣀⣀⠀⠀⢸⡇[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠉⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠿⠿⠿⠿⠟⠃[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠉⠻⠿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#d4cfc7]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]""",
    },
    "alice-light": {
        "name": "alice-light",
        "description": "Alice's Descent — Victorian card-deck light ♠♥♦♣",
        "colors": {
            "banner_border": "#d4ccc0",
            "banner_title": "#2a2438",
            "banner_accent": "#c45a6b",
            "banner_dim": "#958da5",
            "banner_text": "#2a2438",
            "ui_accent": "#c45a6b",
            "ui_label": "#6e687c",
            "ui_ok": "#3a8c8c",
            "ui_error": "#a8213a",
            "ui_warn": "#b8864e",
            "prompt": "#2a2438",
            "input_rule": "#d4ccc0",
            "response_border": "#7848a0",
            "status_bar_bg": "#f0ebe0",
            "status_bar_text": "#2a2438",
            "status_bar_strong": "#c45a6b",
            "status_bar_dim": "#958da5",
            "status_bar_good": "#3a8c8c",
            "status_bar_warn": "#b8864e",
            "status_bar_bad": "#a8213a",
            "status_bar_critical": "#a8213a",
            "session_label": "#6e687c",
            "session_border": "#958da5",
            "selection_bg": "#ece6da",
            "voice_status_bg": "#faf6ee",
            "completion_menu_bg": "#faf6ee",
            "completion_menu_current_bg": "#ece6da",
            "completion_menu_meta_bg": "#f5f0e8",
            "completion_menu_meta_current_bg": "#ece6da",
        },
        "spinner": {
            "waiting_faces": ["(♠)", "(♥)", "(♦)", "(♣)"],
            "thinking_faces": ["(♠)", "(♥)", "(♦)", "(♣)"],
            "thinking_verbs": [
                "dealing", "shuffling", "cutting the deck", "drawing a card",
                "falling down the hole", "reading the spread", "weaving fate", "consulting the oracles",
            ],
            "wings": [
                ["♠", "♣"],
                ["♥", "♦"],
                ["♠", "♦"],
                ["♣", "♥"],
            ],
        },
        "branding": {
            "agent_name": "Alice Agent",
            "welcome": "Curiouser and curiouser! — Down the rabbit hole we go. ♠♥♦♣",
            "goodbye": "We're all mad here. ♠♥♦♣",
            "response_label": " ♥ Alice ♥ ",
            "prompt_symbol": "♠",
            "help_header": "(♠♥♦♣) Available Commands",
        },
        "tool_prefix": "♧",
        "status_symbols": {
            "success": "♠",
            "error": "♣",
            "warning": "♦",
            "info": "❧",
            "brand": "♠",
            "celebration": "✦",
            "bullet": "•",
        },
        "tool_emojis": {
            "terminal": "♠",
            "web_search": "❧",
            "read_file": "✢",
            "write_file": "✒",
            "patch": "✂",
            "browser_navigate": "○",
            "delegate_task": "♛",
            "memory": "∞",
            "cronjob": "♦",
            "todo": "☐",
            "clarify": "❦",
            "execute_code": "⚘",
            "web_extract": "✦",
            "text_to_speech": "♫",
            "computer_use": "◆",
            "skills_list": "♣",
            "skill_manage": "♣",
            "skill_view": "♣",
        },
        "banner_logo": """\
[bold #2a2438]██╗     ██╗   ██╗██████╗ ██╗ █████╗      █████╗  ██████╗ ███████╗███╗   ██║████████╗
██║     ╚██╗ ██╔╝██╔══██╗██║██╔══██╗    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
██║      ╚████╔╝ ██║  ██║██║███████║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
██║       ╚██╔╝  ██║  ██║██║██╔══██║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
███████╗   ██║   ██████╔╝██║██║  ██║    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
╚══════╝   ╚═╝   ╚═════╝ ╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝[/]""",
        "banner_hero": """\
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣤⣄⣀⣠⣤⠾⢿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣧⡈⠉⠉⠀⢠⣾⣣⣤⣶⣾⣿⣿⣿⣷⣶⣶⣤⡀⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣼⡿⠂⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣶⣿⣿⣿⣿⡟⠁⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣶⣿⣿⣿⣿⣿⣿⡟⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡀⠀⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠀⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠄⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠁⠀⠀[/]
[#2a2438]⠀⠀⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠿⣿⣿⣿⣿⠿⠃⠀⠀⠀[/]
[#2a2438]⠀⠀⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#2a2438]⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#2a2438]⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀[/]
[#2a2438]⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠿⠿⠟⠛⠛⠛⠛⠛⠛⠿⣿⣿⣿⡿⠙⣷⣄⠀⠀⠀⠀⠀⠀[/]
[#2a2438]⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⢀⣴⣾⣿⣦⣄⠀⠀⠀⠀⠀⠈⠋⠁⠀⠀⠈⢻⣆⠀⠀⠀⠀⠀[/]
[#2a2438]⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣆⠀⠀⠀⠀[/]
[#2a2438]⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣆⠀⠀⠀[/]
[#2a2438]⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠹⡄⠀⠀[/]
[#2a2438]⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⢻⡀⠀[/]
[#2a2438]⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣄⠀⠀⠀⠀⠀⠘⣧⠀[/]
[#2a2438]⠀⠀⠙⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⢹⡄[/]
[#2a2438]⠀⠀⠀⠀⠀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠋⠙⠻⡿⠛⠉⠙⠻⣿⣿⣆⣀⣀⠀⠀⢸⡇[/]
[#2a2438]⠀⠀⠀⠀⠀⠉⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠿⠿⠿⠿⠟⠃[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠉⠻⠿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#2a2438]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]""",
    },
}


# =============================================================================
# Skin loading and management
# =============================================================================

_active_skin: Optional[SkinConfig] = None
_active_skin_name: str = "default"


def _skins_dir() -> Path:
    """User skins directory."""
    return get_lydia_home() / "skins"


def _load_skin_from_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """Load a skin definition from a YAML file."""
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict) and "name" in data:
            return data
    except Exception as e:
        logger.debug("Failed to load skin from %s: %s", path, e)
    return None


def _mapping_or_empty(value: Any, *, section: str, skin_name: str) -> Dict[str, Any]:
    """Return a mapping value or an empty dict when the section type is invalid."""
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    logger.warning(
        "Skin '%s' has invalid '%s' section type (%s); ignoring section",
        skin_name,
        section,
        type(value).__name__,
    )
    return {}


def _build_skin_config(data: Dict[str, Any]) -> SkinConfig:
    """Build a SkinConfig from a raw dict (built-in or loaded from YAML)."""
    # Start with default values as base for missing keys
    default = _BUILTIN_SKINS["default"]
    skin_name = str(data.get("name", "unknown"))
    color_overrides = _mapping_or_empty(data.get("colors"), section="colors", skin_name=skin_name)
    spinner_overrides = _mapping_or_empty(data.get("spinner"), section="spinner", skin_name=skin_name)
    branding_overrides = _mapping_or_empty(data.get("branding"), section="branding", skin_name=skin_name)
    emoji_overrides = _mapping_or_empty(data.get("tool_emojis"), section="tool_emojis", skin_name=skin_name)
    status_overrides = _mapping_or_empty(data.get("status_symbols"), section="status_symbols", skin_name=skin_name)

    colors = dict(default.get("colors", {}))
    colors.update(color_overrides)
    spinner = dict(default.get("spinner", {}))
    spinner.update(spinner_overrides)
    branding = dict(default.get("branding", {}))
    branding.update(branding_overrides)

    return SkinConfig(
        name=skin_name,
        description=data.get("description", ""),
        colors=colors,
        spinner=spinner,
        branding=branding,
        tool_prefix=data.get("tool_prefix", default.get("tool_prefix", "┊")),
        tool_emojis=emoji_overrides,
        status_symbols=status_overrides,
        banner_logo=data.get("banner_logo", ""),
        banner_hero=data.get("banner_hero", ""),
    )


def list_skins() -> List[Dict[str, str]]:
    """List all available skins (built-in + user-installed).

    Returns list of {"name": ..., "description": ..., "source": "builtin"|"user"}.
    """
    result = []
    for name, data in _BUILTIN_SKINS.items():
        result.append({
            "name": name,
            "description": data.get("description", ""),
            "source": "builtin",
        })

    skins_path = _skins_dir()
    if skins_path.is_dir():
        for f in sorted(skins_path.glob("*.yaml")):
            data = _load_skin_from_yaml(f)
            if data:
                skin_name = data.get("name", f.stem)
                # Skip if it shadows a built-in
                if any(s["name"] == skin_name for s in result):
                    continue
                result.append({
                    "name": skin_name,
                    "description": data.get("description", ""),
                    "source": "user",
                })

    return result


def load_skin(name: str) -> SkinConfig:
    """Load a skin by name. Checks user skins first, then built-in."""
    # Check user skins directory
    skins_path = _skins_dir()
    user_file = skins_path / f"{name}.yaml"
    if user_file.is_file():
        data = _load_skin_from_yaml(user_file)
        if data:
            return _build_skin_config(data)

    # Check built-in skins
    if name in _BUILTIN_SKINS:
        return _build_skin_config(_BUILTIN_SKINS[name])

    # Fallback to default
    logger.warning("Skin '%s' not found, using default", name)
    return _build_skin_config(_BUILTIN_SKINS["default"])


def get_active_skin() -> SkinConfig:
    """Get the currently active skin config (cached)."""
    global _active_skin
    if _active_skin is None:
        _active_skin = load_skin(_active_skin_name)
    return _active_skin


def set_active_skin(name: str) -> SkinConfig:
    """Switch the active skin. Returns the new SkinConfig."""
    global _active_skin, _active_skin_name
    _active_skin_name = name
    _active_skin = load_skin(name)
    return _active_skin


def get_active_skin_name() -> str:
    """Get the name of the currently active skin."""
    return _active_skin_name


def init_skin_from_config(config: dict) -> None:
    """Initialize the active skin from CLI config at startup.

    Call this once during CLI init with the loaded config dict.
    """
    display = config.get("display") or {}
    if not isinstance(display, dict):
        display = {}
    skin_name = display.get("skin", "default")
    if isinstance(skin_name, str) and skin_name.strip():
        set_active_skin(skin_name.strip())
    else:
        set_active_skin("default")


# =============================================================================
# Convenience helpers for CLI modules
# =============================================================================


def get_active_prompt_symbol(fallback: str = "❯") -> str:
    """Return the interactive prompt symbol with a single trailing space.

    Skins store ``prompt_symbol`` as a bare token (no spaces). The trailing
    space is appended here so callers can drop it straight into a rendered
    prompt without hand-rolling whitespace.
    """
    try:
        raw = get_active_skin().get_branding("prompt_symbol", fallback)
    except Exception:
        raw = fallback

    cleaned = (raw or fallback).strip()

    return f"{cleaned or fallback.strip()} "


def get_active_help_header(fallback: str = "(^_^)? Available Commands") -> str:
    """Get the /help header from the active skin."""
    try:
        return get_active_skin().get_branding("help_header", fallback)
    except Exception:
        return fallback


def get_active_goodbye(fallback: str = "Goodbye! ✦") -> str:
    """Get the goodbye line from the active skin."""
    try:
        return get_active_skin().get_branding("goodbye", fallback)
    except Exception:
        return fallback


def get_status_symbol(key: str, fallback: str = "") -> str:
    """Get a status symbol from the active skin.

    Convenience wrapper so callers don't need to get_active_skin() first.
    """
    try:
        return get_active_skin().get_status_symbol(key, fallback)
    except Exception:
        return getattr(_DEFAULT_STATUS_SYMBOLS, key, fallback)


def get_prompt_toolkit_style_overrides() -> Dict[str, str]:
    """Return prompt_toolkit style overrides derived from the active skin.

    These are layered on top of the CLI's base TUI style so /skin can refresh
    the live prompt_toolkit UI immediately without rebuilding the app.
    """
    try:
        skin = get_active_skin()
    except Exception:
        return {}

    # Input/prompt: leave unset by default so the typed text inherits
    # the terminal's foreground color (readable in both light and dark
    # color schemes).  Skins can opt into a colored prompt by setting
    # `prompt` explicitly in their YAML.
    prompt = skin.get_color("prompt", "")
    input_rule = skin.get_color("input_rule", "#56526e")
    title = skin.get_color("banner_title", "#c4a7e7")
    text = skin.get_color("banner_text", "#e0def4")
    dim = skin.get_color("banner_dim", "#6e6a86")
    label = skin.get_color("ui_label", title)
    warn = skin.get_color("ui_warn", "#f6c177")
    error = skin.get_color("ui_error", "#eb6f92")
    status_bg = skin.get_color("status_bar_bg", "#2a273f")
    status_text = skin.get_color("status_bar_text", text)
    status_strong = skin.get_color("status_bar_strong", title)
    status_dim = skin.get_color("status_bar_dim", dim)
    status_good = skin.get_color("status_bar_good", skin.get_color("ui_ok", "#9ccfd8"))
    status_warn = skin.get_color("status_bar_warn", warn)
    status_bad = skin.get_color("status_bar_bad", skin.get_color("banner_accent", warn))
    status_critical = skin.get_color("status_bar_critical", error)
    voice_bg = skin.get_color("voice_status_bg", status_bg)
    menu_bg = skin.get_color("completion_menu_bg", "#2a273f")
    menu_current_bg = skin.get_color("completion_menu_current_bg", "#393552")
    menu_meta_bg = skin.get_color("completion_menu_meta_bg", menu_bg)
    menu_meta_current_bg = skin.get_color("completion_menu_meta_current_bg", menu_current_bg)

    return {
        # Typed input always uses terminal default fg/bg so it's
        # readable in both light and dark Terminal.app modes.  The
        # skin's `prompt` color (if any) only styles the prompt symbol,
        # NOT the user's typed text.
        "input-area": "",
        "placeholder": f"{dim} italic",
        "prompt": prompt,
        "prompt-working": f"{dim} italic",
        "hint": f"{dim} italic",
        "status-bar": f"bg:{status_bg} {status_text}",
        "status-bar-strong": f"bg:{status_bg} {status_strong} bold",
        "status-bar-dim": f"bg:{status_bg} {status_dim}",
        "status-bar-good": f"bg:{status_bg} {status_good} bold",
        "status-bar-warn": f"bg:{status_bg} {status_warn} bold",
        "status-bar-bad": f"bg:{status_bg} {status_bad} bold",
        "status-bar-critical": f"bg:{status_bg} {status_critical} bold",
        "input-rule": input_rule,
        "image-badge": f"{label} bold",
        "completion-menu": f"bg:{menu_bg} {text}",
        "completion-menu.completion": f"bg:{menu_bg} {text}",
        "completion-menu.completion.current": f"bg:{menu_current_bg} {title}",
        "completion-menu.meta.completion": f"bg:{menu_meta_bg} {dim}",
        "completion-menu.meta.completion.current": f"bg:{menu_meta_current_bg} {label}",
        "clarify-border": input_rule,
        "clarify-title": f"{title} bold",
        "clarify-question": f"{text} bold",
        "clarify-choice": dim,
        "clarify-selected": f"{title} bold",
        "clarify-active-other": f"{title} italic",
        "clarify-countdown": input_rule,
        "sudo-prompt": f"{error} bold",
        "sudo-border": input_rule,
        "sudo-title": f"{error} bold",
        "sudo-text": text,
        "approval-border": input_rule,
        "approval-title": f"{warn} bold",
        "approval-desc": f"{text} bold",
        "approval-cmd": f"{dim} italic",
        "approval-choice": dim,
        "approval-selected": f"{title} bold",
        "voice-status": f"bg:{voice_bg} {label}",
        "voice-status-recording": f"bg:{voice_bg} {error} bold",
    }
