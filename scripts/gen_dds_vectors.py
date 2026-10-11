import numpy as np

FRAC = 20
SCALE = 1 << FRAC

def tofx(v):
    return int(round(v * SCALE))

# Application-level validation: a direct-digital-synthesis (DDS) style
# numerically-controlled-oscillator phase ramp. N samples spanning exactly
# one full 2*pi cycle, matching how this engine would be driven as a
# sine/cosine generator in a real NCO/DDS application (the canonical
# CORDIC application). N=4096 gives a clean power-of-two FFT length with
# fine frequency resolution relative to the single generated tone.
N = 4096
angles = [-np.pi + 2*np.pi*k/N for k in range(N)]

def write_hex32(vals, fname_hex):
    with open(fname_hex, 'w') as g:
        for v in vals:
            fx = tofx(v)
            if fx < 0:
                fx += (1 << 32)
            g.write(format(fx, '08x') + "\n")

write_hex32(angles, "dds_angles_h.hex")
print("DDS ramp samples:", len(angles))
