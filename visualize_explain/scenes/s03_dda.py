import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.style import *
from common import raycast as rc


class DeltaDist(Scene):
    """Along q(t)=p+t r the x-lines are crossed every 1/|r_x| and the y-lines every 1/|r_y|."""

    def construct(self):
        grid = [list("0000000") for _ in range(5)]
        W = World(grid, cell=0.85, top_left=(-6.9, 2.3))
        p, r = np.array([1.35, 3.2]), np.array([1.0, -0.6])
        pt = lambda t: W.pt(*(p + t * r))
        title = T("Why 1/|r| ?  The ray is a line  q(t) = p + t·r", 28).to_edge(UP, buff=0.3)
        gm = W.build_map()
        dot_p = Dot(W.pt(*p), color=C_PLAYER, radius=0.09)
        r_arr = Arrow(pt(0), pt(1.0), buff=0, color=C_RAY, stroke_width=5)
        r_lab = M(r"\vec r", color=C_RAY, size=30).next_to(r_arr, DOWN, buff=0.05)
        line = DashedLine(pt(0), pt(5.4), color=C_RAY, stroke_opacity=0.7, dash_length=0.12)

        xs_t = [(k - p[0]) / r[0] for k in range(2, 7)]           # vertical lines x = k
        ys_t = [(p[1] - k) / -r[1] for k in (3, 2, 1, 0)]         # horizontal lines y = k
        xd = VGroup(*[Dot(pt(t), color=C_X, radius=0.07) for t in xs_t])
        yd = VGroup(*[Dot(pt(t), color=C_Y, radius=0.07) for t in ys_t])

        # similar-triangle legs between 2 consecutive x crossings
        A, B = pt(xs_t[0]), pt(xs_t[1])
        corner = np.array([B[0], A[1], 0])
        legs = VGroup(Line(A, corner, color=C_X, stroke_width=4), Line(corner, B, color=C_X, stroke_width=4))
        l_one = M(r"1", color=C_X, size=28).next_to(legs[0], DOWN, buff=0.08)
        l_hyp = M(r"\Delta t_x\,\vec r", color=C_X, size=26).move_to((A + B) / 2 + np.array([-0.5, 0.35, 0]))
        eq_x = M(r"\Delta t_x\,|r_x| = 1\;\Rightarrow\;\Delta t_x=\dfrac{1}{|r_x|}", size=30, color=C_X)
        eq_y = M(r"\Delta t_y=\dfrac{1}{|r_y|}", size=30, color=C_Y)

        # t axis (right)
        ax0, sc, ay = 1.0, 1.0, 0.0
        axis = Arrow([ax0 - 0.1, ay, 0], [ax0 + 5.7, ay, 0], buff=0, color=C_DIM, stroke_width=3, tip_length=0.15)
        t_lab = M(r"t", size=28, color=C_DIM).next_to(axis, RIGHT, buff=0.05)
        tk_x = VGroup(*[Line([ax0 + t * sc, ay, 0], [ax0 + t * sc, ay + 0.4, 0], color=C_X, stroke_width=5) for t in xs_t])
        tk_y = VGroup(*[Line([ax0 + t * sc, ay, 0], [ax0 + t * sc, ay - 0.4, 0], color=C_Y, stroke_width=5) for t in ys_t])
        tk_lab = T("x-lines above, y-lines below:\ntwo evenly spaced ladders on one axis", 20, C_DIM).move_to([3.9, 1.1, 0])
        first = VGroup(
            M(r"\text{side\_dist}_x=(m_x+1-p_x)\,\Delta t_x=0.65", size=27, color=C_X),
            M(r"\text{side\_dist}_y=(p_y-m_y)\,\Delta t_y=0.33", size=27, color=C_Y),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([3.9, -1.6, 0])
        eqs = VGroup(eq_x, eq_y).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([3.9, 2.4, 0])
        eqs.shift(UP * 0.0)

        self.play(FadeIn(title), FadeIn(gm), FadeIn(dot_p), run_time=1.0)
        self.play(GrowArrow(r_arr), FadeIn(r_lab), Create(line), run_time=1.2)
        self.play(LaggedStart(*[FadeIn(d, scale=1.6) for d in xd], lag_ratio=0.25), run_time=1.6)
        self.play(Create(legs), FadeIn(l_one), FadeIn(l_hyp), run_time=1.0)
        self.play(Write(eq_x), run_time=1.4)
        self.play(LaggedStart(*[FadeIn(d, scale=1.6) for d in yd], lag_ratio=0.25), Write(eq_y), run_time=1.6)
        self.play(Create(axis), FadeIn(t_lab), FadeOut(legs), FadeOut(l_one), FadeOut(l_hyp), run_time=0.8)
        self.play(*[TransformFromCopy(d, k) for d, k in zip(xd, tk_x)],
                  *[TransformFromCopy(d, k) for d, k in zip(yd, tk_y)], FadeIn(tk_lab), run_time=1.6)
        self.play(Write(first), run_time=1.6)
        self.play(Indicate(tk_x[0]), Indicate(tk_y[0]), run_time=1.0)
        self.wait(1.2)


def pick_ray(x=1040):
    """Column 1040 of the demo room: 9 iterations, both x- and y-steps, hits the bottom wall."""
    grid, (sx, sy, c) = rc.load_grid(rc.DEMO_MAP)
    p = rc.spawn(sx, sy, c)
    return grid, p, (x, rc.cast(grid, p, x))


class DDAWalk(Scene):
    """Merge two ladders: always step to whichever grid line is reached first."""

    def construct(self):
        grid, p, (xcol, r) = pick_ray()
        r0 = rc.ray_init(p, xcol)
        W = World(grid, cell=0.55, top_left=(-6.9, 2.55))
        title = T(f"DDA on one ray (screen column x = {xcol}, camera_x = {r0.camera_x:+.2f})", 26).to_edge(UP, buff=0.3)
        gm = W.build_map()
        dot_p = Dot(W.pt(p.x, p.y), color=C_PLAYER, radius=0.09)
        start_cell = W.cell_rect(int(p.x), int(p.y), stroke_color=C_PLAYER, stroke_width=3, fill_opacity=0)
        pos = lambda t: W.pt(p.x + t * r0.dir_x, p.y + t * r0.dir_y)

        # replay the real trace
        pre_x, pre_y = r0.side_dist_x, r0.side_dist_y
        steps = []
        for e in r.trace:
            t = pre_x if e["side"] == 0 else pre_y
            steps.append(dict(e, t=t, pre_x=pre_x, pre_y=pre_y))
            pre_x, pre_y = e["side_dist_x"], e["side_dist_y"]
        t_hit = steps[-1]["t"]

        # t-axis ladders
        ax0, ay = 0.7, 1.15
        sc = 5.4 / (t_hit * 1.12)
        axis = Line([ax0, ay, 0], [ax0 + 5.6, ay, 0], color=C_DIM, stroke_width=3)
        lad_x = [r0.side_dist_x + k * r0.delta_dist_x for k in range(12)]
        lad_y = [r0.side_dist_y + k * r0.delta_dist_y for k in range(12)]
        tx = VGroup(*[Line([ax0 + t * sc, ay, 0], [ax0 + t * sc, ay + 0.35, 0], color=C_X, stroke_width=4)
                      for t in lad_x if t <= t_hit * 1.12])
        ty = VGroup(*[Line([ax0 + t * sc, ay, 0], [ax0 + t * sc, ay - 0.35, 0], color=C_Y, stroke_width=4)
                      for t in lad_y if t <= t_hit * 1.12])
        ax_lab = VGroup(T("t", 22, C_DIM).move_to([ax0 + 5.85, ay, 0]),
                        T("x-lines", 20, C_X).move_to([ax0 - 0.05, ay + 0.65, 0], aligned_edge=LEFT),
                        T("y-lines", 20, C_Y).move_to([ax0 - 0.05, ay - 0.65, 0], aligned_edge=LEFT))
        head = M(rf"\Delta t_x=\tfrac1{{|r_x|}}={r0.delta_dist_x:.2f}\qquad\Delta t_y=\tfrac1{{|r_y|}}={r0.delta_dist_y:.2f}",
                 size=28).move_to([3.5, 2.75, 0])
        cursor = Triangle(color=C_PLAYER, fill_opacity=1, stroke_width=0).scale(0.13).rotate(PI).move_to([ax0, ay + 0.25, 0])
        tray = Line(W.pt(p.x, p.y), W.pt(p.x, p.y), color=C_RAY, stroke_width=3)

        self.play(FadeIn(title), FadeIn(gm), FadeIn(dot_p), FadeIn(start_cell), run_time=1.0)
        self.play(Create(axis), FadeIn(tx), FadeIn(ty), FadeIn(ax_lab), Write(head), run_time=1.6)
        self.add(tray, cursor)

        status = None
        for i, s in enumerate(steps):
            which = "x" if s["side"] == 0 else "y"
            col = C_X if which == "x" else C_Y
            st = M(rf"\text{{side\_dist}}_x={s['pre_x']:.2f}\ \ \text{{side\_dist}}_y={s['pre_y']:.2f}"
                   rf"\ \Rightarrow\ \text{{step {which}}}", size=24, color=col).move_to([3.5, -0.55, 0])
            cell = W.cell_rect(s["map_x"], s["map_y"], stroke_color=col, stroke_width=2,
                               fill_color=(C_GOOD if s["hit"] else col), fill_opacity=0.55 if not s["hit"] else 0.8)
            dot = Dot(pos(s["t"]), color=col, radius=0.07)
            new_tray = Line(W.pt(p.x, p.y), pos(s["t"]), color=C_RAY, stroke_width=3)
            cnt = T(f"iteration {i + 1}", 22, C_DIM).move_to([3.5, -1.3, 0])
            new_cnt = cnt
            anims = [(FadeIn(st) if status is None else ReplacementTransform(status, st)),
                     cursor.animate.move_to([ax0 + s["t"] * sc, ay + (0.25 if which == "x" else -0.25), 0]
                                            ).set_color(col),
                     Transform(tray, new_tray), FadeIn(cell), FadeIn(dot, scale=1.8)]
            self.play(*anims, run_time=0.9)
            status = st
            self.wait(0.15)
        fin = VGroup(
            T("wall hit →", 22, C_GOOD),
            M(r"\text{side\_dist}\ \text{is now one }\Delta t\text{ past the wall:}", size=26),
            M(rf"t_{{hit}}=\text{{side\_dist}}-\Delta t={t_hit:.2f}", size=30, color=C_GOOD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([3.5, -2.45, 0])
        self.play(FadeIn(fin, shift=UP * 0.2), run_time=1.0)
        self.wait(1.6)


class StepCount(Scene):
    """Real counts over maps/sample.cub: fixed-step marching vs DDA, all 1280 columns."""

    def construct(self):
        grid, (sx, sy, c) = rc.load_grid(rc.SAMPLE_MAP)
        p = rc.spawn(sx, sy, c)
        dda, naive = 0, {0.05: 0, 0.01: 0}
        for x in range(rc.WIDTH):
            r = rc.cast(grid, p, x)
            dda += len(r.trace)
            th = np.arctan2(r.dir_y, r.dir_x)
            for e in naive:
                naive[e] += rc.naive_march(grid, p.x, p.y, th, e)[0]
        rows = [("fixed step ε = 0.01", naive[0.01], C_BAD), ("fixed step ε = 0.05", naive[0.05], C_Y),
                ("DDA (this project)", dda, C_GOOD)]
        title = T("Grid steps per frame  (maps/sample.cub, 1280 rays)", 28).to_edge(UP, buff=0.4)
        self.play(FadeIn(title))
        mx, y0 = max(v for _, v, _ in rows), 1.3
        objs = []
        for i, (lab, v, col) in enumerate(rows):
            y = y0 - i * 1.4
            l = T(lab, 24, col).move_to([-6.6, y, 0], aligned_edge=LEFT)
            bar = Rectangle(width=max(6.0 * v / mx, 0.06), height=0.55, stroke_width=0, fill_color=col, fill_opacity=0.9) \
                .move_to([-2.7, y, 0], aligned_edge=LEFT)
            num = Integer(0, font_size=30, color=col, group_with_commas=True).move_to([-2.7 + max(6.0 * v / mx, 0.06) + 0.9, y, 0])
            objs.append((l, bar, num, v))
        for l, bar, num, v in objs:
            num.add_updater(lambda m, bar=bar: m.next_to(bar, RIGHT, buff=0.2))
            self.add(num)
        self.play(*[FadeIn(l) for l, *_ in objs], run_time=0.6)
        self.play(*[GrowFromEdge(b, LEFT) for _, b, *_ in objs],
                  *[ChangeDecimalToValue(n, v) for _, _, n, v in objs], run_time=3.0)
        ratio = naive[0.01] / dda
        cap = VGroup(
            M(rf"\text{{DDA needs}}\ \approx {ratio:.0f}\times\ \text{{fewer steps than}}\ \varepsilon=0.01", size=30, color=C_GOOD),
            T("and 0 trig calls per ray (fixed-step marching needs cos and sin every ray)", 22, C_DIM),
        ).arrange(DOWN, buff=0.25).move_to([0, -3.0, 0])
        self.play(FadeIn(cap, shift=UP * 0.2))
        self.wait(1.8)
