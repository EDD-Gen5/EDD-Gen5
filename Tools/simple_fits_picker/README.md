Simple Fits Picker (Calculator)
====================================================================
Windows GUI (ISO 286 – friendly names)

What is this?
-------------
A tiny Tkinter desktop app that lets you:
- Pick a *fit by descriptive name* (e.g., Locational clearance, Sliding, Medium drive)
- Choose *shape*: Cylindrical (shaft in hole) or Rectangular/Square (plug in slot)
- Enter nominal *unfitted* dimensions
- Get the recommended *hole & shaft letters/IT grades* and the exact *min/max limits*,
  plus min/max clearance, ready to drive your CAD and drawings.

Standards & scope
-----------------
- Uses ISO 286 i‑unit approximation for IT5–IT10.
- Hole letters: H, JS.  Shaft letters: h, js, k, m, n, p, r, s, u.
- For Rectangular/Square, the same ISO 286 logic is applied per axis (width, height).

How to run
----------
You can either

- run the stand-alone .exe (compiled from the python code).

- run the python code, as follows:
1) Install Python 3 on Windows (on PATH).  Check: `python --version`.
2) Place these files together:
   - simple_fits_picker_gui.py
   - Run_Simple_Fits_Picker.bat
3) Double‑click `Run_Simple_Fits_Picker.bat` to launch.

Notes
-----
- Fundamental deviations for press/drive shaft letters are implemented from published ISO 286 tables
  (RoyMech summary). For critical tolerances, verify against official ISO 286-2 tables for your size band.

-code by ChatGPT5
