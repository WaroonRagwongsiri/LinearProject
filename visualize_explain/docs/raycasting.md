# How the Raycaster Works — a Linear-Algebra Walkthrough

This document explains the raycaster in `../Raycaster` (your `cub3D` project: a first-person maze view in the style of
*Wolfenstein 3D*), starting from the math and following it into the code. Math is written as LaTeX (`$…$`, `$$…$$`; renders on GitHub, VS Code, Typora).
Every animation was produced with Manim (a Python library for maths animations) from a Python mirror of the C code (`common/raycast.py`) that is
cross-checked against the compiled C functions, so the numbers in the GIFs are the numbers your program computes.

**Conventions used everywhere** (they match the C code, and they matter):

- The map is indexed `grid[y][x]`; **x grows to the right, y grows downward**. North is $(0,-1)$.
- A vector is a pair of numbers, written as a column $\begin{bmatrix}x\\y\end{bmatrix}$ or as $(x,y)$. Colours in every animation: <span style="color:#06d6a0">**d** direction</span>,
  <span style="color:#ef476f">**P** camera plane</span>, <span style="color:#4cc9f0">**r** ray</span>.
- **Every symbol and term is explained where it first appears**, and all of them are collected in
  [Notation and terms](#notation-and-terms-reference) below the contents table.
- C excerpts are lightly reformatted (line breaks collapsed) but otherwise copied from the source.
- The animations use a 12×8 demo room (not one of your `.cub` files) unless a caption says `maps/sample.cub`.

| Section | Idea |
|---|---|
| [Notation](#notation-and-terms-reference) | every symbol, notation and term, in one place |
| [0](#0-the-problem-computers-back-then-were-tiny) | Why the obvious way is too slow, and what we can do: which linear algebra fixes which problem |
| [1](#1-the-naive-angle-method-and-why-it-loses) | Angles, `cos`/`sin`, tiny steps, fisheye |
| [2](#2-the-camera-is-a-matrix) | Camera = 2×2 matrix; rotation = left-multiplication; ray = matrix·vector |
| [3](#3-dda-walking-the-grid) | Ray = line; DDA merges two arithmetic sequences |
| [4](#4-perpendicular-distance-is-a-dot-product) | Why `wall_dist` needs no `cos` |
| [5](#5-projection-to-a-column) | Similar triangles → `line_height` |
| [6](#6-texture-mapping) | `wall_x`, `tex_x`, and a mirroring problem |
| [7](#7-drawing-a-column) | Framebuffer, shading |
| [8](#8-the-player) | Movement as basis vectors, collision |
| [9](#9-one-frame-end-to-end) | The whole pipeline |

---

## Notation and terms (reference)

Each symbol and term is also explained where it first appears. This is the place to look one up later.

### Symbols

| symbol | meaning | in the code / value | first used |
|---|---|---|---|
| $W,\ H$ | screen width and height in pixels | `WIDTH` $=1280$, `HEIGHT` $=720$ here (the 1992 examples in §0 use $320\times200$) | §0, §2.2 |
| $x$ | which screen column: $0$ is the left edge, $W-1$ the right edge | loop variable `x` | §2.2 |
| $c$ | where that column sits across the screen, from $-1$ (left edge) to $+1$ (right edge): $c=\frac{2x}{W}-1$ | `camera_x` | §2.2 |
| $\vec p$ | player position $(x,y)$, measured in cells | `player.x`, `player.y` | §0.1 |
| $\vec d$ | the direction the player faces, a vector of length 1 | `player.dir_x`, `dir_y` | §2.1 |
| $\vec P$ | the **camera plane**: a vector sideways to $\vec d$, length $0.66$, that sets how wide the player sees | `player.plane_x`, `plane_y`; `CAMERA_PLANE` | §2.1 |
| $\vec r$ | the ray of one column: $\vec r=\vec d+c\vec P$ | `ray.dir_x`, `dir_y` | §2.2 |
| $t$ | the **ray parameter**: how many copies of $\vec r$ you have walked. The point is $\vec q(t)=\vec p+t\vec r$ | `side_dist`, `wall_dist` are values of $t$ | §3.1 |
| $M$ | the camera matrix: $\vec d$ and $\vec P$ side by side | (two vectors in the code) | §2.2 |
| $J$ | the "quarter turn" matrix: $J\binom{x}{y}=\binom{-y}{x}$ | | §2.1 |
| $R(\alpha)$ | the rotation matrix: turns a vector by angle $\alpha$ | `player_rotate` | §2.3 |
| $\theta$ | an angle: of one line (§0, §1), or the heading of $\vec d$ (§2.3) | | §0.1 |
| $\alpha$ | how much the player turns in one frame, in radians | `angle` (argument of `player_rotate`) | §2.4 |
| $\varepsilon$ | length of one step of the naive walk, in cells | $0.1$ | §0.1 |
| $i,\ k$ | counters: step number (§0.1); step number in §1, where $i$ numbers the columns | | §0.1, §1 |
| $\Delta t_x,\ \Delta t_y$ | how much $t$ grows between two neighbouring vertical (horizontal) grid lines | `delta_dist_x`, `delta_dist_y` | §3.1 |
| $\text{side\_dist}_x,\ \text{side\_dist}_y$ | the value of $t$ at the next vertical (horizontal) grid line the ray will reach | `side_dist_x`, `side_dist_y` | §3.2 |
| $\vec m=\lfloor\vec p\rfloor$ | the cell the ray is in: the whole-number $(x,y)$ | `map_x`, `map_y` | §3.2 |
| $\text{step}_x,\ \text{step}_y$ | which way the ray walks through the cells: $-1$ or $+1$ | `step_x`, `step_y` | §3.2 |
| $t_{\text{hit}}$ | the value of $t$ where the ray meets the wall | | §4 |
| $a,\ b$ | "camera coordinates" of a world point: $a$ forward along $\vec d$, $b$ sideways along $\vec P$ | | §2.5 |
| $z$ | the wall's depth: its distance straight ahead of the player | `wall_dist` | §5 |
| $\text{lh}$ | the wall's height on screen, in pixel rows | `line_height` | §5 |
| $\text{draw\_start},\ \text{draw\_end}$ | the first and last screen row of the wall in this column | `draw_start`, `draw_end` | §5 |
| $\text{wall\_x}$ | where along the wall face the ray hit: $0$ (one edge) to $1$ (other edge) | `wall_x` | §6.1 |
| $\text{tex\_x}$ | which column of the texture image that is | `texture_x` | §6.1 |
| $W_{\text{tex}}$ | texture width in pixels | `texture->width` | §6.1 |
| $\text{dt}$ | seconds since the previous frame | `delta_time` | §8.1 |
| $s$ | how far the player moves this frame: $s=\text{dt}\cdot\text{MOVE\_SPEED}$ | | §8.1 |
| $\text{MOVE\_SPEED},\ \text{ROT\_SPEED}$ | settings: how fast the player walks ($3.0$ cells per second) and turns ($2.0$ radians per second) | `MOVE_SPEED`, `ROT_SPEED` | §8.1 |

### Mathematical notation

| notation | read as | example |
|---|---|---|
| $\vec v$ | a **vector**: a pair of numbers $(x,y)$. The arrow on top marks it as a vector, not a single number | $\vec p=(2,4)$ |
| $\begin{bmatrix}x\\y\end{bmatrix}$ or $\binom{x}{y}$ | the same vector written as a column | |
| $\lvert\vec v\rvert$ | the **length** of a vector: $\sqrt{x^2+y^2}$ | $\lvert(3,4)\rvert=5$ |
| $\lvert a\rvert$ | absolute value: drop the minus sign | $\lvert-0.4\rvert=0.4$ |
| $a\cdot b$, $\sqrt a$ | between two numbers, $\cdot$ is ordinary multiplication (between two vectors it is the dot product, below). $\sqrt a$ is the square root: the number that multiplied by itself gives $a$ | $\sqrt2\approx1.414$ |
| $\lfloor a\rfloor$ | **floor**: round down to a whole number | $\lfloor 2.87\rfloor=2$, $\lfloor -0.5\rfloor=-1$ |
| $\lceil a\rceil$ | **ceiling**: round up | $\lceil 58.1\rceil=59$ |
| $\operatorname{frac}(a)$ | the part after the decimal point: $a-\lfloor a\rfloor$ | $\operatorname{frac}(2.87)=0.87$ |
| $\operatorname{sign}(a)$ | $-1$, $0$ or $+1$ according to the sign of $a$ | $\operatorname{sign}(-3)=-1$ |
| $\vec a\cdot\vec b$ | the **dot product**: $a_xb_x+a_yb_y$. It is $0$ exactly when the vectors are at a right angle | $(1,0)\cdot(0,1)=0$ |
| $A\vec v$ | a **matrix** times a vector: the matrix turns, stretches or mixes the vector. For $M=[\vec d\ \vec P]$: $M\binom{1}{c}=1\cdot\vec d+c\cdot\vec P$ | |
| $A^{-1}$ | the **inverse** matrix: undoes $A$, so $A^{-1}(A\vec v)=\vec v$ | |
| $A^{\mathsf T}$ | the **transpose**: swap rows and columns | |
| $I$ | the **identity** matrix: changes nothing | |
| $\det A$ | the **determinant**: the factor by which $A$ scales areas. A pure rotation has $\det=1$ | |
| $\operatorname{diag}(1,0.66)$ | the matrix with $1$ and $0.66$ on the diagonal and $0$ elsewhere: it keeps x and scales y by $0.66$ | |
| $\sin,\ \cos,\ \arctan$ | standard angle functions. $\cos\theta,\sin\theta$ give the "across" and "down" part of a length-1 step at angle $\theta$ (§0.1); $\arctan$ turns a ratio back into an angle | |
| radian (rad) | an angle unit: $180^\circ=\pi\approx3.14$ rad, so $1$ rad $\approx57.3^\circ$ | |
| $\leftarrow$ | "becomes": replace the left side with the right side | $\vec p\leftarrow\vec p+s\vec d$ |
| $\in[-1,1]$ | "lies between $-1$ and $1$" | |
| $\Delta$ | a gap or difference between two values | |
| $\approx$, $\pm$ | approximately equal; plus or minus | |

### Terms

| term | meaning |
|---|---|
| pixel, column | a pixel is one dot of the screen. A column is one vertical line of pixels, one pixel wide |
| cell, grid, map | the world is a flat 2D grid of square cells, each $1\times1$. A cell is `1` (wall) or `0` (empty); a letter `N`/`S`/`E`/`W` marks the player's start; a space counts as wall. All walls have the same height. `grid[y][x]` is row $y$, column $x$. Distances are in cells |
| ray | a line that starts at the player and goes on forever in one direction. The raycaster sends one per screen column |
| raycasting | building the picture by sending rays and seeing where each one hits a wall |
| unit vector | a vector of length 1 |
| perpendicular | at a right angle |
| camera plane | an imaginary window one unit in front of the player. $\vec P$ is half of it, from its middle to its right edge |
| basis | two vectors you can combine to reach any point: $\vec d$ and $\vec P$ are the camera's basis |
| linear | "equal change in, equal change out": if $c$ goes up by the same amount, $\vec r$ moves by the same amount |
| pinhole (perspective) camera | far things look smaller: a wall twice as far away looks half as tall |
| field of view (FOV) | the angle the player can see at once |
| Euclidean distance | the ordinary straight-line distance, measured along the ray |
| perpendicular distance, depth | distance measured straight ahead (along $\vec d$), not along the slanted ray |
| fisheye | the bending of straight walls you get if you use the Euclidean distance for wall height |
| perspective divide | dividing by depth to shrink far things: $c=b/a$ (§2.5) |
| DDA | "digital differential analyzer": the method that walks a line from one grid line to the next (§3) |
| arithmetic sequence | numbers with a constant gap, such as $0.5,\,1.5,\,2.5,\dots$ |
| similar triangles | triangles with the same shape, so their sides are in proportion (§5) |
| orthogonal matrix | a matrix that turns without stretching: it keeps lengths and angles (§2.4) |
| texture, texel | a picture pasted on a wall; a texel is one pixel of that picture |
| framebuffer | the block of memory holding the colour of every pixel of the next picture (§7) |
| RGBA, channel | a colour as red, green, blue and alpha (opacity), each channel $0$ to $255$ |
| clamp | limit a number to a range: values below the range become its lowest value, above it its highest |
| normalised | scaled to length 1 |
| strafe | move sideways without turning |
| frame | one finished picture |

---

## 0. The problem: computers back then were tiny

Raycasting exists because the obvious way of drawing a 3D room was far too slow for the computers of 1992. This
section shows the obvious way, why it was too slow, and what we can do about it, with the linear algebra that helps. The rest
of the document explains each part in turn.

### 0.1 The obvious way

*Wolfenstein 3D* (1992) drew into a $320\times200$ screen, which is $64{,}000$ pixels. The world is a space with walls in it,
and the player looks at it. Distances are measured in **cells**: one cell is the width of one wall. The obvious way to
draw it is to give **every pixel its own ray**: ask each pixel "what wall do you see?":

1. Point a line (a *ray*) from the player through that pixel, at some angle $\theta$ (theta).
2. Walk along it in small steps of length $\varepsilon$ (epsilon, say $0.1$ cell). After $i$ steps the point is at

$$\vec p_i=\vec p+i\,\varepsilon\begin{bmatrix}\cos\theta\\ \sin\theta\end{bmatrix}$$

3. After each step ask: *is this point inside a wall?* The first "yes" is the wall, and its distance decides how the pixel
   is coloured.

![The step formula](../media/StepFormula.png)

In words: $\vec p$ is where the player stands, $i$ counts the steps, $\varepsilon$ is the length of one step, and
$(\cos\theta,\ \sin\theta)$ is a direction of length 1 (`cos` and `sin` give its "across" and "down" parts, the dashed
triangle in the picture). Each step just adds the same small arrow, so it costs two additions, one for $x$ and one for $y$.

![Naive marching](../media/NaiveMarching.gif)

Count the work for one picture. In the demo room used for the animations a wall is on average $5.8$ cells away, which is
$\lceil5.81/0.1\rceil=59$ steps ($\lceil\,\rceil$ rounds **up**). So

$$64{,}000\ \text{lines}\times59\ \text{steps}\times2\ \text{additions}\;\approx\;\mathbf{7.6\ million\ additions},$$

plus one `sin`/`cos` pair per line. These numbers have fractions (3.7, 4.25), which a computer stores as
**floating-point** ("decimal") numbers. The computers of 1992 could not do this fast enough: a 386 would need about
**6 seconds** for one picture, and the game needed 70 pictures every second, one every 14 ms.

### 0.2 What can we do?

Four things made the obvious way slow: **too many lines**, **`sin` and `cos` for every line**, **too many tiny steps along
each line**, and **bent walls that need a fix-up**. Each one can be attacked, and the tool that does it is mostly
**linear algebra**: vectors, one small matrix and the dot product. Here is each problem, what we can do, which linear
algebra helps, and the section that explains it.

**1. Too many lines** (64,000 per picture)

- *What we can do:* **simplify the world on purpose.** In a real 3D world every pixel could see something different, which is why
  the obvious way needs a ray per pixel. So we restrict the world:
  - the map is only **2D**: a flat grid of square cells, each $1\times1$, and every cell is `0` (empty floor) or `1` (wall), plus
    one letter (`N`, `S`, `E` or `W`) that marks where the player starts and which way they face. This is the map from your
    `maps/sample.cub`:

    ```
    1111111111
    1000000001
    1000N00001
    1000000001
    1111111111
    ```

    (To find which cell a point $(x,y)$ is in, round both numbers **down**: $\lfloor2.87\rfloor=2$.)
  - every wall stands **straight up** and has **exactly the same height**; floor and ceiling are flat colours;
  - the player only **turns left and right** (no looking up or down) and stays at one height.

  Under these rules everything in one screen column comes from **one wall at one distance**, so every pixel in that column
  shows the same stretch of wall, only stretched to a different height. Cast **one line per column**: 320 lines instead of
  64,000, which is 200× fewer (6 s becomes about 30 ms). The price: no slopes, stairs, different wall heights or rooms above
  rooms.
- *Linear algebra:* because the map is 2D, everything lives in the plane, so a point is a pair of numbers and a direction is a
  2-vector. A column becomes **one number** $c$ between $-1$ and $1$, and its line is the vector $\vec r=\vec d+c\,\vec P$, a
  combination of two vectors: the direction the player faces and the camera plane.
- *Explained in:* [§1](#1-the-naive-angle-method-and-why-it-loses) (one line per column, the angle way and its problems),
  [§2.1–2.2](#21-two-vectors-define-the-camera).

**2. `sin` and `cos` for every line**

- *What we can do:* describe each line with a **vector** (two numbers) instead of an angle, so no trigonometry is needed per
  line.
- *Linear algebra:* put $\vec d$ and $\vec P$ side by side as a **matrix** $M$. Then $\vec r=M\binom{1}{c}$, a matrix times a
  vector. Turning the player is one **matrix product**, $M\leftarrow R(\alpha)M$, so `sin` and `cos` run once per turn instead of
  once per line. Going the other way (world point to screen) is the **inverse matrix** $M^{-1}$.
- *Explained in:* [§2.2](#22-a-screen-column-is-a-coordinate), [§2.3–2.4](#23-the-camera-matrix-is-rotation--scale),
  [§2.5](#25-raycasting-is-the-inverse-of-perspective-projection).

**3. About 59 tiny steps per line**

- *What we can do:* a line only matters where it crosses a cell border. **Jump from grid line to grid line** (DDA): about 8
  jumps instead of 59, and no wall can be skipped.
- *Linear algebra:* a line is $\vec q(t)=\vec p+t\,\vec r$, a point plus a multiple of a vector. Solving for where it meets the
  grid lines gives the gap between crossings, $\Delta t_x=1/\lvert r_x\rvert$ (and the same for $y$): two evenly spaced lists
  of numbers that we merge in order.
- *Explained in:* [§3](#3-dda-walking-the-grid).

**4. Bent walls (fisheye) and the fix-up**

- *What we can do:* measure the distance **straight ahead** instead of along the slanted line, and get the wall's height from it
  with one division. (Using the slanted distance makes straight walls look bent, and undoing that would cost another `cos`.)
- *Linear algebra:* the **dot product**. Because $\vec d\cdot\vec P=0$ and $\lvert\vec d\rvert=1$, we get $\vec d\cdot\vec r=1$ for
  every column, so the ray parameter $t$ already *is* the straight-ahead distance: no `cos`. The height then follows from
  similar triangles, $\text{lh}=H/z$.
- *Explained in:* [§4](#4-perpendicular-distance-is-a-dot-product), [§5](#5-projection-to-a-column).

The same tools finish the picture: the hit point $\vec p+t\,\vec r$ gives the texture column
([§6](#6-texture-mapping)), the column is drawn ([§7](#7-drawing-a-column)), moving the player is a combination of the basis
vectors $\vec d$ and $J\vec d$ ([§8](#8-the-player)), and [§9](#9-one-frame-end-to-end) puts the whole frame together.

Together the four fixes bring one picture to about **8.5 ms** on the same 386, inside the 14 ms allowed.

<details>
<summary>How these numbers were estimated (assumptions and sources)</summary>

A *tick* is one beat of the processor's clock (a 33 MHz chip has 33 million per second); a whole-number addition takes 2 of them, a
decimal addition 24, a decimal division 88, and `sin` with `cos` 194. Only the arithmetic is counted, with the *lowest* published tick count of each instruction, so real costs are higher. Ray
counts (5.81 cells, 59 steps, 7.6 DDA steps) come from the 320 real rays of the demo room run through the Python mirror of
the C code; the tick prices are my own estimate. `python common/budget.py` prints every number.

- **Obvious way:** setup = `FSINCOS` 194 + 2 `FMUL` 54 = 248 ticks per line; each step = 2 `FADD` = 48 ticks
  (`FADD`/`FMUL`/`FDIV` are the maths chip's decimal add, multiply, divide).
- **This project, one line per column:** about 878 ticks per column (380 set up the ray, 227 for 7.6 DDA steps, 112 for
  distance and wall height, 158 to draw 39.6 pixels). Times 320 columns is 281,000 ticks, which is 8.5 ms.
- **Not a profile of the real game.** I priced *decimal* instructions to match this project's C code (which uses `double`).
  The shipped game used whole-number (fixed-point) maths and its own variant of the algorithm. Read the numbers as "why the
  obvious method was hopeless".
- **Today** (1280×720, 60 pictures per second, a 3 GHz core) there are about 54 ticks per pixel, so per-pixel rays became
  feasible (GPUs do them). The ratio between the methods is unchanged: 720× fewer lines with one per column.

**Sources.**
[Wolfenstein 3D (Wikipedia)](https://en.wikipedia.org/wiki/Wolfenstein_3D) ·
[Mode 13h (Wikipedia)](https://en.wikipedia.org/wiki/Mode_13h) (320×200, 64,000 bytes) ·
[tech specs](https://www.pixelatedarcade.com/games/wolfenstein-3d/techspecs) ·
Fabien Sanglard, [*Game Engine Black Book: Wolfenstein 3D*](https://fabiensanglard.net/Game_Engine_Black_Book/index.php)
(ch. 2.1.1 target CPU, 2.1.3 instruction costs, 2.3.7 the 70 pictures per second) ·
[Intel i387 datasheet](https://www.ardent-tool.com/CPU/docs/Intel/387/datasheets/271074-006.pdf) ·
[Lo-tech wiki, 80x87](https://www.lo-tech.co.uk/wiki/80x87_Math_Coprocessors) (`FDIV`) ·
Lode Vandevenne's [Raycasting tutorial](https://lodev.org/cgtutor/raycasting.html) (source of the DDA variant used here).

</details>

---

## 1. The naive angle method and why it loses

The obvious approach: give each column an angle and walk along it.

$$\theta_i=\theta_p+\Big(\tfrac{i}{W}-\tfrac12\Big)\text{FOV},\qquad
\vec p_k=\vec p+k\,\varepsilon\begin{bmatrix}\cos\theta_i\\ \sin\theta_i\end{bmatrix},\quad k=1,2,\dots$$

stop at the first $\vec p_k$ inside a wall cell. Here $\theta_p$ is the direction the player faces, FOV (field of view) is the total angle the player sees, $W$ is the screen width in pixels and $i$ is the column number, so the columns share the field of view equally, one angle per column. $\theta_i$ is the angle of column $i$.

(This is the formula from [§0.1](#01-the-obvious-way). Here the steps are numbered $k$ because $i$ numbers the screen columns.)

![Naive marching](../media/NaiveMarching.gif)

Three problems:

1. **Cost.** A ray of length $d$ (the straight-line, or *Euclidean*, distance it has to walk) needs $N=\lceil d/\varepsilon\rceil$ steps, each with a multiply-add and a cell
   lookup. Smaller $\varepsilon$ is more accurate and proportionally slower. Two trig calls ($\cos\theta_i$,
   $\sin\theta_i$) per ray, every frame (counted in [§0.1](#01-the-obvious-way)).
2. **Missed walls.** With a large $\varepsilon$ a ray can step over a thin wall or slip through a corner.
3. **Fisheye.** The walk measures the *Euclidean* distance $d$. The height of a wall on screen should depend on the
   *perpendicular* distance $D$, how far the wall is straight ahead. A flat wall at perpendicular distance $D$ is seen
   at angle $\theta$ from the view direction with $d=D/\cos\theta$, so its edges look farther and the wall bows. Undoing it needs
   $D=d\cos\theta$: one more trig call per ray.

![Fisheye](../media/FisheyeCompare.gif)

The fix for all three is to stop thinking in angles and use **vectors**: a ray is a line, a line crosses a square
grid at predictable places, and the "angle" never has to be computed.

---

## 2. The camera is a matrix

### 2.1 Two vectors define the camera

From `includes/cub3d.h` and `player_init.c`, the player has a position $\vec p$, a **unit** direction $\vec d$ (a vector
of length 1 pointing where the player faces) and a **camera plane** $\vec P$, **perpendicular** (at a right angle) to $\vec d$,
with length `CAMERA_PLANE` $=0.66$. Think of the camera plane as an imaginary window one unit in front of the player:
$\vec P$ goes from the middle of the window to its right edge, so a longer $\vec P$ means a wider view.

$$\vec P = 0.66\,J\vec d,\qquad J=\begin{bmatrix}0&-1\\1&0\end{bmatrix}\;(\text{rotation by }90^\circ),\qquad J\begin{bmatrix}x\\y\end{bmatrix}=\begin{bmatrix}-y\\x\end{bmatrix}.$$

$J$ is a matrix (a table of numbers that turns one vector into another: each row is multiplied against $(x,y)$ and added).
This one turns any vector a quarter turn, so $J\vec d$ is perpendicular to $\vec d$ and has the same length.

In code: `plane_x = -dir_y * CAMERA_PLANE; plane_y = dir_x * CAMERA_PLANE;`. Facing north,
$\vec d=\begin{bmatrix}0\\-1\end{bmatrix}$ and $\vec P=\begin{bmatrix}0.66\\0\end{bmatrix}$.

### 2.2 A screen column is a coordinate

Column $x$ of a screen $W$ pixels wide ($W=1280$ here; $x=0$ is the left edge) gets the coordinate $c=\frac{2x}{W}-1\in[-1,1]$
(`camera_x`): $-1$ at the left edge, $0$ in the middle, $+1$ at the right edge. Its ray is

$$\vec r \;=\; \vec d + c\,\vec P \;=\; \underbrace{\begin{bmatrix}\vec d&\vec P\end{bmatrix}}_{M}\begin{bmatrix}1\\c\end{bmatrix}.$$

The last step is a matrix times a vector: $M\binom{1}{c}=1\cdot\vec d+c\cdot\vec P$. Here $M$ is the matrix whose two columns are $\vec d$ and
$\vec P$. In words: the ray is one step forward plus $c$ steps sideways. This is `ray_init`:

```c
ray->camera_x = 2.0 * x / (double)WIDTH - 1.0;
ray->dir_x = game->player.dir_x + game->player.plane_x * ray->camera_x;
ray->dir_y = game->player.dir_y + game->player.plane_y * ray->camera_x;
```

![Camera basis](../media/CameraBasis.gif)

Three facts come for free from the matrix view:

- **Equal spacing on the plane.** $\vec r$ is *linear* in $c$ (an equal change in $c$ moves $\vec r$ by an equal amount), so the
  columns sample the camera plane at equal steps. That is exactly a perspective (*pinhole*) projection, the way a camera sees
  (far things smaller); equal steps in *angle* would not be (§1).
- **Field of view.** $\text{FOV}=2\arctan\dfrac{|\vec P|}{|\vec d|}=2\arctan 0.66\approx 66.8^\circ$
  ($|\vec v|$ is a vector's length; $\arctan$ turns the ratio 0.66 back into an angle, about $33.4^\circ$ to each side).
  A longer plane widens it (animation), which is the same as zooming out.
- **No trig.** Nothing here calls `cos` or `sin`.

### 2.3 The camera matrix is rotation × scale

Write $\theta$ for the heading of $\vec d$ (its angle from the x axis) and $R(\theta)$ for the 2-D **rotation matrix**, which turns a
vector by $\theta$:

$$R(\theta)=\begin{bmatrix}\cos\theta&-\sin\theta\\ \sin\theta&\cos\theta\end{bmatrix}.$$

Then

$$M=\begin{bmatrix}\vec d&\vec P\end{bmatrix}=R(\theta)\begin{bmatrix}1&0\\0&0.66\end{bmatrix},\qquad \det M = 0.66 .$$

The second matrix is $\operatorname{diag}(1,0.66)$: it keeps the x part and shrinks the y part to $0.66$. $\det M$, the
*determinant*, is the factor by which $M$ scales areas: a rotation keeps areas, the shrink by $0.66$ scales them by $0.66$.

Check for north ($\theta=-90^\circ$): $R(-90^\circ)\,\text{diag}(1,0.66)=\begin{bmatrix}0&0.66\\-1&0\end{bmatrix}$, which is
the matrix $[\vec d\ \vec P]$ above. In the camera's own frame the ray is simply $\begin{bmatrix}1\\0.66\,c\end{bmatrix}$:
one unit forward, $0.66c$ sideways. The matrix $R(\theta)$ only carries that picture into the world.

### 2.4 Turning the player is one matrix product

`player_rotate` rotates **both columns** of $M$ with the same matrix:

$$M'=R(\alpha)\,M,\qquad R(\alpha)=\begin{bmatrix}\cos\alpha&-\sin\alpha\\ \sin\alpha&\cos\alpha\end{bmatrix}$$

($\alpha$ is the angle turned this frame, in *radians*: $180^\circ=\pi\approx3.14$ rad, so $0.5$ rad is about $29^\circ$. $M'$ is the new camera matrix.)

```c
game->player.dir_x   = old_dir_x   * cosine - game->player.dir_y   * sine;
game->player.dir_y   = old_dir_x   * sine   + game->player.dir_y   * cosine;
game->player.plane_x = old_plane_x * cosine - game->player.plane_y * sine;
game->player.plane_y = old_plane_x * sine   + game->player.plane_y * cosine;
```

![Rotating the camera](../media/RotateCamera.gif)

Because $R$ is **orthogonal** it turns without stretching. In symbols $R^{\mathsf T}R=I$, where $R^{\mathsf T}$ (the *transpose*) is
$R$ with rows and columns swapped and $I$ is the *identity* matrix, which changes nothing, so $R^{\mathsf T}$ undoes $R$; also
$\det R=1$, so areas are kept. It therefore preserves lengths and angles, so after any turn $|\vec d|=1$, $|\vec P|=0.66$ and
$\vec d\cdot\vec P=0$ still hold. (The *dot product* $\vec a\cdot\vec b=a_xb_x+a_yb_y$ is $0$ exactly when the two vectors are at a
right angle.) Example, $\alpha=0.5$ from north:

$$R(0.5)\begin{bmatrix}0&0.66\\-1&0\end{bmatrix}=\begin{bmatrix}0.4794&0.5792\\-0.8776&0.3164\end{bmatrix},$$

which is exactly what `player_rotate(game, 0.5)` produces. The only trig in the whole render loop is this one
`cos`/`sin` pair per rotation event, not per ray.

With $y$ pointing down, a positive $\alpha$ turns **clockwise on screen** (north $(0,-1)$ becomes $(\sin\alpha,-\cos\alpha)$,
which points east for small $\alpha$): right arrow = positive angle = turn right.

### 2.5 Raycasting is the inverse of perspective projection

Going *forward* means asking where a world point $\vec q$ lands on the screen. First express it in camera coordinates: $a$ is how far
forward it is (along $\vec d$) and $b$ how far sideways (along $\vec P$). For that we need the *inverse* matrix $M^{-1}$, which undoes $M$:

$$\begin{bmatrix}a\\b\end{bmatrix}=M^{-1}(\vec q-\vec p),\qquad c=\frac{b}{a}\quad(\text{perspective divide}),\qquad x=\frac{W}{2}(1+c).$$

The *perspective divide* $c=b/a$ is what makes far things smaller: the same sideways offset $b$ is divided by a bigger depth $a$.
The last formula turns $c\in[-1,1]$ back into a pixel column.

Example: $\vec p=(4.5,2.5)$ facing north, $\vec q=(5.5,0.5)$. With $M=\begin{bmatrix}0&0.66\\-1&0\end{bmatrix}$,
$M^{-1}=\begin{bmatrix}0&-1\\1.515&0\end{bmatrix}$, so $(a,b)=(2,\,1.515)$, $c=0.7576$, pixel $x\approx1125$. Casting the ray
for that column gives $\vec r=\vec d+c\vec P=(0.5,-1)$ and $\vec p+2\vec r=(5.5,0.5)=\vec q$. ✓ (verified numerically.)

The raycaster runs this backwards: for each column it starts from $c$, builds $\vec r=M\binom{1}{c}$, and searches the
grid for the point where the ray arrives. Note that $a$ is the **depth** of the hit along $\vec d$; §4 shows the
ray parameter $t$ is that same number.

---

## 3. DDA: walking the grid

### 3.1 A ray is a line, and grid lines are at integers

$$\vec q(t)=\vec p+t\,\vec r,\qquad t\ge 0.$$

$\vec q(t)$ is the point you reach after walking $t$ copies of $\vec r$ from the player; $t$ is the **ray parameter**, and $t=0$ is the
player. The grid lines are the lines $x=k$ and $y=k$ for whole numbers $k$ (the borders of the cells). $p_x,\,r_x$ are the x parts of
$\vec p,\,\vec r$. The ray crosses a vertical grid line $x=k$ when $p_x+t\,r_x=k$, i.e. at $t=\dfrac{k-p_x}{r_x}$. Consecutive
vertical lines are hit at parameters that differ by

$$\Delta t_x=\frac1{|r_x|},\qquad \Delta t_y=\frac1{|r_y|}.$$

In the code these two numbers are `delta_dist_x` and `delta_dist_y`.

($\Delta$ means "the gap between two neighbours"; $|r_x|$ is $r_x$ without its minus sign.) Geometrically: moving by
$\Delta t_x\,\vec r$ changes $x$ by exactly 1. The crossings of the vertical lines form an *arithmetic sequence* in $t$ (numbers
with a constant gap, like $0.5,\,1.5,\,2.5,\dots$), and so do the crossings of the horizontal lines.

![delta_dist](../media/DeltaDist.gif)

```c
ray->delta_dist_x = 1e30;              /* r_x == 0: the ray never crosses a vertical line */
if (ray->dir_x != 0)
    ray->delta_dist_x = fabs(1.0 / ray->dir_x);
```

### 3.2 The first crossings

Starting at the cell $\vec m=\lfloor\vec p\rfloor$ (the player's position rounded down; `map_x`, `map_y`), the first crossing of each family
of lines is the part of a cell still ahead, times $\Delta t$:

$$\text{side\_dist}_x=\begin{cases}(p_x-m_x)\,\Delta t_x & r_x<0\\ (m_x+1-p_x)\,\Delta t_x & r_x\ge0\end{cases}$$

(and the same for $y$), with $\text{step}_x=\operatorname{sign}(r_x)$, i.e. $-1$ if the ray goes left and $+1$ if it goes right. That is
`ray_set_x_distance`:

```c
if (ray->dir_x < 0) { ray->step_x = -1; ray->side_dist_x = (game->player.x - ray->map_x) * ray->delta_dist_x; }
else                { ray->step_x =  1; ray->side_dist_x = (ray->map_x + 1.0 - game->player.x) * ray->delta_dist_x; }
```

### 3.3 The loop merges two sorted lists

We have two increasing sequences, $\text{side\_dist}_x+k\,\Delta t_x$ and $\text{side\_dist}_y+k\,\Delta t_y$ ($k=0,1,2,\dots$). Walking the
grid means visiting their union **in order**: always advance whichever comes next. That is the whole algorithm, called **DDA**
(digital differential analyzer, the name of this kind of line-walking method). `side` records which kind of line was just
crossed: $0$ = a vertical line (the ray moved in x), $1$ = a horizontal line (it moved in y).

```c
while (!ray->hit)
{
    if (ray->side_dist_x < ray->side_dist_y) { ray->side_dist_x += ray->delta_dist_x; ray->map_x += ray->step_x; ray->side = 0; }
    else                                     { ray->side_dist_y += ray->delta_dist_y; ray->map_y += ray->step_y; ray->side = 1; }
    if (map_is_wall(game, ray->map_x, ray->map_y))
        ray->hit = 1;
}
```

![DDA walk](../media/DDAWalk.gif)

Real trace for column $x=1040$ of the demo room (player at $(2.5,4.5)$ facing east; $c=0.625$, so $\vec r=(1,\,0.4125)$,
$\Delta t_x=1.00$, $\Delta t_y=2.42$):

| iter | side_dist_x | side_dist_y | smaller → step | cell entered |
|---:|---:|---:|:--:|:--:|
| 1 | 0.500 | 1.212 | x | (3,4) |
| 2 | 1.500 | 1.212 | y | (3,5) |
| 3 | 1.500 | 3.636 | x | (4,5) |
| 4 | 2.500 | 3.636 | x | (5,5) |
| 5 | 3.500 | 3.636 | x | (6,5) |
| 6 | 4.500 | 3.636 | y | (6,6) |
| 7 | 4.500 | 6.061 | x | (7,6) |
| 8 | 5.500 | 6.061 | x | (8,6) |
| 9 | 6.500 | 6.061 | y | **(8,7) wall** |

(values are those *before* each step; ties go to $y$ because the test is `<`.) Nine iterations instead of hundreds, no
trig, and no wall can be skipped, because every cell the ray passes through is visited.

The number of iterations is at most $|\Delta m_x|+|\Delta m_y|$, the number of grid lines crossed ($\Delta m_x$ and $\Delta m_y$ are
how many cells the ray moves in x and in y between the player and the wall). Over a whole
frame on `maps/sample.cub` (player at spawn, 1280 rays), counted with the same Python mirror:

![Step count](../media/StepCount.gif)

| method | grid steps per frame |
|---|---:|
| fixed step $\varepsilon=0.01$ | 205,830 |
| fixed step $\varepsilon=0.05$ | 41,766 |
| DDA (this project) | **3,193** |

That is 64× fewer than $\varepsilon=0.01$, with exact cell boundaries and 0 trig calls per ray. (Counts are for this small
map; the gap grows with room size since DDA is linear in distance and stepping is $d/\varepsilon$ per ray.)

`map_is_wall` treats out-of-bounds and `' '` as walls, so the loop always terminates on maps the parser accepted.

---

## 4. Perpendicular distance is a dot product

When the loop ends, `side_dist` has already been advanced one $\Delta t$ past the crossing we care about, so the
ray parameter of the hit is

$$t_{\text{hit}}=\text{side\_dist}-\Delta t .$$

($t_{\text{hit}}$ is the ray parameter at the wall.) The Euclidean distance is $t_{\text{hit}}\,|\vec r|$ (the length of $\vec r$ times
how many copies of it we walked), but the quantity we need for projection is the distance **along the view axis** $\vec d$, the
depth $a$ of §2.5:

$$\frac{\vec d\cdot(t\,\vec r)}{|\vec d|}=t\,\big(\vec d\cdot\vec d+c\,\vec d\cdot\vec P\big)=t\,(1+c\cdot 0)=t .$$

$\vec d\cdot\vec P=0$ (perpendicular) and $|\vec d|=1$ make $\vec d\cdot\vec r=1$ for **every** column. So the ray parameter *is* the perpendicular
distance; no correction is needed. This is the whole fisheye fix:

```c
if (ray->side == 0) ray->wall_dist = ray->side_dist_x - ray->delta_dist_x;
else                ray->wall_dist = ray->side_dist_y - ray->delta_dist_y;
```

It agrees with the angle picture of §1 (here $\theta$ is the angle between the ray and $\vec d$): $|\vec r|=\sqrt{1+(0.66c)^2}=1/\cos\theta$, so
$\text{Euclid}=t|\vec r|=t/\cos\theta$ and $\text{perp}=\text{Euclid}\cdot\cos\theta=t$ (checked numerically, e.g. $|\vec r|=1.0597$,
$1/|\vec r|=0.94367=\cos\theta$).

![Perpendicular distance](../media/PerpDistance.gif)

---

## 5. Projection to a column

Put the view plane (the imaginary window) at depth 1. A wall of height 1 at depth $z$ (`wall_dist`, the perpendicular distance
from §4) is, by *similar triangles* (triangles of the same shape, so their sides are in proportion), $1/z$ tall on that plane.
Scaling the plane to $H$ pixels (`HEIGHT`) gives the height in pixel rows, $\text{lh}$ (`line_height`):

$$\text{line\_height}=\Big\lfloor\frac{H}{z}\Big\rfloor,\qquad
\text{draw\_start}=\tfrac H2-\tfrac{\text{lh}}2,\quad \text{draw\_end}=\tfrac H2+\tfrac{\text{lh}}2$$

where $\lfloor\cdot\rfloor$ rounds down. The wall is centred on the middle row $H/2$; $\text{draw\_start}$ and $\text{draw\_end}$ are its first and
last screen row. "Clamped to $[0,H-1]$" means a value below $0$ becomes $0$ and a
value above $H-1$ becomes $H-1$, so nothing is drawn outside the screen (`ray_project`):

```c
ray->line_height = (int)(HEIGHT / ray->wall_dist);
ray->draw_start = HEIGHT / 2 - ray->line_height / 2;
ray->draw_end   = HEIGHT / 2 + ray->line_height / 2;
```

![Projection](../media/Projection.gif)

Examples ($H=720$): $z=3\Rightarrow$ 240 rows (240..480); $z=1\Rightarrow$ the full 720. Below $z=1$ the wall is taller than
the screen and the clamp applies. The demo column of §3 ($z=6.06$) draws 118 rows, 301..419.

Sweeping $c$ from $-1$ to $1$ and drawing each column gives the picture (96 columns shown; the C code uses 1280):

![Frame sweep](../media/FrameSweep.gif)

---

## 6. Texture mapping

### 6.1 Which column of the texture

A *texture* is a picture pasted on the wall, and a *texel* is one pixel of it. The hit point is $\vec q=\vec p+t\,\vec r$. Only the
coordinate *along* the wall matters (y for a vertical wall, `side 0`; x for a horizontal wall, `side 1`; call it $p_{\text{along}}$,
$r_{\text{along}}$ for $\vec p,\vec r$), and only its fractional part $\operatorname{frac}(a)=a-\lfloor a\rfloor$ (the digits after
the decimal point, so $\operatorname{frac}(2.87)=0.87$). That is $\text{wall\_x}$, how far along the wall face the ray hit, from $0$ to $1$.
$W_{\text{tex}}$ is the texture's width in pixels:

$$\text{wall\_x}=\operatorname{frac}\big(p_{\text{along}}+t\,r_{\text{along}}\big),\qquad \text{tex\_x}=\lfloor \text{wall\_x}\cdot W_{\text{tex}}\rfloor .$$

Going down the screen column, the texture row advances by a constant `texture_step = tex_height / line_height` (how many texture
rows to move per screen row), starting at
`texture_pos = (draw_start - HEIGHT/2 + line_height/2) * texture_step` (`texture_pos` is the texture row used for the first drawn pixel,
`tex_height` the texture's height in pixels; the start is non-zero when the wall is taller than the screen and its top is cut off).

![Texture column](../media/TextureColumn.gif)

The texture is also chosen per face, using the side and the ray's step: `side 0, step_x>0` hits a wall's **west** face
(`TEX_WE`), `step_x<0` its east face; `side 1, step_y>0` hits the **north** face (`TEX_NO`) (y grows downward). The
names are faces seen, not directions travelled.

### 6.2 ⚠ The horizontal flip is mirrored (finding)

After `tex_x` is computed the code flips it:

```c
if (ray->side == 0 && ray->dir_x > 0)  ray->texture_x = ray->texture->width - ray->texture_x - 1;
if (ray->side == 1 && ray->dir_y < 0)  ray->texture_x = ray->texture->width - ray->texture_x - 1;
```

These are the conditions from Lode Vandevenne's tutorial, whose starting vectors are $\vec d=(-1,0)$, $\vec P=(0,0.66)$, i.e.
$\vec P=0.66\,(d_y,\,-d_x)$. This project uses $\vec P=0.66\,(-d_y,\,d_x)$, the *opposite* sign, which is the correct
handedness for a y-down map (facing north, screen-right is $+x$, see §2.1). With the plane mirrored, the tutorial's flip
rule ends up mirroring the picture. (That is my explanation for the mismatch; the numeric check below is what shows it.)

Checked on the Python mirror (whose `texture_x` matches the compiled C on all sampled columns): standing in a room
and looking at a wall in each of the four directions, `tex_x` **decreases** as the screen $x$ increases in all four cases,
whereas it should increase. Swapping the two conditions to `dir_x < 0` and `dir_y > 0` makes it increase in all four.

![Mirror test](../media/MirrorFlip.png)

The stone textures in `Raycaster/textures/` are irregular enough that this is hard to notice by eye. I did not run the
game window; if you want to confirm, load a texture with visible asymmetry (text or an arrow) and look at it. I have not
modified anything under `Raycaster/`.

---

## 7. Drawing a column

The *framebuffer* is the block of memory holding one colour per screen pixel; the pixel at column $x$, row $y$ lives at index
$y\cdot W+x$. For each column, `draw_column` fills three vertical runs of it:

| rows | colour |
|---|---|
| $[0,\text{draw\_start})$ | ceiling `C r,g,b` |
| $[\text{draw\_start},\text{draw\_end}]$ | texel `(tex_x, int(texture_pos))`, sampled down the column |
| $(\text{draw\_end},H)$ | floor `F r,g,b` |

Walls hit on a horizontal edge (`side == 1`) are darkened by halving each colour channel (red, green, blue), the cheap lighting trick that gives corners depth:

```c
if (shade) return (get_rgba(r / 2, g / 2, b / 2, a));
```

Colours are packed into one 32-bit number, `r<<24 | g<<16 | b<<8 | a` (`get_rgba`; `<<` shifts bits left, `|` joins them; $a$ is alpha,
the opacity). The demo frame below was drawn with a software copy of this
code (`common/frame.py`, real textures, `maps/sample.cub` colours):

![Demo frame](../media/frame_demo.png)

---

## 8. The player

### 8.1 Movement is a combination of the camera basis

Let $\text{dt}$ be the seconds since the previous frame (`delta_time`). The distance moved this frame is
$s=\text{dt}\cdot\text{MOVE\_SPEED}$ ($3.0$ cells per second, so speed does not depend on frame rate). Forward/back (W/S) moves along
$\vec d$; A/D *strafe*, i.e. move sideways without turning. $\leftarrow$ means "becomes":

$$\text{W/S: } \vec p\leftarrow\vec p\pm s\,\vec d,\qquad \text{A/D: } \vec p\leftarrow\vec p\pm s\,J\vec d,\qquad J=\begin{bmatrix}0&-1\\1&0\end{bmatrix}.$$

$J\vec d=\vec P/0.66$, so strafing moves parallel to the camera plane. Turning is $R(\alpha)$ from §2.4 with
$\alpha=\text{dt}\cdot\text{ROT\_SPEED}$ ($2.0$ radians per second).

![Player motion](../media/PlayerMotion.gif)

Two small observations: W+D moves by $s(\vec d+J\vec d)$, of length $\sqrt2\,s$, so diagonal movement is 41% faster
(the input is not *normalised*, i.e. not scaled back to length 1). And since `player_rotate` is applied incrementally, rounding error could in principle make
$|\vec d|$ drift from 1, which would break $\vec d\cdot\vec r=1$; measured over $10^6$ rotations it stays within $4\times10^{-11}$
(and $\vec d\cdot\vec P\approx10^{-14}$), so it is not a practical problem.

### 8.2 Collision

`position_is_open` checks the four corners $(x\pm0.2,\;y\pm0.2)$ (`WALL_MARGIN`) against the grid, and `player_try_move`
tests the two axes separately:

```c
if (position_is_open(game, next_x, game->player.y)) game->player.x = next_x;
if (position_is_open(game, game->player.x, next_y)) game->player.y = next_y;
```

If the diagonal is blocked on one axis only, the player **slides** along the wall instead of sticking.

![Collision](../media/Collision.gif)

---

## 9. One frame end to end

```c
void render_frame(t_game *game)
{
    for (x = 0; x < WIDTH; x++)
    {
        ray_init(game, &ray, x);        /* c, r = M(1,c), delta_dist, side_dist */
        ray_dda(game, &ray);            /* merge the two crossing sequences      */
        ray_project(&ray);              /* t_hit = depth; line_height = H/t      */
        ray_set_texture(game, &ray);    /* wall_x, tex_x, tex_step               */
        draw_column(game, &ray, x);
    }
}
```

![Pipeline](../media/Pipeline.gif)

| Object | Where | What it does |
|---|---|---|
| $M=[\vec d\ \vec P]$ | `player.dir_*`, `player.plane_*` | camera basis; $\vec r=M\binom{1}{c}$ |
| $J$ (90° rotation) | `player_init`, strafe in `player_input` | builds $\vec P$; right-hand direction |
| $R(\alpha)$ | `player_rotate` | turn: $M\leftarrow R(\alpha)M$ |
| $\vec r\cdot\vec d=1$ | `ray_project` | `wall_dist` is already perpendicular |
| $\vec p+t\vec r$ | `ray_dda`, `ray_set_texture` | grid walk and hit point |

Per column: 0 trig calls, 0 square roots, one division for $1/r_x$, one for $1/r_y$, one for $H/z$ (plus `camera_x` and
`texture_step`), and at most $|\Delta m_x|+|\Delta m_y|$ loop iterations. Trig appears only when the player turns.

---

## Appendix A. Findings while reading the code

| # | Finding | Severity |
|---|---|---|
| 1 | Texture `tex_x` is mirrored in all four wall directions (§6.2); swap the two flip conditions. | visible if the texture is asymmetric |
| 2 | W+D (and any two movement keys) are not normalised: diagonal speed is $\sqrt2$× (§8.1). | minor |
| 3 | `draw_start..draw_end` is inclusive, so an even `line_height` draws `line_height+1` rows. | cosmetic |
| 4 | Horizontal scale is $(W/2)/0.66\approx970$ px per unit at depth 1 but the vertical scale is `HEIGHT` $=720$, so the image is about 26% vertically compressed relative to a square-pixel pinhole camera. Standard for this algorithm; change only if you want a true 66.8° vertical-consistent view. | informational |
| 5 | `Raycaster/README.md` mentions MLX42, but the code uses GLFW/OpenGL (`cub3d.h`, `gl_ext.h`). | docs |

## Appendix B. Rebuilding everything

```sh
cd visualize_explain
uv run python tools/render.py            # all GIFs/PNGs into media/  (needs LaTeX for MathTex; ffmpeg for GIFs)
uv run python tools/render.py DDAWalk    # one scene
uv run python tools/crosscheck.py        # compares common/raycast.py with the real C (needs gcc)
```

Scenes live in `scenes/s01…s09`, the C mirror in `common/raycast.py`. Nothing in `Raycaster/` is modified.
