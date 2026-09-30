"""Compare common/raycast.py with the REAL C functions.

Builds Raycaster/src/render/ray_*.c + map_access.c + player_rotate.c against a
copy of cub3d.h with the GLFW/libft includes removed (scratch dir, repo is not
touched), runs a small C harness and diffs every printed number.

    uv run python tools/crosscheck.py        # needs gcc; RAYCASTER=path overrides ../Raycaster
"""
import math, os, re, subprocess, sys, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from common import raycast as rc

RC = os.environ.get("RAYCASTER", os.path.join(ROOT, "..", "Raycaster"))
HARNESS = os.path.join(ROOT, "tools", "harness.c")
POSES = [(4.5, 2.5, 0.0), (2.3, 1.7, 0.9), (7.25, 3.1, -2.2), (1.5, 1.5, 3.0)]
XS = [0, 160, 320, 480, 640, 800, 960, 1120, 1279]


def build(tmp):
    for d in ("src/render", "src/map", "src/player", "includes"):
        os.makedirs(os.path.join(tmp, d))
    for f in ("render/ray_init.c", "render/ray_dda.c", "render/ray_projection.c",
              "render/ray_texture.c", "map/map_access.c", "player/player_rotate.c"):
        shutil.copy(os.path.join(RC, "src", f), os.path.join(tmp, "src", f))
    hdr = open(os.path.join(RC, "includes", "cub3d.h")).read()
    hdr = re.sub(r'#\s*include\s*(<GLFW[^\n]*|"gl_ext[^\n]*|"\.\./[^\n]*)\n', "", hdr)
    hdr = hdr.replace("# undef iszero\n", "")
    hdr = hdr.replace("# include <unistd.h>", "# include <unistd.h>\ntypedef void GLFWwindow; "
                      "typedef unsigned int GLuint; typedef int GLint;")
    open(os.path.join(tmp, "includes", "cub3d.h"), "w").write(hdr)
    shutil.copy(HARNESS, os.path.join(tmp, "harness.c"))
    srcs = [os.path.join("src", f) for f in ("render/ray_init.c", "render/ray_dda.c",
            "render/ray_projection.c", "render/ray_texture.c", "map/map_access.c",
            "player/player_rotate.c")]
    subprocess.check_call(["gcc", "-O0", "-o", "harness", "harness.c", *srcs, "-lm"], cwd=tmp)


def main():
    grid, _ = rc.load_grid(["1111111111", "1000000001", "1000000001", "1000000001", "1111111111"])
    bad = n = 0
    with tempfile.TemporaryDirectory() as tmp:
        build(tmp)
        for px, py, ang in POSES:
            out = subprocess.check_output(["./harness", str(px), str(py), str(ang)], cwd=tmp, text=True).splitlines()
            p = rc.Player(px, py, 1.0, 0.0, -0.0, rc.CAMERA_PLANE)
            rc.rotate(p, ang)
            for line in out[1:]:
                t = line.split()
                x = int(t[1])
                r = rc.cast(grid, p, x)
                c = dict(map_x=int(t[8]), map_y=int(t[9]), side=int(t[11]), wall_dist=float(t[13]),
                         line_height=int(t[15]), draw_start=int(t[17]), draw_end=int(t[19]),
                         texture_x=int(t[21]), texture_index=int(t[23]))
                for k, v in c.items():
                    n += 1
                    pv = getattr(r, k)
                    ok = math.isclose(pv, v, rel_tol=0, abs_tol=2e-9) if isinstance(v, float) else pv == v
                    if not ok:
                        bad += 1
                        print("MISMATCH", (px, py, ang), x, k, "C:", v, "py:", pv)
    print(f"{n} values compared, {bad} mismatches")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
