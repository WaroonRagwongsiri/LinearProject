import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.style import *


class PlayerMotion(Scene):
    """Forward = d, strafe = J d (a 90° rotation of d), turning = R(α) on the camera matrix."""

    def construct(self):
        S = 1.25
        px, py, ang = ValueTracker(-3.6), ValueTracker(-2.7), ValueTracker(0.0)
        P = lambda: np.array([px.get_value(), py.get_value(), 0.0])
        dvec = lambda: np.array([np.sin(ang.get_value()), np.cos(ang.get_value()), 0.0])      # N-facing d rotated by α
        jvec = lambda: np.array([np.cos(ang.get_value()), -np.sin(ang.get_value()), 0.0])    # J d  (strafe right)
        title = T("Moving = adding multiples of the camera basis", 28).to_edge(UP, buff=0.3)
        player = always_redraw(lambda: Dot(P(), color=C_PLAYER, radius=0.11))
        d_arr = always_redraw(lambda: Arrow(P(), P() + dvec() * S, buff=0, color=C_DIR, stroke_width=6))
        j_arr = always_redraw(lambda: Arrow(P(), P() + jvec() * S, buff=0, color=C_PLANE, stroke_width=6))
        d_lab = M(r"\vec d", color=C_DIR, size=28)
        d_lab.add_updater(lambda m: m.move_to(P() + dvec() * S * 0.55 - jvec() * 0.3))
        j_lab = M(r"J\vec d", color=C_PLANE, size=28)
        j_lab.add_updater(lambda m: m.move_to(P() + jvec() * S * 0.6 - dvec() * 0.3))
        trace = TracedPath(P, stroke_color=C_PLAYER, stroke_width=3, stroke_opacity=0.55)
        rx = 1.0
        f = VGroup(
            M(r"\texttt{W}:\ \ \vec p\leftarrow\vec p+s\,\vec d", size=30, color=C_DIR),
            M(r"\texttt{D}:\ \ \vec p\leftarrow\vec p+s\,J\vec d,\quad J=\begin{bmatrix}0&-1\\1&0\end{bmatrix}", size=30, color=C_PLANE),
            M(r"\vec P=0.66\,J\vec d\ \Rightarrow\ \text{strafe}\parallel\text{camera plane}", size=26),
            M(r"\texttt{W+D}:\ |s(\vec d+J\vec d)|=\sqrt2\,s\ \ \text{(not normalised)}", size=26, color=C_BAD),
            M(r"s=\Delta t\cdot\texttt{MOVE\_SPEED}\ (3.0\ \text{cells/s})", size=26, color=C_DIM),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.42).move_to([rx + 2.9, 0.4, 0])
        step = 1.0

        self.play(FadeIn(title), run_time=0.6)
        self.add(trace, player, d_arr, j_arr, d_lab, j_lab)
        self.play(FadeIn(f[0]), run_time=0.6)
        self.play(py.animate.set_value(py.get_value() + step * S), run_time=1.2)                      # W (d = up)
        self.play(FadeIn(f[1]), run_time=0.6)
        self.play(px.animate.set_value(px.get_value() + step * S), run_time=1.2)                      # D
        self.play(FadeIn(f[2]), run_time=0.6)
        start = P().copy()
        ghost = Arrow(start, start + (dvec() + jvec()) * S, buff=0, color=C_BAD, stroke_width=5)
        self.play(GrowArrow(ghost), FadeIn(f[3]), run_time=1.0)
        self.play(px.animate.set_value(start[0] + S), py.animate.set_value(start[1] + S), run_time=1.2)
        self.play(FadeOut(ghost), FadeIn(f[4]), run_time=0.6)
        self.play(ang.animate.set_value(0.9), run_time=2.0)
        self.play(px.animate.set_value(px.get_value() + np.sin(0.9) * S * 1.0),
                  py.animate.set_value(py.get_value() + np.cos(0.9) * S * 1.0), run_time=1.6)   # W again, along the NEW d
        self.wait(1.0)


class Collision(Scene):
    """player_try_move: test x and y separately, so the player slides along walls."""

    def construct(self):
        grid = [list("111111"), list("100001"), list("100001"), list("111111")]
        W = World(grid, cell=1.0, top_left=(-6.8, 2.6))
        gm = W.build_map()
        title = T("Collision: four corners, one axis at a time", 28).to_edge(UP, buff=0.3)
        p = np.array([2.3, 1.45])
        dx, dy = 0.45, -0.4
        m = 0.2
        box = lambda q, col: Square(2 * m * W.cell, color=col, stroke_width=3, fill_opacity=0.25, fill_color=col).move_to(W.pt(*q))
        b0 = box(p, C_PLAYER)
        corners = lambda q, col: VGroup(*[Dot(W.pt(q[0] + sx * m, q[1] + sy * m), radius=0.05, color=col)
                                          for sx in (-1, 1) for sy in (-1, 1)])
        want = Arrow(W.pt(*p), W.pt(p[0] + dx, p[1] + dy), buff=0, color=C_BAD, stroke_width=4)
        want_l = T("wanted move", 18, C_BAD).move_to(W.pt(p[0] + 0.45, p[1] - 0.6))
        bx = box((p[0] + dx, p[1]), C_GOOD)
        by = box((p[0] + dx, p[1] + dy), C_BAD)
        cx, cy = corners((p[0] + dx, p[1]), C_GOOD), corners((p[0] + dx, p[1] + dy), C_BAD)
        ax = Arrow(W.pt(*p), W.pt(p[0] + dx, p[1]), buff=0, color=C_GOOD, stroke_width=6)
        rx = 0.6
        code = VGroup(
            T("player_try_move():", 20, C_DIM),
            T("if (position_is_open(x + dx, y))    x += dx;", 19, C_GOOD),
            T("if (position_is_open(x, y + dy))    y += dy;", 19, C_BAD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([rx + 2.6, 1.9, 0])
        t1 = M(r"\text{test}\ (x+dx,\ y):\ \text{all 4 corners in open cells}\ \checkmark", size=24, color=C_GOOD).move_to([rx + 2.6, 0.6, 0])
        t2 = M(r"\text{test}\ (x,\ y+dy):\ \text{2 corners in a wall cell}\ \times", size=24, color=C_BAD).move_to([rx + 2.6, -0.3, 0])
        t3 = M(r"\text{result: slide}\ (dx,\ 0)\ \text{instead of sticking}", size=26).move_to([rx + 2.6, -1.4, 0])
        m_lab = M(r"\text{corners at }\pm 0.2\ \text{(WALL\_MARGIN)}", size=22, color=C_DIM).move_to([rx + 2.6, -2.3, 0])

        self.play(FadeIn(title), FadeIn(gm), FadeIn(b0), FadeIn(corners(p, C_PLAYER)), run_time=1.0)
        self.play(GrowArrow(want), FadeIn(want_l), FadeIn(code), run_time=1.0)
        self.play(FadeIn(bx), FadeIn(cx), Write(t1), run_time=1.3)
        self.play(GrowArrow(ax), run_time=0.7)
        self.play(FadeIn(by), FadeIn(cy), Write(t2), run_time=1.3)
        self.play(Write(t3), FadeIn(m_lab), run_time=1.2)
        self.play(FadeOut(by), FadeOut(cy), FadeOut(want), FadeOut(want_l), b0.animate.move_to(W.pt(p[0] + dx, p[1])), run_time=1.0)
        self.wait(1.2)
