"""Checks the colour pairs of the design tokens against WCAG AA.

Reads frontend/app/assets/css/tokens.css (light and dark mode) and exits with 1 if a text pair is
below 4.5:1 or a category line below 3:1 against the page. Run: python scripts/check_contrast.py
"""

import re
import sys
from pathlib import Path

TOKENS = Path(__file__).resolve().parent.parent / "frontend" / "app" / "assets" / "css" / "tokens.css"
CATEGORIES = ("blue", "teal", "coral", "amber", "violet", "slate")
text = TOKENS.read_text(encoding="utf8")


def read_block(marker):
    start = text.index(marker)
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", text[start:text.index("\n}", start)]))


def luminance(color):
    channels = [int(color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def ratio(a, b):
    lighter, darker = sorted((luminance(a), luminance(b)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def pairs(t):
    # (label, foreground, background, minimum ratio)
    rows = [
        ("text on page", "text", "page", 4.5), ("text on sheet", "text", "bg", 4.5),
        ("secondary text on page", "text-secondary", "page", 4.5), ("muted text on page", "text-muted", "page", 4.5),
        ("link on sheet", "accent", "bg", 4.5), ("link on page", "accent", "page", 4.5),
        ("accent text on accent tint", "accent-text", "accent-light", 4.5),
        ("main button", "on-primary", "primary", 4.5), ("step badge", "badge-text", "accent", 4.5),
        ("hero title", "hero-text", "hero-bg", 4.5), ("hero text", "hero-sub", "hero-bg", 4.5),
        ("hero button", "hero-btn-text", "hero-btn-bg", 4.5),
        ("important notice", "caution-text", "caution-light", 4.5), ("error notice", "warning-text", "warning-light", 4.5),
        ("result notice", "ok-text", "ok-light", 4.5), ("danger notice", "on-danger", "danger", 4.5),
    ]
    for name in CATEGORIES:
        rows.append((f"{name}: text on tint", f"c-{name}-ink", f"c-{name}-bg", 4.5))
        rows.append((f"{name}: line on page", f"c-{name}-fg", "page", 3.0))
    return [(label, t[fg], t[bg], minimum) for label, fg, bg, minimum in rows]


failed = 0
for mode, marker in (("light", ":root {\n  color-scheme: light;"), ("dark", ':root[data-mode="dark"]')):
    tokens = read_block(marker)
    for label, fg, bg, minimum in pairs(tokens):
        value = ratio(fg, bg)
        if value < minimum:
            failed += 1
            print(f"{mode}: {label} {value:.1f}:1 (needs {minimum}:1)")
print("all pairs pass" if not failed else f"{failed} pairs below the minimum")
sys.exit(1 if failed else 0)
