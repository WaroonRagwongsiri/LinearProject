import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.style import *
from common import raycast as rc


class Projection(Scene):
    """Similar triangles: a wall of height 1 at perpendicular distance z covers HEIGHT/z pixels."""

    def construct(self):
        S, H = 1.25, 720
        z = ValueTracker(3.0)
        eye = np.array([-6.4, -0.2, 0.0])
        X = lambda zz: eye[0] + zz * S
        title = T("Projection: line_height = HEIGHT / wall_dist", 28).to_edge(UP, buff=0.3)
        eye_dot = Dot(eye, color=C_PLAYER, radius=0.1)
        screen = Line(eye + RIGHT * S + UP * 1.5, eye + RIGHT * S + DOWN * 1.5, color=C_PLANE, stroke_width=4)
        l_scr = T("view plane (z = 1)", 18, C_PLANE).next_to(screen, UP, buff=0.12)
        axis = DashedLine(eye, eye + RIGHT * 7.5 * S, color=C_DIM, stroke_width=2, stroke_opacity=0.6)
        floor_h = 0.5 * S                                   # wall spans ±0.5 around eye height
        wall = always_redraw(lambda: Line([X(z.get_value()), eye[1] + floor_h, 0], [X(z.get_value()), eye[1] - floor_h, 0],
                                          color=C_WALL_EDGE, stroke_width=10))
        r_top = always_redraw(lambda: Line(eye, [X(z.get_value()), eye[1] + floor_h, 0], color=C_RAY, stroke_width=2.5))
        r_bot = always_redraw(lambda: Line(eye, [X(z.get_value()), eye[1] - floor_h, 0], color=C_RAY, stroke_width=2.5))
        hs = lambda: floor_h / z.get_value()                # half-height on the view plane
        proj = always_redraw(lambda: Line(eye + RIGHT * S + UP * hs(), eye + RIGHT * S + DOWN * hs(), color=C_GOOD, stroke_width=8))
        l_z = always_redraw(lambda: DoubleArrow(eye + DOWN * 1.2, [X(z.get_value()), eye[1] - 1.2, 0], buff=0, color=C_DIM,
                                                 stroke_width=2, tip_length=0.12))
        l_zt = M(r"z=\texttt{wall\_dist}", size=24, color=C_DIM)
        l_zt.add_updater(lambda m: m.move_to([(eye[0] + X(z.get_value())) / 2, eye[1] - 1.55, 0]))
        sim = M(r"\dfrac{h_{\text{screen}}}{1}=\dfrac{1}{z}", size=30, color=C_GOOD).move_to([-2.2, 2.2, 0])

        # the screen column (HEIGHT px) on the right
        cx, top, bot = 5.6, 2.3, -2.3
        colbox = Rectangle(width=0.9, height=top - bot, color=C_DIM, stroke_width=2).move_to([cx, (top + bot) / 2, 0])
        mid = Line([cx - 0.65, (top + bot) / 2, 0], [cx + 0.65, (top + bot) / 2, 0], color=C_DIM, stroke_width=1)
        l_col = T("one screen column\n(HEIGHT = 720 px)", 18, C_DIM).next_to(colbox, UP, buff=0.12)
        lh = lambda: max(1, int(H / z.get_value()))

        def col_wall():
            ds = max(0, H // 2 - lh() // 2)
            de = min(H - 1, H // 2 + lh() // 2)
            y_of = lambda px: top - (top - bot) * px / H
            return Rectangle(width=0.9, height=max(y_of(ds) - y_of(de + 1), 0.02), stroke_width=0,
                             fill_color=C_WALL_EDGE, fill_opacity=0.95).move_to([cx, (y_of(ds) + y_of(de + 1)) / 2, 0])

        colwall = always_redraw(col_wall)

        def readout(label, fn, y, fmt, col=C_TEXT):
            lab = T(label, 22, C_DIM).move_to([1.3, y, 0], aligned_edge=LEFT)
            n = DecimalNumber(0, num_decimal_places=fmt, font_size=26, color=col)
            n.add_updater(lambda m: m.set_value(fn()).move_to(lab.get_right() + RIGHT * 0.15, aligned_edge=LEFT))
            n.update()
            return lab, n
        rd = [readout("wall_dist z =", z.get_value, 2.2, 2, C_TEXT),
              readout("line_height =", lh, 1.45, 0, C_GOOD),
              readout("draw_start =", lambda: max(0, H // 2 - lh() // 2), 0.7, 0, C_GOOD),
              readout("draw_end =", lambda: min(H - 1, H // 2 + lh() // 2), -0.05, 0, C_GOOD)]
        form = M(r"\texttt{line\_height}=\left\lfloor\dfrac{H}{z}\right\rfloor", size=28, color=C_GOOD).move_to([2.9, -1.3, 0])
        clamp = T("clamped to [0, HEIGHT−1] when z is tiny", 18, C_Y).move_to([2.6, -2.0, 0])

        self.play(FadeIn(title), FadeIn(eye_dot), Create(axis), Create(screen), FadeIn(l_scr), run_time=1.2)
        self.add(wall, r_top, r_bot, proj)
        self.play(Write(sim), FadeIn(l_z), FadeIn(l_zt), run_time=1.4)
        self.play(Create(colbox), Create(mid), FadeIn(l_col), run_time=0.8)
        self.add(colwall)
        for a, b in rd:
            self.add(a, b)
        self.play(Write(form), run_time=1.0)
        self.play(z.animate.set_value(6.0), run_time=2.6)
        self.play(z.animate.set_value(1.0), run_time=3.2)
        self.play(FadeIn(clamp), run_time=0.5)
        self.play(z.animate.set_value(0.6), run_time=1.2)
        self.play(z.animate.set_value(3.0), run_time=2.0)
        self.wait(0.6)


class FrameSweep(Scene):
    """Sweep camera_x from -1 to 1: one ray per column builds the picture (96 columns shown, C uses 1280)."""

    def construct(self):
        from common.frame import load_textures
        grid, (sx, sy, c) = rc.load_grid(rc.DEMO_MAP)
        p = rc.spawn(sx, sy, c)
        rc.rotate(p, -0.45)
        N = 96
        W = World(grid, cell=0.42, top_left=(-6.9, 2.1))
        title = T(f"One ray per screen column  ({N} shown, WIDTH = 1280 in the C code)", 24).to_edge(UP, buff=0.3)
        gm = W.build_map()
        pl = Dot(W.pt(p.x, p.y), color=C_PLAYER, radius=0.07)
        fov = VGroup(*[Line(W.pt(p.x, p.y), W.pt(p.x + (p.dir_x + p.plane_x * s) * 0.9, p.y + (p.dir_y + p.plane_y * s) * 0.9),
                            color=C_PLANE if abs(s) == 1 else C_DIM, stroke_width=2, stroke_opacity=0.8) for s in (-1, 1)])
        d_arr = Arrow(W.pt(p.x, p.y), W.pt(p.x + p.dir_x * 0.9, p.y + p.dir_y * 0.9), buff=0, color=C_DIR, stroke_width=4)

        # average texture colours (shaded like draw_column: side==1 -> r/2,g/2,b/2)
        try:
            avg = [tuple(int(v) for v in t[..., :3].reshape(-1, 3).mean(0)) for t in load_textures()]
        except Exception:
            avg = [(150, 150, 160)] * 4
        vx, vw, vh, vy = 0.3, 6.6, 3.7, -0.35
        res = [rc.cast(grid, p, x, width=N) for x in range(N)]
        cw = vw / N

        def rgb(t):
            return "#%02x%02x%02x" % t
        ceil, floor = (100, 180, 240), (220, 100, 0)
        cols = VGroup()
        for i, r in enumerate(res):
            xc = vx + cw * (i + 0.5)
            ds, de = r.draw_start, r.draw_end + 1
            yt = lambda px: vy + vh / 2 - vh * px / rc.HEIGHT
            base = avg[r.texture_index]
            wc = tuple(v // 2 for v in base) if r.side == 1 else base
            parts = VGroup(
                Rectangle(width=cw * 1.04, height=yt(0) - yt(ds), stroke_width=0, fill_color=rgb(ceil), fill_opacity=1).move_to([xc, (yt(0) + yt(ds)) / 2, 0]),
                Rectangle(width=cw * 1.04, height=max(yt(ds) - yt(de), 0.01), stroke_width=0, fill_color=rgb(wc), fill_opacity=1).move_to([xc, (yt(ds) + yt(de)) / 2, 0]),
                Rectangle(width=cw * 1.04, height=yt(de) - yt(rc.HEIGHT), stroke_width=0, fill_color=rgb(floor), fill_opacity=1).move_to([xc, (yt(de) + yt(rc.HEIGHT)) / 2, 0]),
            )
            cols.add(parts)
        frame_box = Rectangle(width=vw, height=vh, color=C_DIM, stroke_width=2).move_to([vx + vw / 2, vy, 0])
        idx = ValueTracker(-1)
        cols.add_updater(lambda m: [sub.set_opacity(1.0 if i <= idx.get_value() else 0.0) for i, sub in enumerate(m)])
        ray = always_redraw(lambda: Line(W.pt(p.x, p.y), W.pt(p.x + res[max(0, int(idx.get_value()))].wall_dist * res[max(0, int(idx.get_value()))].dir_x,
                                                              p.y + res[max(0, int(idx.get_value()))].wall_dist * res[max(0, int(idx.get_value()))].dir_y),
                                         color=C_RAY, stroke_width=3))
        lab = T("x = ", 20, C_DIM).move_to([-6.6, -2.35, 0], aligned_edge=LEFT)
        xn = Integer(0, font_size=24, color=C_RAY).add_updater(lambda m: m.set_value(int(max(idx.get_value(), 0) * 1280 / N)).next_to(lab, RIGHT, buff=0.1))
        cam = T("camera_x = ", 20, C_DIM).move_to([-4.3, -2.35, 0], aligned_edge=LEFT)
        cn = DecimalNumber(-1, num_decimal_places=2, include_sign=True, font_size=24, color=C_RAY) \
            .add_updater(lambda m: m.set_value(2.0 * max(idx.get_value(), 0) / N - 1.0).next_to(cam, RIGHT, buff=0.1))
        steps = VGroup(T("per column:  ray_init → ray_dda → ray_project → ray_set_texture → draw_column", 18, C_DIM)).move_to([0, -3.65, 0])
        self.play(FadeIn(title), FadeIn(gm), FadeIn(pl), FadeIn(fov), GrowArrow(d_arr), Create(frame_box), run_time=1.4)
        self.add(cols)
        self.add(ray, lab, xn, cam, cn)
        self.play(FadeIn(steps), run_time=0.5)
        self.play(idx.animate.set_value(N - 1), run_time=7.0, rate_func=linear)
        self.wait(1.0)
