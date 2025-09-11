#!/usr/bin/env python3
# Simple Fits Picker GUI (ISO 286 – friendly names) — Windows / Tkinter
# Supports:
#   • Cylindrical (shaft in hole)
#   • Rectangular/Square (plug in slot)
# Letters supported:
#   Holes: H, JS
#   Shafts: h, js, k, m, n, p, r, s, u   (press/interference included)
# IT grades supported: 5–10 (common shop range)
# Shows friendly "Intent" and "Example" for the selected fit type.
# Author: ChatGPT (Atria)

import tkinter as tk
from tkinter import ttk, messagebox

# -------------------------- ISO 286 helpers --------------------------

def i_unit_um(D_mm: float) -> float:
    """ISO 286-1 standard tolerance unit (i) in micrometres for size D in mm."""
    # i = 0.45 * D^(1/3) + 0.001 * D
    return 0.45 * (D_mm ** (1.0/3.0)) + 0.001 * D_mm

IT_COEFF = {5: 7, 6: 10, 7: 16, 8: 25, 9: 40, 10: 64}

def tol_mm_from_IT(IT_grade: int, D_mm: float) -> float:
    """Return tolerance (mm) for given IT grade at size D using i-unit approximation."""
    coeff = IT_COEFF.get(int(IT_grade))
    if coeff is None:
        raise ValueError(f"Unsupported IT grade: {IT_grade}")
    return (coeff * i_unit_um(D_mm)) / 1000.0  # → mm

# Fundamental deviation (nearest zero) for shaft letters k..u (hole-basis) in µm.
# Source: RoyMech (ISO Shaft Limit Nearest Zero 0–500 mm) — k..zc table.
# We include k, m, n, p, r, s, u (common press/drive fits).
# Each row: (over_mm, up_to_incl_mm, {"k":ei, "m":ei, ...})   values in µm.
SHAFT_FUND_DEV_EI_UM = [
    (0, 3,  {"k":0, "m":2,  "n":4,  "p":6,  "r":10, "s":14, "u":18}),
    (3, 6,  {"k":1, "m":4,  "n":8,  "p":12, "r":15, "s":19, "u":23}),
    (6, 10, {"k":1, "m":6,  "n":10, "p":15, "r":19, "s":23, "u":28}),
    (10,14, {"k":1, "m":7,  "n":12, "p":18, "r":23, "s":28, "u":33}),
    (14,18, {"k":1, "m":7,  "n":12, "p":18, "r":23, "s":28, "u":33}),
    (18,24, {"k":2, "m":8,  "n":15, "p":22, "r":28, "s":35, "u":41}),
    (24,30, {"k":2, "m":8,  "n":15, "p":22, "r":28, "s":35, "u":41}),
    (30,40, {"k":2, "m":9,  "n":17, "p":26, "r":34, "s":43, "u":60}),  # u=60 per RoyMech
    (40,50, {"k":2, "m":9,  "n":17, "p":26, "r":34, "s":43, "u":70}),
    (50,65, {"k":2, "m":11, "n":20, "p":32, "r":41, "s":53, "u":87}),
    (65,80, {"k":2, "m":11, "n":20, "p":32, "r":43, "s":59, "u":102}),
    (80,100,{"k":3, "m":13, "n":23, "p":37, "r":51, "s":71, "u":124}),
    (100,120,{"k":3,"m":13, "n":23, "p":37, "r":54, "s":79, "u":144}),
    (120,140,{"k":3,"m":15, "n":27, "p":43, "r":63, "s":92, "u":170}),
    (140,160,{"k":3,"m":15, "n":27, "p":43, "r":65, "s":100,"u":190}),
    (160,180,{"k":3,"m":15, "n":27, "p":43, "r":68, "s":108,"u":210}),
    (180,200,{"k":4,"m":17, "n":31, "p":50, "r":77, "s":122,"u":236}),
    (200,225,{"k":4,"m":17, "n":31, "p":50, "r":80, "s":130,"u":258}),
    (225,250,{"k":4,"m":17, "n":31, "p":50, "r":84, "s":140,"u":284}),
    (250,280,{"k":4,"m":20, "n":34, "p":56, "r":94, "s":158,"u":315}),
    (280,315,{"k":4,"m":20, "n":34, "p":56, "r":98, "s":170,"u":350}),
    (315,355,{"k":4,"m":21, "n":37, "p":62, "r":108,"s":190,"u":390}),
    (355,400,{"k":4,"m":21, "n":37, "p":62, "r":114,"s":208,"u":435}),
    (400,450,{"k":5,"m":23, "n":40, "p":68, "r":126,"s":232,"u":490}),
    (450,500,{"k":5,"m":23, "n":40, "p":68, "r":132,"s":252,"u":540}),
]

def shaft_ei_um(letter: str, D_mm: float) -> float:
    """Return fundamental deviation ei (µm) for shaft letter among {h, js, k, m, n, p, r, s, u} at size D."""
    letter = letter.lower()
    if letter in ("h", "js"):
        # These are handled analytically later (0 / symmetric), no table needed
        return 0.0
    for over, upto, row in SHAFT_FUND_DEV_EI_UM:
        if D_mm > over and D_mm <= upto:
            if letter in row:
                return row[letter]
            break
    raise ValueError(f"No fundamental deviation data for letter '{letter}' at size {D_mm} mm")

# -------------------------- Fit presets (friendly) --------------------------
# name, (hole_letter, hole_IT, shaft_letter, shaft_IT, intent, example)
FRIENDLY_MAP = [
    ("Loose running (easy assembly)", ("H", 9,  "h", 9,
        "Large clearance for dirty/rough service",
        "Jigs, coarse guides")),
    ("Free running", ("H", 9,  "h", 8,
        "Reliable motion with generous clearance",
        "Basic bearings, pulleys")),
    ("Close running", ("H", 8,  "h", 7,
        "Reduced play without risk of binding",
        "Better guides, sleeves")),
    ("Sliding (low play)", ("H", 7,  "js", 6,
        "Smooth sliding with near-zero mean clearance",
        "Precision sliders")),
    ("Locational clearance (snug)", ("H", 7,  "h", 6,
        "Accurate location; easy assembly",
        "Dowel-like location without press")),
    ("Locational transition (near 0)", ("JS", 7, "js", 5,
        "May end up slightly tight or slightly loose",
        "Pins, collars")),
    ("Very tight clearance", ("H", 6,  "h", 6,
        "Minimal clearance; needs good alignment/lube",
        "Lightly loaded fits")),
    ("General clearance", ("H", 7,  "h", 7,
        "Balanced ease and guidance",
        "General purpose")),
    ("Precision sliding", ("H", 6,  "js", 5,
        "High accuracy sliding, near-zero play",
        "Metrology fixtures")),

    # Press / interference fits (hole-basis) — from RoyMech examples
    ("Locational slight interference", ("H", 7, "k", 6,
        "Location with light interference; assembly possible with mild force/thermal assist",
        "H7/k6")),
    ("Transition (near interference)", ("H", 7, "n", 6,
        "Between clearance and interference; depends on actual sizes",
        "H7/n6")),
    ("Interference (separable press)", ("H", 7, "p", 6,
        "Press fit with noticeable holding; can often be separated",
        "H7/p6")),
    ("Medium drive", ("H", 7, "s", 6,
        "Strong drive fit; for permanent or semi-permanent assemblies",
        "H7/s6")),
    ("Force / shrink", ("H", 7, "u", 6,
        "Heavy interference for permanent fits; typically needs thermal assembly",
        "H7/u6")),
]

SHAPES = ["Cylindrical (shaft in hole)", "Rectangular/Square (plug in slot)"]

# -------------------------- Utility --------------------------

def fmt(v, places=3):
    return f"{v:.{places}f}"

def parse_pos_float(s: str, fieldname: str) -> float:
    s = (s or "").strip().replace(",", ".")
    val = float(s)
    if not (val > 0.0):
        raise ValueError(f"{fieldname} must be > 0")
    return val

# -------------------------- Core calculations --------------------------

def hole_limits(letter: str, IT: int, D: float):
    T = tol_mm_from_IT(IT, D)
    L = letter.upper()
    if L == "H":
        ei, es = 0.0, T                 # EI=0, ES=+T
    elif L == "JS":
        ei, es = -T/2.0, +T/2.0         # symmetric about zero
    else:
        raise ValueError(f"Unsupported hole letter: {letter}")
    return (D + ei, D + es, T)          # (lower, upper, total T)

def shaft_limits(letter: str, IT: int, D: float):
    T = tol_mm_from_IT(IT, D)
    l = letter.lower()
    if l == "h":
        ei, es = -T, 0.0                # zone below zero
    elif l == "js":
        ei, es = -T/2.0, +T/2.0         # symmetric
    elif l in ("k","m","n","p","r","s","u"):
        ei_um = shaft_ei_um(l, D)       # nearest-zero deviation in µm
        ei = ei_um / 1000.0             # → mm
        es = ei + T                     # zone above zero
    else:
        raise ValueError(f"Unsupported shaft letter: {letter}")
    return (D + ei, D + es, T)          # (lower, upper, total T)

def compute_axis(D: float, hole_letter: str, hole_IT: int, shaft_letter: str, shaft_IT: int):
    h_lo, h_hi, Th = hole_limits(hole_letter, hole_IT, D)
    s_lo, s_hi, Ts = shaft_limits(shaft_letter, shaft_IT, D)
    min_clear = h_lo - s_hi
    max_clear = h_hi - s_lo
    return {
        "D": D,
        "hole_lo": h_lo, "hole_hi": h_hi, "hole_T": Th,
        "shaft_lo": s_lo, "shaft_hi": s_hi, "shaft_T": Ts,
        "min_clear": min_clear, "max_clear": max_clear,
    }

# -------------------------- GUI --------------------------

class FitsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simple Fits Picker")
        self.resizable(False, False)

        # State vars
        self.shape_var = tk.StringVar(value=SHAPES[0])
        self.fit_var = tk.StringVar(value=FRIENDLY_MAP[4][0])  # Locational clearance (snug)
        self.diam_var = tk.StringVar(value="34.0")
        self.w_var = tk.StringVar(value="34.0")
        self.h_var = tk.StringVar(value="34.0")

        self._build_ui()
        self._on_shape_change()
        self._on_fit_change()

    def _build_ui(self):
        pad = 8
        frm = ttk.Frame(self, padding=pad)
        frm.grid(row=0, column=0, sticky="nsew")

        # Shape
        ttk.Label(frm, text="Shape:").grid(row=0, column=0, sticky="w")
        self.shape_cb = ttk.Combobox(frm, textvariable=self.shape_var, values=SHAPES, state="readonly", width=35)
        self.shape_cb.grid(row=0, column=1, sticky="w", padx=(0, pad))
        self.shape_cb.bind("<<ComboboxSelected>>", lambda e: self._on_shape_change())

        # Fit type
        ttk.Label(frm, text="Fit type:").grid(row=1, column=0, sticky="w")
        fit_names = [x[0] for x in FRIENDLY_MAP]
        self.fit_cb = ttk.Combobox(frm, textvariable=self.fit_var, values=fit_names, state="readonly", width=35)
        self.fit_cb.grid(row=1, column=1, sticky="w", padx=(0, pad))
        self.fit_cb.bind("<<ComboboxSelected>>", lambda e: self._on_fit_change())

        # Intent / Example
        self.intent_lbl = ttk.Label(frm, text="Intent:", font=("", 9, "bold"))
        self.intent_lbl.grid(row=2, column=0, sticky="ne", pady=(4,0))
        self.intent_val = ttk.Label(frm, text="—", wraplength=420, justify="left")
        self.intent_val.grid(row=2, column=1, sticky="w", pady=(4,0))

        self.example_lbl = ttk.Label(frm, text="Example:", font=("", 9, "bold"))
        self.example_lbl.grid(row=3, column=0, sticky="ne")
        self.example_val = ttk.Label(frm, text="—", wraplength=420, justify="left")
        self.example_val.grid(row=3, column=1, sticky="w")

        # Size inputs (dynamic)
        self.diam_row = ttk.Frame(frm)
        ttk.Label(self.diam_row, text="Diameter (mm):").grid(row=0, column=0, sticky="w")
        self.diam_entry = ttk.Entry(self.diam_row, textvariable=self.diam_var, width=12)
        self.diam_entry.grid(row=0, column=1, sticky="w")
        self.diam_row.grid(row=4, column=0, columnspan=2, sticky="w", pady=(6,0))

        self.rect_row = ttk.Frame(frm)
        ttk.Label(self.rect_row, text="Width (mm):").grid(row=0, column=0, sticky="w")
        self.w_entry = ttk.Entry(self.rect_row, textvariable=self.w_var, width=12)
        self.w_entry.grid(row=0, column=1, sticky="w", padx=(0, 16))
        ttk.Label(self.rect_row, text="Height (mm):").grid(row=0, column=2, sticky="w")
        self.h_entry = ttk.Entry(self.rect_row, textvariable=self.h_var, width=12)
        self.h_entry.grid(row=0, column=3, sticky="w")

        # Compute button
        self.compute_btn = ttk.Button(frm, text="Compute", command=self._compute)
        self.compute_btn.grid(row=6, column=0, columnspan=2, sticky="we", pady=(6, 6))

        sep = ttk.Separator(frm, orient="horizontal")
        sep.grid(row=7, column=0, columnspan=2, sticky="we", pady=(4,8))

        # Output
        self.callout_lbl = ttk.Label(frm, text="Recommended drawing callout:", font=("", 10, "bold"))
        self.callout_lbl.grid(row=8, column=0, columnspan=2, sticky="w")
        self.callout_val = ttk.Label(frm, text="—")
        self.callout_val.grid(row=9, column=0, columnspan=2, sticky="w")

        self.letters_lbl = ttk.Label(frm, text="Hole / Shaft:", font=("", 10, "bold"))
        self.letters_lbl.grid(row=10, column=0, columnspan=2, sticky="w")
        self.letters_val = ttk.Label(frm, text="—")
        self.letters_val.grid(row=11, column=0, columnspan=2, sticky="w")

        self.results = ttk.Frame(frm)
        self.results.grid(row=12, column=0, columnspan=2, sticky="we", pady=(6,0))
        self.res_text = tk.Text(self.results, width=64, height=12, wrap="word")
        self.res_text.grid(row=0, column=0, sticky="nsew")
        self.res_text.configure(state="disabled")

    def _on_shape_change(self):
        shape = self.shape_var.get()
        if shape.startswith("Cylindrical"):
            self.rect_row.grid_remove()
            self.diam_row.grid()
        else:
            self.diam_row.grid_remove()
            self.rect_row.grid()
        # Do not compute here to avoid transient empty-entry errors

    def _get_fit_record(self):
        name = self.fit_var.get()
        for friendly, params in FRIENDLY_MAP:
            if friendly == name:
                (hole_letter, hole_IT, shaft_letter, shaft_IT, intent, example) = params
                return friendly, hole_letter, hole_IT, shaft_letter, shaft_IT, intent, example
        # Fallback
        return ("Locational clearance (snug)", "H", 7, "h", 6,
                "Accurate location; easy assembly", "Dowel-like location without press")

    def _on_fit_change(self):
        friendly, hole_letter, hole_IT, shaft_letter, shaft_IT, intent, example = self._get_fit_record()
        self.intent_val.configure(text=intent)
        self.example_val.configure(text=example)
        # Do not compute here to avoid transient empty-entry errors

    def _compute(self):
        try:
            friendly, hole_letter, hole_IT, shaft_letter, shaft_IT, intent, example = self._get_fit_record()
            shape = self.shape_var.get()

            if shape.startswith("Cylindrical"):
                D = parse_pos_float(self.diam_var.get(), "Diameter")
                res = compute_axis(D, hole_letter, hole_IT, shaft_letter, shaft_IT)
                callout = f"⌀{fmt(D)} {hole_letter}{hole_IT}/{shaft_letter}{shaft_IT}"
                letters = f"Hole: {hole_letter}{hole_IT}   Shaft: {shaft_letter}{shaft_IT}"
                self._show_results(callout, letters, res, shape="cyl")

            else:
                W = parse_pos_float(self.w_var.get(), "Width")
                H = parse_pos_float(self.h_var.get(), "Height")
                resW = compute_axis(W, hole_letter, hole_IT, shaft_letter, shaft_IT)
                resH = compute_axis(H, hole_letter, hole_IT, shaft_letter, shaft_IT)
                callout = f"Rectangular plug — Width: {fmt(W)} {hole_letter}{hole_IT}/{shaft_letter}{shaft_IT},  Height: {fmt(H)} {hole_letter}{hole_IT}/{shaft_letter}{shaft_IT}"
                letters = f"Hole: {hole_letter}{hole_IT}   Shaft: {shaft_letter}{shaft_IT}  (applied on both axes)"
                self._show_results(callout, letters, (resW, resH), shape="rect")

        except ValueError as ex:
            messagebox.showerror("Input error", str(ex))
        except Exception:
            messagebox.showerror("Input error", "Please enter valid positive numbers for dimensions.")

    def _show_results(self, callout, letters, res, shape="cyl"):
        self.callout_val.configure(text=callout)
        self.letters_val.configure(text=letters)

        self.res_text.configure(state="normal")
        self.res_text.delete("1.0", "end")

        if shape == "cyl":
            R = res
            body = []
            body.append("CYLINDRICAL FIT (shaft in hole)")
            body.append(f"Nominal D = {fmt(R['D'])} mm")
            body.append(f"Hole limits:  {fmt(R['hole_lo'])}  to  {fmt(R['hole_hi'])}  mm")
            body.append(f"Shaft limits: {fmt(R['shaft_lo'])}  to  {fmt(R['shaft_hi'])}  mm")
            body.append(f"Clearance:    min {fmt(R['min_clear'])}   max {fmt(R['max_clear'])}  mm")
            body.append("")
            body.append(f"Tolerances:   Hole {fmt(R['hole_T'],6)} mm,  Shaft {fmt(R['shaft_T'],6)} mm")
            self.res_text.insert("1.0", "\n".join(body))

        else:
            RW, RH = res
            body = []
            body.append("RECTANGULAR/SQUARE FIT (plug in slot)")
            body.append(f"Nominal W × H = {fmt(RW['D'])} × {fmt(RH['D'])} mm")
            body.append("Width axis:")
            body.append(f"  Hole limits:  {fmt(RW['hole_lo'])}  to  {fmt(RW['hole_hi'])}  mm")
            body.append(f"  Shaft limits: {fmt(RW['shaft_lo'])}  to  {fmt(RW['shaft_hi'])}  mm")
            body.append(f"  Clearance:    min {fmt(RW['min_clear'])}   max {fmt(RW['max_clear'])}  mm")
            body.append("Height axis:")
            body.append(f"  Hole limits:  {fmt(RH['hole_lo'])}  to  {fmt(RH['hole_hi'])}  mm")
            body.append(f"  Shaft limits: {fmt(RH['shaft_lo'])}  to  {fmt(RH['shaft_hi'])}  mm")
            body.append(f"  Clearance:    min {fmt(RH['min_clear'])}   max {fmt(RH['max_clear'])}  mm")
            body.append("")
            body.append(f"Tolerances per axis:   Hole {fmt(RW['hole_T'],6)} mm,  Shaft {fmt(RW['shaft_T'],6)} mm")
            self.res_text.insert("1.0", "\n".join(body))

        self.res_text.configure(state="disabled")


if __name__ == "__main__":
    app = FitsApp()
    app.mainloop()
