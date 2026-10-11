import numpy as np, random

WIDTH = 24
FRAC = 20
SCALE = 1 << FRAC
ITER_MAX = 18

def tofx(v):
    return int(round(v*SCALE))
def fromfx(v):
    return v/SCALE

atan_fx = [tofx(np.arctan(2.0**-i)) for i in range(ITER_MAX)]
Kc = 1.0
for i in range(ITER_MAX):
    Kc *= 1.0/np.sqrt(1+2**(-2*i))
K_fx = tofx(Kc)

def sat(v, w=WIDTH+8):
    lim = 1 << (w-1)
    if v >= lim: v = lim-1
    if v < -lim: v = -lim
    return v

def rotate_fx(theta_fx, depth, thresh=None, floor=0):
    x, y, z = K_fx, 0, theta_fx
    i = 0
    while i < depth:
        d = 1 if z >= 0 else -1
        xn = sat(x - d*(y >> i))
        yn = sat(y + d*(x >> i))
        zn = sat(z - d*atan_fx[i])
        x, y, z = xn, yn, zn
        i += 1
        if thresh is not None and i >= floor and abs(z) < thresh:
            break
    return x, y, i  # cos_fx, sin_fx, cycles_used

def vector_fx(x0_fx, y0_fx, depth, thresh=None, floor=0):
    x, y, z = x0_fx, y0_fx, 0
    i = 0
    while i < depth:
        d = -1 if y >= 0 else 1
        xn = sat(x - d*(y >> i))
        yn = sat(y + d*(x >> i))
        zn = sat(z - d*atan_fx[i])
        x, y, z = xn, yn, zn
        i += 1
        if thresh is not None and i >= floor and abs(y) < thresh:
            break
    return z, i  # angle_fx, cycles_used

def fold_rotate(theta, depth, thresh=None, floor=0):
    t = np.mod(theta+np.pi, 2*np.pi)-np.pi
    neg = False
    if t > np.pi/2:
        t2 = np.pi - t; neg = True
    elif t < -np.pi/2:
        t2 = t + np.pi; neg = True; sflip=True
    else:
        t2 = t
    theta_fx = tofx(t2)
    xfx, yfx, cyc = rotate_fx(theta_fx, depth, thresh, floor)
    c, s = fromfx(xfx), fromfx(yfx)
    if t > np.pi/2:
        return -c, s, cyc
    elif t < -np.pi/2:
        return -c, -s, cyc
    else:
        return c, s, cyc

def fold_atan2(y, x, depth, thresh=None, floor=0):
    if x < 0:
        x, y, flip = -x, -y, True
    else:
        flip = False
    afx, cyc = vector_fx(tofx(x), tofx(y), depth, thresh, floor)
    ang = fromfx(afx)
    if flip:
        ang = ang + np.pi if ang <= 0 else ang - np.pi
    return ang, cyc

# ---- sweep to choose depths/thresholds (mirrors paper's Table II methodology) ----
random.seed(1)
test_angles = [random.uniform(-np.pi, np.pi) for _ in range(500)]
test_xy = []
for _ in range(500):
    x = random.uniform(-3,3); y = random.uniform(-3,3)
    if x*x+y*y < 1e-4: x=1.0
    test_xy.append((x,y))

def eval_rot(depth, thresh, floor):
    errs=[]; cycs=[]
    for th in test_angles:
        c,s,cyc = fold_rotate(th, depth, thresh, floor)
        ref_c, ref_s = np.cos(th), np.sin(th)
        errs.append(max(abs(c-ref_c), abs(s-ref_s)))
        cycs.append(cyc)
    return np.mean(errs), np.max(errs), np.mean(cycs)

def eval_vec(depth, thresh, floor):
    errs=[]; cycs=[]
    for x,y in test_xy:
        a,cyc = fold_atan2(y,x, depth, thresh, floor)
        ref = np.arctan2(y,x)
        errs.append(abs(a-ref))
        cycs.append(cyc)
    return np.mean(errs), np.max(errs), np.mean(cycs)

print("=== ROTATION (sin/cos) stage sweep ===")
print("depth=18 (no early stop, reference-ish):", eval_rot(18, None, 18))
for depth,floor in [(18,12),(14,10),(11,8)]:
    for thexp in [16,14,12,10]:
        th = 1<<(FRAC-thexp)
        avg,mx,mc = eval_rot(depth, th, floor)
        print(f"depth={depth} floor={floor} thresh=2^-{thexp}: avgerr={avg:.3e} maxerr={mx:.3e} meancyc={mc:.2f}")

print("=== VECTORING (atan2) stage sweep ===")
print("depth=18 (no early stop, reference-ish):", eval_vec(18, None, 18))
for depth,floor in [(18,12),(14,10),(11,8)]:
    for thexp in [16,14,12,10]:
        th = 1<<(FRAC-thexp)
        avg,mx,mc = eval_vec(depth, th, floor)
        print(f"depth={depth} floor={floor} thresh=2^-{thexp}: avgerr={avg:.3e} maxerr={mx:.3e} meancyc={mc:.2f}")
