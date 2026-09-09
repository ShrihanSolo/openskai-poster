#!/usr/bin/env python
"""
Render poster.html headlessly, save a reviewable image set, and check the things
that are easy to get wrong at 24x36 and impossible to judge in a browser window.

Why this exists: nothing in this container could turn the poster into pixels, so
every layout iteration needed a human to look at it. Chromium is now in the
devcontainer image (/usr/bin/chromium), and this script is the loop.

    python render.py --label first-pass --note "tightened the results band"
    python render.py --label contour-bigger --dsf 2      # detail crops
    python render.py --pdf                               # print-ready PDF
    python render.py --gallery                           # rebuild gallery.html

Each run writes poster/renders/NNN-label/ containing

    full.png       the sheet at render resolution, stage chrome cropped off
    review.png     downscaled, for looking at the whole poster at once
    band-N-*.png   one crop per band at full resolution, for judging type
    manifest.json  geometry, checks, the command that produced it

and appends a row to poster/renders/log.md.

Two things worth knowing about the rendering:

  * The screenshot is taken under *screen* media, the PDF under *print* media.
    In poster_style.css the only screen/print differences are the stage padding,
    the drop shadow, the sheet transform and the overflow banner -- none of which
    affect layout inside the sheet. So the PNG is faithful for layout. It is not
    faithful for fonts: Debian's Liberation/DejaVu are not the faces a Mac will
    use, so glyph shapes and exact line breaks can differ from your Chrome.

  * poster.html builds its DOM from poster_config.js, so a naive screenshot
    catches an empty page. --virtual-time-budget below is what waits for it.

Run with the `simple` conda env, which has Pillow:

    /home/node/.conda/envs/simple/bin/python render.py
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit(
        "Pillow is missing. Run this with the `simple` env:\n"
        "  /home/node/.conda/envs/simple/bin/python render.py"
    )

HERE = Path(__file__).resolve().parent
POSTER = HERE / "poster.html"
RENDERS = HERE / "renders"
CHROME = shutil.which("chromium") or shutil.which("chromium-browser") or "/usr/bin/chromium"

# The sheet is 24 in wide at the CSS reference 96 px/in. Used to convert element
# widths into inches, which is the only way to talk about figure resolution.
SHEET_W_IN = 24.0
CSS_PX_PER_IN = 96.0

# Dots per inch at final size. These are large-format thresholds, not the 300
# dpi of handheld print: a 24x36 poster is read from a few feet away, where the
# accepted floor is around 150 and 200+ is comfortably crisp. Judging poster
# figures against a photographic standard would fail every one of them.
DPI_SOFT = 120
DPI_GOOD = 200

# Chromium in a container: no sandbox (uid 1000, no user namespaces), no GPU,
# and dbus chatter on stderr that means nothing.
BASE_FLAGS = [
    "--headless=new",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--hide-scrollbars",
    "--virtual-time-budget=8000",
]

# Injected into a throwaway copy of poster.html. Reports where every band and
# image landed, plus the overflow the page already computes for itself.
PROBE_JS = r"""
<style id="__render_reset__">
/* poster.html's fit() scales the sheet to the browser window, which would make
   every render depend on --window-size. Neutralise it so the sheet always lays
   out at exactly 24x36 in -- which is what print media does anyway, making the
   PNG and the PDF the same geometry. The banner is hidden because its overflow
   is reported numerically below; painted, it would cover the title. */
@media screen {
  .stage  { padding: 0 !important; height: auto !important; }
  .sheet  { transform: none !important; box-shadow: none !important; }
  html, body { background: #fff !important; }
  #overflow-warn, #type-warn { display: none !important; }
}
</style>
<script>
(function () {
  function report() {
    var sheet = document.getElementById("sheet");
    var srect = sheet.getBoundingClientRect();

    var bands = Array.prototype.map.call(
      document.querySelectorAll(".band"),
      function (b, i) {
        var r = b.getBoundingClientRect();
        var h = b.querySelector("h1, h2, h3, .band-title, .kicker");
        return {
          index: i,
          label: h ? h.textContent.trim().slice(0, 60) : "",
          x: r.x, y: r.y, w: r.width, h: r.height
        };
      }
    );

    // offsetWidth is pre-transform layout px, so it converts straight to inches
    // on the printed sheet; getBoundingClientRect would fold in the preview
    // scale and lie about the physical size.
    var imgs = Array.prototype.map.call(
      document.querySelectorAll("img"),
      function (im) {
        return {
          src: im.getAttribute("src"),
          natural_w: im.naturalWidth,
          natural_h: im.naturalHeight,
          layout_w: im.offsetWidth,
          layout_h: im.offsetHeight,
          complete: im.complete
        };
      }
    );

    // The sheet is overflow:hidden, so a line too wide for its column is cut
    // off with no warning at all. Catch it here instead of in print.
    var clipped = [];
    Array.prototype.forEach.call(
      document.querySelectorAll(".sheet *"),
      function (n) {
        if (!n.children.length || n.tagName === "TD" || n.tagName === "TH") {
          if (n.scrollWidth - n.clientWidth > 1 && n.clientWidth > 0) {
            clipped.push({
              tag: n.tagName.toLowerCase(),
              cls: n.className || "",
              over_px: n.scrollWidth - n.clientWidth,
              text: (n.textContent || "").trim().slice(0, 60)
            });
          }
        }
      }
    );

    var warn = document.getElementById("overflow-warn");
    var pre = document.createElement("pre");
    pre.id = "__render_geom__";
    pre.textContent = JSON.stringify({
      sheet: {
        x: srect.x, y: srect.y, w: srect.width, h: srect.height,
        client_h: sheet.clientHeight, scroll_h: sheet.scrollHeight,
        client_w: sheet.clientWidth, scroll_w: sheet.scrollWidth
      },
      overflow_px: sheet.scrollHeight - sheet.clientHeight,
      clipped: clipped,
      overflow_banner: warn ? warn.textContent.trim() : null,
      bands: bands,
      imgs: imgs
    });
    document.body.appendChild(pre);
  }
  if (document.readyState === "complete") report();
  else window.addEventListener("load", report);
})();
</script>
</body>
"""


def run_chromium(args: list[str], timeout: int = 300) -> str:
    """Run chromium, returning stdout. Chromium's stderr is noise; ignore it."""
    proc = subprocess.run(
        [CHROME, *BASE_FLAGS, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0 and not proc.stdout:
        noise = ("dbus", "Failed to call method", "GLib", "gpu", "Fontconfig")
        stderr = "\n".join(
            ln for ln in proc.stderr.splitlines()
            if ln.strip() and not any(n.lower() in ln.lower() for n in noise)
        )
        raise RuntimeError(f"chromium failed (exit {proc.returncode}):\n{stderr[:2000]}")
    return proc.stdout


def measure(probe: Path, window: tuple[int, int]) -> dict:
    """Load the page and pull the geometry the probe script left in the DOM.

    Rendered in the same window as the screenshot: the probe stylesheet pins the
    sheet size, but matching the two runs keeps them honest if that ever changes.
    """
    dom = run_chromium([f"--window-size={window[0]},{window[1]}", "--dump-dom", probe.as_uri()])
    m = re.search(r'<pre id="__render_geom__">(.*?)</pre>', dom, re.S)
    if not m:
        raise RuntimeError(
            "geometry probe did not run. The page likely failed to build its DOM "
            "-- check poster_config.js for a syntax error."
        )
    return json.loads(html.unescape(m.group(1)))


def make_probe(dest: Path) -> Path:
    """A copy of poster.html with the probe script injected.

    It has to live beside poster.html so the relative CSS, config and figure
    paths still resolve.
    """
    src = POSTER.read_text()
    if "</body>" not in src:
        raise RuntimeError("poster.html has no </body> to inject before")
    dest.write_text(src.replace("</body>", PROBE_JS, 1))
    return dest


def ink_margins(full: Image.Image, geom: dict, dsf: int) -> list[dict]:
    """Report ink sitting outside the page margin.

    Nothing clips when this happens -- the element is still inside the sheet --
    so no DOM measurement catches it. But on a printed poster an element in the
    margin reads as a mistake and sits nearer the trim edge than everything
    else, so it is worth failing on. The margin is recovered from where the
    bands start rather than parsed out of the CSS.
    """
    if not geom["bands"]:
        return []
    s = geom["sheet"]
    m = min(b["x"] for b in geom["bands"]) - s["x"]
    if m <= 0:
        return []

    import numpy as np

    a = np.asarray(full.convert("L"))
    ink = a < 245
    rows, cols = np.where(ink.any(axis=1))[0], np.where(ink.any(axis=0))[0]
    if not len(rows) or not len(cols):
        return []

    edge = {
        "left": m * dsf - cols.min(),
        "right": cols.max() - (full.width - m * dsf),
        "top": m * dsf - rows.min(),
        "bottom": rows.max() - (full.height - m * dsf),
    }
    out = []
    for side, over in edge.items():
        if over > 2:
            out.append({
                "level": "fail",
                "what": "ink in the margin",
                "detail": f"content reaches {over / (CSS_PX_PER_IN * dsf):.2f} in "
                          f"into the {side} margin",
            })
    return out


def check(geom: dict) -> list[dict]:
    """Everything worth failing on that a numeric check can catch."""
    out: list[dict] = []

    over_in = geom["overflow_px"] / CSS_PX_PER_IN
    if geom["overflow_px"] > 1:
        out.append({
            "level": "fail",
            "what": "sheet overflow",
            "detail": f"content runs {over_in:.2f} in past the 36 in sheet and "
                      f"will be clipped in print",
        })

    wide = geom["sheet"]["scroll_w"] - geom["sheet"]["client_w"]
    if wide > 1:
        out.append({
            "level": "fail",
            "what": "sheet too narrow",
            "detail": f"content runs {wide / CSS_PX_PER_IN:.2f} in past the right "
                      f"edge; something in a row will not shrink further",
        })

    for c in geom.get("clipped", []):
        out.append({
            "level": "fail",
            "what": "text clipped",
            "detail": f'<{c["tag"]} class="{c["cls"]}"> overruns its box by '
                      f'{c["over_px"]}px: "{c["text"]}"',
        })

    for im in geom["imgs"]:
        src = im["src"] or "(inline)"
        if not im["complete"] or not im["natural_w"]:
            out.append({
                "level": "fail",
                "what": "image did not load",
                "detail": src,
            })
            continue
        if not im["layout_w"]:
            continue
        if src.lower().endswith(".svg"):
            # Vector: naturalWidth is the intrinsic pt size, not a pixel budget,
            # so dpi is meaningless here. The contour is an SVG and would score
            # ~107 dpi and read as a hard failure while printing perfectly.
            continue
        width_in = im["layout_w"] / CSS_PX_PER_IN
        dpi = im["natural_w"] / width_in if width_in else 0
        if dpi < DPI_SOFT:
            level, verdict = "fail", "visibly soft in print"
        elif dpi < DPI_GOOD:
            level, verdict = "warn", "acceptable, not crisp"
        else:
            continue
        out.append({
            "level": level,
            "what": "figure resolution",
            "detail": f"{src} renders {width_in:.1f} in wide at {dpi:.0f} dpi "
                      f"({im['natural_w']}px source) -- {verdict}",
        })

    return out


def next_slot(label: str) -> Path:
    RENDERS.mkdir(exist_ok=True)
    n = 1 + max(
        (int(p.name.split("-", 1)[0]) for p in RENDERS.glob("[0-9][0-9][0-9]-*") if p.is_dir()),
        default=0,
    )
    safe = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "render"
    d = RENDERS / f"{n:03d}-{safe}"
    d.mkdir()
    return d


def render(args: argparse.Namespace) -> Path:
    probe = HERE / ".render_probe.html"
    try:
        make_probe(probe)
        geom = measure(probe, (args.window_w, args.window_h))

        out = next_slot(args.label)
        shot = out / "_raw.png"
        run_chromium([
            f"--force-device-scale-factor={args.dsf}",
            f"--window-size={args.window_w},{args.window_h}",
            f"--screenshot={shot}",
            probe.as_uri(),
        ])

        im = Image.open(shot)
        s = geom["sheet"]
        # Crop the stage padding and drop shadow away; keep only the sheet.
        box = tuple(round(v * args.dsf) for v in (s["x"], s["y"], s["x"] + s["w"], s["y"] + s["h"]))
        box = (max(0, box[0]), max(0, box[1]), min(im.width, box[2]), min(im.height, box[3]))
        full = im.crop(box)
        full.save(out / "full.png")

        if full.width < s["w"] * args.dsf - 2 or full.height < s["h"] * args.dsf - 2:
            print(
                f"  ! window {args.window_w}x{args.window_h} clipped the sheet "
                f"({full.width}x{full.height} of {round(s['w']*args.dsf)}x"
                f"{round(s['h']*args.dsf)}). Raise --window-w/--window-h.",
                file=sys.stderr,
            )

        review = full.copy()
        review.thumbnail((args.review_width, 10_000), Image.LANCZOS)
        review.save(out / "review.png")

        crops = []
        if not args.no_crops:
            for b in geom["bands"]:
                pad = 12
                bx = (b["x"] - s["x"] - pad, b["y"] - s["y"] - pad,
                      b["x"] - s["x"] + b["w"] + pad, b["y"] - s["y"] + b["h"] + pad)
                bx = tuple(round(v * args.dsf) for v in bx)
                bx = (max(0, bx[0]), max(0, bx[1]), min(full.width, bx[2]), min(full.height, bx[3]))
                if bx[2] - bx[0] < 8 or bx[3] - bx[1] < 8:
                    continue
                slug = re.sub(r"[^a-z0-9]+", "-", b["label"].lower()).strip("-") or "band"
                name = f"band-{b['index']}-{slug[:40]}.png"
                full.crop(bx).save(out / name)
                crops.append(name)

        shot.unlink()

        checks = check(geom) + ink_margins(full, geom, args.dsf)
        manifest = {
            "label": args.label,
            "note": args.note,
            "when": dt.datetime.now().isoformat(timespec="seconds"),
            "dsf": args.dsf,
            "sheet_px": [round(s["w"] * args.dsf), round(s["h"] * args.dsf)],
            "checks": checks,
            "bands": geom["bands"],
            "imgs": geom["imgs"],
            "overflow_px": geom["overflow_px"],
            "crops": crops,
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2))

        if args.pdf:
            run_chromium([
                "--no-pdf-header-footer",
                f"--print-to-pdf={out / 'poster.pdf'}",
                POSTER.as_uri(),          # the real file, not the probe
            ])

        log(out, manifest)
        report(out, manifest)
        return out
    finally:
        probe.unlink(missing_ok=True)


def log(out: Path, man: dict) -> None:
    f = RENDERS / "log.md"
    if not f.exists():
        f.write_text(
            "# Render log\n\n"
            "Written by `render.py`. Newest at the bottom.\n\n"
            "| # | when | label | checks | note |\n"
            "|---|------|-------|--------|------|\n"
        )
    fails = sum(c["level"] == "fail" for c in man["checks"])
    warns = sum(c["level"] == "warn" for c in man["checks"])
    status = "clean" if not (fails or warns) else f"{fails} fail, {warns} warn"
    with f.open("a") as fh:
        fh.write(
            f"| {out.name.split('-')[0]} | {man['when']} | {man['label']} | "
            f"{status} | {man['note'] or ''} |\n"
        )


def report(out: Path, man: dict) -> None:
    print(f"\n{out.relative_to(HERE)}  ({man['sheet_px'][0]}x{man['sheet_px'][1]} px)")
    print(f"  review.png, full.png, {len(man['crops'])} band crops")
    if not man["checks"]:
        print("  checks: clean")
    for c in man["checks"]:
        mark = "FAIL" if c["level"] == "fail" else "warn"
        print(f"  {mark}: {c['what']} -- {c['detail']}")


def gallery(limit: int = 12) -> Path:
    """One self-contained page showing recent iterations, newest first.

    Images are inlined so the file can be published as an Artifact and opened
    anywhere, with no server and no missing-image boxes. They are re-encoded as
    JPEG and the listing is capped, because an Artifact must stay under 16 MB
    and a PNG of a whole poster is over a megabyte on its own.
    """
    runs = sorted(
        (p for p in RENDERS.glob("[0-9][0-9][0-9]-*") if (p / "manifest.json").exists()),
        key=lambda p: p.name,
        reverse=True,
    )[:limit]
    if not runs:
        sys.exit("no renders yet -- run without --gallery first")

    cards = []
    for p in runs:
        man = json.loads((p / "manifest.json").read_text())
        buf = io.BytesIO()
        Image.open(p / "review.png").convert("RGB").save(
            buf, "JPEG", quality=82, optimize=True, progressive=True)
        uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        rows = "".join(
            f'<li class="{c["level"]}"><b>{html.escape(c["what"])}</b> '
            f'{html.escape(c["detail"])}</li>'
            for c in man["checks"]
        ) or '<li class="ok">checks clean</li>'
        cards.append(f"""
<section class="card">
  <header>
    <h2>{html.escape(p.name)}</h2>
    <time>{html.escape(man["when"].replace("T", " "))}</time>
  </header>
  {f'<p class="note">{html.escape(man["note"])}</p>' if man.get("note") else ""}
  <ul class="checks">{rows}</ul>
  <div class="shot"><img src="{uri}" alt="Render {html.escape(p.name)}"></div>
</section>""")

    total = len(runs)
    all_runs = len([q for q in RENDERS.glob("[0-9][0-9][0-9]-*") if q.is_dir()])
    latest = json.loads((runs[0] / "manifest.json").read_text())
    fails = sum(c["level"] == "fail" for c in latest["checks"])

    doc = f"""<title>OpenSkAI Poster Renders</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?\
family=IBM+Plex+Mono:wght@400;500&\
family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
  /* Tokens are the poster's own: the UChicago maroon from poster_style.css and
     the warm off-white it uses for washes, so this reads as part of that work. */
  :root {{
    --bg:#f7f2f0; --card:#ffffff; --fg:#17130f; --soft:#5a504a;
    --edge:#e3d8d4; --maroon:#800000; --warn:#8a5a00; --ok:#2f6b4f;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg:#14100e; --card:#1e1815; --fg:#f2ece9; --soft:#a99d96;
      --edge:#3a322e; --maroon:#e79a9a; --warn:#dcae63; --ok:#82c6a3;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg:#14100e; --card:#1e1815; --fg:#f2ece9; --soft:#a99d96;
    --edge:#3a322e; --maroon:#e79a9a; --warn:#dcae63; --ok:#82c6a3;
  }}
  body {{
    background: var(--bg); color: var(--fg); margin: 0;
    font: 400 15px/1.55 "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
  }}
  .wrap {{ max-width: 940px; margin: 0 auto; padding: 40px 20px 72px; }}
  header.top {{ border-bottom: 2px solid var(--maroon); padding-bottom: 14px; margin-bottom: 8px; }}
  h1 {{ font-size: 25px; font-weight: 600; margin: 0 0 6px; color: var(--maroon); text-wrap: balance; }}
  .sub {{ color: var(--soft); margin: 0; max-width: 62ch; }}
  .summary {{
    display: flex; flex-wrap: wrap; gap: 26px; margin: 18px 0 34px;
    font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace; font-size: 13px;
  }}
  .summary div {{ display: flex; flex-direction: column; gap: 2px; }}
  .summary dt {{ color: var(--soft); text-transform: uppercase; letter-spacing: .08em; font-size: 11px; }}
  .summary dd {{ margin: 0; font-size: 17px; font-variant-numeric: tabular-nums; }}
  .runs {{ display: flex; flex-direction: column; gap: 30px; }}
  .card {{ background: var(--card); border: 1px solid var(--edge); border-radius: 8px; overflow: hidden; }}
  .card > header {{
    display: flex; align-items: baseline; justify-content: space-between; gap: 14px;
    padding: 14px 18px; border-bottom: 1px solid var(--edge); flex-wrap: wrap;
  }}
  .card h2 {{
    font: 500 15px/1.3 "IBM Plex Mono", ui-monospace, Menlo, monospace;
    margin: 0; color: var(--maroon);
  }}
  time {{
    color: var(--soft); font-size: 12.5px;
    font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace;
    font-variant-numeric: tabular-nums;
  }}
  .note {{ margin: 0; padding: 13px 18px 0; color: var(--soft); }}
  .checks {{ list-style: none; margin: 13px 0 0; padding: 0 18px; font-size: 13.5px; }}
  .checks li {{ padding: 4px 0 4px 12px; border-left: 3px solid var(--edge); }}
  .checks li + li {{ margin-top: 3px; }}
  .checks b {{ font-weight: 600; }}
  .checks .fail {{ border-left-color: var(--maroon); }}
  .checks .warn {{ border-left-color: var(--warn); }}
  .checks .ok {{ border-left-color: var(--ok); color: var(--soft); }}
  .shot {{ padding: 16px 18px 18px; }}
  .shot img {{
    width: 100%; height: auto; display: block;
    border: 1px solid var(--edge); background: #fff;
  }}
  footer {{ margin-top: 40px; color: var(--soft); font-size: 13px; }}
  code {{ font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace; font-size: .92em; }}
</style>
<div class="wrap">
  <header class="top">
    <h1>Do we need full field level inference?</h1>
    <p class="sub">Headless renders of the OpenSkAI poster, newest first. Each entry is one
       layout iteration: what changed, what the automated checks found, and the sheet as
       Chromium drew it at 24&thinsp;&times;&thinsp;36&nbsp;in.
       {f"Showing the most recent {total} of {all_runs}." if all_runs > total else ""}</p>
  </header>

  <dl class="summary">
    <div><dt>Iterations</dt><dd>{all_runs}</dd></div>
    <div><dt>Latest</dt><dd>{html.escape(runs[0].name.split("-", 1)[1])}</dd></div>
    <div><dt>Sheet</dt><dd>{latest["sheet_px"][0]}&times;{latest["sheet_px"][1]}</dd></div>
    <div><dt>Failing checks</dt><dd>{fails}</dd></div>
  </dl>

  <div class="runs">{"".join(cards)}</div>

  <footer>Generated by <code>poster/render.py --gallery</code>. Rendering is Debian
     Chromium, whose fonts differ from macOS &mdash; layout is faithful, exact glyphs are not.</footer>
</div>
"""
    out = RENDERS / "gallery.html"
    out.write_text(doc)
    print(f"{out.relative_to(HERE)}  ({len(runs)} renders, {out.stat().st_size / 1e6:.1f} MB)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", default="render", help="short slug for this iteration's directory")
    ap.add_argument("--note", default="", help="what changed, for the log and gallery")
    ap.add_argument("--dsf", type=int, default=1, help="device scale factor; 2 for detail crops")
    ap.add_argument("--review-width", type=int, default=1100, help="width of review.png")
    ap.add_argument("--window-w", type=int, default=2400, help="chromium window width")
    ap.add_argument("--window-h", type=int, default=3560, help="chromium window height")
    ap.add_argument("--no-crops", action="store_true", help="skip per-band crops")
    ap.add_argument("--pdf", action="store_true", help="also write the print-media PDF")
    ap.add_argument("--gallery", action="store_true", help="rebuild gallery.html and exit")
    args = ap.parse_args()

    if not Path(CHROME).exists():
        sys.exit(f"chromium not found at {CHROME}. Rebuild the devcontainer.")
    if not POSTER.exists():
        sys.exit(f"{POSTER} not found")

    if args.gallery:
        gallery()
        return
    render(args)


if __name__ == "__main__":
    main()
