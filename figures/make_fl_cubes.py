#!/usr/bin/env python
"""
Draw band 2's field pictures for the OpenSkAI poster: the two simulation cubes
of the Full Field column, and the flat z = 1 tile the other two columns open with.

The column's claim is that field level inference runs the forward model itself:
JaxPM evolves the initial conditions to z = 1 in under a second. So the diagram
is that sentence -- the linear density field as a cube, an arrow, the evolved
field at z = 1 as a second cube -- painted with real data from the same sims as
the band 1 density panels.

Three modes, one geometry:

    # Delta, env skai_jax. The only step that needs jax.
    python make_fl_cubes.py --export

    # anywhere, simple env: read the npz, draw the two cubes and the flat tile
    /home/node/.conda/envs/simple/bin/python make_fl_cubes.py

    # layout only, before the export exists: synthetic fields, same geometry
    /home/node/.conda/envs/simple/bin/python make_fl_cubes.py --blank

Splitting export from drawing is the point. The initial conditions are not saved
by anything -- gen_sim_LC.py writes only the final state -- but they are
deterministic in (Omega_c, sigma_8, ic_seed) and the seed is in every filename,
so --export regenerates them once on the cluster and writes the six face images
as a small npz. Every drawing iteration after that runs on real data, locally.

GEOMETRY -- see poster/README.md. Each cube is drawn at CUBE_H inches tall for
the poster; the SVG strip in poster.html places them and draws the arrow, so
nothing here needs to know the column width.
"""

from __future__ import annotations

import argparse
import glob
import os
import re

import numpy as np

# matplotlib is imported inside the drawing functions, not here: --export needs jax and
# runs in skai_jax on Delta, which does not necessarily carry matplotlib, and
# the export does no drawing at all. Nothing about the cluster step should
# depend on a plotting library being installed there.

# --- Where the sims live (cluster path; see CLAUDE.md -- do not relativize) ---
# The same directory make_density_fields.py reads.
DATA_DIR = "/work/hdd/benb/shrihan/jaxpm_sims"

# --- The realization drawn ---------------------------------------------------
# The centre of the band 1 density panels, so both figures show the same universe.
OMEGA_C = 0.25
SIGMA_8 = 0.75
FILE_INDEX = 1        # which matching realization, as make_density_fields.py does

# --- Initial-conditions recipe ----------------------------------------------
# Copied from pm/gen_sims/gen_sim_LC.py, which is NOT importable -- its module
# body runs the whole LHC batch. These must stay in sync with that file, or the
# regenerated ICs are not the ones the saved final field grew from.
#
# box_size is the one value that cannot be checked against the filename (mesh is,
# below). Confirm it on Delta before trusting the IC cube.
K_GRID = (-4, 1, 128)             # logspace args for the P(k) tabulation
BOX_SIZE = (128.0, 128.0, 128.0)  # Mpc/h

# --- Faces -------------------------------------------------------------------
SLAB = 8              # cells deep. A near-face slab reads as a solid box; a
                      # projection through the whole cube reads as a flat picture.

SMOOTH_IC = 2.0       # cells of in-plane Gaussian, applied to the IC faces only.
                      # The linear field has power out to the Nyquist scale, so an
                      # 8-cell slab of it is mostly grain: at 2.2in printed it read
                      # as static rather than as the seeds the z = 1 web grew from.
                      # Smoothing is a display choice, not a change to the data --
                      # it happens at draw time, on the face images, so it costs no
                      # cluster round trip. Set it to 0 to see the raw field.
                      # The box is periodic, hence mode="wrap".

# --- Cube geometry, inches ---------------------------------------------------
CUBE_H = 2.0          # printed height of the front face plus the top face
TILE_W = 1.5          # printed width of the flat z = 1 tile that opens the P(k)
                      # and CNN diagrams -- 128 of poster.html's 620 strip units
                      # in a 7.1in column is 1.47in.
DEPTH = 0.55          # depth as a fraction of the front face
ANGLE = 32.0          # degrees the depth axis rises
DPI = 300

CMAP = "magma"
EDGE = "#5a504a"      # the arrow colour in poster.html; the cube outline matches
EDGE_W = 1.1

NPZ = "fl_cube_faces.npz"


# --- Data --------------------------------------------------------------------

def find_field(omega_c: float, sigma_8: float) -> str:
    """The saved final field for this cosmology. Filename carries the metadata."""
    key = f"omc_{omega_c:.4f}_sig8_{sigma_8:.4f}"
    files = sorted(f for f in glob.glob(os.path.join(DATA_DIR, "*.npy")) if key in f)
    if not files:
        raise FileNotFoundError(f"no sim matching {key} in {DATA_DIR}")
    return files[min(FILE_INDEX, len(files) - 1)]


def parse_name(path: str) -> tuple[float, float, int, int]:
    """(omega_c, sigma_8, ic_seed, mesh) out of omc_..._sig8_..._s..._mesh_..._2lpt.npy"""
    m = re.search(r"omc_([\d.]+)_sig8_([\d.]+)_s(\d+)_mesh_(\d+)_", os.path.basename(path))
    if not m:
        raise ValueError(f"cannot parse cosmology out of {path}")
    return float(m[1]), float(m[2]), int(m[3]), int(m[4])


def initial_conditions(omega_c: float, sigma_8: float, ic_seed: int, mesh: int):
    """Regenerate the linear field the saved sim grew from. Needs jax + jaxpm."""
    import jax
    import jax.numpy as jnp
    import jax_cosmo as jc
    from jaxpm.pm import linear_field

    cosmo = jc.Planck15(Omega_c=omega_c, sigma8=sigma_8)
    k = jnp.logspace(*K_GRID)
    pk = jc.power.linear_matter_power(cosmo, k)

    def pk_fn(x):
        return jnp.interp(x.reshape(-1), k, pk).reshape(x.shape)

    return np.asarray(
        linear_field((mesh,) * 3, BOX_SIZE, pk_fn, seed=jax.random.PRNGKey(ic_seed))
    )


def faces(field: np.ndarray) -> dict[str, np.ndarray]:
    """The three visible boundary slabs, oriented for the cube below.

    field is (nx, ny, nz). Each face is a mean over SLAB cells of the boundary
    plane it sits on, so the three share their edges and the box reads as solid.
    """
    return {
        # front: the z = 0 plane, rows = y, cols = x
        "front": field[:, :, :SLAB].mean(axis=2).T,
        # top: the y = max plane, rows = depth (z), cols = x
        "top": field[:, -SLAB:, :].mean(axis=1).T,
        # right: the x = max plane, rows = y, cols = depth (z)
        "right": field[-SLAB:, :, :].mean(axis=0),
    }


def synthetic(seed: int, clumpy: bool) -> np.ndarray:
    """A correlated field for --blank. Not physics -- geometry stands in for it."""
    rng = np.random.default_rng(seed)
    n = 128
    noise = rng.standard_normal((n, n, n))
    kx = np.fft.fftfreq(n)[:, None, None]
    ky = np.fft.fftfreq(n)[None, :, None]
    kz = np.fft.fftfreq(n)[None, None, :]
    kk = np.sqrt(kx**2 + ky**2 + kz**2)
    # inf, not a small number: k**-1.6 must vanish at the DC mode, not blow it
    # up. A tiny kk here gives the mean a ~1e5 offset and flattens the field.
    kk[0, 0, 0] = np.inf
    field = np.real(np.fft.ifftn(np.fft.fftn(noise) * kk**-1.6))
    field /= field.std()
    # clipped before the exponential: k**-1.6 leaves rare huge modes, and
    # expm1 on those overflows. Only --blank goes through here.
    return np.expm1(1.6 * np.clip(field, -4, 4)) if clumpy else field


# --- Drawing -----------------------------------------------------------------

def transform(kind: str, field: np.ndarray) -> np.ndarray:
    """Applied to the whole field BEFORE the faces are cut.

    Order matters: log10(1 + delta) then average, the way the band 1 panels do
    it. Averaging the raw density first and taking the log after lets a handful
    of collapsed peaks own the entire colour range and the cube renders black.
    """
    return np.log10(1 + np.clip(field, 0, None)) if kind == "z1" else field


def smooth(kind: str, f: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """In-plane Gaussian on the IC faces. See SMOOTH_IC."""
    if kind != "ic" or not SMOOTH_IC:
        return f
    from scipy.ndimage import gaussian_filter
    return {n: gaussian_filter(v, SMOOTH_IC, mode="wrap") for n, v in f.items()}


def scale_for(kind: str, f: dict[str, np.ndarray]) -> tuple[float, float]:
    """Per-cube colour scale. The two cubes are different quantities, not two
       cosmologies, so they do not share limits the way the band 1 panels do."""
    stack = np.concatenate([v.ravel() for v in f.values()])
    if kind == "z1":
        return tuple(np.percentile(stack, [1.0, 99.5]))
    # the linear field is signed and Gaussian: symmetric limits, or half the
    # colormap is spent on underdensities and the cube reads flat.
    v = np.percentile(np.abs(stack), 99.7)
    return -v, v


def draw_cube(kind: str, f: dict[str, np.ndarray], out: str) -> None:
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from matplotlib.transforms import Affine2D

    dx = DEPTH * np.cos(np.radians(ANGLE))
    dy = DEPTH * np.sin(np.radians(ANGLE))
    w, h = 1.0 + dx, 1.0 + dy

    fig = plt.figure(figsize=(CUBE_H * w / h, CUBE_H), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-0.02, w + 0.02)
    ax.set_ylim(-0.02, h + 0.02)
    ax.set_aspect("equal")
    ax.axis("off")

    f = smooth(kind, f)
    lo, hi = scale_for(kind, f)

    # Each face is the unit square carried onto its parallelogram by one affine.
    # imshow under an affine is exact, so the image fills the face with no gap
    # and no bleed -- which mplot3d's depth sorting would not give us.
    quads = {
        "front": ([[1, 0, 0], [0, 1, 0]], [(0, 0), (1, 0), (1, 1), (0, 1)]),
        "top":   ([[1, dx, 0], [0, dy, 1]], [(0, 1), (1, 1), (1 + dx, 1 + dy), (dx, 1 + dy)]),
        "right": ([[dx, 0, 1], [dy, 1, 0]], [(1, 0), (1 + dx, dy), (1 + dx, 1 + dy), (1, 1)]),
    }

    for name, (mat, corners) in quads.items():
        tr = Affine2D(matrix=np.array(mat + [[0, 0, 1]], dtype=float))
        im = ax.imshow(
            f[name],
            extent=(0, 1, 0, 1), origin="lower", cmap=CMAP, vmin=lo, vmax=hi,
            interpolation="nearest", transform=tr + ax.transData,
        )
        im.set_clip_path(Polygon(corners, transform=ax.transData))

    # The silhouette plus the three edges that meet at the near-top-right corner.
    ax.add_patch(Polygon(
        [(0, 0), (1, 0), (1 + dx, dy), (1 + dx, 1 + dy), (dx, 1 + dy), (0, 1)],
        closed=True, fill=False, edgecolor=EDGE, linewidth=EDGE_W, joinstyle="miter"))
    for a, b in (((0, 1), (1, 1)), ((1, 1), (1, 0)), ((1, 1), (1 + dx, 1 + dy))):
        ax.plot(*zip(a, b), color=EDGE, linewidth=EDGE_W, solid_capstyle="round")

    fig.savefig(out, dpi=DPI, transparent=True)
    plt.close(fig)
    px = round(CUBE_H * w / h * DPI)
    print(f"wrote {out}  ({px}x{round(CUBE_H * DPI)}px, {round(DPI)} dpi at {CUBE_H}in tall)")


def draw_tile(f: dict[str, np.ndarray], out: str) -> None:
    """The flat field tile that opens the P(k) and CNN diagrams.

    The z = 1 cube's own front face, with the same transform and the same colour
    limits as the cube, so all three columns of band 2 visibly show one universe
    rather than three unrelated pictures.

    Square, while poster.html draws it into a 128x118 box with
    preserveAspectRatio="slice": the tile is cropped a little top and bottom
    rather than squashed, which a density field does not mind.
    """
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    lo, hi = scale_for("z1", f)
    fig = plt.figure(figsize=(TILE_W, TILE_W), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.imshow(f["front"], origin="lower", cmap=CMAP, vmin=lo, vmax=hi,
              interpolation="nearest")
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    px = round(TILE_W * DPI)
    print(f"wrote {out}  ({px}x{px}px, {DPI} dpi at {TILE_W}in wide)")


# --- Modes -------------------------------------------------------------------

def do_export(here: str) -> None:
    path = find_field(OMEGA_C, SIGMA_8)
    omega_c, sigma_8, seed, mesh = parse_name(path)
    print(f"final field: {os.path.basename(path)}")
    print(f"  Omega_c={omega_c} sigma_8={sigma_8} seed={seed} mesh={mesh}")

    z1 = np.load(path)
    assert z1.shape == (mesh,) * 3, f"{z1.shape} is not mesh {mesh} from the filename"

    print("regenerating initial conditions (jax)...")
    ic = initial_conditions(omega_c, sigma_8, seed, mesh)

    out = os.path.join(here, NPZ)
    # The npz holds transformed faces, not raw density: log10(1 + delta) for the
    # z = 1 cube, the linear field as it stands for the ICs. See transform().
    np.savez_compressed(
        out,
        **{f"ic_{k}": v for k, v in faces(transform("ic", ic)).items()},
        **{f"z1_{k}": v for k, v in faces(transform("z1", z1)).items()},
        meta=np.array([omega_c, sigma_8, seed, mesh, SLAB], dtype=float),
        source=np.array(os.path.basename(path)),
    )
    print(f"wrote {out}  ({os.path.getsize(out) / 1e6:.2f} MB)")


def load_faces(here: str, blank: bool) -> dict[str, dict[str, np.ndarray]]:
    if blank:
        return {"ic": faces(transform("ic", synthetic(0, clumpy=False))),
                "z1": faces(transform("z1", synthetic(0, clumpy=True)))}
    path = os.path.join(here, NPZ)
    if not os.path.exists(path):
        raise SystemExit(
            f"{NPZ} is missing. Run --export on Delta first, or --blank to work\n"
            f"on the layout with synthetic fields.")
    d = np.load(path, allow_pickle=True)
    m = d["meta"]
    print(f"{NPZ}: Omega_c={m[0]} sigma_8={m[1]} seed={int(m[2])} mesh={int(m[3])}")
    return {c: {n: d[f"{c}_{n}"] for n in ("front", "top", "right")} for c in ("ic", "z1")}


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--export", action="store_true",
                   help="regenerate the ICs on Delta and write the face npz (needs jax)")
    p.add_argument("--blank", action="store_true",
                   help="draw the layout from synthetic fields; no npz, no sims")
    a = p.parse_args()

    if a.export:
        do_export(here)
        return

    f = load_faces(here, a.blank)
    suffix = "_blank" if a.blank else ""
    draw_cube("ic", f["ic"], os.path.join(here, f"fl_cube_ic{suffix}.png"))
    draw_cube("z1", f["z1"], os.path.join(here, f"fl_cube_z1{suffix}.png"))
    draw_tile(f["z1"], os.path.join(here, f"field_tile{suffix}.png"))


if __name__ == "__main__":
    main()
