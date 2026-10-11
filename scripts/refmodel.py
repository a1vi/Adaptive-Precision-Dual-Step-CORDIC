import numpy as np

WIDTH = 24
FRAC = 20
SCALE = 1 << FRAC
ITER_MAX = 20

def to_fixed(v):
    return int(round(v * SCALE))

def from_fixed(v):
    return v / SCALE

atan_table = [np.arctan(2.0**-i) for i in range(ITER_MAX)]
K = 1.0
for i in range(ITER_MAX):
    K *= 1.0/np.sqrt(1+2**(-2*i))
INV_K = 1.0/K

def cordic_rotate(theta, depth=ITER_MAX):
    # assumes theta in [-pi/2, pi/2]
    x, y, z = K, 0.0, theta
    for i in range(depth):
        d = 1.0 if z >= 0 else -1.0
        xn = x - d*y*(2.0**-i)
        yn = y + d*x*(2.0**-i)
        zn = z - d*atan_table[i]
        x, y, z = xn, yn, zn
    return x, y  # cos, sin

def cordic_vector(x0, y0, depth=ITER_MAX):
    # assumes x0 >= 0 (first/fourth quadrant range for convergence)
    x, y, z = x0, y0, 0.0
    for i in range(depth):
        d = -1.0 if y >= 0 else 1.0
        xn = x - d*y*(2.0**-i)
        yn = y + d*x*(2.0**-i)
        zn = z - d*atan_table[i]
        x, y, z = xn, yn, zn
    return x*K, z  # magnitude, angle

def full_sin_cos(theta, depth=ITER_MAX):
    # quadrant folding to bring theta into [-pi/2, pi/2]
    t = np.mod(theta + np.pi, 2*np.pi) - np.pi  # wrap to [-pi,pi)
    if t > np.pi/2:
        c, s = cordic_rotate(np.pi - t, depth)
        return -c, s
    elif t < -np.pi/2:
        c, s = cordic_rotate(t + np.pi, depth)
        return -c, -s
    else:
        c, s = cordic_rotate(t, depth)
        return c, s

def full_atan2(y, x, depth=ITER_MAX):
    if x >= 0:
        mag, ang = cordic_vector(x, y, depth)
        return ang
    else:
        mag, ang = cordic_vector(-x, -y, depth)
        ang = ang + np.pi if ang <= 0 else ang - np.pi
        return ang

if __name__ == "__main__":
    print("K =", K, "1/K =", INV_K)
    import random
    random.seed(0)
    maxerr_sin=0; maxerr_cos=0; maxerr_atan=0
    for _ in range(2000):
        th = random.uniform(-np.pi, np.pi)
        c,s = full_sin_cos(th, ITER_MAX)
        maxerr_sin = max(maxerr_sin, abs(s-np.sin(th)))
        maxerr_cos = max(maxerr_cos, abs(c-np.cos(th)))
        x = random.uniform(-4,4); y = random.uniform(-4,4)
        if abs(x)<1e-6 and abs(y)<1e-6: continue
        a = full_atan2(y,x,ITER_MAX)
        ref = np.arctan2(y,x)
        maxerr_atan = max(maxerr_atan, abs(a-ref))
    print("max sin err", maxerr_sin, "max cos err", maxerr_cos, "max atan2 err", maxerr_atan)
