# T-ETH-Elite ↔ Raspberry Pi HAT adapter

Hardware that lets a **Raspberry Pi HAT** run on a **LilyGO T-ETH-Elite**
(ESP32-S3) instead of a Pi. Built for one specific HAT — TSN Lab's
`10BASE-T1S HAT` (Microchip LAN8651, [devicemart #15980354](https://www.devicemart.co.kr/goods/view?no=15980354)),
which is a Pi-only product — so that a 10BASE-T1S node can be an ESP32 rather
than a Raspberry Pi. Firmware side lives in
[esp32-t1s-bridge](https://github.com/hwkim3330/esp32-t1s-bridge).

```
   TSN Lab 10Base-T1S HAT  (LAN8651)
   ── adapter PCB ──                    pcb/
   LilyGO T-ETH-Elite  (ESP32-S3)
   ── printed tray ──                   case/
```

| | |
|---|---|
| `pcb/` | the adapter board — KiCad project, gerbers, BOM/CPL |
| `case/` | printed base tray for the Elite, generated and clearance-checked by script |
| `reference/` | LilyGo's own DXF and 3D models, plus the script that re-derives every dimension from them |
| [`pcb/GEOMETRY.md`](pcb/GEOMETRY.md) | **the single source of truth** — every measured number, with its provenance |

## The short version of why this exists

Plugging the HAT straight onto the T-ETH-Elite *almost* works, and the two
reasons it doesn't are worth stating up front:

1. **Electrically it already works.** LilyGo wired the Elite's 40-pin header to
   the standard Raspberry Pi GPIO assignment, pin for pin. No level shifting,
   no remapping, nothing to translate. The adapter carries no signal logic at
   all — the connection is the stacking header's own pins, straight through.
2. **The near mounting holes already line up.** Deriving where a Pi's
   header-end holes must sit, from the Elite's own header position, lands on
   the Elite's own bottom hole pair to within **0.005 mm**. Same holes.
3. **But the RJ45 is in the way.** The Elite's RJ45 stands **15.97 mm** off the
   PCB while its header pins stop at **10.10 mm**. Any flat, un-notched board
   dropped onto that header — which is exactly what a standard Pi HAT is — hits
   the jack 5.87 mm before it seats. LilyGo's own shields cut a notch for it.
4. **And the far mounting holes fall off the end.** A HAT's far holes sit 49 mm
   from the near pair, i.e. at y = 53.63 in the Elite's frame — past the Elite's
   own board edge at 49.19. There is nothing there to screw into.

So the adapter is not a convenience. It is a notch and two mounting holes, and
without them the HAT physically cannot sit on this board.

## Provenance

Nothing here was scaled off a drawing by eye. The mounting holes, the 40-pin
grid, the outline notches and the component heights all come out of LilyGo's own
published DXF and 3D CAD, cross-checked three ways — and the hole pattern was
independently validated against a real board on a laser-cut plate in
`~/stl-model/acrylic-frame`. `reference/measure.py` re-derives the whole set
from the vendor files, so the numbers can be audited rather than trusted:

```bash
pip install --user ezdxf trimesh manifold3d py7zr
python3 reference/measure.py
```

The one number that is *not* from CAD is the HAT's own 58 × 49 hole pattern,
which is inferred from a product photo (method and error bars in
[`pcb/GEOMETRY.md`](pcb/GEOMETRY.md)). Only the placement of the adapter's two far holes depends
on it.

## Status

Designed, checked, **never built**. No board has been fabricated, nothing has
been printed, and no part of the stack has been assembled or powered. The
clearance check the case script runs is against LilyGo's model, not against a
real board. Read the "not verified" sections in [`pcb/README.md`](pcb/README.md) and
[`case/README.md`](case/README.md) before spending money.
