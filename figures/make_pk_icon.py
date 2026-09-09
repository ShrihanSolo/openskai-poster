#!/usr/bin/env python
"""
Produce the SVG path for the P(k) icon in band 2 (SUMMARIZATION) of the poster.

The middle stage of the Power Spectrum column is a small log-log plot of P(k)
against k. Its curve is not drawn by eye: it is a linear matter power spectrum
from the Eisenstein & Hu (1998) no-wiggle transfer function, sampled and mapped
into the schematic's viewBox. This script prints that path; the numbers are then
pasted into PK_CURVE in poster.html, so the poster stays a self-contained set of
static files with no runtime dependency.

    /home/node/.conda/envs/simple/bin/python make_pk_icon.py

The overall amplitude is irrelevant -- the icon carries no ticks, and the y range
is normalized to the plot box -- so sigma_8 never enters. Only the *shape* over
the plotted k range is real: the turnover near k ~ 0.02 h/Mpc and the steepening
fall towards the small scales where the analysis cuts off (k_c = 0.8 h/Mpc). The
low end runs below the box fundamental (2*pi/320 ~ 0.02 h/Mpc) on purpose: with the
turnover in frame the icon reads as a power spectrum at a glance.

GEOMETRY -- the plot box below must match the one drawn in poster.html's
schematic(). Both are in schematic viewBox units (the schematic is 620x168, and
the field tile beside this plot spans y = 10..128).
"""

from __future__ import annotations

import numpy as np

# --- fiducial cosmology (the LHC centre; see pm/gen_sims) --------------------
OMEGA_M = 0.30
OMEGA_B = 0.049
H = 0.70
N_S = 0.96
T_CMB = 2.7255

# --- plot box, in schematic viewBox units -----------------------------------
X0, X1 = 246.0, 380.0          # left/right of the axes
Y0, Y1 = 122.0, 20.0           # bottom/top (SVG y grows downward)
PAD_TOP, PAD_RIGHT = 4.0, 2.0  # keep the curve off the corners
PAD_BOTTOM = 7.0               # ...and off the x-axis, which it would otherwise
                               # meet exactly at the bottom-right corner

K_MIN, K_MAX = 0.004, 1.5       # h/Mpc; the low end reaches below the box
                               # fundamental so the turnover is in frame
N_POINTS = 24


def transfer_nowiggle(k):
    """EH98 eq. 28-31: the no-wiggle (baryon-smoothed) transfer function.

    `k` is in h/Mpc; the fitting formula is in physical units, so it is
    converted with h on the way in.
    """
    k = np.asarray(k, dtype=float) * H          # -> 1/Mpc
    om_h2 = OMEGA_M * H**2
    ob_h2 = OMEGA_B * H**2
    f_b = OMEGA_B / OMEGA_M
    theta = T_CMB / 2.7

    # sound horizon (eq. 26) and the shape parameter with baryon suppression
    s = 44.5 * np.log(9.83 / om_h2) / np.sqrt(1.0 + 10.0 * ob_h2**0.75)
    alpha_gamma = (1.0 - 0.328 * np.log(431.0 * om_h2) * f_b
                   + 0.38 * np.log(22.3 * om_h2) * f_b**2)
    gamma_eff = om_h2 * (alpha_gamma
                         + (1.0 - alpha_gamma) / (1.0 + (0.43 * k * s)**4))

    q = k * theta**2 / gamma_eff
    c0 = 14.2 + 731.0 / (1.0 + 62.5 * q)
    l0 = np.log(2.0 * np.e + 1.8 * q)
    return l0 / (l0 + c0 * q**2)


def main():
    k = np.geomspace(K_MIN, K_MAX, N_POINTS)
    pk = k**N_S * transfer_nowiggle(k) ** 2

    # log-log, each axis stretched to fill the box: the icon shows shape, not
    # values, and a faithful decade-per-unit mapping would leave it near-flat.
    lx = np.log10(k)
    ly = np.log10(pk)
    x = X0 + (lx - lx.min()) / np.ptp(lx) * (X1 - PAD_RIGHT - X0)
    y_bot = Y0 - PAD_BOTTOM
    y = y_bot - (ly - ly.min()) / np.ptp(ly) * (y_bot - Y1 - PAD_TOP)

    pts = [f"{a:.1f} {b:.1f}" for a, b in zip(x, y)]
    print("M " + " L ".join(pts))


if __name__ == "__main__":
    main()
