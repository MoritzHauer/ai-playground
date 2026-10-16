"""A Job = stock + operations. `build()` runs the whole pipeline:
operations -> toolpaths -> G-code -> (re-parse) -> checks -> simulation -> setup sheet.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from shapely.geometry.base import BaseGeometry

from . import check as checks
from . import gcode, sim
from .config import Machine, Stock, Tool, load_machine, load_tools
from .post import to_gcode
from .report import setup_sheet, write_svg


@dataclass
class Job:
    name: str
    stock: Stock
    operations: list = field(default_factory=list)
    parts: list[BaseGeometry] = field(default_factory=list)  # exported as SVG
    notes: list[str] = field(default_factory=list)            # shown on the setup sheet
    machine: Machine = field(default_factory=load_machine)
    tools: dict[str, Tool] = field(default_factory=load_tools)

    def tool(self, tool_id: str) -> Tool:
        try:
            return self.tools[tool_id]
        except KeyError:
            raise KeyError(f"Unbekannter Fraeser '{tool_id}' (siehe config/tools.toml)") from None


@dataclass
class Output:
    nc: Path
    tool: Tool
    rpm: int
    findings: list[checks.Finding]
    minutes: float
    preview: Path


def build(job: Job, out_dir: Path) -> list[Output]:
    out_dir.mkdir(parents=True, exist_ok=True)
    toolpaths = [op.generate(job) for op in job.operations]

    # one file per tool, in operation order (tool change = new file, new Z zero)
    by_tool: dict[str, list] = {}
    for tp in toolpaths:
        by_tool.setdefault(tp.tool_id, []).append(tp)
    outputs = []
    for n, (tool_id, tps) in enumerate(by_tool.items(), 1):
        suffix = f"_{n}_{tool_id}" if len(by_tool) > 1 else ""
        nc = out_dir / f"{job.name}{suffix}.nc"
        nc.write_text(to_gcode(job, tps), encoding="ascii")

        tool = job.tool(tool_id)
        prog = gcode.parse(nc.read_text(encoding="ascii"))
        preset = tool.presets.get(job.stock.material)
        findings = checks.check(prog, job.machine, job.stock, tool, preset)
        heights, extent = sim.simulate(prog, job.stock, tool)
        preview = nc.with_suffix(".png")
        sim.render(prog, job.stock, heights, extent, preview, f"{job.name}{suffix} - {tool.id}")
        outputs.append(Output(nc, tool, tps[0].rpm, findings,
                              checks.estimate_minutes(prog, job.machine), preview))

    if job.parts:
        write_svg(job.parts, job.stock, out_dir / f"{job.name}.svg")
    (out_dir / "SETUP.md").write_text(setup_sheet(job, outputs), encoding="utf-8")
    return outputs
