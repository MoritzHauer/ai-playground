"""Grbl post-processor: Toolpaths -> G-code text (ASCII only, mm, absolute)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .toolpath import Toolpath

if TYPE_CHECKING:
    from .job import Job


def _num(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def to_gcode(job: Job, toolpaths: list[Toolpath]) -> str:
    tool_ids = {tp.tool_id for tp in toolpaths}
    if len(tool_ids) != 1:
        raise ValueError("Eine G-Code-Datei pro Fraeser (Werkzeugwechsel ist manuell)")
    tool = job.tool(toolpaths[0].tool_id)
    st = job.stock
    lines = [
        f"(Job: {job.name})",
        f"(Material: {st.material}, {_num(st.size_x)} x {_num(st.size_y)} x {_num(st.thickness)} mm)",
        f"(Fraeser: {tool.id}, D={_num(tool.diameter)} mm)",
        f"(Spindel MANUELL einschalten: {toolpaths[0].rpm} U/min)",
        "(Nullpunkt: X0 Y0 = vordere linke Werkstueckecke, Z0 = Werkstueckoberseite)",
        "G21 G90 G17 G94",
        # the tool may still sit on Z0 after zeroing: lift straight up before any XY move
        f"G0 Z{_num(job.machine.safe_z)}",
    ]
    state: dict[str, float | None] = {"X": None, "Y": None, "Z": job.machine.safe_z, "F": None}
    for tp in toolpaths:
        lines.append(f"({tp.label})")
        for m in tp.moves:
            g = 0 if m.rapid else 1
            words = []
            for axis, v in (("X", m.x), ("Y", m.y), ("Z", m.z)):
                if state[axis] is None or abs(state[axis] - v) > 5e-4:
                    words.append(f"{axis}{_num(v)}")
                    state[axis] = v
            if not words:
                continue
            if g == 1 and state["F"] != m.feed:
                words.append(f"F{_num(m.feed)}")
                state["F"] = m.feed
            lines.append(f"G{g} " + " ".join(words))
    lines += ["G0 X0 Y0", "M2", ""]
    return "\n".join(lines)
