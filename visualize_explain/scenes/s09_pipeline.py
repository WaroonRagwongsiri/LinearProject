import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.style import *
from common import raycast as rc


class Pipeline(Scene):
    """render_frame(): the same five calls for every one of the 1280 columns (real numbers for 3 columns)."""

    def construct(self):
        grid, (sx, sy, c) = rc.load_grid(rc.DEMO_MAP)
        p = rc.spawn(sx, sy, c)
        rc.rotate(p, -0.2)
        names = ["ray_init", "ray_dda", "ray_project", "ray_set_texture", "draw_column"]
        cols = [C_RAY, C_X, C_GOOD, C_PLANE, C_PLAYER]
        bw, gap = 2.3, 0.33
        x0 = -6.4 + bw / 2
        boxes = VGroup()
        for i, n in enumerate(names):
            b = RoundedRectangle(corner_radius=0.12, width=bw, height=0.8, stroke_color=cols[i], stroke_width=3)
            b.move_to([x0 + i * (bw + gap), 1.7, 0])
            b.add(T(n, 20, cols[i]).move_to(b))
            boxes.add(b)
        arrows = VGroup(*[Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.03, stroke_width=3, color=C_DIM,
                                max_tip_length_to_length_ratio=0.5) for i in range(4)])
        title = T("One frame = 1280 columns x five calls", 28).to_edge(UP, buff=0.3)
        loop = T("for (x = 0; x < WIDTH; x++)", 22, C_DIM).move_to([-4.2, 2.8, 0])
        title.move_to([0, 3.6, 0])

        def rows(x):
            r = rc.cast(grid, p, x)
            return [
                [f"camera_x = {r.camera_x:+.3f}", f"dir = ({r.dir_x:+.2f}, {r.dir_y:+.2f})", f"Δt = ({r.delta_dist_x:.2f}, {r.delta_dist_y:.2f})"],
                [f"{len(r.trace)} grid steps", f"cell = ({r.map_x}, {r.map_y})", f"side = {r.side}"],
                [f"wall_dist = {r.wall_dist:.3f}", f"line_height = {r.line_height}", f"rows {r.draw_start}..{r.draw_end}"],
                [f"wall_x = {r.wall_x:.3f}", f"tex_x = {r.texture_x}", f"texture #{r.texture_index}"],
                ["ceiling  [0, start)", "wall  [start, end]", "floor  (end, H)"],
            ], r

        self.play(FadeIn(title), FadeIn(loop), LaggedStart(*[FadeIn(b) for b in boxes], lag_ratio=0.15), FadeIn(arrows), run_time=1.6)
        xlab = T("x =", 26, C_DIM).move_to([-0.3, 2.8, 0], aligned_edge=LEFT)
        self.add(xlab)
        prev = VGroup(); prev_x = None
        for x in (0, 400, 1279):
            data, r = rows(x)
            xn = Integer(x, font_size=30, color=C_RAY).next_to(xlab, RIGHT, buff=0.15)
            outs = VGroup()
            for i, lines in enumerate(data):
                g = VGroup(*[T(s, 18, cols[i]) for s in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
                g.next_to(boxes[i], DOWN, buff=0.35)
                g.align_to(boxes[i], LEFT)
                outs.add(g)
            anims = [FadeOut(prev), FadeOut(prev_x)] if prev_x is not None else []
            self.play(*anims, FadeIn(xn), run_time=0.4)
            for i in range(5):
                self.play(Indicate(boxes[i], color=cols[i], scale_factor=1.06), FadeIn(outs[i], shift=DOWN * 0.15), run_time=0.55)
            self.wait(0.5)
            prev, prev_x = outs, xn
        cost = VGroup(
            M(r"\text{per column: }\ 0\ \text{trig},\ 0\ \text{sqrt},\ \le |\Delta m_x|+|\Delta m_y|\ \text{grid steps}", size=28, color=C_GOOD),
            M(r"\text{per frame: trig only in}\ \texttt{player\_rotate}\ (\cos\alpha,\sin\alpha)", size=26, color=C_DIM),
        ).arrange(DOWN, buff=0.3).move_to([0, -2.9, 0])
        self.play(FadeIn(cost, shift=UP * 0.2), run_time=1.0)
        self.wait(1.8)
