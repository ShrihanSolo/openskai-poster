# Bundle the poster into one self-contained HTML file.
#
# poster.html loads its CSS, its config and its figures as separate files, which
# is what makes it pleasant to edit. Anywhere the poster has to travel as a
# single file -- publishing it as a Claude Artifact, emailing it, dropping it in
# a shared drive -- those pieces have to be inlined instead.
#
# This inlines the stylesheet, the config, and every image the config references
# as a base64 data: URI, and strips the <!doctype>/<html>/<head>/<body> wrapper,
# because the Artifact publisher supplies its own. The Google Fonts <link> is
# kept: fonts.googleapis.com is the one external host artifacts may load from.
#
# Standard library only, deliberately -- this checkout has no numpy, no PIL, no
# anything, and this script has to run wherever the poster does.
#
#   python3 build_artifact.py                       # -> build/poster_artifact.html
#   python3 build_artifact.py --out /tmp/poster.html
#
# Re-run it after any edit to poster_config.js that you want reflected in the
# published Artifact. Editing the config alone does not update a published page.
import argparse
import base64
import mimetypes
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Quoted relative paths in the config that look like images. The config writes
# every asset path as a plain quoted string, so this finds all of them.
ASSET_RE = re.compile(r'"([^"\s]+\.(?:png|webp|jpe?g|svg|gif))"', re.IGNORECASE)


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0]
    if mime is None:
        # .webp predates some stdlib mimetypes tables; guess from the suffix.
        mime = "image/" + path.suffix.lstrip(".").lower()
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def inline_assets(js: str) -> tuple[str, int, int]:
    """Replace every quoted image path in the config with a data: URI."""
    seen, missing = {}, []

    def sub(m):
        rel = m.group(1)
        if rel.startswith("data:"):
            return m.group(0)
        p = (HERE / rel).resolve()
        if not p.is_file():
            missing.append(rel)
            return m.group(0)
        if rel not in seen:
            seen[rel] = data_uri(p)
            print(f"  inlined {rel}  ({p.stat().st_size / 1024:.0f} KB)")
        return f'"{seen[rel]}"'

    out = ASSET_RE.sub(sub, js)
    for rel in missing:
        print(f"  WARNING: {rel} not found -- it will be a broken image", file=sys.stderr)
    return out, len(seen), len(missing)


def main():
    ap = argparse.ArgumentParser(description="Bundle the poster into one HTML file.")
    ap.add_argument("--out", default=str(HERE / "build" / "poster_artifact.html"))
    args = ap.parse_args()

    html = (HERE / "poster.html").read_text(encoding="utf-8")
    css = (HERE / "poster_style.css").read_text(encoding="utf-8")
    cfg = (HERE / "poster_config.js").read_text(encoding="utf-8")

    print("Inlining figures and logos:")
    cfg, n_ok, n_bad = inline_assets(cfg)

    # Inline the stylesheet and the config in place of their external references.
    html = html.replace(
        '<link rel="stylesheet" href="poster_style.css">',
        "<style>\n" + css + "\n</style>",
    )
    html = html.replace(
        '<script src="poster_config.js"></script>',
        "<script>\n" + cfg + "\n</script>",
    )

    # The Artifact publisher wraps the file in its own document skeleton, so
    # hand it body content only. Keep <title> and the font <link> by lifting
    # them out of the head before it is discarded.
    keep = re.findall(r"<title>.*?</title>|<link[^>]+fonts\.googleapis[^>]*>", html, re.S)
    body = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    if body is None:
        sys.exit("could not find <body> in poster.html -- did its structure change?")
    html = "\n".join(keep) + "\n" + body.group(1).strip() + "\n"

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    size = out.stat().st_size / 1e6
    print(f"\nWrote {out}  ({size:.2f} MB, {n_ok} assets inlined"
          + (f", {n_bad} MISSING" if n_bad else "") + ")")
    if size > 16:
        print("WARNING: over the 16 MB artifact limit -- shrink the figures.",
              file=sys.stderr)


if __name__ == "__main__":
    main()
