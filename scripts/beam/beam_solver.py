
"""Beta"""
import math
import numpy as np
import array as arr

def beta(fc):
    Beta_Calc = 0.85 - 0.05 * (fc - 27.579) / 6.895
    if Beta_Calc > 0.85:
        beta = 0.85
    else:
        beta = Beta_Calc
    return beta

"""Beam Effective Depth"""
def depth(h, cc, dties, dbar):
    return h - cc - dties - dbar / 2

"""Rebar Area"""
def dbararea(dbar):
    return 0.25*dbar**2*math.pi

"""Concrete Strength"""
def fcon(fc, bw, cna):
    return -0.85*fc*bw*cna*beta(fc) / 1000

"""Steel Strength"""
def fs(fc, fy, ast, di, ci):
    esteel = 200000
    ec = 0.003
    ey = fy / esteel
    estrain = ec * (di-ci) / ci
    ai = beta(fc)*ci

    if estrain >= 0 and estrain >= ey:
        fs = ast * fy / 1000 # Steel yield
    elif 0 <= estrain < ey:
        fs = ast * esteel * estrain / 1000 # Steel will not yield
    elif estrain < 0 and estrain < -ey and ai >= di:
        fs = ast * (-fy + 0.85 * fc) / 1000 # Steel yields in compression
    elif estrain < 0 and estrain < -ey and ai < di:
        fs = ast * (-fy) / 1000
    elif 0 > estrain > -ey and ai >= di:
        fs = ast * (esteel * estrain + 0.85 * fc) / 1000
    elif 0 > estrain > -ey and ai < di:
        fs = ast * (esteel * estrain) / 1000
    return fs

"""Steel - Bending"""
def mnsteel(fsi, di):
    return fsi * di / 1000

"""Concrete - Bending"""
def mncon(fcon,ai):
    return fcon * ai / 2 / 1000

"""Rebar Spacing"""
def rebarsp(db, d_aggregate):
    return max(db, 25, 4 * d_aggregate / 3)

"""Maximum number of reinforcement per layer"""
def nlayers(bw, cc, dties, db, sp):
    return math.floor((bw - 2 * dties - 2 * cc + sp + 2 * (2 * dties - 0.5 * db)) / (db + sp))

"""Beam Design - Singly Reinforced - As"""
def nbardesign(mu, fc, fy, bw, h, dmain, frametype):
    esteel = 200000
    ecu = 0.003
    pbal = 0.85 * beta(fc) * fc * (600 / (600 + fy)) / fy # balanced reinforcement ratio
    pmax = pbal * ((ecu + fy / esteel) / 0.008) # max reinf. ratio with reduction factor of 0.9, steel strain 0.004
    pmax_seismic = 0.025
    de1 = h - 77.5 # Assuming two layers of tension Reinforcement
    phi = 0.90
    ru = abs(mu) * 1000000 / (phi * bw * de1 ** 2)
    xu = 1 - 2 * ru / (0.85 * fc)
    ast = dbararea(dmain)
    # Minimum number of Reinforcements
    nmin1 = (fc ** 0.5 / (4 * fy)) * bw * de1 / ast
    nmin2 = 1.4 * bw * de1 / fy / ast
    if xu < 0:
        return 0
    else:
        rho = 0.85 * fc * (1 - xu ** 0.5) / fy
        nbarreq = rho * bw * de1 / ast
        if frametype == "SMRF":
            if rho <= pmax_seismic and rho < pmax:
                return round(max(nbarreq , nmin1, nmin2))
            else:
                nmax = pmax * bw * de1 / ast
                nmax_seismic = pmax_seismic * bw * de1 / ast
                return round(min(nmax, nmax_seismic))
        else:
            if rho <= pmax:
                return round(max(nbarreq, nmin1, nmin2))
            else:
                return math.floor(pmax * bw * de1 / ast)

def nbarlayers(totalbar, rebarperlayer, nlayer):
    j = 1
    ast = []
    for i in range(0,nlayer):
        chk = totalbar - rebarperlayer * j
        if chk >= 0:
            ast.append(rebarperlayer)
        else:
            ast.append(totalbar - rebarperlayer * (j - 1))
        j += 1
    return ast

def di_comp(dties,dmain,nlayer):
    di = []
    for i in range(0,nlayer):
        di.append(40 + dties + ((i) + 0.5) * dmain + 25 * (i))
    return di

def di_ten(dties, dmain, nlayer, hbeam):
    di = []
    for i in range(0,nlayer):
        di.append(hbeam - (40 + dties + ((i) + 0.5) * dmain + 25 * (i)))
    return di[::-1]

"""Reduction Factor"""
def reduction(fy,es, di, ci):
    ey = fy / es
    et = 0.003 * (di - ci) / ci
    phi_comp = 0.65
    phi_ten = 0.9
    if et >= 0.005:
        return phi_ten
    elif et <= ey:
        return phi_comp
    else:
        return phi_ten - (phi_ten - phi_comp) * (0.005 - et) / (0.005 - ey)

"""Moment Flexural Capacity"""
def flexcap(fc, fy, bw, h, dties, dmain, maxlayer, ncomp, nten, type):
    # Flexural Capacity Type
    # 1: Nominal Moment
    # 2: Ultimate Moment
    # 3: Probable Moment
    # 4: Yield Moment
    es = 200000
    ast = dbararea(dmain)
    nlayercomp = math.ceil(ncomp/maxlayer)
    nlayerten = math.ceil(nten/maxlayer)
    totalrebar = nlayercomp + nlayerten

    ast_comp = nbarlayers(ncomp, maxlayer, nlayercomp)
    ast_ten = nbarlayers(nten, maxlayer, nlayerten)[::-1]

    di = di_comp(dties, dmain, nlayercomp) + di_ten(dties, dmain, nlayerten, h)
    ni = ast_comp + ast_ten
    asi = np.dot(ast, ni)

    fsi = []
    ci = 40 # initial value
    criteria = 1.01 #initial value
    while criteria > 1:
        fsi.clear()
        for i in range(0, totalrebar):
            fsi.append(fs(fc, fy, asi[i], di[i], ci))
        fci = fcon(fc, bw, ci)
        sumforces = np.sum(fsi) + fci
        criteria = abs(np.sum(fsi) / fci)
        ci = ci + 0.1
    ai = beta(fc) * ci
    #Concrete Flexural
    mn_con = mncon(fci,ai)
    #Steel Flexural
    mn_steel = []
    for j in range(0, totalrebar):
        mn_steel.append(mnsteel(fsi[j],di[j]))
    #Extreme Tensile Strain
    est = 0.003 * (di[totalrebar-1] - ci) / ci
    #Nominal Moment
    nom_moment = np.sum(mn_steel) + mn_con
    phi = reduction(fy, es, di[totalrebar-1], ci)
    return nom_moment*phi, ci, est, di


print(dbararea(12))
print(beta(21))
print(depth(400, 40, 10, 12))
print(fcon(20.7, 300, 28))
print(fs(20.7,414,339,60,40))
print(rebarsp(16, 29))
print(nlayers(300,40,12,16,25))
print(nbardesign(5000,28,300,300,600,25,"IMRF"))

print(nbarlayers(8,4,2))


print(flexcap(20.7,414,300,600,12,25,4,8,8,2))
