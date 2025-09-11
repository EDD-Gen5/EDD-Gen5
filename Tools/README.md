# General Tools

## Available Tools  

This repository already includes general-purpose utilities:  

---

### CAD Assembly Matrix Generator  
Location: [`/cad_assembly_matrix_generator/`](cad_assembly_matrix_generator/)  

A Python tool that converts a FreeCAD assembly tree (exported as a `.txt` file)  
into a structured spreadsheet (`.xlsx` or `.ods`) showing direct children and rollup parts views.  

This script is not project-specific and may be useful to anyone working with FreeCAD assemblies.  
See the [tool’s README](cad_assembly_matrix_generator/README.md) for usage instructions.  

---

### CAD Simple Fits Calculator
Location: [`/simple_fits_picker/`](simple_fits_picker/)  

A tiny Tkinter desktop app that lets you:
- Pick a *fit by descriptive name* (e.g., Locational clearance, Sliding, Medium drive)
- Choose *shape*: Cylindrical (shaft in hole) or Rectangular/Square (plug in slot)
- Enter nominal *unfitted* dimensions
- Get the recommended *hole & shaft letters/IT grades* and the exact *min/max limits*,
  plus min/max clearance, ready to drive your CAD and drawings.

This tool is not project-specific and may be useful to anyone working with FreeCAD assemblies.  
See the [tool’s README](simple_fits_picker/README.md) for usage instructions.

---
