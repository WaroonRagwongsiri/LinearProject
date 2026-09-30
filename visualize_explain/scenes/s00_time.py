import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.style import *
from common import budget as B

CLOCK = 33e6                        # 386DX at 33 MHz


def fmt(t):
    return f"{t:.1f} s" if t >= 1 else (f"{t * 1000:.0f} ms" if t >= 0.1 else f"{t * 1000:.1f} ms")


class TimePerPicture(Scene):
    """How long ONE picture takes on a 386 at 33 MHz, for each way of casting rays (log axis)."""

    def construct(self):
        r = B.summary()
        allowed = 1 / B.FPS
        rows = [
            ("per pixel, steps of 0.01", r["naive_0.01"]["per_frame"] / CLOCK, C_BAD),
            ("per pixel, steps of 0.1", r["naive_0.1"]["per_frame"] / CLOCK, C_BAD),
            ("per column, steps of 0.01", r["naive_0.01"]["per_frame_cols"] / CLOCK, C_Y),
            ("per column, steps of 0.1", r["naive_0.1"]["per_frame_cols"] / CLOCK, C_Y),
            ("raycasting (vectors + DDA)", r["dda_frame"] / CLOCK, C_GOOD),
        ]
        X0, LEN, LO, HI = -2.6, 5.2, -3.0, 2.0
        pos = lambda t: X0 + LEN * (np.log10(t) - LO) / (HI - LO)

        title = T("Time to draw ONE picture on a 386 (33 MHz): one line per …", 26).to_edge(UP, buff=0.3)
        self.play(FadeIn(title))

        ay = -1.75
        axis = Line([X0, ay, 0], [X0 + LEN, ay, 0], color=C_DIM, stroke_width=2)
        ticks = VGroup()
        for e, name in zip(range(-3, 3), ["1 ms", "10 ms", "0.1 s", "1 s", "10 s", "100 s"]):
            x = pos(10.0 ** e)
            ticks.add(Line([x, ay, 0], [x, ay - 0.12, 0], color=C_DIM, stroke_width=2))
            ticks.add(T(name, 17, C_DIM).move_to([x, ay - 0.42, 0]))
        self.play(Create(axis), FadeIn(ticks), run_time=0.8)

        ax = pos(allowed)
        line = DashedLine([ax, 2.55, 0], [ax, ay, 0], color=C_PLANE, stroke_width=4, dash_length=0.12)
        lab = T("time allowed: 14 ms  (70 pictures per second)", 20, C_PLANE).move_to([ax + 0.15, 2.85, 0], aligned_edge=LEFT)
        self.play(Create(line), FadeIn(lab), run_time=0.9)

        objs = []
        for i, (name, t, col) in enumerate(rows):
            y = 2.0 - i * 0.78
            l = T(name, 19, col).move_to([-6.9, y, 0], aligned_edge=LEFT)
            bar = Rectangle(width=max(pos(t) - X0, 0.05), height=0.46, stroke_width=0, fill_color=col, fill_opacity=0.9) \
                .move_to([X0, y, 0], aligned_edge=LEFT)
            ratio = t / allowed
            verdict = "fits" if ratio < 1 else (f"{ratio:,.0f}× too slow" if ratio >= 10 else f"{ratio:.1f}× too slow")
            num = T(f"{fmt(t)}  ·  {verdict}", 19, col).move_to([6.9, y, 0], aligned_edge=RIGHT)
            objs.append((l, bar, num))

        for grp in (objs[0:2], objs[2:4], objs[4:5]):
            self.play(*[FadeIn(l) for l, *_ in grp], run_time=0.4)
            self.play(*[GrowFromEdge(b, LEFT) for _, b, _ in grp], run_time=1.4)
            self.play(*[FadeIn(n) for *_, n in grp], run_time=0.4)
            self.wait(0.5)

        cap = VGroup(
            T("Only the last one is fast enough. It combines three savings:", 22, C_TEXT),
            T("200× fewer lines  ·  about 8 checks per line instead of 59  ·  no sin / cos", 20, C_DIM),
        ).arrange(DOWN, buff=0.15).move_to([0, -3.35, 0])
        self.play(FadeIn(cap, shift=UP * 0.2))
        self.wait(2.0)
