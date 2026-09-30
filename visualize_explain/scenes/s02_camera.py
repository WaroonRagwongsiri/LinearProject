import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.style import *

S = 1.75                                   # screen units per world unit
P0 = np.array([-3.6, -1.55, 0.0])          # player position (screen coords)


def readout(label, tracker_fn, anchor, places=2, color=C_TEXT, sign=True):
    lab = T(label, 26, color=C_DIM).move_to(anchor, aligned_edge=LEFT)
    num = DecimalNumber(0, num_decimal_places=places, include_sign=sign, font_size=30, color=color)
    num.add_updater(lambda m: (m.set_value(tracker_fn()),
                               m.move_to(lab.get_right() + RIGHT * 0.15, aligned_edge=LEFT)))
    num.update()            # settle digits/position now so FadeIn sees the final shape
    return lab, num


class CameraBasis(Scene):
    """r = d + c P  is a matrix-vector product:  r = [d | P] (1, c)^T."""

    def construct(self):
        c, k = ValueTracker(-1.0), ValueTracker(0.66)
        d_end = P0 + UP * S
        tip = lambda: d_end + RIGHT * S * k.get_value() * c.get_value()

        title = T("The camera is a 2-column matrix", 30).to_edge(UP, buff=0.3)
        player = Dot(P0, color=C_PLAYER, radius=0.11)
        d_arr = Arrow(P0, d_end, buff=0, color=C_DIR, stroke_width=6)
        d_lab = M(r"\vec d", color=C_DIR).next_to(d_arr, LEFT, buff=0.12)
        plane = always_redraw(lambda: Line(d_end - RIGHT * S * k.get_value(),
                                           d_end + RIGHT * S * k.get_value(),
                                           color=C_PLANE, stroke_width=3, stroke_opacity=0.55))
        p_arr = always_redraw(lambda: Arrow(d_end, d_end + RIGHT * S * k.get_value(), buff=0,
                                            color=C_PLANE, stroke_width=6))
        p_lab = M(r"\vec P", color=C_PLANE)
        p_lab.add_updater(lambda m: m.move_to(d_end + RIGHT * S * k.get_value() * 0.5 + DOWN * 0.3))
        ray = always_redraw(lambda: Arrow(P0, tip(), buff=0, color=C_RAY, stroke_width=4))
        ray_ext = always_redraw(lambda: DashedLine(tip(), P0 + (tip() - P0) * 1.75, color=C_RAY,
                                                   stroke_opacity=0.45, dash_length=0.12))
        tip_dot = always_redraw(lambda: Dot(tip(), color=C_RAY, radius=0.07))
        ray_lab = M(r"\vec r", color=C_RAY)
        ray_lab.add_updater(lambda m: m.move_to(P0 + (tip() - P0) * 0.55 + LEFT * 0.28 * np.sign(c.get_value() + 1e-9) * -1
                                                + UP * 0.05))
        note = T("P ⟂ d", 22, color=C_DIM).next_to(P0, DOWN, buff=0.22)

        # screen strip: pixel column x  <->  camera_x = c
        sx0, sx1, sy = -6.3, -0.9, -3.25
        strip = Line([sx0, sy, 0], [sx1, sy, 0], color=C_DIM, stroke_width=3)
        ticks = VGroup(*[Line([sx0 + (sx1 - sx0) * f, sy - 0.1, 0], [sx0 + (sx1 - sx0) * f, sy + 0.1, 0],
                              color=C_DIM, stroke_width=2) for f in np.linspace(0, 1, 9)])
        s_lab = VGroup(T("x = 0", 20, C_DIM).next_to(strip.get_left(), DOWN, buff=0.22),
                       T("x = W−1", 20, C_DIM).next_to(strip.get_right(), DOWN, buff=0.22),
                       T("screen columns", 20, C_DIM).next_to(strip, DOWN, buff=0.22))
        marker = always_redraw(lambda: Triangle(color=C_RAY, fill_opacity=1, stroke_width=0)
                               .scale(0.11).rotate(PI)
                               .move_to([sx0 + (sx1 - sx0) * (c.get_value() + 1) / 2, sy + 0.2, 0]))

        # equations (right panel)
        rx = 1.0
        eq1 = M(r"\vec r \;=\; \vec d + c\,\vec P", tex_to_color_map={r"\vec d": C_DIR, r"\vec P": C_PLANE, r"\vec r": C_RAY}) \
            .move_to([rx + 2.7, 2.6, 0])
        eq2 = M(r"=\begin{bmatrix}\vec d & \vec P\end{bmatrix}\begin{bmatrix}1\\ c\end{bmatrix}",
                tex_to_color_map={r"\vec d": C_DIR, r"\vec P": C_PLANE}).next_to(eq1, DOWN, buff=0.35, aligned_edge=LEFT)
        eq3 = M(r"=\begin{bmatrix}0 & 0.66\\ -1 & 0\end{bmatrix}\begin{bmatrix}1\\ c\end{bmatrix}") \
            .next_to(eq2, DOWN, buff=0.35, aligned_edge=LEFT)
        eq3_note = T("N-facing: d=(0,−1), P=(0.66,0)", 17, C_DIM).next_to(eq3, DOWN, buff=0.15, aligned_edge=LEFT)

        l_c, n_c = readout("c =", c.get_value, [rx, -1.0, 0], color=C_RAY)
        l_x, n_x = readout("x =", lambda: (c.get_value() + 1) * 640, [rx + 2.6, -1.0, 0], places=0, color=C_RAY, sign=False)
        l_rx, n_rx = readout("r =  (", lambda: 0.66 * c.get_value(), [rx, -1.65, 0], color=C_RAY)
        n_rx.clear_updaters()
        n_rx.add_updater(lambda m: (m.set_value(k.get_value() * c.get_value()),
                                    m.move_to(l_rx.get_right() + RIGHT * 0.15, aligned_edge=LEFT)))
        l_ry, n_ry = readout(",", lambda: -1.0, [rx + 2.1, -1.65, 0], color=C_RAY)
        close = T(")", 26, C_DIM).move_to([rx + 3.75, -1.65, 0])
        l_ry.add_updater(lambda m: m.move_to(n_rx.get_right() + RIGHT * 0.2))
        n_ry.clear_updaters()
        n_ry.add_updater(lambda m: (m.set_value(-1.0), m.move_to(l_ry.get_right() + RIGHT * 0.15, aligned_edge=LEFT)))
        close.add_updater(lambda m: m.move_to(n_ry.get_right() + RIGHT * 0.15))
        for m_ in (n_rx, l_ry, n_ry, close):
            m_.update()

        fov = always_redraw(lambda: Angle(Line(P0, d_end + RIGHT * S * k.get_value()),
                                          Line(P0, d_end - RIGHT * S * k.get_value()),
                                          radius=0.8, color=C_PLAYER, stroke_width=4))
        edges = always_redraw(lambda: VGroup(
            DashedLine(P0, d_end + RIGHT * S * k.get_value(), color=C_PLAYER, stroke_opacity=0.6, dash_length=0.1),
            DashedLine(P0, d_end - RIGHT * S * k.get_value(), color=C_PLAYER, stroke_opacity=0.6, dash_length=0.1)))
        l_fov, n_fov = readout("FOV =", lambda: 2 * np.degrees(np.arctan(k.get_value())), [rx, -2.45, 0],
                               places=1, color=C_PLAYER, sign=False)
        deg = T("°", 26, C_PLAYER)
        deg.add_updater(lambda m: m.move_to(n_fov.get_right() + RIGHT * 0.12))
        l_k, n_k = readout("|P| =", k.get_value, [rx + 3.3, -2.45, 0], color=C_PLANE, sign=False)
        fov_eq = M(r"\mathrm{FOV}=2\arctan\frac{|\vec P|}{|\vec d|}", size=30, color=C_PLAYER) \
            .move_to([rx + 2.6, -3.3, 0])

        # ---------------- timeline ----------------
        self.play(FadeIn(title), FadeIn(player), GrowArrow(d_arr), FadeIn(d_lab), run_time=1.2)
        self.play(Create(plane), GrowArrow(p_arr), FadeIn(p_lab), FadeIn(note), run_time=1.2)
        self.play(Write(eq1), run_time=0.9)
        self.play(Write(eq2), run_time=1.0)
        self.play(Write(eq3), FadeIn(eq3_note), run_time=1.0)
        self.play(Create(strip), FadeIn(ticks), FadeIn(s_lab), run_time=0.8)
        self.add(ray, ray_ext, tip_dot, marker, ray_lab)
        self.play(FadeIn(l_c), FadeIn(n_c), FadeIn(l_x), FadeIn(n_x), FadeIn(l_rx), FadeIn(n_rx),
                  FadeIn(l_ry), FadeIn(n_ry), FadeIn(close), run_time=0.6)
        self.play(c.animate.set_value(1.0), run_time=5, rate_func=linear)
        self.play(c.animate.set_value(0.0), run_time=1.2)
        self.add(edges, fov)
        self.play(FadeIn(l_fov), FadeIn(n_fov), FadeIn(deg), FadeIn(l_k), FadeIn(n_k), Write(fov_eq), run_time=1.0)
        self.wait(0.6)
        self.play(k.animate.set_value(1.0), run_time=2.0)
        self.play(k.animate.set_value(0.33), run_time=2.4)
        self.play(k.animate.set_value(0.66), run_time=1.6)
        self.wait(0.8)


class RotateCamera(Scene):
    """Turning the player = left-multiplying the camera matrix by a rotation R(a)."""

    def construct(self):
        ang = ValueTracker(0.0)
        S2 = 1.9
        P0b = np.array([-4.2, -1.3, 0.0])

        def dvec(a):       # N-facing d rotated by a (y-down: screen y flipped)
            return np.array([np.sin(a), np.cos(a), 0.0]) * S2

        def pvec(a):       # P = 0.66 * (-d_y, d_x)  ->  world (0.66cos a, 0.66 sin a) -> screen flip y
            return np.array([np.cos(a), -np.sin(a), 0.0]) * 0.66 * S2

        title = T("Turning = one matrix product on both columns", 30).to_edge(UP, buff=0.3)
        player = Dot(P0b, color=C_PLAYER, radius=0.11)
        d_arr = always_redraw(lambda: Arrow(P0b, P0b + dvec(ang.get_value()), buff=0, color=C_DIR, stroke_width=6))
        p_arr = always_redraw(lambda: Arrow(P0b + dvec(ang.get_value()),
                                            P0b + dvec(ang.get_value()) + pvec(ang.get_value()),
                                            buff=0, color=C_PLANE, stroke_width=6))
        p_neg = always_redraw(lambda: Line(P0b + dvec(ang.get_value()),
                                           P0b + dvec(ang.get_value()) - pvec(ang.get_value()),
                                           color=C_PLANE, stroke_width=3, stroke_opacity=0.5))
        d_lab = M(r"\vec d", color=C_DIR)
        d_lab.add_updater(lambda m: m.move_to(P0b + dvec(ang.get_value()) * 0.5 + np.array([-0.3, 0.0, 0.0])))
        p_lab = M(r"\vec P", color=C_PLANE)
        p_lab.add_updater(lambda m: m.move_to(P0b + dvec(ang.get_value()) + pvec(ang.get_value()) * 0.5
                                              + np.array([0.0, -0.3, 0.0])))
        # old (dashed) pose for reference
        ghost = VGroup(Arrow(P0b, P0b + dvec(0), buff=0, color=C_DIM, stroke_width=3),
                       Line(P0b + dvec(0) - pvec(0), P0b + dvec(0) + pvec(0), color=C_DIM, stroke_width=2))
        arc = always_redraw(lambda: Arc(radius=0.7, start_angle=PI / 2, angle=-ang.get_value(), arc_center=P0b,
                                        color=C_PLAYER, stroke_width=4))
        a_lab = M(r"\alpha", color=C_PLAYER, size=30).move_to(P0b + np.array([0.35, 0.95, 0]))

        # right panel: R * [d | P] = [d' | P']
        rx = 0.5
        Rm = M(r"R(\alpha)=\begin{bmatrix}\cos\alpha & -\sin\alpha\\ \sin\alpha & \cos\alpha\end{bmatrix}", size=34) \
            .move_to([rx + 3.2, 2.35, 0])
        big = M(r"\underbrace{\begin{bmatrix}d'_x & P'_x\\ d'_y & P'_y\end{bmatrix}}_{\text{new camera}}"
                r"=R(\alpha)\underbrace{\begin{bmatrix}d_x & P_x\\ d_y & P_y\end{bmatrix}}_{\text{old camera}}", size=30) \
            .move_to([rx + 3.2, 0.75, 0])
        code = VGroup(
            T("player_rotate()  (C):", 19, C_DIM),
            T("dir_x   = old_dir_x*cos − dir_y*sin", 18, C_DIR),
            T("dir_y   = old_dir_x*sin + dir_y*cos", 18, C_DIR),
            T("plane_x = old_plane_x*cos − plane_y*sin", 18, C_PLANE),
            T("plane_y = old_plane_x*sin + plane_y*cos", 18, C_PLANE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([rx + 3.0, -1.2, 0])
        keep = VGroup(M(r"|\vec d|,\ |\vec P|\ \text{unchanged}", size=26, color=C_TEXT),
                      M(r"\vec d\cdot\vec P=0\ \text{still}", size=26, color=C_TEXT)) \
            .arrange(RIGHT, buff=0.6).move_to([rx + 3.2, -3.1, 0])
        a_val = DecimalNumber(0, num_decimal_places=2, font_size=28, color=C_PLAYER)
        a_val_lab = T("α =", 24, C_DIM).move_to([-6.4, -3.3, 0])
        a_val.add_updater(lambda m: m.move_to(a_val_lab.get_right() + RIGHT * 0.15, aligned_edge=LEFT).set_value(ang.get_value()))
        rad = T("rad", 22, C_DIM)
        rad.add_updater(lambda m: m.move_to(a_val.get_right() + RIGHT * 0.3))

        self.play(FadeIn(title), FadeIn(player), run_time=0.8)
        self.add(d_arr, p_arr, p_neg, d_lab, p_lab)
        self.play(FadeIn(ghost), Write(Rm), run_time=1.4)
        self.play(Write(big), run_time=1.6)
        self.play(FadeIn(code), run_time=1.0)
        self.add(arc, a_lab, a_val, a_val_lab, rad)
        self.play(ang.animate.set_value(0.9), run_time=2.6)
        self.play(ang.animate.set_value(-0.7), run_time=3.0)
        self.play(ang.animate.set_value(0.35), run_time=2.0)
        self.play(FadeIn(keep), run_time=0.8)
        self.wait(1.0)
