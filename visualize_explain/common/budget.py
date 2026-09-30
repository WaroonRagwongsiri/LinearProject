"""Cost model for section 0 of docs/raycasting.md (shared by the document and the BudgetVsCost scene).

Every hardware number below was taken from a published source (see docs/raycasting.md, section 0);
everything that is MY estimate is marked ASSUMPTION. Costs are LOWER bounds: we count only the arithmetic
instructions, never loop overhead, float<->int conversions or memory waits. The real cost can only be higher.

    python common/budget.py        # prints every number quoted in the document
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import raycast as rc

# ---- the screen: VGA mode 13h ------------------------------------------------------------------
W, H = 320, 200
PIXELS, COLUMNS = W * H, W                      # 64,000 and 320
FPS = 70                                        # Sanglard, Game Engine Black Book, ch. 2.3.7 (target frame rate)

# ---- the machines (Sanglard ch. 2.1.1, fig. 2.3: MIPS) -----------------------------------------
MACHINES = [            # name, clock MHz, MIPS
    ("286 @ 8 MHz",      8,  1.5),
    ("386SX @ 16 MHz",  16,  2.5),
    ("386DX @ 33 MHz",  33,  8.0),
    ("386DX @ 40 MHz",  40,  9.6),
]

# ---- clocks per instruction (lower end of the published range) ---------------------------------
INT = dict(ADD=2, MOV_MEM=4, IMUL=12, IDIV=27)   # 386 integer, Sanglard ch. 2.1.3 / fig. 2.6
FPU = dict(FADD=24, FMUL=27, FDIV=88, FSQRT=122, FSIN=122, FCOS=123, FSINCOS=194)
#   FADD/FMUL/FSQRT/FSIN/FCOS/FSINCOS: Intel i387 datasheet 271074-006 (32-bit operands, |x| <= pi/4;
#   up to +76 clocks for argument reduction). FDIV 88-91: Lo-tech wiki table for the 80387.
#   A 286/386 had NO FPU unless you bought one: Sanglard ch. 2.1.3 -> floats are "emulated in software".


def cost_naive(eps, dist):
    """One angle-marched ray (section 1): sin+cos once, then x += eps*cos, y += eps*sin every step
    (the incremental version: the cheapest way to write the naive method)."""
    n = math.ceil(dist / eps)
    setup = FPU["FSINCOS"] + 2 * FPU["FMUL"]                 # sincos, then eps*cos and eps*sin
    return n, setup + n * 2 * FPU["FADD"]


def cost_dda(steps, line_height):
    """One column with DDA (this project): setup + steps + drawing the column."""
    f = FPU
    setup = (f["FMUL"] + f["FADD"]) * 2 \
          + 2 * f["FDIV"] \
          + (f["FMUL"] + f["FADD"]) * 2                      # dir (2 mul + 2 add), delta_dist (2 div), side_dist (2 mul + 2 add)
    per_step = f["FADD"] + INT["ADD"] + INT["MOV_MEM"]       # side_dist += delta (FADD), map += step, grid lookup
    project = f["FADD"] + f["FDIV"]                          # wall_dist = side - delta ; H / wall_dist
    draw = line_height * INT["MOV_MEM"]                      # one store per pixel of the column
    return setup + steps * per_step + project + draw


def demo_rays():
    """The 320 real rays of the demo room (same room as the GIFs), at 320x200."""
    grid, (sx, sy, c) = rc.load_grid(rc.DEMO_MAP)
    p = rc.spawn(sx, sy, c)
    out = []
    for x in range(COLUMNS):
        r = rc.cast(grid, p, x, width=W, height=H)
        euclid = r.wall_dist * math.hypot(r.dir_x, r.dir_y)  # |r| * t_hit  (section 4: |r| = 1/cos)
        out.append((euclid, len(r.trace), r.line_height))
    return out


def summary():
    rays = demo_rays()
    mean = lambda i: sum(t[i] for t in rays) / len(rays)
    d, s, lh = mean(0), mean(1), mean(2)
    res = dict(d=d, steps=s, line_height=lh)
    for eps in (0.1, 0.01):
        n, per_ray = cost_naive(eps, d)
        res[f"naive_{eps}"] = dict(steps=n, per_ray=per_ray, per_frame=per_ray * PIXELS, per_frame_cols=per_ray * COLUMNS)
    res["dda_col"] = cost_dda(s, lh)
    res["dda_frame"] = res["dda_col"] * COLUMNS
    res["machines"] = {}
    for name, mhz, mips in MACHINES:
        clk = mhz * 1e6
        res["machines"][name] = dict(
            clk_frame=clk / FPS, clk_pixel=clk / FPS / PIXELS, clk_col=clk / FPS / COLUMNS,
            instr_frame=mips * 1e6 / FPS, instr_pixel=mips * 1e6 / FPS / PIXELS)
    return res


if __name__ == "__main__":
    r = summary()
    print(f"demo room, 320 rays: mean Euclid distance {r['d']:.2f}, mean DDA steps {r['steps']:.2f}, mean line_height {r['line_height']:.1f}")
    for k in ("naive_0.1", "naive_0.01"):
        v = r[k]
        print(f"{k}: {v['steps']} steps/ray, {v['per_ray']:,.0f} clk/ray, all-pixel {v['per_frame']:,.0f} clk/frame, per-column {v['per_frame_cols']:,.0f}")
    print(f"DDA: {r['dda_col']:,.0f} clk/column, {r['dda_frame']:,.0f} clk/frame")
    for n, v in r["machines"].items():
        print(f"{n}: {v['clk_frame']:,.0f} clk/frame @70fps, {v['clk_pixel']:.2f} clk/pixel, {v['clk_col']:,.0f} clk/column, "
              f"{v['instr_frame']:,.0f} instr/frame, {v['instr_pixel']:.2f} instr/pixel")
    m = r["machines"]["386DX @ 33 MHz"]
    for k in ("naive_0.1", "naive_0.01"):
        f = r[k]["per_frame"]
        print(f"{k} all-pixel on 386DX33: {f/33e6:.1f} s/frame, {f/m['clk_frame']:,.0f}x over budget")
        f = r[k]["per_frame_cols"]
        print(f"{k} per-column on 386DX33: {f/33e6*1000:.0f} ms/frame, {f/m['clk_frame']:.1f}x over budget")
    f = r["dda_frame"]
    print(f"DDA per-column on 386DX33: {f/33e6*1000:.1f} ms/frame ({33e6/f:.0f} fps), {f/m['clk_frame']:.2f}x of budget")
    print(f"pixel stores only (64,000 x 4 clk): {PIXELS*4:,} clk = {PIXELS*4/33e6*1000:.1f} ms on 386DX33; 286@8MHz {PIXELS*4/8e6*1000:.0f} ms")
    print(f"today 3 GHz, 1280x720, 60 fps: {3e9/60/(1280*720):.0f} clk/pixel, {3e9/60/1280:,.0f} clk/column")
