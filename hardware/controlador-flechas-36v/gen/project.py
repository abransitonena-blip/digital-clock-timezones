"""Escribe el archivo de proyecto KiCad 9 (.kicad_pro) con las reglas de diseño y las
clases de red, y el archivo de reglas personalizadas (.kicad_dru)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import design as DZ

HERE = os.path.dirname(os.path.abspath(__file__))
KIDIR = os.path.join(HERE, "..", "kicad")
TEMPLATE = "/usr/share/kicad/template/kicad.kicad_pro"


def main():
    pro = json.load(open(TEMPLATE))
    ds = pro.setdefault("board", {}).setdefault("design_settings", {})
    rules = ds.setdefault("rules", {})
    rules.update({
        "min_clearance": 0.6, "min_track_width": 0.8, "min_copper_edge_clearance": 0.5,
        "min_through_hole_diameter": 0.8, "min_hole_to_hole": 0.5, "min_hole_clearance": 0.25,
        "min_via_diameter": 0.8, "min_via_annular_width": 0.3, "min_connection": 0.0,
        "min_silk_clearance": 0.0, "min_text_height": 0.8, "min_text_thickness": 0.12,
        "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1, "max_error": 0.005,
        "min_resolved_spokes": 1, "solder_mask_to_copper_clearance": 0.0, "allow_blind_buried_vias": False,
        "allow_microvias": False})
    sev = ds.setdefault("rule_severities", {})
    # Las huellas THT no llevan cobre en F.Cu: el cobre superior no se usa (una sola cara).
    sev.update({"silk_over_copper": "ignore", "silk_overlap": "ignore", "silk_edge_clearance": "ignore",
                "lib_footprint_mismatch": "ignore", "lib_footprint_issues": "ignore",
                "text_height": "ignore", "text_thickness": "ignore"})
    ds["track_widths"] = [0.0, 0.8, 1.2, 1.5]
    ns = pro.setdefault("net_settings", {})
    base = {"bus_width": 12, "clearance": 0.6, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "name": "Default", "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647,
            "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": 0.8, "via_diameter": 1.6,
            "via_drill": 0.8, "wire_width": 6}
    pw = dict(base)
    pw.update({"name": "Potencia", "track_width": 1.2, "priority": 0})
    ns["classes"] = [base, pw]
    ns["meta"] = {"version": 4}
    ns["netclass_patterns"] = [{"netclass": "Potencia", "pattern": n} for n in sorted(DZ.POWER_NETS_W)]
    pro.setdefault("meta", {})["filename"] = "ControladorFlechas.kicad_pro"
    json.dump(pro, open(os.path.join(KIDIR, "ControladorFlechas.kicad_pro"), "w"), indent=2)
    dru = '''(version 1)
(rule "Pistas de potencia >= 1.2 mm"
  (condition "A.NetClass == 'Potencia'")
  (constraint track_width (min 1.2mm)))
(rule "Pistas de senal >= 0.8 mm"
  (condition "A.Type == 'track'")
  (constraint track_width (min 0.8mm)))
(rule "Separacion minima 0.6 mm"
  (constraint clearance (min 0.6mm)))
'''
    open(os.path.join(KIDIR, "ControladorFlechas.kicad_dru"), "w").write(dru)


if __name__ == "__main__":
    main()
