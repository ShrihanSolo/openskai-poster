#!/usr/bin/env python
"""
Draw the density-field panels for band 1 (MOTIVATION) of the OpenSkAI poster.

Six projected density fields in a 2x3 grid: the top row varies sigma_8 at fixed
Omega_c, the bottom row varies Omega_c at fixed sigma_8. The panels touch, carry
no colorbar, ticks or axis labels, and name only the parameter that varies --
the row label in the left gutter names the one held fixed.

Ported from field/yuuki/PlotField.ipynb (cell 4). The data handling is that
notebook's, unchanged; only the drawing is new.

Two ways to run it:

    # on Delta, env skai_stats -- reads the sims, writes the real figure
    python make_density_fields.py

    # here, layout only -- no sims touched, no imshow, flat panels
    /home/node/.conda/envs/simple/bin/python make_density_fields.py --blank

The blank mode exists because the layout is worth iterating on without a cluster
round trip. It is the same figure, the same geometry and the same type; only the
fields are missing, so what it shows about composition is true.

GEOMETRY -- read poster/README.md before changing it. The figure is sized to the
poster, not to a screen: 9.4in is the band 1 figure track (--col-question-fig in
poster_style.css) and 5.68in is the height of the prose column beside it, so the
figure sits flush with the text and the band's height does not change.

    3 panels x 2.84in + 0.88in gutter = 9.40in
    2 panels x 2.84in                 = 5.68in
"""

from __future__ import annotations

import argparse
import glob
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np

# --- Where the sims live (cluster path; see CLAUDE.md -- do not relativize) ---
DATA_DIR = "/work/hdd/benb/shrihan/jaxpm_sims"

# --- What is drawn -----------------------------------------------------------
OMEGA_C_FIXED = 0.25
SIGMA_8_FIXED = 0.75
SIGMA_8_ROW = [0.5, 0.75, 1.0]     # top row, at OMEGA_C_FIXED
OMEGA_C_ROW = [0.13, 0.49, 0.85]   # bottom row, at SIGMA_8_FIXED

FILE_INDEX = 1        # which matching realization to take, as the notebook did
PROJECT_AXIS = 2      # sum along this axis, over the first quarter of the box

# --- Geometry, inches --------------------------------------------------------
FIG_W, FIG_H = 10.30, 6.22
GUTTER = 0.88         # left strip holding the rotated row labels
DPI = 250             # 2575 x 1555 px, i.e. 250 dpi at the poster's 10.3in.
                      # The committed PNG predates the widening and is 2350px,
                      # which still prints at 228 dpi -- above render.py's 200
                      # dpi bar, so it is not urgent. Re-export on Delta to get
                      # the full 250.

# --- Type --------------------------------------------------------------------
INK = "#17130f"       # --ink from poster_style.css
PT_PANEL = 23         # inset panel title, white on the field
PT_ROW = 30           # gutter row label; "large so it would be visible"

CMAP = "magma"
BLANK_FILL = 0.45     # position in the colormap used for --blank panels


def load_field(omega_c: float, sigma_8: float) -> np.ndarray:
    """The notebook's loader: substring-match the filename, take the second hit.

    Filenames are omc_{Omega_c:.4f}_sig8_{sigma_8:.4f}_s{seed}_mesh_{N}_2lpt.npy,
    and the .2f key below is a prefix of the .4f field, so the match still works.
    """
    key = f"omc_{omega_c:.4f}_sig8_{sigma_8:.4f}"
    files = sorted(f for f in glob.glob(os.path.join(DATA_DIR, "*.npy")) if key in f)
    if not files:
        raise FileNotFoundError(f"no sim matching {key} in {DATA_DIR}")
    return np.load(files[min(FILE_INDEX, len(files) - 1)])


def project(delta: np.ndarray) -> np.ndarray:
    """log10(1 + delta), summed over the first quarter of the box in depth."""
    field = np.log10(delta + 1)
    depth = field.shape[0] // 4
    sl = [slice(None)] * field.ndim
    sl[PROJECT_AXIS] = slice(None, depth)
    return field[tuple(sl)].sum(axis=PROJECT_AXIS)


def panels(blank: bool):
    """The six panels in display order, each (inset title, projection or None)."""
    top = [(rf"$\sigma_8 = {s8}$", None if blank else project(load_field(OMEGA_C_FIXED, s8)))
           for s8 in SIGMA_8_ROW]
    bottom = [(rf"$\Omega_c = {oc}$", None if blank else project(load_field(oc, SIGMA_8_FIXED)))
              for oc in OMEGA_C_ROW]
    return top + bottom


def draw(cells, out: str) -> None:
    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=DPI)

    # Panels bleed to the top, right and bottom edges; the gutter is the only
    # margin, and wspace/hspace are zero so neighbours share an edge.
    gs = fig.add_gridspec(
        2, 3,
        left=GUTTER / FIG_W, right=1.0, bottom=0.0, top=1.0,
        wspace=0.0, hspace=0.0,
    )

    # One colour scale for all six. With the colorbar gone, per-panel autoscaling
    # would flatten the very differences the figure exists to show.
    shown = [f for _, f in cells if f is not None]
    vmin, vmax = (min(f.min() for f in shown), max(f.max() for f in shown)) if shown else (0, 1)

    for i, (title, field) in enumerate(cells):
        ax = fig.add_subplot(gs[divmod(i, 3)])
        if field is None:
            ax.set_facecolor(plt.get_cmap(CMAP)(BLANK_FILL))
        else:
            ax.imshow(field, cmap=CMAP, vmin=vmin, vmax=vmax, origin="lower")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)

        # Inset, top left, in white. The dark stroke is what keeps it readable
        # where a panel goes bright, which magma does at the massive end.
        ax.text(
            0.035, 0.965, title,
            transform=ax.transAxes, ha="left", va="top",
            color="white", fontsize=PT_PANEL,
            path_effects=[pe.withStroke(linewidth=3.0, foreground="#000000", alpha=0.55)],
        )

    # Row labels: the parameter each row holds fixed, centred in the gutter.
    x = 0.5 * GUTTER / FIG_W
    for y, label in ((0.75, rf"$\Omega_c = {OMEGA_C_FIXED}$"),
                     (0.25, rf"$\sigma_8 = {SIGMA_8_FIXED}$")):
        fig.text(x, y, label, rotation=90, ha="center", va="center",
                 fontsize=PT_ROW, color=INK)

    # Transparent *figure* patch so the gutter takes the poster's paper, but not
    # transparent=True, which would zero the axes patches along with it and
    # erase the flat panels --blank draws.
    fig.savefig(out, dpi=DPI, facecolor=(1, 1, 1, 0))
    plt.close(fig)
    print(f"wrote {out}  ({FIG_W}x{FIG_H}in @ {DPI}dpi = "
          f"{round(FIG_W * DPI)}x{round(FIG_H * DPI)}px)")


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--blank", action="store_true",
                   help="draw the layout only: no sims read, no imshow, flat panels")
    p.add_argument("--out", default=None,
                   help="output path (default: density_fields[_blank].png beside this script)")
    a = p.parse_args()

    out = a.out or os.path.join(
        here, "density_fields_blank.png" if a.blank else "density_fields.png")
    draw(panels(a.blank), out)


if __name__ == "__main__":
    main()
