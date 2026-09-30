import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.style import *

C_I = "#e6e9f2"


class StepFormula(Scene):
    """Still picture: what each symbol of  p_i = p + i*eps*(cos t, sin t)  is on the map (y grows downward)."""

    def construct(self):
        grid = [list("00000") for _ in range(4)]
        W = World(grid, cell=1.2, top_left=(-6.8, 2.9))
        th = np.radians(30.0)
        u = np.array([np.cos(th), np.sin(th)])            # (cos t, sin t), length 1
        p = np.array([0.8, 1.2])
        eps = 0.4                                         # drawn large; the game uses 0.1
        P = lambda q: W.pt(*q)

        self.add(W.build_map())
        # the unit direction as a right triangle: cos = across, sin = down
        leg_x = DashedLine(P(p), P(p + [u[0], 0]), color=C_DIR, stroke_width=3)
        leg_y = DashedLine(P(p + [u[0], 0]), P(p + u), color=C_DIR, stroke_width=3)
        arrow = Arrow(P(p), P(p + u), buff=0, color=C_DIR, stroke_width=5, tip_length=0.18, max_tip_length_to_length_ratio=0.3)
        arc = Arc(radius=0.5, start_angle=0, angle=-th, arc_center=P(p), color=C_DIR, stroke_width=3)
        t_lab = M(r"\theta", size=24, color=C_DIR).move_to(P(p) + np.array([0.26, 0.24, 0]))
        c_lab = M(r"\cos\theta", size=24, color=C_DIR).move_to(P(p + [u[0] / 2 + 0.12, 0]) + np.array([0.22, 0.25, 0]))
        s_lab = M(r"\sin\theta", size=24, color=C_DIR).next_to(P(p + [u[0], u[1] / 2]), RIGHT, buff=0.12)
        self.add(leg_x, leg_y, arrow, arc, t_lab, c_lab, s_lab)

        # the stepping points p_1, p_2, ... spaced eps apart along the same direction
        dots = VGroup(*[Dot(P(p + i * eps * u), color=C_RAY, radius=0.075) for i in range(1, 9)])
        self.add(dots)
        for i in (1, 2, 3):
            self.add(M(rf"\vec p_{i}", size=22, color=C_RAY).move_to(P(p + i * eps * u) + np.array([-0.05, -0.36, 0])))
        a, b = P(p + 4 * eps * u), P(p + 5 * eps * u)
        self.add(Line(a, b, color=C_Y, stroke_width=7))
        self.add(M(r"\varepsilon", size=28, color=C_Y).move_to((a + b) / 2 + np.array([0.0, 0.36, 0])))
        self.add(Dot(P(p), color=C_PLAYER, radius=0.11))
        self.add(M(r"\vec p", size=28, color=C_PLAYER).move_to(P(p) + np.array([-0.3, 0.3, 0])))

        # the formula, each part in the colour used in the picture
        f = MathTex(r"\vec p_i", "=", r"\vec p", "+", "i", r"\varepsilon",
                    r"\begin{bmatrix}\cos\theta\\ \sin\theta\end{bmatrix}", font_size=40, color=C_TEXT)
        for part, col in zip(f, [C_RAY, C_TEXT, C_PLAYER, C_TEXT, C_I, C_Y, C_DIR]):
            part.set_color(col)
        f.move_to([3.3, 2.45, 0])
        self.add(f)

        rows = [
            (r"\vec p", C_PLAYER, "where the player stands"),
            ("i", C_I, "step number: 1, 2, 3, …"),
            (r"\varepsilon", C_Y, "length of one step (0.1 cell)"),
            (r"\cos\theta", C_DIR, "across, per 1 of walking"),
            (r"\sin\theta", C_DIR, "down, per 1 of walking"),
            (r"\vec p_i", C_RAY, "the point after i steps"),
        ]
        y = 1.15
        for sym, col, txt in rows:
            s = M(sym, size=30, color=col)
            d = T(txt, 20, C_TEXT)
            s.move_to([0.45 + 0.45, y, 0])
            d.move_to([1.75, y, 0], aligned_edge=LEFT)
            self.add(s, d)
            y -= 0.62
        self.add(T("(the picture draws ε larger than the real 0.1 so the dots are visible;  y grows downward)", 16, C_DIM)
                 .move_to([0.0, -3.45, 0]))
        self.wait(0.1)
