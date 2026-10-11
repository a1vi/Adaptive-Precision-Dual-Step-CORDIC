import numpy as np, random

FRAC = 20
SCALE = 1 << FRAC

def tofx(v): return int(round(v*SCALE))

# --- Held-out evaluation set: disjoint seed/size from the tuning sweep (seed=1, N=500) ---
random.seed(777)
N_EVAL = 5000
angles = [random.uniform(-np.pi, np.pi) for _ in range(N_EVAL)]
xy = []
for _ in range(N_EVAL):
    x = random.uniform(-3,3); y = random.uniform(-3,3)
    if x*x+y*y < 1e-4: x = 1.0
    xy.append((x,y))

# --- Structured / boundary / worst-case set (deterministic, not random) ---
# Angles at and near quadrant boundaries and extremes, plus a dense uniform grid.
boundary_angles = []
eps = 1e-6
for a in [0.0, np.pi/2, -np.pi/2, np.pi-eps, -np.pi+eps, np.pi/2-eps, np.pi/2+eps,
          -np.pi/2-eps, -np.pi/2+eps, 1e-6, -1e-6]:
    boundary_angles.append(a)
grid_angles = list(np.linspace(-np.pi, np.pi, 400, endpoint=False))
struct_angles = boundary_angles + grid_angles

boundary_xy = []
for x in [0.0, 1e-6, -1e-6, 3.0, -3.0]:
    for y in [0.0, 1e-6, -1e-6, 3.0, -3.0]:
        if abs(x) < 1e-9 and abs(y) < 1e-9:
            x = 1.0
        boundary_xy.append((x,y))
# dense angular grid converted to unit-circle (x,y) pairs to hit every vectoring angle
grid_xy = [(np.cos(t), np.sin(t)) for t in np.linspace(-np.pi, np.pi, 400, endpoint=False)]
struct_xy = boundary_xy + grid_xy

def write_fx(fname, vals):
    with open(fname, 'w') as f:
        for v in vals:
            f.write(str(tofx(v)) + "\n")

def write_hex32(fname_dec, fname_hex):
    with open(fname_dec) as f, open(fname_hex, 'w') as g:
        for line in f:
            v = int(line.strip())
            if v < 0: v += (1 << 32)
            g.write(format(v, '08x') + "\n")

write_fx("eval_angles.dec", angles)
write_fx("struct_angles.dec", struct_angles)
with open("eval_xy_x.dec","w") as fx, open("eval_xy_y.dec","w") as fy:
    for x,y in xy:
        fx.write(str(tofx(x))+"\n"); fy.write(str(tofx(y))+"\n")
with open("struct_xy_x.dec","w") as fx, open("struct_xy_y.dec","w") as fy:
    for x,y in struct_xy:
        fx.write(str(tofx(x))+"\n"); fy.write(str(tofx(y))+"\n")

for f in ["eval_angles","struct_angles"]:
    write_hex32(f+".dec", f+"_h.hex")
for f in ["eval_xy_x","eval_xy_y","struct_xy_x","struct_xy_y"]:
    write_hex32(f+".dec", f+"_h.hex")

print("eval angles:", len(angles), " eval xy:", len(xy))
print("struct angles:", len(struct_angles), " struct xy:", len(struct_xy))
