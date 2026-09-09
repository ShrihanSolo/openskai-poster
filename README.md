# OpenSkAI poster — "Do we need full field level inference?"

Portrait, 24 in × 36 in. Built as HTML so it can be edited without a LaTeX
toolchain and printed to an exact-size PDF from Chrome.

## Editing

Everything you'd want to change lives in **`poster_config.js`** — title, authors,
affiliations, every paragraph, the callout boxes, figure paths, the sampling
aside and the results prose. Edit it, save, reload the page in the
browser. You should not have to open `poster.html` at all.

Three conventions in that file:

- Any string containing **`TODO`** renders with a loud yellow highlight, so an
  unfinished field can't be printed by accident. Search the file for `TODO` to
  find what's outstanding.
- Body text is HTML, so `<b>`, `<i>`, `<sub>`, `&nbsp;` all work — and a literal
  `<` or `&` has to be escaped. Greek letters are written as Unicode (Ω, σ, δ),
  which prints correctly with no LaTeX involved.
- **Maths goes between dollar signs**, written as a subset of LaTeX — see
  [Maths](#maths) below.

Everything visible is now reachable from the config, including things that used
to be baked into `poster.html`:

- `meta.title` / `meta.subtitle` / `meta.authors` / `meta.affiliations`
- `approaches[].stages` — the three captions under each column's diagram
  (`field` / `k-shells` / `5 components` and so on). The drawing's geometry is
  fixed per `schematic` kind; only the words are yours.
- `cost.ticks`, `cost.unit`, `cost.tbdLabel`, `cost.zeroLabel` — the log-axis
  tick labels and the wording used for a `null` (not measured yet) and an exact
  `0` (which a log axis cannot plot). The cost band is not drawn at the moment;
  see the kept-but-not-rendered list below.
- `setup.eyebrow` and `summarization.eyebrow` — the band rules over the fact
  strip (DATASET) and the three approach columns (SUMMARIZATION). Every band on
  the poster now carries a rule, which is what makes the sheet read as five
  bands rather than three plus two loose blocks. Both of these are set with an
  empty `heading`, so they draw as a hairline from the left margin out to the
  eyebrow and nothing else: the strip says what it is in its own `label`, and
  the approach columns say it in their headings. Give either one a `heading`
  string and the maroon head appears at the left, like the other three bands.
- `sampling` — the shaded method column on the *left* of the results band:
  `eyebrow`, `heading`, `paras` (body paragraphs) and, optionally, `note`
  (small print, pinned to the floor of the panel — currently unset). It is a
  fixed 5 in track with no slack — about 20 lines at the current size. If you
  add much, drop `--t-aside` in `.results-aside`. It used to be the target the
  rest of the band was tuned to; the contour is now sized to the sheet instead
  and runs taller than this column, which is why the aside's `note` is pinned
  to its floor.
- `results.discussion` — the text to the *right* of the contour: `lede` (the
  one-line claim), `bullets` (an array, drawn as a dashed list), `note` (the
  small print, pinned to the floor). It is set larger than the aside on
  purpose. Five bullets is what the column holds at the current size; a sixth,
  or a bullet that takes a third line, grows the band and pushes everything
  below it down. Retune `.results-mid .lede` and `.results-mid .body-text`
  together if you need more.
  Wrapping a figure in `<span class="c-pk">`, `c-cnn` or `c-fl` colours it to
  match that analysis's contour in the plot next to it.
- Figure `caption` fields are `null`, so no captions are drawn anywhere. Put a
  string back on any `figure` and its caption reappears. A caption's height
  comes out of the band, not out of the figure — so on the density panels,
  which were then grown to fill that space (`--col-question-fig`, below),
  putting a caption back will make band 1 taller and push everything under it
  down. There is about 0.6 in of slack at the foot of the sheet.
- `meta.logos[].height`, in inches. Sized to the height of the title block
  beside them: taller and the header grows, pushing every band down.

Three blocks are **kept but not rendered**, so nothing is lost if you want
them back:

- `cost` — the whole cost-versus-gain band, chart and all. It came off because
  GPU-hours on a 320 Mpc/h mock is not the cost that decides anything: what
  decides it is that field level does not scale to DESI volume, which that
  chart does not show. `costBand()` and `costChart()` are untouched in
  `poster.html`; uncomment the `costBand(POSTER.cost)` line in its build block
  and the band returns, ~3.6 in tall.
- `results.table` — the measured Ω_m, σ₈ and FoM per analysis. `discussion`
  says the same thing in prose. These rows remain the numeric record.
  Re-append it in `resultsBand()`.
- `results.takeaway` — a panel that stood in a third column; that width went to
  the contour instead. Also `resultsBand()`.
- `approaches[].costNote` is **gone**, not hidden: the per-column cost line was
  removed from both the config and `approachBand()`.

The title is set on one line (`white-space: nowrap` on `.title`) and has a row
of its own, the full 22.3 in width of the text block — the logos no longer take
width away from it. At `--t-title: 58pt` the current title measures 20.1 in, so
there is about 2.2 in spare; it would fit up to roughly 63 pt. If you lengthen
it past the width, drop `--t-title` a few points: the sheet is `overflow:
hidden`, so a browser clips an over-wide title silently. `render.py` catches it.

The row *below* the title is still coupled, and worth knowing about before you
edit it. The byline block and the logos share it: a taller logo can push the
header down, and a wider one narrows the byline column, which can wrap the
subtitle onto a second line and push every band below it down by ~0.37 in. The
sheet has about 0.3 in spare. So if a small change to a logo produces an
overflow at the *bottom* of the poster, this is why — check whether the subtitle
still sits on one line.

## Maths

Write inline maths as a small subset of LaTeX between dollar signs:

```js
"a flow learns $p(Ω_m, σ_8 | s)$ from the summary $s$"
```

`mathHTML()` in `poster.html` turns that into spans that `poster_style.css`
sets the way TeX would: variables italic; digits, capital Greek and function
names (`log`, `max`, ...) upright; a thin space after a comma, a wider one
around `=` and the conditional bar. Spaces inside `$...$` are ignored, so
`$z = 1$` and `$z=1$` come out identical.

| you write | you get |
|---|---|
| `$Ω_m$` or `$\Omega_m$` | Ω with a subscript m — Unicode Greek and `\name` are the same thing |
| `$σ_8$` | a real subscript, not the Unicode `₈` |
| `$b_{s^2}$` | brace anything longer than one character |
| `$\log P(k)$` | upright `log`, italic *P* and *k* |
| `$k_{max}$` | `max` is a known operator name, so it sets upright |
| `$\text{FoM} = 1/\sqrt{\det C}$` | `\text{...}` for upright words, spaces kept |

Backslashes sit inside a JS string, so they have to be **doubled**:
`"$\\Omega_m$"`. Typing Greek straight in as Unicode avoids that entirely and
reads better in the config, which is what the file mostly does.

A `\command` it doesn't know, and a `$` you forgot to close, come out in the
loud TODO highlight instead of silently wrong — same rule as an unfinished
field, so neither reaches the printer unnoticed.

Two limits worth knowing. An expression is `white-space: nowrap` and will never
break across lines, so a long one is a clipping risk — `render.py` checks for
that. And the labels inside the two SVGs (`approaches[].stages` and the cost
chart) are SVG text, not HTML, so a `$` there would print literally. Everything
else in the config takes maths, including the fact strip, the stat tiles and
the cost legend.

Subscripts are positioned rather than `vertical-align`ed so they don't open up
the line they sit on. That matters here: the default adds a hundredth of an inch
to every line carrying maths, on a sheet with about 0.3 in to spare.

`--math-family` inherits the body face, which keeps the poster in one voice.
Set it to a serif for the Computer Modern look.

## Type sizes

`POSTER.type`, at the bottom of `poster_config.js`, holds **every** size on the
poster — header, band headings, body copy, the fact strip, the approach columns,
both results columns, the stats, the footer, and the text inside the two SVGs.
Values are points; write a plain number. A string is passed through as written,
so `"62.5pt"` or `"1.2in"` also work.

Mechanically: each size is a CSS variable declared in `poster_style.css`'s
`:root`, and `applyType()` in `poster.html` writes `POSTER.type` over those
variables at load. So the stylesheet holds the defaults and the config holds
your overrides — delete a line from `type` and it falls back; delete the whole
block and the poster is unchanged. `TYPE_VARS` in `poster.html` is the name map;
a `type` key that isn't in it raises a maroon banner on screen (never printed)
rather than doing nothing quietly. If you add a new size to the CSS, add it to
`TYPE_VARS` too, or the config can't reach it.

The SVG sizes under `type.svg` are viewBox units, not points — the drawings
scale with their columns, so one unit is roughly 0.8 pt in a schematic and
0.72 pt in the cost chart.

Two are load-bearing: `title` must keep the title on one line, and `subtitle`
must keep the subtitle on one line (a second line pushes every band down by
~0.37 in, and the sheet has ~0.3 in to spare). Re-run `render.py` after changing
sizes — the sheet is a fixed 36 in, and two points on a body size can push the
footer off the bottom.

`poster_style.css` still holds band spacing and the figure sizing, marked
`TUNE`. Two of those are worth knowing:

- `--band-gap` (0.56 in) is the space between the header, the four bands and the
  footer. It is the cheapest vertical knob on the sheet — five gaps, so 0.1 in
  here is 0.5 in of poster. `.band`'s own `gap` (0.26 in) is the space between a
  band's rule and its content.
- `--col-question-fig` (10.3 in) is the width of the density-panel track in
  band 1. That figure is 1.655:1 and not height-limited, so this width is what
  sets its size; `--fig-question` (6.22 in) is parked at exactly what the width
  allows. The ceiling here is the prose, not the sheet: much past 10.5 in the
  left column gets too narrow to justify without opening rivers.
- `--fig-contour` (7.00 in) caps the results contour, which *is* height-limited.
  The source is 1051x924, so 7.00 in of height is 7.96 in of width, and the
  middle track of `.results-grid` is set to exactly that. **Change one and
  change the other** — the figure stops filling its track, and `.fig-tag` (the
  "Preliminary" stamp) lands in the gap beside the plot rather than on it.

The sheet is a fixed 36 in and these three between them decide how much of it is
used. As of the last render the content ends 0.64 in above the bottom margin, so
there is very little left to spend: check `render.py`'s overflow number after
raising any of them.

## Rendering and checking it without a browser

`render.py` drives the headless Chromium in the devcontainer, so the poster can
be rendered and checked from a shell:

```bash
/home/node/.conda/envs/simple/bin/python render.py --label some-change \
    --note "what you changed"
python render.py --dsf 2      # 2x supersample, for judging type
python render.py --pdf        # print-media PDF, exact 24x36 in
python render.py --gallery    # rebuild renders/gallery.html
```

Each run writes `renders/NNN-label/` with the full sheet, a downscaled
`review.png`, one crop per band, and `manifest.json`; it appends to
`renders/log.md`. `renders/` is gitignored.

It checks three things and reports them per run:

- **sheet overflow** — content past the 36 in sheet, in inches
- **text clipped** — anything whose content is wider than its box, which the
  sheet's `overflow: hidden` would otherwise hide
- **figure resolution** — effective dpi of every image at its printed size,
  against large-format thresholds (120 fail / 200 good), not the 300 dpi of
  handheld print
- **sheet too narrow** — a row that will not shrink further, pushing content off
  the right edge
- **ink in the margin** — any ink landing inside the 0.85 in page margin,
  measured off the rendered pixels. Nothing clips when this happens, so no DOM
  measurement catches it, but on a printed poster it reads as a mistake

It renders a throwaway copy of `poster.html` with the preview transform
neutralised, so the sheet always lays out at exactly 24x36 in regardless of
window size. Your file is not modified.

Debian's Chromium does not have the fonts a Mac has. Layout, spacing and
overflow transfer faithfully; exact glyphs and line breaks do not, so do a final
print preview in your own Chrome before sending it to a printer.

## Printing

1. Open `poster.html` in **Chrome** (Safari's PDF export ignores `@page size`).
2. ⌘P → Destination **Save as PDF**.
3. Paper size **24 × 36 in** — Chrome picks this up from the CSS, but confirm it.
4. Margins **None**, and tick **Background graphics**, or the maroon rules and
   the takeaway cloud will not print.

If content runs past the bottom of the sheet, a maroon banner says so on screen
with the exact overflow in inches. It never prints. The sheet clips silently
without it, so don't ignore it.

## Figures

`poster/figures/` holds copies, not symlinks, so the bundler below can inline
them.

The contour on the poster is **`contours_poster.svg`**, the vector export — no
longer the soft 180-dpi screen figure. To regenerate it, run the **"Poster
export"** cell in `compare/compare_contours.ipynb` (it sits right after the
single-panel plot). It redraws the figure at the physical size it occupies on
the poster, tightens the axis limits around the contours, and writes both
`contours_poster.svg` and a 400-dpi PNG into `compare/figures/`, then copies
them here. `poster_config.js` already points at the SVG, so a fresh export
needs no config change.

Keep the aspect ratio close to **1.137** when re-exporting. `--fig-contour`
(7.00 in) and the 7.96 in middle track of `.results-grid` are a matched pair
tuned to it — an export at a different shape will either leave a gap beside the
figure or push the band taller.

`render.py` skips its resolution check for any `.svg` source: `naturalWidth` on
a vector is the intrinsic pt size, not a pixel budget, and this one would
otherwise score ~107 dpi and be reported as a hard failure while printing
perfectly.

### The density panels (band 1)

`figures/make_density_fields.py` draws them, and writes `density_fields.png`
straight into this directory — no copy step. Two ways to run it:

```bash
# Delta, env skai_stats: reads /u/shrihan/sumstats/spectra/sims, real fields
python figures/make_density_fields.py

# here: layout only. No sims read, no imshow, panels filled flat, so the
# composition can be judged without a cluster round trip.
/home/node/.conda/envs/simple/bin/python figures/make_density_fields.py --blank
```

`--blank` writes `density_fields_blank.png`, which is a layout proof and never
the figure the poster ships. Point `question.figure.src` at it to see it in
place, then point it back.

The figure is sized to the poster, not to a screen: **10.3 × 6.22 in**, which is
the band 1 figure track (`--col-question-fig`) at the aspect the panels make.
That splits as

```
3 panels x 3.14in + 0.88in label gutter = 10.30in
2 panels x 3.11in                       =  6.22in
```

`--fig-question` in `poster_style.css` must equal that 6.22 in height, or it caps
the figure before the track width does and the panels come out narrow. The two
numbers are coupled the same way `--fig-contour` and `.results-grid` are; change
`FIG_W`/`FIG_H` in the script and both follow.

At `dpi=250` a fresh export is 2575 × 1555 px. **The committed PNG predates the
widening** — it is 2350 px, exported at 9.4 in, and prints at 228 dpi. Same
aspect, so nothing shifts; it is just not the full 250. Re-export on Delta when
convenient.

### The Full Field cubes, and the field tile (band 2)

`figures/make_fl_cubes.py` draws everything in band 2 that is real data: the two
cubes in the Full Field column — the initial conditions, an arrow, the same box
at z = 1 — and `field_tile.png`, the flat z = 1 tile the P(k) and CNN drawings
open with. The tile is the z = 1 cube's own front face under the same transform
and the same colour limits, so the three columns read as one universe compressed
three ways rather than three unrelated pictures.

The catch is that **the initial conditions are not saved by anything** —
`pm/gen_sims/gen_sim_LC.py` writes only the final state. They are deterministic
in `(Ω_c, σ₈, ic_seed)` though, and the seed is in every filename, so they can be
regenerated. That is the one step needing jax, and it runs once:

```bash
# Delta, env skai_jax: regenerate the ICs, write the six face images as an npz
python figures/make_fl_cubes.py --export

# anywhere, simple env: read the npz, draw the two cubes and the tile
/home/node/.conda/envs/simple/bin/python figures/make_fl_cubes.py

# before the export exists: synthetic fields, same geometry
/home/node/.conda/envs/simple/bin/python figures/make_fl_cubes.py --blank
```

`fl_cube_faces.npz` is committed (~555 KB): it holds only the three visible
boundary slabs per cube, already transformed — `log10(1 + δ)` for z = 1, the
linear field as it stands for the ICs. That is the whole point of the split. The
cluster step happens once and every drawing change after it runs locally on real
data.

Two things to check before trusting a fresh export:

- **`BOX_SIZE` is an assumption.** The IC recipe is copied from `gen_sim_LC.py`
  (which cannot be imported — its module body runs the whole LHC batch), and
  `mesh` is asserted against the `mesh_{N}` in the filename, but the box size
  cannot be. The poster's fact strip quotes 320 Mpc/h for the *field-level* sims,
  which are a different set from this LHC.
- **The IC cube is smoothed for display.** It did not wash out, as feared — it
  came back the other way, as grain: the linear field has power to the Nyquist
  scale, so an 8-cell slab of it printed as static rather than as the seeds the
  z = 1 web grew from. `SMOOTH_IC` (2 cells, periodic) is an in-plane Gaussian
  on the IC faces only, applied at *draw* time, so changing it costs no cluster
  round trip. Set it to 0 to see the raw field. The z = 1 cube is untouched.

The strip these sit in is sized by `SCHEM` in `poster.html`: `viewBox 620 × 227`,
which in a 7.1 in column is **2.6 in tall**, so `SCHEM.h` moves band 2's height
and everything under it. The P(k) and CNN drawings do **not** scale up with it:
both already run nearly the full 620 units wide, so `native()` only recentres
them in the taller box. Full Field has two items instead of three, which is why
its cubes reach 2.2 in.

Inside that strip the caption x positions are the *centres of the things they
name*, not an even division of the row — the items are not evenly sized. The CNN
row is the tight one: four items, and its captions ("conv blocks" is 112 units
against a 21-unit vector) are wider than most of what they label, so its conv
stack and vector sit left of where a purely visual layout would put them and its
arrows are drawn at 0.8 weight to give the length back. Move a box there and
move its `cap()` with it.

Note that `render.py` does **not** resolution-check the tile or the cubes: it
collects images with `querySelectorAll("img")` and these are SVG `<image>`. The
script prints the dpi instead.

Still wanted for the framing band: `obs_field.png` from the field-level run
directory on Delta (`fieldinfer_vH2.py` writes it next to `model.yaml`). The
poster currently uses `density_fields.png` in its place.

## Sharing it as a link

```bash
python3 build_artifact.py        # -> build/poster_artifact.html
```

This inlines the CSS, the config and every image as data URIs into one
self-contained file, which is what gets published as a Claude Artifact. Re-run
it after any config change you want reflected in the published page — editing
`poster_config.js` alone does not update an already-published link.

## Publishing it as a GitHub Pages site

The poster is mirrored to a separate **public** repo,
`ShrihanSolo/openskai-poster`, which GitHub Pages serves at
<https://shrihansolo.github.io/openskai-poster/>. This directory stays an
ordinary directory of `sumstats` — no submodule, nothing here changes.

```bash
python3 publish_site.py            # stage, and print exactly what would change
python3 publish_site.py --push     # stage, commit and push
```

`SITE_FILES` at the top of `publish_site.py` is the whole contract: **a file not
named there is not published.** The script fails before touching anything if a
listed file is missing, or if `poster_config.js` points at an image the site
would not carry — which is the failure that would otherwise show up as a broken
image on the live page.

Not published, deliberately: `Neurips.jpeg` (someone else's poster, kept here as
the style reference), `poster_context.txt` (the original brief), `canvas/` (the
abandoned first draft), the `*_blank.png` layout proofs, the superseded contour
exports, and `renders/`.

**Why not `git subtree`.** A subtree split carries the entire history of
`poster/`, so everything in that list would still be in the published history
even after being deleted. `publish_site.py` commits the allowlist to an orphan
branch (`site`) that started from nothing and has never held anything else. The
branch lives in this repo's `.git`, so its history survives `build/` being
deleted and no clone is ever needed; `build/site` is just a scratch checkout of
it, and is gitignored.

The site needs no build step — `poster.html` links its CSS, config and figures
by relative path. `index.html` redirects to it and `.nojekyll` keeps Pages from
running the tree through Jekyll. To look at exactly what will be published
before pushing:

```bash
python3 -m http.server -d build/site 8000
```

Turning Pages on is a one-time step in the site repo: Settings → Pages →
Source `main`, folder `/ (root)`.

## Provenance

Numbers on the poster come from `compare/figures/fom_summary.csv`, written by
`compare_contours.ipynb` at commit `8bbc622`, with the field-level posterior
built from 6 of 8 MCLMC chains (`FL_CHAINS = [0, 1, 2, 4, 5, 7]`) and all three
posteriors conditioned on the same `_obsfl` mock observation.

`Neurips.jpeg` is the previous poster, kept as the style reference. It is not
used in the output.

The colophon at the foot of the sheet prints `meta.venue` and nothing else. It
used to name this notebook and commit as well; that provenance lives here now,
not on the poster.
