"""Shared look for all scenes: palette, y-down world->screen mapping, helpers."""
import numpy as np
from manim import *

# palette: one colour per mathematical object, used in every scene
BG = "#0f1320"
C_GRID = "#252c40"
C_WALL = "#56658a"
C_WALL_EDGE = "#8fa0c8"
C_PLAYER = "#ffd166"
C_DIR = "#06d6a0"       # d      (direction vector)
C_PLANE = "#ef476f"     # P      (camera plane)
C_RAY = "#4cc9f0"       # r      (ray)
C_X = "#4cc9f0"         # x-grid-line crossings
C_Y = "#f4a261"         # y-grid-line crossings
C_TEXT = "#e6e9f2"
C_DIM = "#8b93a8"
C_BAD = "#ff6b6b"
C_GOOD = "#7bd88f"

config.background_color = BG


def T(s, size=24, color=C_TEXT, **kw):
    return Text(s, font_size=size, color=color, **kw)


def M(s, size=34, color=C_TEXT, **kw):
    return MathTex(s, font_size=size, color=color, **kw)


class World:
    """Maps cub3D world coords (x right, y DOWN) onto Manim coords (y up)."""

    def __init__(self, grid, cell=0.55, top_left=(-6.6, 3.4)):
        self.grid, self.cell = grid, cell
        self.ox, self.oy = top_left
        self.h, self.w = len(grid), len(grid[0])

    def pt(self, x, y):
        return np.array([self.ox + x * self.cell, self.oy - y * self.cell, 0.0])

    def vec(self, dx, dy):                      # direction vectors flip y too
        return np.array([dx * self.cell, -dy * self.cell, 0.0])

    def cell_rect(self, cx, cy, **kw):
        sq = Square(self.cell, **kw)
        sq.move_to(self.pt(cx + 0.5, cy + 0.5))
        return sq

    def build_map(self, show_grid=True):
        g = VGroup()
        for y in range(self.h):
            for x in range(self.w):
                wall = self.grid[y][x] in "1 "
                sq = self.cell_rect(x, y, stroke_color=C_GRID, stroke_width=1.2,
                                    fill_color=C_WALL if wall else BG,
                                    fill_opacity=0.9 if wall else 0.0)
                g.add(sq)
        return g

    def arrow(self, p, dx, dy, color, **kw):
        return Arrow(self.pt(*p), self.pt(p[0] + dx, p[1] + dy), buff=0,
                     color=color, stroke_width=kw.pop("stroke_width", 5),
                     max_tip_length_to_length_ratio=kw.pop("ratio", 0.22), **kw)
