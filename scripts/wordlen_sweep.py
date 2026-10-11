import numpy as np, random

def build_atan_table(frac, itmax):
    return [int(round(np.arctan(2.0**-i)*(1<<frac))) for i in range(itmax)]

def gain_fx(frac, itmax):
    K = 1.0
    for i in range(itmax):
        K *= 1.0/np.sqrt(1+2**(-2*i))
    return int(round(K*(1<<frac)))

def sat(v, w):
    lim = 1 << (w-1)
    if v >= lim: v = lim-1
    if v < -lim: v = -lim
    return v

def rotate_fx(theta_fx, K_fx, atan_fx, depth, w):
    x, y, z = K_fx, 0, theta_fx
    for i in range(depth):
        d = 1 if z >= 0 else -1
        xn = sat(x - d*(y >> i), w)
        yn = sat(y + d*(x >> i), w)
        zn = sat(z - d*atan_fx[i], w)
        x, y, z = xn, yn, zn
    return x, y

def fold_rotate(theta, frac, K_fx, atan_fx, depth, w):
    t = np.mod(theta+np.pi, 2*np.pi)-np.pi
    if t > np.pi/2:
        t2 = np.pi - t; sign=(-1,1)
    elif t < -np.pi/2:
        t2 = t + np.pi; sign=(-1,-1)
    else:
        t2 = t; sign=(1,1)
    theta_fx = int(round(t2*(1<<frac)))
    xfx, yfx = rotate_fx(theta_fx, K_fx, atan_fx, depth, w)
    c, s = xfx/(1<<frac), yfx/(1<<frac)
    return sign[0]*c, sign[1]*s

random.seed(2)
angles = [random.uniform(-np.pi, np.pi) for _ in range(500)]

print(f"{'FRAC':>5s} {'ITMAX':>6s} {'AvgErr':>12s} {'MaxErr':>12s}")
for frac in [14,16,18,20,22,24]:
    for itmax in [12,15,18,20]:
        if itmax > frac:  # atan(2^-i) below 2^-frac resolution is pointless past ~frac iters
            continue
        w = frac+8
        atan_fx = build_atan_table(frac, itmax)
        K_fx = gain_fx(frac, itmax)
        errs=[]
        for th in angles:
            c,s = fold_rotate(th, frac, K_fx, atan_fx, itmax, w)
            errs.append(max(abs(c-np.cos(th)), abs(s-np.sin(th))))
        print(f"{frac:5d} {itmax:6d} {np.mean(errs):12.3e} {np.max(errs):12.3e}")
