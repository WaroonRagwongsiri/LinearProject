"""Software version of draw_column(): renders a frame with PIL so the docs can show
what the C code draws (same math as render_frame / ray_texture / draw_column)."""
import os
import numpy as np
from PIL import Image
from . import raycast as rc

RAYCASTER = os.environ.get("RAYCASTER", os.path.join(os.path.dirname(__file__), "..", "..", "Raycaster"))
FLOOR, CEIL = (220, 100, 0), (100, 180, 240)           # maps/sample.cub  F / C


def load_textures():
    names = ["wall_1", "wall_2", "wall_3", "wall_4"]      # NO SO WE EA as in sample.cub
    return [np.array(Image.open(os.path.join(RAYCASTER, "textures", n + ".png")).convert("RGBA")) for n in names]


def test_texture(size=64):
    """Asymmetric texture: red on the left, blue on the right, white arrow pointing right."""
    a = np.zeros((size, size, 4), np.uint8)
    for x in range(size):
        t = x / (size - 1)
        a[:, x] = (int(235 * (1 - t) + 30 * t), 60, int(40 * (1 - t) + 235 * t), 255)
    mid = size // 2
    for i in range(-3, 4):
        a[mid + i, 10:size - 12] = (255, 255, 255, 255)
    for k in range(10):                               # arrow head: base on the left, apex on the right
        a[mid - (9 - k):mid + (9 - k) + 1, size - 24 + k] = (255, 255, 255, 255)
    a[:4, :] = (255, 255, 255, 255); a[-4:, :] = (255, 255, 255, 255)
    return a


def render(grid, p, width, height, textures, fixed=False, shade=True):
    img = np.zeros((height, width, 4), np.uint8)
    img[:, :] = (*CEIL, 255)
    img[height // 2:, :] = (*FLOOR, 255)
    tex_fn = rc.ray_texture_fixed if fixed else rc.ray_texture
    for x in range(width):
        r = rc.ray_init(p, x, width)
        rc.ray_dda(grid, r)
        rc.ray_project(r, height)
        tex = textures[0]
        tex_fn(p, r, tex.shape[1])
        tex = textures[r.texture_index]
        step = tex.shape[0] / r.line_height
        pos = (r.draw_start - height / 2.0 + r.line_height / 2.0) * step
        ys = np.arange(r.draw_start, r.draw_end + 1)
        ty = np.clip((pos + step * np.arange(len(ys))).astype(int), 0, tex.shape[0] - 1)
        col = tex[ty, r.texture_x].copy()
        if shade and r.side == 1:
            col[:, :3] //= 2                   # draw_column.c: r/2, g/2, b/2
        img[ys, x] = col
    return Image.fromarray(img)
