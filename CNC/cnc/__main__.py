"""CLI.

  python -m cnc build projects/herz                      # build a project
  python -m cnc check datei.nc --stock 100x95x6 \\
        --tool flat-4mm-2f [--material holz] [--preview p.png]   # check any .nc (e.g. from Estlcam)
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

from . import gcode, sim
from .check import check
from .config import Stock, load_machine, load_tools
from .job import build


def _load_job(project: Path):
    spec = importlib.util.spec_from_file_location(f"project_{project.name}", project / "job.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.job()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cnc")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="Projekt bauen: G-Code, Pruefung, Vorschau, Einrichteblatt")
    b.add_argument("project", type=Path)
    c = sub.add_parser("check", help="Beliebige .nc-Datei pruefen und simulieren")
    c.add_argument("nc", type=Path)
    c.add_argument("--stock", required=True, help="BxTxD in mm, z.B. 100x95x6")
    c.add_argument("--tool", required=True)
    c.add_argument("--material", default="holz")
    c.add_argument("--preview", type=Path)
    a = ap.parse_args(argv)

    if a.cmd == "build":
        outputs = build(_load_job(a.project), a.project / "out")
        findings = [f for o in outputs for f in o.findings]
        for o in outputs:
            print(f"== {o.nc}")
            for f in o.findings:
                print(f"  {f}")
        print(f"Einrichteblatt: {a.project / 'out' / 'SETUP.md'}")
    else:
        sx, sy, sz = (float(v) for v in a.stock.lower().split("x"))
        stock = Stock(sx, sy, sz, a.material)
        tool = load_tools()[a.tool]
        prog = gcode.parse(a.nc.read_text(encoding="utf-8", errors="replace"))
        findings = check(prog, load_machine(), stock, tool, tool.presets.get(a.material))
        for f in findings:
            print(f)
        if a.preview:
            heights, extent = sim.simulate(prog, stock, tool)
            sim.render(prog, stock, heights, extent, a.preview, a.nc.name)
            print(f"Vorschau: {a.preview}")
    return 1 if any(f.level == "FEHLER" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
