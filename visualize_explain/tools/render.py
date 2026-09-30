"""Render every scene used by docs/raycasting.md into media/ (GIFs + PNG stills).

    uv run python tools/render.py            # everything
    uv run python tools/render.py DDAWalk    # one scene by class name

Needs: Manim (already in this project) and a LaTeX install (for MathTex).
GIFs are made from Manim's MP4 with ffmpeg (palette) when available, otherwise Manim's own GIF writer.
"""
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(ROOT, "media")
#            file                class               kind
SCENES = [("s00_formula.py", "StepFormula", "png"), ("s00_time.py", "TimePerPicture", "gif"), ("s01_naive.py", "NaiveMarching", "gif"), ("s01_naive.py", "FisheyeCompare", "gif"),
          ("s02_camera.py", "CameraBasis", "gif"), ("s02_camera.py", "RotateCamera", "gif"),
          ("s03_dda.py", "DeltaDist", "gif"), ("s03_dda.py", "DDAWalk", "gif"), ("s03_dda.py", "StepCount", "gif"),
          ("s04_perp.py", "PerpDistance", "gif"),
          ("s05_projection.py", "Projection", "gif"), ("s05_projection.py", "FrameSweep", "gif"),
          ("s06_texture.py", "TextureColumn", "gif"), ("s06_texture.py", "MirrorFlip", "png"),
          ("s08_player.py", "PlayerMotion", "gif"), ("s08_player.py", "Collision", "gif"),
          ("s09_pipeline.py", "Pipeline", "gif")]


def to_gif(mp4, gif):
    if shutil.which("ffmpeg"):
        vf = ("fps=15,scale=880:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];"
              "[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle")
        subprocess.check_call(["ffmpeg", "-loglevel", "error", "-y", "-i", mp4, "-vf", vf, gif])
    else:
        raise SystemExit("ffmpeg not found: install it (brew install ffmpeg) or render with `manim --format gif`")


def main(only):
    os.makedirs(MEDIA, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=ROOT)
    with tempfile.TemporaryDirectory() as tmp:
        for f, cls, kind in SCENES:
            if only and cls not in only:
                continue
            cmd = [sys.executable, "-m", "manim", os.path.join("scenes", f), cls,
                   "--media_dir", tmp, "-r", "960,540", "--frame_rate", "15"]
            if kind == "png":
                cmd.insert(3, "-s")                       # save last frame only
            print("render", cls, flush=True)
            subprocess.check_call(cmd, cwd=ROOT, env=env)
            stem = f[:-3]
            if kind == "png":
                src = os.path.join(tmp, "images", stem, f"{cls}_ManimCE_v0.21.0.png")
                shutil.copy(src, os.path.join(MEDIA, cls + ".png"))
            else:
                to_gif(os.path.join(tmp, "videos", stem, "540p15", cls + ".mp4"), os.path.join(MEDIA, cls + ".gif"))
    if only:                                          # a single-scene render leaves frame_demo.png alone
        return
    # the software-rendered frame used in section 7
    sys.path.insert(0, ROOT)
    from common import raycast as rc, frame
    grid, (sx, sy, c) = rc.load_grid(rc.DEMO_MAP)
    p = rc.spawn(sx, sy, c)
    rc.rotate(p, -0.35)
    frame.render(grid, p, 960, 540, frame.load_textures()).save(os.path.join(MEDIA, "frame_demo.png"))


if __name__ == "__main__":
    main(set(sys.argv[1:]))
