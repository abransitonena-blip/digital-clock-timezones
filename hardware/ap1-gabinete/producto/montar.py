import sys, uuid
src, dst, modelos = sys.argv[1], sys.argv[2], sys.argv[3:]
s = open(src).read().rstrip()
assert s.endswith(")")
fp = ""
for i, m in enumerate(modelos):
    fp += f'''  (footprint "AP:CARCASA{i}" (layer "F.Cu") (uuid "{uuid.uuid4()}") (at 0 0)
    (property "Reference" "CAJA{i}" (at 0 0 0) (layer "F.SilkS") (uuid "{uuid.uuid4()}") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
    (property "Value" "carcasa" (at 0 0 0) (layer "F.Fab") (uuid "{uuid.uuid4()}") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
    (attr board_only exclude_from_pos_files exclude_from_bom)
    (model "{m}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))
  )
'''
open(dst, "w").write(s[:-1] + fp + ")\n")
