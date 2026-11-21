"""Tabla de capacitor X2 y zener de 5 W por salida (127 V / 60 Hz, LED de 5 mm)."""
import math
CAPS = [0.1, 0.15, 0.22, 0.27, 0.33, 0.39, 0.47, 0.56, 0.68, 0.82, 1.0]
Z = [(12,"1N5349B"),(15,"1N5352B"),(18,"1N5355B"),(20,"1N5357B"),(22,"1N5358B"),(24,"1N5359B"),(27,"1N5361B"),
     (30,"1N5363B"),(36,"1N5365B"),(39,"1N5366B"),(43,"1N5367B"),(47,"1N5368B"),(51,"1N5369B"),(56,"1N5370B"),
     (62,"1N5372B"),(68,"1N5373B"),(75,"1N5374B"),(82,"1N5375B"),(91,"1N5377B"),(100,"1N5378B"),(110,"1N5379B"),
     (120,"1N5380B"),(130,"1N5381B"),(150,"1N5383B")]
EXTRA = 2.0 + 1.8      # LED testigo + caída en RO (100 Ω × 18 mA)
def I(C, vac, vo): return max(0, 240*C*1e-6*(vac*math.sqrt(2)-1.4-vo))*1000
def code(u):
    pf = round(u*1e6); e = 0
    while pf >= 100: pf /= 10; e += 1
    return f"{round(pf)}{e}J"
def fila(n, vf, vfmax):
    vo = n*vf + EXTRA
    c = [x for x in CAPS if I(x, 139.7, vo) <= 21.5][-1]
    z = next(z for z in Z if z[0] >= 1.15*(n*vfmax + 2.2 + 2.0))
    p_open = z[0]*I(c, 139.7, z[0])/1000
    return code(c), round(I(c, 127, vo), 1), f"{z[1]} ({z[0]} V)", round(p_open, 2)
if __name__ == "__main__":
    for name, vf, vfm in [("blanco/azul/verde", 3.1, 3.4), ("rojo/amarillo", 2.0, 2.3)]:
        print(name)
        for n in [1, 3, 5, 8, 10, 15, 20, 25, 30]:
            print(" ", n, *fila(n, vf, vfm))
