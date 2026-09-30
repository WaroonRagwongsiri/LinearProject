import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.style import *
from common import raycast as rc, frame
from PIL import Image


def px_image(arr, **kw):
    im = ImageMobject(arr, **kw)
    im.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
    return im


class TextureColumn(Scene):
    """wall_x -> tex_x (which texture column), then tex_step (how fast to walk down that column)."""

    def construct(self):
        tex = frame.load_textures()[1]                              # wall_2.png
        f, tx = 0.40, 25
        ex0, ex1, ey, tw = -6.4, -2.8, 1.75, 3.6
        title = T("Texture mapping: one texture column per screen column", 26).to_edge(UP, buff=0.3)
        edge = Line([ex0, ey, 0], [ex1, ey, 0], color=C_WALL_EDGE, stroke_width=8)
        lm = M(r"m", size=26, color=C_DIM).next_to([ex0, ey, 0], UP, buff=0.15)
        lm1 = M(r"m+1", size=26, color=C_DIM).next_to([ex1, ey, 0], UP, buff=0.15)
        Q = np.array([ex0 + (ex1 - ex0) * f, ey, 0])
        q_dot = Dot(Q, color=C_RAY, radius=0.09)
        hit_lab = T("ray hits the wall here", 18, C_RAY).next_to(Q, UP, buff=0.4)
        hit_arrow = Arrow(hit_lab.get_bottom(), Q + UP * 0.1, buff=0.05, color=C_RAY, stroke_width=3, tip_length=0.15)
        br = BraceBetweenPoints([ex0, ey, 0], Q, direction=DOWN, color=C_Y) if False else None
        wx_line = Line([ex0, ey - 0.25, 0], [Q[0], ey - 0.25, 0], color=C_Y, stroke_width=5)
        wx_lab = M(r"\texttt{wall\_x}=0.40", size=26, color=C_Y).move_to([ex0 + 0.9, ey - 0.6, 0])
        img = px_image(tex).scale_to_fit_width(tw).move_to([(ex0 + ex1) / 2, ey - 0.95 - tw / 2, 0])
        hl = Rectangle(width=0.13, height=tw, stroke_color=C_PLANE, stroke_width=2, fill_color=C_PLANE, fill_opacity=0.35)
        hl.move_to([ex0 + tw * (tx + 0.5) / 64, img.get_center()[1], 0])
        drop = DashedLine(Q, [Q[0], img.get_top()[1], 0], color=C_Y, stroke_width=2)
        f2 = M(r"\texttt{tex\_x}=\lfloor \texttt{wall\_x}\cdot 64\rfloor=25", size=28, color=C_PLANE).move_to([2.1, 2.0, 0])
        f1 = M(r"\texttt{wall\_x}=\mathrm{frac}\!\left(p_{\text{along}}+t\,r_{\text{along}}\right)", size=26).move_to([2.1, 0.95, 0])
        note = T("along = y for side 0 walls, x for side 1 walls", 16, C_DIM).move_to([2.1, 0.35, 0])

        # part B: stretch the chosen column to line_height rows
        col = tex[:, tx:tx + 1]
        strip = px_image(col).stretch_to_fit_width(0.45)
        strip.stretch_to_fit_height(0.01).move_to([5.7, -0.95, 0])
        H_SCR = 4.0
        box = Rectangle(width=0.6, height=H_SCR, color=C_DIM, stroke_width=2).move_to([5.7, -0.95, 0])
        l_box = T("screen column", 16, C_DIM).next_to(box, UP, buff=0.1)
        ts = M(r"\texttt{tex\_step}=\dfrac{64}{\texttt{line\_height}}", size=28, color=C_GOOD).move_to([2.1, -1.0, 0])
        ex1_ = M(r"\text{near: }\ \tfrac{64}{480}=0.13\ \text{texel per pixel}", size=24, color=C_TEXT).move_to([2.1, -2.0, 0])
        ex2_ = M(r"\text{far: }\ \tfrac{64}{120}=0.53\ \text{texel per pixel}", size=24, color=C_TEXT).move_to([2.1, -2.7, 0])
        arr = lambda lh: H_SCR * lh / 720

        self.play(FadeIn(title), Create(edge), FadeIn(lm), FadeIn(lm1), run_time=1.0)
        self.play(FadeIn(q_dot), FadeIn(hit_lab), GrowArrow(hit_arrow), run_time=0.8)
        self.play(Create(wx_line), FadeIn(wx_lab), FadeIn(img), run_time=1.2)
        self.play(Create(drop), FadeIn(hl), Write(f1), FadeIn(note), run_time=1.6)
        self.play(Write(f2), run_time=1.2)
        self.play(FadeIn(box), FadeIn(l_box), FadeIn(strip), Write(ts), run_time=1.0)
        self.play(strip.animate.stretch_to_fit_height(arr(480)), FadeIn(ex1_), run_time=1.6)
        self.wait(0.6)
        self.play(strip.animate.stretch_to_fit_height(arr(120)), FadeIn(ex2_), run_time=1.6)
        self.wait(1.2)


class MirrorFlip(Scene):
    """Still: the same view drawn with the C code's flip rule vs the swapped rule (asymmetric test texture)."""

    def construct(self):
        grid, _ = rc.load_grid(["1111111", "1000001", "1000001", "1000001", "1000001", "1111111"])
        p = rc.Player(3.5, 3.5, 0.0, -1.0, 0.66, 0.0)
        tt = frame.test_texture()
        a = frame.render(grid, p, 480, 270, [tt] * 4, fixed=False, shade=False)
        b = frame.render(grid, p, 480, 270, [tt] * 4, fixed=True, shade=False)
        ia = ImageMobject(np.array(a)).scale_to_fit_width(6.3).move_to([-3.5, 0.2, 0])
        ib = ImageMobject(np.array(b)).scale_to_fit_width(6.3).move_to([3.5, 0.2, 0])
        t1 = T("as written in ray_set_texture()", 24, C_BAD).next_to(ia, UP, buff=0.25)
        t2 = T("flip rule swapped", 24, C_GOOD).next_to(ib, UP, buff=0.25)
        c1 = T("red is on the RIGHT: image is mirrored", 22, C_BAD).next_to(ia, DOWN, buff=0.25)
        c2 = T("red on the LEFT, arrow points right", 22, C_GOOD).next_to(ib, DOWN, buff=0.25)
        head = T("Test texture: red → blue left to right, arrow points right", 22, C_DIM).to_edge(UP, buff=0.25)
        rule = M(r"\text{C: flip if }(\text{side}=0\wedge r_x>0)\ \vee\ (\text{side}=1\wedge r_y<0)\qquad"
                 r"\text{swapped: }(\text{side}=0\wedge r_x<0)\ \vee\ (\text{side}=1\wedge r_y>0)", size=22).move_to([0, -3.35, 0])
        self.add(ia, ib, t1, t2, c1, c2, head, rule)
