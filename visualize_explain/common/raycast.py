"""Python mirror of the C raycaster in ../Raycaster (float64, same operations).

Every function here is a line-by-line port of a C function, so the Manim scenes
animate the *real* numbers. `tools/crosscheck.py` compares this module against
the compiled C code.
"""
import math
from dataclasses import dataclass, field

WIDTH, HEIGHT = 1280, 720
CAMERA_PLANE = 0.66
MOVE_SPEED, ROT_SPEED, WALL_MARGIN = 3.0, 2.0, 0.2
TEX_NO, TEX_SO, TEX_WE, TEX_EA = 0, 1, 2, 3

# Raycaster/maps/sample.cub (map part only)
SAMPLE_MAP = [
    "1111111111",
    "1000000001",
    "1000N00001",
    "1000000001",
    "1111111111",
]


def load_grid(rows=SAMPLE_MAP):
    """Return (grid, start_x, start_y, start_char); player cell becomes '0'."""
    grid, start = [], None
    for y, row in enumerate(rows):
        cells = list(row)
        for x, c in enumerate(cells):
            if c in "NSEW":
                start = (x, y, c)
                cells[x] = "0"
        grid.append(cells)
    return grid, start


@dataclass
class Player:               # t_player
    x: float
    y: float
    dir_x: float
    dir_y: float
    plane_x: float
    plane_y: float


def spawn(x, y, c):         # player_init.c: set_direction + set_player
    d = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}[c]
    dx, dy = float(d[0]), float(d[1])
    return Player(x + 0.5, y + 0.5, dx, dy, -dy * CAMERA_PLANE, dx * CAMERA_PLANE)


def rotate(p, angle):       # player_rotate.c
    c, s = math.cos(angle), math.sin(angle)
    odx, opx = p.dir_x, p.plane_x
    p.dir_x = odx * c - p.dir_y * s
    p.dir_y = odx * s + p.dir_y * c
    p.plane_x = opx * c - p.plane_y * s
    p.plane_y = opx * s + p.plane_y * c


def map_is_wall(grid, x, y):  # map_access.c
    if x < 0 or y < 0 or y >= len(grid) or x >= len(grid[0]):
        return True
    return grid[y][x] in "1 "


def position_is_open(grid, x, y):
    m = WALL_MARGIN
    return not any(map_is_wall(grid, int(x + sx * m), int(y + sy * m))
                   for sx in (-1, 1) for sy in (-1, 1))


def try_move(grid, p, dx, dy):  # player_move.c
    nx, ny = p.x + dx, p.y + dy
    if position_is_open(grid, nx, p.y):
        p.x = nx
    if position_is_open(grid, p.x, ny):
        p.y = ny


@dataclass
class Ray:                  # t_ray (only what the docs need)
    camera_x: float = 0.0
    dir_x: float = 0.0
    dir_y: float = 0.0
    side_dist_x: float = 0.0
    side_dist_y: float = 0.0
    delta_dist_x: float = 0.0
    delta_dist_y: float = 0.0
    wall_dist: float = 0.0
    map_x: int = 0
    map_y: int = 0
    step_x: int = 0
    step_y: int = 0
    side: int = 0
    hit: int = 0
    line_height: int = 0
    draw_start: int = 0
    draw_end: int = 0
    texture_index: int = 0
    texture_x: int = 0
    wall_x: float = 0.0
    trace: list = field(default_factory=list)   # one dict per DDA iteration


def ray_init(p, x, width=WIDTH):   # ray_init.c
    r = Ray()
    r.camera_x = 2.0 * x / float(width) - 1.0
    r.dir_x = p.dir_x + p.plane_x * r.camera_x
    r.dir_y = p.dir_y + p.plane_y * r.camera_x
    r.map_x, r.map_y = int(p.x), int(p.y)
    r.delta_dist_x = abs(1.0 / r.dir_x) if r.dir_x != 0 else 1e30
    r.delta_dist_y = abs(1.0 / r.dir_y) if r.dir_y != 0 else 1e30
    if r.dir_x < 0:
        r.step_x, r.side_dist_x = -1, (p.x - r.map_x) * r.delta_dist_x
    else:
        r.step_x, r.side_dist_x = 1, (r.map_x + 1.0 - p.x) * r.delta_dist_x
    if r.dir_y < 0:
        r.step_y, r.side_dist_y = -1, (p.y - r.map_y) * r.delta_dist_y
    else:
        r.step_y, r.side_dist_y = 1, (r.map_y + 1.0 - p.y) * r.delta_dist_y
    return r


def ray_dda(grid, r):              # ray_dda.c  (records every iteration)
    while not r.hit:
        if r.side_dist_x < r.side_dist_y:
            r.side_dist_x += r.delta_dist_x
            r.map_x += r.step_x
            r.side = 0
        else:
            r.side_dist_y += r.delta_dist_y
            r.map_y += r.step_y
            r.side = 1
        if map_is_wall(grid, r.map_x, r.map_y):
            r.hit = 1
        r.trace.append(dict(side=r.side, map_x=r.map_x, map_y=r.map_y,
                            side_dist_x=r.side_dist_x, side_dist_y=r.side_dist_y,
                            hit=r.hit))
    return r


def ray_project(r, height=HEIGHT):  # ray_projection.c
    r.wall_dist = (r.side_dist_x - r.delta_dist_x if r.side == 0
                   else r.side_dist_y - r.delta_dist_y)
    if r.wall_dist < 0.0001:
        r.wall_dist = 0.0001
    r.line_height = max(1, int(height / r.wall_dist))
    r.draw_start = max(0, height // 2 - r.line_height // 2)
    r.draw_end = min(height - 1, height // 2 + r.line_height // 2)
    return r


def ray_texture(p, r, tex_w=64):    # ray_texture.c (texture index + texture_x)
    if r.side == 0:
        r.texture_index = TEX_WE if r.step_x > 0 else TEX_EA
        wx = p.y + r.wall_dist * r.dir_y
    else:
        r.texture_index = TEX_NO if r.step_y > 0 else TEX_SO
        wx = p.x + r.wall_dist * r.dir_x
    wx -= math.floor(wx)
    r.wall_x = wx
    r.texture_x = int(wx * tex_w)
    if r.side == 0 and r.dir_x > 0:
        r.texture_x = tex_w - r.texture_x - 1
    if r.side == 1 and r.dir_y < 0:
        r.texture_x = tex_w - r.texture_x - 1
    return r


def cast(grid, p, x, width=WIDTH, height=HEIGHT):
    r = ray_init(p, x, width)
    ray_dda(grid, r)
    ray_project(r, height)
    ray_texture(p, r)
    return r


# ---- the naive method the docs compare against (NOT in the C project) ------
def naive_march(grid, px, py, theta, eps, max_dist=50.0):
    """Fixed-step marching along angle theta. Returns (steps, euclid_dist, cos/sin calls)."""
    cs, sn = math.cos(theta), math.sin(theta)       # 2 trig calls per ray
    t, steps = 0.0, 0
    while t < max_dist:
        t += eps
        steps += 1
        if map_is_wall(grid, int(px + t * cs), int(py + t * sn)):
            return steps, t
    return steps, None


# Demo room used by the animations (NOT a file from the repo; 12 x 8, player E at (2,4))
DEMO_MAP = [
    "111111111111",
    "100000000001",
    "100000110001",
    "100000010001",
    "10E000000001",
    "100000000101",
    "100000000001",
    "111111111111",
]

# Correct orientation for this repo's y-down world (see docs, section 6).
def ray_texture_fixed(p, r, tex_w=64):
    """Same as ray_texture but with the mirror rule swapped: tex_x grows with screen x."""
    ray_texture(p, r, tex_w)
    wx = r.wall_x
    tx = int(wx * tex_w)
    if r.side == 0 and r.dir_x < 0:
        tx = tex_w - tx - 1
    if r.side == 1 and r.dir_y > 0:
        tx = tex_w - tx - 1
    r.texture_x = tx
    return r
