"""Huellas (footprints) en mm. Cada pad: (pin, dx, dy, w, h, forma, taladro). forma: 'r' rect, 'c' círculo, 'o' óvalo.
Taladro None => SMD capa superior. Origen = centro del componente, +y hacia arriba (vista superior)."""

def _dos(px, w, h):            # pasivo de 2 terminales a lo largo de x
    return [("1", -px, 0, w, h, "r", None), ("2", px, 0, w, h, "r", None)]

def huella(tipo):
    if tipo == "0603": return _dos(0.8, 0.9, 1.0), (3.0, 1.6)
    if tipo == "0805": return _dos(1.0, 1.1, 1.4), (3.4, 1.9)
    if tipo == "1206": return _dos(1.55, 1.2, 1.8), (4.4, 2.3)
    if tipo == "1210": return _dos(1.55, 1.2, 2.7), (4.4, 3.2)
    if tipo == "2512": return _dos(2.9, 1.8, 3.4), (8.0, 3.9)
    if tipo == "2410": return _dos(2.6, 1.6, 2.8), (7.0, 3.3)
    if tipo == "SOD123": return _dos(1.65, 0.9, 1.2), (4.4, 1.9)      # 1 = cátodo
    if tipo == "SMA": return _dos(2.0, 1.5, 1.7), (5.6, 2.6)
    if tipo == "SMB": return _dos(2.15, 2.0, 2.3), (6.6, 3.9)
    if tipo == "SMC": return _dos(3.4, 2.5, 3.3), (9.0, 6.4)
    if tipo == "SOT23":                                                  # 1,2 abajo; 3 arriba
        return [("1", -0.95, -1.05, 0.6, 1.0, "r", None), ("2", 0.95, -1.05, 0.6, 1.0, "r", None),
                ("3", 0, 1.05, 0.6, 1.0, "r", None)], (3.4, 3.4)
    if tipo == "SOT23-5":
        return [("1", -0.95, -1.1, 0.6, 1.0, "r", None), ("2", 0, -1.1, 0.6, 1.0, "r", None),
                ("3", 0.95, -1.1, 0.6, 1.0, "r", None), ("4", 0.95, 1.1, 0.6, 1.0, "r", None),
                ("5", -0.95, 1.1, 0.6, 1.0, "r", None)], (3.4, 3.6)
    if tipo == "SOT23-6":
        return [(str(i + 1), x, -1.1, 0.6, 1.0, "r", None) for i, x in enumerate((-0.95, 0, 0.95))] + \
               [(str(i + 4), x, 1.1, 0.6, 1.0, "r", None) for i, x in enumerate((0.95, 0, -0.95))], (3.4, 3.6)
    if tipo in ("SOIC8", "HSOP8"):
        p = [(str(i + 1), -1.905 + 1.27 * i, -2.7, 0.6, 1.55, "r", None) for i in range(4)] + \
            [(str(i + 5), 1.905 - 1.27 * i, 2.7, 0.6, 1.55, "r", None) for i in range(4)]
        if tipo == "HSOP8": p.append(("9", 0, 0, 3.1, 2.4, "r", None))   # PowerPAD = GND
        return p, (5.6, 7.0)
    if tipo == "VSSOP10":
        return [(str(i + 1), -1.0 + 0.5 * i, -2.2, 0.3, 1.45, "r", None) for i in range(5)] + \
               [(str(i + 6), 1.0 - 0.5 * i, 2.2, 0.3, 1.45, "r", None) for i in range(5)], (3.8, 5.6)
    if tipo == "DFN3x3":                                                 # 1-3 S, 4 G, D = pad grande
        return [(str(i + 1), -0.975 + 0.65 * i, -1.35, 0.4, 0.75, "r", None) for i in range(4)] + \
               [("D", 0, 0.45, 2.45, 2.25, "r", None)], (3.8, 3.8)
    if tipo == "SO8-PMOS": return huella("SOIC8")
    if tipo == "ELEC6": return _dos(2.5, 2.6, 1.6), (8.2, 7.0)            # 1 = +
    if tipo == "ELEC8": return _dos(3.2, 3.0, 1.8), (9.8, 8.6)            # 1 = +
    if tipo == "IND1265": return _dos(4.9, 3.6, 5.2), (13.4, 13.4)
    if tipo == "IND4020": return _dos(1.5, 1.3, 3.6), (4.8, 4.8)
    if tipo == "TACT6": return [("1", -3.975, 2.25, 1.55, 1.0, "r", None), ("x1", 3.975, 2.25, 1.55, 1.0, "r", None),
                               ("x2", -3.975, -2.25, 1.55, 1.0, "r", None), ("2", 3.975, -2.25, 1.55, 1.0, "r", None)], (9.6, 6.6)
    if tipo == "TP": return [("1", 0, 0, 1.6, 1.6, "c", None)], (2.0, 2.0)
    if tipo.startswith("BORNE35_"):                                      # bornera 3.5 mm
        n = int(tipo[8:])
        return [(str(i + 1), 0, (n - 1) * 1.75 - 3.5 * i, 2.0, 2.0, "r" if i == 0 else "c", 1.1) for i in range(n)], (7.0, 3.5 * n + 0.6)
    if tipo.startswith("BORNE"):                                         # bornera enchufable 5.08 mm, pines en y
        n = int(tipo[5:])
        return [(str(i + 1), 0, (n - 1) * 2.54 - 5.08 * i, 2.6 if i else 2.6, 2.6, "r" if i == 0 else "c", 1.4)
                for i in range(n)], (8.0, 5.08 * n + 0.6)
    if tipo.startswith("HDR1x"):                                         # tira hembra 2.54 en y
        n = int(tipo[5:])
        return [(str(i + 1), 0, (n - 1) * 1.27 - 2.54 * i, 1.7, 1.7, "r" if i == 0 else "c", 1.0) for i in range(n)], (2.6, 2.54 * n + 0.2)
    if tipo == "SUPERMINI":                                              # ESP32-C3 SuperMini, USB hacia +y
        izq = ["5V", "GND", "3V3", "IO4", "IO3", "IO2", "IO1", "IO0"]
        der = ["IO5", "IO6", "IO7", "IO8", "IO9", "IO10", "IO20", "IO21"]
        p = [(n, -7.62, 8.89 - 2.54 * i, 1.7, 1.7, "r" if i == 0 else "c", 1.0) for i, n in enumerate(izq)]
        p += [(n, 7.62, 8.89 - 2.54 * i, 1.7, 1.7, "c", 1.0) for i, n in enumerate(der)]
        return p, (18.4, 23.0)
    raise ValueError(tipo)
