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
    """Equal-angle rays + Euclidean distance: a flat wall bulges. Perpendicular distance fixes it."""

    def construct(self):
        D, S = 3.0, 1.15
        p = np.array([-3.5, -2.75, 0.0])
        wall_y = p[1] + D * S
        half = np.radians(33.4)
        angs = np.linspace(-half, half, 9)
        title = T("Fisheye: a flat wall drawn from Euclidean distance", 28).to_edge(UP, buff=0.3)
        wall = Line([-6.3, wall_y, 0], [-0.7, wall_y, 0], color=C_WALL_EDGE, stroke_width=8)
        player = Dot(p, color=C_PLAYER, radius=0.1)
        rays = VGroup(*[Line(p, [p[0] + D * S * np.tan(a), wall_y, 0], color=C_RAY, stroke_width=2.5) for a in angs])
        perp = DashedLine(p, [p[0], wall_y, 0], color=C_DIR, stroke_width=3)
        l_perp = M(r"D", color=C_DIR, size=30).next_to(perp, LEFT, buff=0.1)
        edge_ray = rays[-1]
        l_euc = M(r"d=\frac{D}{\cos\theta}", color=C_RAY, size=28).move_to([p[0] + 1.9, p[1] + 1.25 + 0.0, 0])

        # screen columns, equal-angle spacing
        n, base = 21, -2.3
        a21 = np.linspace(-half, half, n)
        xs = 1.0 + (np.arange(n) + 0.5) * 0.27
        euc = [3.0 * np.cos(a) for a in a21]          # height ∝ 1/d = cosθ / D
        flat = [3.0 for _ in a21]

        def bars(hs, col):
            return VGroup(*[Rectangle(width=0.25, height=h, stroke_width=0, fill_color=col, fill_opacity=0.9)
                            .move_to([x, base + h / 2, 0]) for x, h in zip(xs, hs)])

        b1, b2 = bars(euc, C_BAD), bars(flat, C_GOOD)

        def top(hs):
            return VMobject(color=C_PLAYER, stroke_width=4).set_points_as_corners(
                [[x, base + h, 0] for x, h in zip(xs, hs)])

        t1, t2 = top(euc), top(flat)
        cap1 = T("height ∝ 1/d  →  edges shrink: the wall bows", 22, C_BAD).move_to([3.4, 1.9, 0])
        cap2 = T("height ∝ 1/D  →  flat, using D = d·cosθ", 22, C_GOOD).move_to([3.4, 1.9, 0])
        floor = Line([0.8, base, 0], [6.6, base, 0], color=C_DIM, stroke_width=2)

        self.play(FadeIn(title), Create(wall), FadeIn(player), run_time=1.0)
        self.play(LaggedStart(*[Create(r) for r in rays], lag_ratio=0.1), run_time=1.6)
        self.play(Create(perp), FadeIn(l_perp), FadeIn(l_euc), run_time=1.0)
        self.play(Create(floor), FadeIn(b1), Create(t1), FadeIn(cap1), run_time=1.6)
        self.wait(0.8)
        self.play(ReplacementTransform(b1, b2), ReplacementTransform(t1, t2), ReplacementTransform(cap1, cap2),
                  run_time=1.6)
        note = T("fix: one extra cos per ray  (or use vectors →)", 20, C_DIM).move_to([3.4, -3.35, 0])
        self.play(FadeIn(note), run_time=0.8)
        self.wait(1.4)
