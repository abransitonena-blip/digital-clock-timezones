"""Optimización topológica 2D (SIMP, filtro de densidad) en numpy/scipy, a la manera del código de 88 líneas de Sigmund.

Se usa para el diseño generativo del soporte de riel DIN (generar.py). Es un modelo plano de elasticidad lineal con una sola carga: sirve para
repartir el material, NO sustituye un análisis por elementos finitos 3D ni una prueba de carga de la pieza impresa (la impresión FDM es anisótropa).
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve


def _ke(nu):
    k = np.array([1 / 2 - nu / 6, 1 / 8 + nu / 8, -1 / 4 - nu / 12, -1 / 8 + 3 * nu / 8,
                  -1 / 4 + nu / 12, -1 / 8 - nu / 8, nu / 6, 1 / 8 - 3 * nu / 8])
    return 1 / (1 - nu ** 2) * np.array([
        [k[0], k[1], k[2], k[3], k[4], k[5], k[6], k[7]], [k[1], k[0], k[7], k[6], k[5], k[4], k[3], k[2]],
        [k[2], k[7], k[0], k[5], k[6], k[3], k[4], k[1]], [k[3], k[6], k[5], k[0], k[7], k[2], k[1], k[4]],
        [k[4], k[5], k[6], k[7], k[0], k[1], k[2], k[3]], [k[5], k[4], k[3], k[2], k[1], k[0], k[7], k[6]],
        [k[6], k[3], k[4], k[1], k[2], k[7], k[0], k[5]], [k[7], k[2], k[1], k[4], k[3], k[6], k[5], k[0]]])


def optimizar(nx, ny, fraccion, rmin, fijos_x, cargas, solido=None, vacio=None, penal=3.0, iteraciones=120, E0=1.0, nu=0.35, callback=None):
    """nx x ny elementos (x derecha, y ARRIBA al imprimir; aquí la fila 0 es la de arriba).
    fijos_x: lista de (ix, iy, 'xy'|'x'|'y') nodos empotrados. cargas: lista de (ix, iy, fx, fy) en nodos (fy positivo = hacia arriba).
    solido / vacio: máscaras booleanas (ny, nx) de elementos que se quedan llenos o vacíos. Devuelve (densidad (ny, nx), historial de la flexibilidad)."""
    KE = _ke(nu)
    nodo = lambda ix, iy: iy + ix * (ny + 1)                       # numeración por columnas, como el código de referencia
    edof = np.zeros((nx * ny, 8), dtype=int)
    for ex in range(nx):
        for ey in range(ny):
            n1, n2 = nodo(ex, ey), nodo(ex + 1, ey)
            e = ex * ny + ey
            edof[e] = [2 * n1 + 2, 2 * n1 + 3, 2 * n2 + 2, 2 * n2 + 3, 2 * n2, 2 * n2 + 1, 2 * n1, 2 * n1 + 1]
    iK = np.kron(edof, np.ones((8, 1), dtype=int)).ravel(); jK = np.kron(edof, np.ones((1, 8), dtype=int)).ravel()
    ndof = 2 * (nx + 1) * (ny + 1)
    F = np.zeros(ndof)
    for ix, iy, fx, fy in cargas:
        F[2 * nodo(ix, iy)] += fx; F[2 * nodo(ix, iy) + 1] += fy
    fijos = []
    for ix, iy, tipo in fijos_x:
        if "x" in tipo: fijos.append(2 * nodo(ix, iy))
        if "y" in tipo: fijos.append(2 * nodo(ix, iy) + 1)
    fijos = np.array(sorted(set(fijos))); libres = np.setdiff1d(np.arange(ndof), fijos)
    # filtro de densidad
    R = int(np.ceil(rmin)); filas, cols, vals = [], [], []
    for i in range(nx):
        for j in range(ny):
            e1 = i * ny + j
            for k in range(max(i - R + 1, 0), min(i + R, nx)):
                for l in range(max(j - R + 1, 0), min(j + R, ny)):
                    w = max(0.0, rmin - np.hypot(i - k, j - l))
                    if w > 0: filas.append(e1); cols.append(k * ny + l); vals.append(w)
    H = coo_matrix((vals, (filas, cols)), shape=(nx * ny, nx * ny)).tocsr(); Hs = np.asarray(H.sum(axis=1)).ravel()
    x = np.full(nx * ny, fraccion)
    def en_vec(m):                                                   # máscara (ny, nx) -> vector por columnas
        return None if m is None else m.T.ravel()
    sol = en_vec(solido); vac = en_vec(vacio)
    if sol is not None: x[sol] = 1.0
    if vac is not None: x[vac] = 1e-3
    xf = x.copy(); hist = []
    Emin = 1e-9
    for it in range(iteraciones):
        xf = H @ x / Hs
        sK = ((KE.ravel()[None, :] * (Emin + xf[:, None] ** penal * (E0 - Emin))).ravel())
        K = coo_matrix((sK, (iK, jK)), shape=(ndof, ndof)).tocsc()
        U = np.zeros(ndof); U[libres] = spsolve(K[libres][:, libres], F[libres])
        ce = np.einsum("ij,jk,ik->i", U[edof], KE, U[edof])
        c = float(np.sum((Emin + xf ** penal * (E0 - Emin)) * ce)); hist.append(c)
        dc = -penal * xf ** (penal - 1) * (E0 - Emin) * ce
        dc = H.T @ (dc / Hs)
        l1, l2 = 0.0, 1e9                                            # criterio de optimalidad con bisección
        while (l2 - l1) / (l1 + l2 + 1e-12) > 1e-4:
            lm = 0.5 * (l1 + l2)
            xn = np.clip(x * np.sqrt(np.maximum(-dc, 1e-30) / lm), np.maximum(0.0, x - 0.2), np.minimum(1.0, x + 0.2))
            if sol is not None: xn[sol] = 1.0
            if vac is not None: xn[vac] = 1e-3
            if (H @ xn / Hs).mean() > fraccion: l1 = lm
            else: l2 = lm
        cambio = np.abs(xn - x).max(); x = xn
        if callback: callback(it, c, xf.mean())
        if cambio < 0.01 and it > 40: break
    xf = H @ x / Hs
    return xf.reshape(nx, ny).T, hist, float(np.max(np.abs(U)))
