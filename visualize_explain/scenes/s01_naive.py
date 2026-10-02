import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.style import *
from common import raycast as rc


class NaiveMarching(Scene):
    """The angle method: walk along (cos θ, sin θ) in tiny steps. Cost grows as 1/ε."""

    def construct(self):
        grid, (sx, sy, _) = rc.load_grid(rc.DEMO_MAP)
        W = World(grid, cell=0.55, top_left=(-6.9, 2.55))
        px, py, theta = sx + 0.5, sy + 0.5, -0.2
        d_hit = rc.naive_march(grid, px, py, theta, 0.001)[1]
        cs, sn = np.cos(theta), np.sin(theta)

        title = T("Naive: walk along (cos θ, sin θ) in small steps", 28).to_edge(UP, buff=0.3)
        mp = W.build_map()
        player = Dot(W.pt(px, py), color=C_PLAYER, radius=0.09)
        ray = Line(W.pt(px, py), W.pt(px + d_hit * cs, py + d_hit * sn), color=C_RAY, stroke_width=2, stroke_opacity=0.5)

        def dots(eps, rad):
            n = int(np.ceil(d_hit / eps))
            return VGroup(*[Dot(W.pt(px + i * eps * cs, py + i * eps * sn), radius=rad, color=C_RAY) for i in range(1, n + 1)]), n

        def info(eps, n):
            return VGroup(M(rf"\varepsilon = {eps}", size=34, color=C_RAY),
                          M(rf"N=\lceil d/\varepsilon\rceil = {n}\ \text{{steps for this ray}}", size=30)
                          ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([3.3, 1.2, 0])

        f1 = M(r"\vec p_i=\vec p+i\,\varepsilon\begin{bmatrix}\cos\theta\\ \sin\theta\end{bmatrix}", size=34) \
            .move_to([3.3, 2.5, 0])
        self.play(FadeIn(title), FadeIn(mp), FadeIn(player), run_time=1.0)
        self.play(Create(ray), Write(f1), run_time=1.0)
        cur = None
        for eps, rad in [(0.5, 0.06), (0.25, 0.045), (0.05, 0.03)]:
            g, n = dots(eps, rad)
            inf = info(eps, n)
            self.play(LaggedStart(*[FadeIn(d) for d in g], lag_ratio=0.03 if n < 40 else 0.004),
                      (Write(inf) if cur is None else ReplacementTransform(cur[1], inf)),
                      *( [FadeOut(cur[0])] if cur else []), run_time=1.8)
            cur = (g, inf)
            self.wait(0.4)
        ledger = VGroup(
            T("every ray, every frame:", 24, C_DIM),
            M(r"2\times\text{trig}\ (\cos\theta,\ \sin\theta)\ \times\ 1280\ \text{rays}", size=28),
            M(r"\text{+ 1 more } \cos\text{ per ray to undo fisheye}", size=28, color=C_BAD),
            M(r"\text{+ thin walls can be stepped over if }\varepsilon\text{ is large}", size=26, color=C_BAD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([3.3, -1.75, 0])
        self.play(FadeIn(ledger, shift=UP * 0.2), run_time=1.0)
        self.wait(1.5)


class FisheyeCompare(Scene):
    """Why the slanted distance d is wrong for a flat wall: the perpendicular distance D is the same everywhere,
    d = D/cos(theta) grows toward the edges. Also shows the camera plane the vector method uses instead."""

    def construct(self):
        D, S = 2.7, 1.5                                   # D wall distance (world units), S = screen units per world unit
        p = np.array([-2.3, -3.1, 0.0])
        wall_y = p[1] + D * S
        half = np.radians(33.4)                           # FOV 66.8 deg  <->  camera plane half-length 0.66
        halo = lambda m: m.set_stroke(BG, width=5, background=True)
        title = T("Fisheye: the slanted distance d is not the wall's distance", 28).to_edge(UP, buff=0.3)
        wall = Line([p[0] - 3.4, wall_y, 0], [p[0] + 3.4, wall_y, 0], color=C_WALL_EDGE, stroke_width=8)
        l_wall = halo(T("flat wall", 20, C_WALL_EDGE).move_to([p[0] - 2.7, wall_y + 0.3, 0]))
        player = Dot(p, color=C_PLAYER, radius=0.1)
        fan = VGroup(*[Line(p, [p[0] + D * S * np.tan(a), wall_y, 0], color=C_RAY, stroke_width=1.5, stroke_opacity=0.25)
                       for a in np.linspace(-half, half, 9)])

        # camera plane: the line at distance 1 from the player, perpendicular to d, half-length 0.66
        py = p[1] + 1.0 * S
        plane = Line([p[0] - 0.66 * S, py, 0], [p[0] + 0.66 * S, py, 0], color=C_PLANE, stroke_width=5)
        arr_d = Arrow(p, [p[0], py, 0], buff=0, color=C_DIR, stroke_width=5, max_tip_length_to_length_ratio=0.25)
        arr_P = Arrow([p[0], py, 0], [p[0] + 0.66 * S, py, 0], buff=0, color=C_PLANE, stroke_width=5,
                      max_tip_length_to_length_ratio=0.3)
        l_vd = halo(M(r"\vec d", color=C_DIR, size=28).move_to([p[0] - 0.33, p[1] + 0.5 * S, 0]))
        l_vP = halo(M(r"\vec P", color=C_PLANE, size=28).move_to([p[0] + 0.5 * S, py + 0.3, 0]))
        l_plane = halo(T("camera plane", 20, C_PLANE).next_to(plane, LEFT, buff=0.15))
        sq_plane = Square(0.18, stroke_width=2, color=C_DIM).move_to([p[0] + 0.09, py + 0.09, 0])

        # D: the perpendicular distance, a solid line from the player straight to the wall (perpendicular to both)
        foot = np.array([p[0], wall_y, 0])
        perp = Line(p, foot, color=C_DIR, stroke_width=7)
        sq_wall = Square(0.2, stroke_width=2, color=C_DIM).move_to(foot + np.array([0.1, -0.1, 0]))
        l_D = halo(M(r"D", color=C_DIR, size=36).move_to([p[0] - 0.3, p[1] + 2.3 * S, 0]))
        l_D2 = halo(T("straight ahead,\nthe same for the whole wall", 17, C_DIR).next_to(l_D, DOWN, buff=0.1, aligned_edge=RIGHT))

        # the moving ray: d, with theta from 0 to the edge of the view
        th = ValueTracker(0.02)
        hit = lambda: np.array([p[0] + D * S * np.tan(th.get_value()), wall_y, 0])
        ray = always_redraw(lambda: Line(p, hit(), color=C_RAY, stroke_width=6))
        tri = always_redraw(lambda: Polygon(p, foot, hit(), stroke_width=0, fill_color=C_RAY, fill_opacity=0.12))
        along = always_redraw(lambda: Line(foot, hit(), color=C_WALL_EDGE, stroke_width=2))
        arc = always_redraw(lambda: Arc(radius=0.8, start_angle=PI / 2 - th.get_value(), angle=th.get_value(),
                                        arc_center=p, color=C_PLAYER, stroke_width=4))
        l_th = always_redraw(lambda: halo(M(r"\theta", color=C_PLAYER, size=30).move_to(
            p + 1.15 * np.array([np.sin(th.get_value() / 2), np.cos(th.get_value() / 2), 0]) + np.array([0.12, 0, 0]))))
        l_d = always_redraw(lambda: halo(M(r"d", color=C_RAY, size=36).move_to(
            (p + hit()) / 2 + np.array([0.32, -0.05, 0]))))

        # right panel: live numbers and the two formulas
        X = 2.3
        r_th = always_redraw(lambda: T(f"θ = {np.degrees(th.get_value()):4.1f}°", 28, C_PLAYER)
                             .move_to([X, 2.35, 0], aligned_edge=LEFT))
        r_d = always_redraw(lambda: T(f"d = {1 / np.cos(th.get_value()):.2f} · D", 28, C_RAY)
                            .move_to([X, 1.65, 0], aligned_edge=LEFT))
        f_d = M(r"d=\frac{D}{\cos\theta}", color=C_RAY, size=38).move_to([X, 0.45, 0], aligned_edge=LEFT)
        f_D = M(r"D=d\cos\theta", color=C_DIR, size=38).move_to([X, -0.55, 0], aligned_edge=LEFT)
        c1 = T("wall height ∝ 1 / distance", 22).move_to([X, -1.55, 0], aligned_edge=LEFT)
        c2 = T("using d: edges shrink, it bows", 18, C_BAD).move_to([X, -2.1, 0], aligned_edge=LEFT)
        c3 = T("using D: the wall stays flat", 18, C_GOOD).move_to([X, -2.55, 0], aligned_edge=LEFT)
        note = T("fix: extra cos per ray, or vectors →", 18, C_DIM).move_to([X, -3.3, 0], aligned_edge=LEFT)

        self.play(FadeIn(title), Create(wall), FadeIn(l_wall), FadeIn(player), run_time=1.0)
        self.play(Create(plane), GrowArrow(arr_d), GrowArrow(arr_P), FadeIn(l_vd), FadeIn(l_vP), FadeIn(l_plane),
                  FadeIn(sq_plane), run_time=1.4)
        self.play(Create(perp), FadeIn(sq_wall), FadeIn(l_D), FadeIn(l_D2), run_time=1.2)
        self.play(FadeIn(fan), FadeIn(tri), FadeIn(along), Create(ray), Create(arc), FadeIn(l_th), FadeIn(l_d),
                  FadeIn(r_th), FadeIn(r_d), run_time=1.2)
        self.play(th.animate.set_value(half), run_time=3.5, rate_func=smooth)
        self.play(Write(f_d), run_time=1.0)
        self.play(Write(f_D), run_time=1.0)
        self.play(FadeIn(c1), run_time=0.6)
        self.play(FadeIn(c2), run_time=0.6)
        self.play(FadeIn(c3), run_time=0.6)
        self.play(FadeIn(note), run_time=0.6)
        self.wait(2.0)
