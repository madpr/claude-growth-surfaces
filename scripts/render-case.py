#!/usr/bin/env python3
"""Render one case README to a page on the site.

    python3 scripts/render-case.py <markdown file> <output html> <case directory>

The markdown is the source of truth and stays in the repository. This renders it with
the same palette as the home page, and points relative links somewhere useful: the top
README goes to the home page, the proposal goes to its own page, and files under
research/, prototype/, and page/ go to the repository on GitHub, since the site does
not host them.

Needs python-markdown:  python3 -m pip install --user markdown
"""

import html
import pathlib
import sys

try:
    import markdown
except ImportError:  # pragma: no cover
    sys.stderr.write("render-case.py: python-markdown is missing. "
                     "Install it with: python3 -m pip install --user markdown\n")
    sys.exit(2)

REPO_BLOB = "https://github.com/madpr/claude-growth-surfaces/blob/master"

PAGE_FOR = {
    "../README.md": "index.html",
    "proposal-credential-precedence.md": "proposal.html",
    "README.md": "bonus.html",
}


def rewrite_links(text, case_dir):
    """Rewrite relative markdown link targets. Plain string scanning, no regex."""
    out = []
    i = 0
    while True:
        j = text.find("](", i)
        if j < 0:
            out.append(text[i:])
            break
        k = text.find(")", j)
        if k < 0:
            out.append(text[i:])
            break
        target = text[j + 2:k]
        out.append(text[i:j + 2])
        if target.startswith(("http://", "https://", "#", "mailto:")):
            out.append(target)
        elif target in PAGE_FOR:
            out.append(PAGE_FOR[target])
        else:
            out.append(f"{REPO_BLOB}/{case_dir}/{target}")
        out.append(")")
        i = k + 1
    return "".join(out)


def first_heading(text):
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Case"


TEMPLATE = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap">
<style>
:root{{
  --bg:#141312; --panel:#1B1A18; --sunk:#201F1C;
  --ink:#EDEAE3; --ink-2:#B0ABA1; --ink-3:#837E74;
  --rule:#2C2A26; --rule-soft:#232120;
  --accent:#E08A66; --accent-dim:#2A211C; --accent-ink:#EFA98A;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}}
*{{box-sizing:border-box}}
html{{color-scheme:dark}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:16.5px;line-height:1.6;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:820px;margin:0 auto;padding:44px 28px 80px}}
.top{{display:flex;justify-content:space-between;align-items:baseline;gap:16px;margin-bottom:28px}}
.eyebrow{{font-family:var(--mono);font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}}
.top a{{color:var(--ink-2);text-decoration:none;font-size:14px}}
.top a:hover{{color:var(--ink)}}
h1{{font-size:32px;line-height:1.15;letter-spacing:-.01em;margin:0 0 18px;text-wrap:balance}}
h2{{font-size:21px;margin:38px 0 10px;letter-spacing:-.005em}}
h3{{font-size:17px;margin:26px 0 8px}}
p{{margin:0 0 14px}}
ul,ol{{padding-left:22px;margin:0 0 14px}}
li{{margin:4px 0}}
a{{color:var(--accent-ink)}}
strong{{color:var(--ink);font-weight:600}}
code{{font-family:var(--mono);font-size:.88em;background:var(--sunk);padding:1px 5px;border-radius:4px}}
pre{{background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:14px 16px;overflow-x:auto;margin:0 0 16px}}
pre code{{background:none;padding:0;font-size:13px}}
blockquote{{margin:0 0 16px;padding:12px 16px;border-left:3px solid var(--accent);background:var(--panel);border-radius:0 8px 8px 0}}
blockquote p:last-child{{margin:0}}
.tbl{{overflow-x:auto;margin:0 0 18px}}
table{{border-collapse:collapse;width:100%;font-size:14.5px}}
th,td{{border:1px solid var(--rule);padding:7px 10px;text-align:left;vertical-align:top}}
th{{background:var(--sunk);font-weight:600}}
hr{{border:0;border-top:1px solid var(--rule);margin:32px 0}}
footer{{margin-top:48px;padding-top:18px;border-top:1px solid var(--rule);font-size:13.5px;color:var(--ink-3)}}
footer a{{color:var(--ink-2)}}
</style>

<div class="wrap">
  <div class="top">
    <span class="eyebrow">Claude API &middot; growth surfaces</span>
    <a href="index.html">&larr; All ideas</a>
  </div>

  <main>
{body}
  </main>

  <footer>
    Rendered from <a href="{source}">{source_label}</a> in the repository.
  </footer>
</div>
"""


def main(argv):
    if len(argv) != 4:
        sys.stderr.write(__doc__)
        return 2
    src, out, case_dir = argv[1], argv[2], argv[3]
    text = pathlib.Path(src).read_text()
    title = first_heading(text)
    body = markdown.markdown(
        rewrite_links(text, case_dir),
        extensions=["tables", "fenced_code"],
        output_format="html5",
    )
    body = body.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    rel = pathlib.Path(src).resolve().relative_to(repo_root).as_posix()
    page = TEMPLATE.format(
        title=html.escape(title),
        body=body,
        source=f"{REPO_BLOB}/{rel}",
        source_label=html.escape(rel),
    )
    pathlib.Path(out).write_text(page)
    print(f"  {pathlib.Path(out).name:<24} <- {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
