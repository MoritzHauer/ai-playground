"""CNC-as-code toolkit for the FLKA Shapeoko: design -> toolpath -> G-code -> check -> simulate."""
from .config import Stock
from . import gcode, sim
from .job import Job, build

__all__ = ["Job", "Stock", "build", "gcode", "sim"]
