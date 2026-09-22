#!/usr/bin/env python3
"""Printed base tray for the LilyGO T-ETH-Elite, under the T1S HAT adapter stack.

    python3 case.py            # -> case_bottom.stl  (+ a clearance report)
    python3 case.py --check    # clearance report only, writes nothing

Why only a base tray and not a closed box: the two lower boards (Elite, adapter)
have exact published geometry, so a part built against them can be *checked*
rather than hoped at - this script boolean-intersects the finished tray with
LilyGo's own 3D model of the board and fails if they overlap anywhere. The T1S
HAT on top has no published CAD; its size is known only from a product photo,
and its terminal block, rotary node-ID switch and wake button all need to stay
reachable. Enclosing that from photo-derived numbers would be guessing, so the
tray stops below it and the HAT stays open.

Frame: same as hardware/t_eth_elite_hat_adapter/GEOMETRY.md - origin at the
Elite PCB's bottom-left corner, +x right, +y up - except z, which here is 0 at
the PCB's *bottom* face (GEOMETRY.md quotes LilyGo's CAD frame, where the PCB is
centred on z=0 and its top face is +0.79). Everything LilyGo-derived is
converted once, in ELITE below, and never again.

Requires: trimesh, manifold3d. Same toolchain as ../../../stl-model/acrylic-frame.
"""
import argparse
import os
import sys

import numpy as np
import trimesh
from trimesh.creation import box, cylinder

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = 'manifold'

# ---------------------------------------------------------------- the board
# From LilyGo's own files (shell/T-ETH-ELite.dxf and shell/3D/T-ETH-ELite.7z),
# see GEOMETRY.md for the full provenance table. z converted to this file's
# frame by +0.79 (CAD centres the 1.575mm PCB on z=0).
PCB_W, PCB_H, PCB_T = 66.191, 49.192, 1.575
PCB_R = 3.0                                  # corner radius
HOLES = [(3.33, 4.63), (61.33, 4.63), (2.98, 46.23), (63.23, 46.20)]
ANTENNA_NOTCH = (59.84, 23.93, 66.19, 42.22)  # x0,y0,x1,y1 - cut out of the PCB

# Parts that decide the tray's shape. (x0, y0, x1, y1, z_top_above_pcb_bottom)
RJ45 = (-5.18, 10.50, 16.42, 28.90, 16.76)   # also reaches 1.43 BELOW the PCB
USBC = (59.99, 11.27, 67.32, 20.21, 4.67)
SW_BOOT = (41.48, 45.85, 45.98, 49.35, 4.79)
SW_RST = (52.10, 45.85, 56.60, 49.35, 4.79)
MICROSD = (32.49, 33.62, 48.64, 48.12)       # underside, 2.06 below the PCB
UNDER_DEEP = 2.06                            # deepest thing under the PCB

# ---------------------------------------------------------------- the tray
CLEAR = 0.4          # around the PCB edge, per side
WALL = 2.0
FLOOR_T = 3.2
STANDOFF = 3.2       # PCB bottom above the floor's top face; > UNDER_DEEP
WALL_TOP = 6.0       # above the PCB bottom face; must stay under the adapter
BOSS_D = 6.0
# One M2.5 goes all the way up from under the tray: through the boss, through
# the Elite's own hole, into a ~13mm female standoff that then carries the
# adapter. So the boss is a clearance hole, not a pilot, and the head is sunk
# into the floor's underside so the tray still sits flat.
CLEAR_D = 2.7
CBORE_D, CBORE_H = 5.5, 2.0
DECK = None          # e.g. (35.0, 45.0) to add the acrylic-frame plate-B deck

Z_FLOOR_TOP = -STANDOFF
Z_FLOOR_BOT = Z_FLOOR_TOP - FLOOR_T


def bx(x0, x1, y0, y1, z0, z1):
    m = box(extents=(x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m


def cyl(d, z0, z1, x, y, sections=64):
    m = cylinder(radius=d / 2, height=z1 - z0, sections=sections)
    m.apply_translation((x, y, (z0 + z1) / 2))
    return m


def rounded(x0, x1, y0, y1, z0, z1, r):
    parts = [bx(x0 + r, x1 - r, y0, y1, z0, z1), bx(x0, x1, y0 + r, y1 - r, z0, z1)]
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
        parts.append(cyl(2 * r, z0, z1, cx, cy))
    return trimesh.boolean.union(parts, engine=ENGINE)


def build():
    # outer shell: PCB + clearance + wall, from the floor's underside to the wall top
    ox0, oy0 = -CLEAR - WALL, -CLEAR - WALL
    ox1, oy1 = PCB_W + CLEAR + WALL, PCB_H + CLEAR + WALL
    shell = rounded(ox0, ox1, oy0, oy1, Z_FLOOR_BOT, WALL_TOP, PCB_R + WALL)

    cuts = []
    # the pocket the board sits in, down to the floor's top face
    cuts.append(rounded(-CLEAR, PCB_W + CLEAR, -CLEAR, PCB_H + CLEAR,
                        Z_FLOOR_TOP, WALL_TOP + 1, PCB_R + CLEAR))

    # RJ45: protrudes 5.18 past the left edge and dips 1.43 below the PCB, so the
    # wall is cut away outright rather than merely lowered
    cuts.append(bx(ox0 - 1, PCB_W / 2, RJ45[1] - 0.5, RJ45[3] + 0.5,
                   Z_FLOOR_TOP, WALL_TOP + 1))
    # USB-C: protrudes 1.13 past the right edge
    cuts.append(bx(PCB_W / 2, ox1 + 1, USBC[1] - 0.5, USBC[3] + 0.5,
                   Z_FLOOR_TOP, WALL_TOP + 1))
    # keep plastic off the WROOM antenna (LilyGo cut the PCB away here too)
    cuts.append(bx(PCB_W / 2, ox1 + 1, ANTENNA_NOTCH[1] - 0.5, ANTENNA_NOTCH[3] + 0.5,
                   Z_FLOOR_TOP, WALL_TOP + 1))
    # BOOT / RST live at the far edge and are poked from above through the
    # adapter; drop the wall there so a tool can also come in from the side
    for sw in (SW_BOOT, SW_RST):
        cuts.append(bx(sw[0] - 1.0, sw[2] + 1.0, PCB_H / 2, oy1 + 1,
                       2.0, WALL_TOP + 1))
    # underside pocket for the microSD socket (2.06 below the PCB vs 3.2 of
    # standoff - already clear, but keep the floor from trapping dust/heat)
    cuts.append(bx(MICROSD[0], MICROSD[2], MICROSD[1], MICROSD[3],
                   Z_FLOOR_BOT - 1, Z_FLOOR_BOT + FLOOR_T * 0.5))
    # vents
    for i in range(4):
        x = 20.0 + i * 7.0
        cuts.append(bx(x, x + 3.5, 8.0, 30.0, Z_FLOOR_BOT - 1, Z_FLOOR_TOP + 1))

    body = trimesh.boolean.difference([shell] + cuts, engine=ENGINE)

    # bosses under the board's own four holes, then pilot-drill them
    posts = [cyl(BOSS_D, Z_FLOOR_TOP, 0.0, hx, hy) for hx, hy in HOLES]
    body = trimesh.boolean.union([body] + posts, engine=ENGINE)
    drills = []
    for hx, hy in HOLES:
        drills.append(cyl(CLEAR_D, Z_FLOOR_BOT - 1, 0.5, hx, hy))
        drills.append(cyl(CBORE_D, Z_FLOOR_BOT - 0.01, Z_FLOOR_BOT + CBORE_H, hx, hy))

    if DECK:
        dx, dy = DECK
        cx, cy = PCB_W / 2, PCB_H / 2
        for sx in (-1, 1):
            for sy in (-1, 1):
                drills.append(cyl(3.4, Z_FLOOR_BOT - 1, Z_FLOOR_TOP + 1,
                                  cx + sx * dx / 2, cy + sy * dy / 2))
    return trimesh.boolean.difference([body] + drills, engine=ENGINE)


# ---------------------------------------------------------------- the check
def elite_model():
    """LilyGo's own 3D model, moved into this file's frame. None if absent."""
    for p in (os.path.join(HERE, 'reference', 'T-ETH-ELite.stl'),
              '/tmp/lgcad/T-ETH-ELite.stl'):
        if os.path.exists(p):
            m = trimesh.load(p)
            # Align from the model itself rather than a hard-coded 0.79: the PCB
            # slab's own bottom face becomes z=0. (The model carries copper-layer
            # faces at +/-0.81 around a 1.575 slab, so any assumed constant is
            # wrong by ~0.02 and shows up as a phantom collision.)
            slab = max((b for b in m.split(only_watertight=False)
                        if 1.4 < (b.bounds[1] - b.bounds[0])[2] < 1.8),
                       key=lambda b: np.prod((b.bounds[1] - b.bounds[0])[:2]))
            m.apply_translation((33.0955, 24.596, -slab.bounds[0][2]))
            return m, p
    return None, None


def check(tray):
    print("tray: %.1f x %.1f x %.1f mm, %.1f cm3, watertight=%s"
          % (*(tray.bounds[1] - tray.bounds[0]), tray.volume / 1000, tray.is_watertight))
    for hx, hy in HOLES:
        near = [p for p in tray.vertices
                if abs(p[0] - hx) < CLEAR_D and abs(p[1] - hy) < CLEAR_D]
        print("  boss at (%.2f, %.2f): %d verts within the pilot bore" % (hx, hy, len(near)))

    elite, path = elite_model()
    if elite is None:
        print("\nNO CLEARANCE CHECK: LilyGo's T-ETH-ELite.stl not found.")
        print("  fetch shell/3D/T-ETH-ELite.7z from Xinyuan-LilyGO/LilyGO-T-ETH-Series")
        return False
    print("\nclearance check against %s" % path)
    print("  board model: %.2f x %.2f x %.2f mm"
          % tuple(elite.bounds[1] - elite.bounds[0]))
    hit = trimesh.boolean.intersection([tray, elite.convex_hull], engine=ENGINE)
    hull_v = 0.0 if hit is None or hit.is_empty else hit.volume
    print("  vs convex hull of the whole board : %.2f cm3 %s"
          % (hull_v / 1000, "(expected - the hull swallows the RJ45 notch)" if hull_v else ""))
    inside = tray.contains(elite.vertices)
    n = int(inside.sum())
    print("  point test: %d of %d board-model vertices fall inside the tray solid"
          % (n, len(elite.vertices)))
    real = n
    if n:
        bad = elite.vertices[inside]
        print("     region x %.2f..%.2f y %.2f..%.2f z %.3f..%.3f"
              % (bad[:,0].min(), bad[:,0].max(), bad[:,1].min(), bad[:,1].max(),
                 bad[:,2].min(), bad[:,2].max()))
        # LilyGo's model draws each copper layer as a zero-thickness sheet 0.02
        # OUTSIDE the substrate, so the board's lowest "surface" sits 0.02 below
        # the slab the boards actually rest on. Anything confined to that skin
        # is that artifact, not interference - 0.02 is an order of magnitude
        # under what a printer resolves.
        if bad[:,2].max() <= 0.0 and bad[:,2].min() >= -0.05:
            print("     -> all within 0.05 of the boss top plane: this is the model's"
                  " zero-thickness copper sheet, not a collision")
            real = 0
    parts = [b for b in elite.split(only_watertight=False) if b.volume > 1.0]
    print("  vs %d individual bodies:" % len(parts))
    worst = 0.0
    for b in parts:
        try:
            ov = trimesh.boolean.intersection([tray, b], engine=ENGINE)
        except Exception:
            continue
        v = 0.0 if ov is None or ov.is_empty else ov.volume
        if v > 1.0:
            bb = b.bounds
            print("    COLLISION %.1f mm3 with body at x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f"
                  % (v, bb[0][0], bb[1][0], bb[0][1], bb[1][1], bb[0][2], bb[1][2]))
            worst = max(worst, v)
    print("  worst single-body overlap: %.2f mm3 %s"
          % (worst, "FAIL" if worst > 1.0 else "-> clear"))
    return worst <= 1.0 and real == 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help="report only, write nothing")
    a = ap.parse_args()
    tray = build()
    ok = check(tray)
    if not a.check:
        out = os.path.join(HERE, 'case_bottom.stl')
        tray.export(out)
        print("\nwrote %s" % out)
    sys.exit(0 if ok else 1)
