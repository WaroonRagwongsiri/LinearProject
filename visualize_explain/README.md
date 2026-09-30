# visualize_explain

Documentation and Manim animations for the raycaster in `../Raycaster`.

- **`docs/raycasting.md`** – the document (math in LaTeX blocks, GIFs from `media/`).
- `scenes/` – Manim scenes, one file per section (`s00_time.py` … `s09_pipeline.py`).
- `common/raycast.py` – Python mirror of the C ray code; `common/frame.py` – software frame renderer.
- `common/budget.py` – the 1990s clock-budget / cost model behind section 0 (`python common/budget.py` prints every number).
- `tools/render.py` – renders every scene into `media/`; `tools/crosscheck.py` – checks the mirror against the real C.

```sh
uv run python tools/render.py             # all scenes (needs LaTeX for MathTex, ffmpeg for GIFs)
uv run python tools/render.py DDAWalk     # one scene
uv run python tools/crosscheck.py         # needs gcc
```

`media/_manim/` (Manim's intermediate files when you run `manim` directly) is safe to add to `.gitignore`.
