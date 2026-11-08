import hashlib
import json
import re
import textwrap
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

URL = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "fact.svg"
README = ROOT / "README.md"

SANS = "'Inter','Helvetica Neue',Arial,sans-serif"
MONO = "'SFMono-Regular',Menlo,Consolas,monospace"


def build(fact: str) -> str:
    lines = textwrap.wrap(fact, width=60) or [""]
    height = 62 + 24 * (len(lines) - 1) + 26

    body = "\n  ".join(
        f'<text x="24" y="{62 + 24 * i}" '
        f'font-family="{SANS}" font-size="15" '
        f'font-weight="300" letter-spacing="-0.3" '
        f'fill="#d4d0c9">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="560" height="{height}" viewBox="0 0 560 {height}">
  <rect x="0.5" y="0.5" width="559" height="{height - 1}" rx="10" fill="#141414" stroke="#d4d0c9" stroke-opacity="0.15"/>
  <text x="24" y="30" font-family="{MONO}" font-size="10" letter-spacing="1.5" fill="#878581">FUN FACT OF THE DAY</text>
  {body}
</svg>
"""


def main() -> None:
    with urllib.request.urlopen(URL, timeout=15) as response:
        fact = json.load(response)["text"].strip()

    if not fact:
        raise ValueError("The API returned an empty fact.")

    svg = build(fact)
    version = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:12]

    content = README.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'src="assets/fact\.svg(?:\?[^"]*)?"',
        f'src="assets/fact.svg?v={version}"',
        content,
    )

    if count == 0:
        raise ValueError(
            'README.md must contain an image with src="assets/fact.svg".'
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    README.write_text(updated, encoding="utf-8")

    print(f"Updated fact.svg and README.md (version: {version})")


if __name__ == "__main__":
    main()
