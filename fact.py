import json
import os
import textwrap
import urllib.request
from xml.sax.saxutils import escape

URL = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
OUT = "assets/fact.svg"

SANS = "'Inter','Helvetica Neue',Arial,sans-serif"
MONO = "'SFMono-Regular',Menlo,Consolas,monospace"


def build(fact: str) -> str:
    lines = textwrap.wrap(fact, width=60)
    height = 62 + 24 * (len(lines) - 1) + 26
    body = "\n  ".join(
        f'<text x="24" y="{62 + 24 * i}" font-family="{SANS}" font-size="15" '
        f'font-weight="300" letter-spacing="-0.3" fill="#d4d0c9">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="560" height="{height}" viewBox="0 0 560 {height}">
  <rect x="0.5" y="0.5" width="559" height="{height - 1}" rx="10" fill="#141414" stroke="#d4d0c9" stroke-opacity="0.15"/>
  <text x="24" y="30" font-family="{MONO}" font-size="10" letter-spacing="1.5" fill="#878581">FUN FACT OF THE DAY</text>
  {body}
</svg>
"""


if __name__ == "__main__":
    with urllib.request.urlopen(URL, timeout=15) as r:
        fact = json.load(r)["text"].strip()
    os.makedirs("assets", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build(fact))
