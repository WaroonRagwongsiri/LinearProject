import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.style import *


class PerpDistance(Scene):
    """d·r = 1 for every column, so the ray parameter t IS the distance along the view axis."""

    def construct(self):
        S, D, k = 1.3, 3.0, 0.66
        p = np.array([-3.6, -3.2, 0.0])
        c = ValueTracker(-0.9)
        wall_y = p[1] + D * S
        d_end = p + UP * S
        wall = Line([-6.6, wall_y, 0], [-0.6, wall_y, 0], color=C_WALL_EDGE, stroke_width=8)
        player = Dot(p, color=C_PLAYER, radius=0.1)
        d_arr = Arrow(p, d_end, buff=0, color=C_DIR, stroke_width=6)
        plane = Line(d_end + LEFT * S * k, d_end + RIGHT * S * k, color=C_PLANE, stroke_width=5)
        axis = DashedLine(d_end, [p[0], wall_y, 0], color=C_DIR, stroke_width=3, stroke_opacity=0.8)
        tip = lambda: p + np.array([D * S * k * c.get_value(), D * S, 0])
        hit = always_redraw(lambda: Dot(tip(), color=C_RAY, radius=0.08))
        ray = always_redraw(lambda: Line(p, tip(), color=C_RAY, stroke_width=4))
        # projection of the hit onto the view axis  (horizontal dashed "drop")
        drop = always_redraw(lambda: DashedLine(tip(), [p[0], wall_y, 0], color=C_DIM, stroke_width=2))
        foot = Dot([p[0], wall_y, 0], color=C_DIR, radius=0.07)
        l_perp = M(r"t=\vec d\cdot(t\vec r)", color=C_DIR, size=26).move_to([p[0] - 0.95, p[1] + 2.25, 0])
        l_euc = M(r"t\,|\vec r|", color=C_RAY, size=26)
        l_euc.add_updater(lambda m: m.move_to(p + (tip() - p) * 0.5 + np.array([0.75 * np.sign(c.get_value() + 1e-9), -0.1, 0])))

        title = T("Perpendicular distance comes for free", 28).to_edge(UP, buff=0.3)
        rx = 1.0
        e1 = M(r"\vec d\cdot\vec r=\vec d\cdot\vec d+c\,(\vec d\cdot\vec P)=1+0=1", size=30).move_to([rx + 2.8, 2.35, 0])
        e2 = M(r"\text{Euclid}=t\,|\vec r|=\dfrac{t}{\cos\theta}\qquad \text{perp}=\dfrac{\vec d\cdot(t\vec r)}{|\vec d|}=t",
               size=28).move_to([rx + 2.8, 1.0, 0])
        e3 = M(r"\texttt{wall\_dist}=\text{side\_dist}-\Delta t = t", size=30, color=C_GOOD).move_to([rx + 2.8, -0.35, 0])
        e4 = T("no cos, no sqrt, no extra division", 24, C_GOOD).move_to([rx + 2.8, -1.05, 0])

        def num(label, fn, y, col, places=3):
            lab = T(label, 24, C_DIM).move_to([rx + 0.1, y, 0], aligned_edge=LEFT)
            n = DecimalNumber(0, num_decimal_places=places, font_size=28, color=col)
            n.add_updater(lambda m: m.set_value(fn()).move_to(lab.get_right() + RIGHT * 0.15, aligned_edge=LEFT))
            n.update()
            return lab, n
        r_len = lambda: np.sqrt(1 + (k * c.get_value()) ** 2)
        a1, b1 = num("camera_x  c =", c.get_value, -1.55, C_RAY, 2)
        a2, b2 = num("|r| =", r_len, -2.15, C_RAY)
        a3, b3 = num("Euclid t|r| =", lambda: D * r_len(), -2.75, C_BAD)
        a4, b4 = num("perp  t =", lambda: D, -3.35, C_GOOD)
        for b in (b1,):
            b.include_sign = True

        self.play(FadeIn(title), Create(wall), FadeIn(player), GrowArrow(d_arr), Create(plane), run_time=1.2)
        self.play(Create(axis), FadeIn(foot), run_time=0.6)
        self.add(ray, hit, drop, l_euc)
        self.play(FadeIn(l_perp), run_time=0.6)
        self.play(Write(e1), run_time=1.6)
        self.play(FadeIn(a1), FadeIn(b1), FadeIn(a2), FadeIn(b2), FadeIn(a3), FadeIn(b3), FadeIn(a4), FadeIn(b4), run_time=0.8)
        self.play(c.animate.set_value(0.9), run_time=4.0, rate_func=linear)
        self.play(Write(e2), run_time=1.6)
        self.play(c.animate.set_value(-0.5), run_time=2.0)
        self.play(Write(e3), FadeIn(e4), run_time=1.6)
        self.play(c.animate.set_value(0.3), run_time=1.6)
        self.wait(1.0)
