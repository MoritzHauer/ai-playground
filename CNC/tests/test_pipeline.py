import importlib.util
from pathlib import Path

import numpy as np
import pytest

from cnc import Stock, build, gcode, sim
from cnc.check import check
from cnc.config import load_machine, load_tools
from cnc.shapes import heart

ROOT = Path(__file__).resolve().parent.parent
MACHINE = load_machine()
TOOLS = load_tools()
STOCK = Stock(100, 100, 6)
HEADER = "G21 G90\nG0 Z5\n"


def levels(code: str, **kw) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"FEHLER": [], "WARNUNG": [], "INFO": []}
    tool = TOOLS["flat-4mm-2f"]
    for f in check(gcode.parse(code), MACHINE, kw.get("stock", STOCK), tool, tool.presets["holz"]):
        out[f.level].append(f.text)
    return out


def herz_job():
    spec = importlib.util.spec_from_file_location("herz", ROOT / "projects/herz/job.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.job()


def test_heart_size():
    minx, miny, maxx, maxy = heart(75).bounds
    assert (minx, miny) == pytest.approx((0, 0))
    assert maxx - minx == pytest.approx(75)
    assert 60 < maxy - miny < 75


def test_herz_builds_clean(tmp_path):
    [out] = build(herz_job(), tmp_path)
    assert not [f for f in out.findings if f.level == "FEHLER"]
    prog = gcode.parse(out.nc.read_text())
    assert prog.points()[:, 2].min() == pytest.approx(-6.3)
    assert (tmp_path / "SETUP.md").exists() and (tmp_path / "herz.svg").exists()


def test_herz_has_tabs_and_cuts_through(tmp_path):
    job = herz_job()
    [out] = build(job, tmp_path)
    h, _ = sim.simulate(gcode.parse(out.nc.read_text()), job.stock, out.tool)
    tab_top = -job.stock.thickness + 1.5
    assert np.isclose(h, tab_top, atol=0.05).sum() > 500   # bridges remain
    assert (h < -job.stock.thickness).sum() > 5000         # rest is cut through


def test_first_move_lifts_z_before_xy(tmp_path):
    [out] = build(herz_job(), tmp_path)
    seg = gcode.parse(out.nc.read_text()).segments[0]
    assert seg.rapid and seg.start[:2] == seg.end[:2] and seg.end[2] > 0


@pytest.mark.parametrize("code, expected", [
    (HEADER + "G1 X10 Y10 F500\nG1 Z-7.5\nG0 Z5\n", "Opferplatte"),
    (HEADER + "G0 X10 Y10\nG0 Z-1\n", "Eilgang"),
    (HEADER + "G1 Z-1 F500\nG0 X20\n", "Eilgang"),
    ("G90\nG0 Z5\nG1 X10 F500\n", "G21"),
    (HEADER + "G1 X10 Y10 Z-1 F5000\nG0 Z5\n", "Maschinengrenze"),
    (HEADER + "G0 X150 Y10\nG1 Z-1 F500\nG0 Z5\n", "verlaesst das Werkstueck"),
    (HEADER + "G1 X10 Z-13 F500\nG0 Z5\n", "Schneidenlaenge"),
])
def test_checker_catches(code, expected):
    stock = Stock(100, 100, 20) if "Schneidenlaenge" == expected else STOCK
    assert any(expected in t for t in levels(code, stock=stock)["FEHLER"]), levels(code, stock=stock)


def test_vertical_retract_is_ok():
    assert not levels(HEADER + "G0 X10 Y10\nG1 Z-1 F300\nG1 X20 F500\nG0 Z5\n")["FEHLER"]


def test_arc_parsing():
    prog = gcode.parse("G21 G90\nG0 X10 Y0\nG3 X0 Y10 I-10 J0 F500\n")
    pts = prog.points()
    assert pts[-1][:2] == pytest.approx((0, 10))
    assert np.hypot(pts[1:, 0], pts[1:, 1]) == pytest.approx(10, abs=1e-6)
