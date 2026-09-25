"""Parser/serializador mínimo de expresiones S de KiCad."""
import re

class Sym(str):
    """Átomo sin comillas (palabra clave o número)."""

_tok = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))', re.S)

def parse(text):
    stack = [[]]
    pos = 0
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError("error de sintaxis en %d" % pos)
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            item = stack.pop()
            stack[-1].append(item)
        elif m.group(3):
            s = m.group(3)[1:-1]
            s = s.replace('\\"', '"').replace('\\\\', '\\')
            stack[-1].append(s)
        else:
            stack[-1].append(Sym(m.group(4)))
    return stack[0][0] if len(stack[0]) == 1 else stack[0]

def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

def dump(e, ind=0):
    if isinstance(e, list):
        if not e:
            return "()"
        simple = all(not isinstance(x, list) for x in e)
        if simple and len(e) < 12:
            return "(" + " ".join(dump(x) for x in e) + ")"
        out = "(" + dump(e[0])
        for x in e[1:]:
            if isinstance(x, list):
                out += "\n" + "\t" * (ind + 1) + dump(x, ind + 1)
            else:
                out += " " + dump(x)
        return out + "\n" + "\t" * ind + ")"
    if isinstance(e, Sym):
        return str(e)
    if isinstance(e, bool):
        return "yes" if e else "no"
    if isinstance(e, (int, float)):
        return fmt(e)
    return q(e)

def fmt(v):
    if isinstance(v, int):
        return str(v)
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

def find(e, key):
    return [x for x in e if isinstance(x, list) and x and x[0] == key]

def find1(e, key):
    r = find(e, key)
    return r[0] if r else None
