#include "includes/cub3d.h"
#include <stdio.h>
#include <string.h>
/* Drives the REAL ray_init / ray_dda / ray_project / ray_set_texture /
   player_rotate from the repo. Prints one line per sampled column. */
static t_texture tex[4];
int main(int argc, char **argv)
{
	static const char *rows[] = {"1111111111","1000000001","1000000001","1000000001","1111111111"};
	t_game g; t_ray r; int i, xs[] = {0, 160, 320, 480, 640, 800, 960, 1120, 1279};
	double px, py, ang;
	if (argc < 4) return 1;
	px = atof(argv[1]); py = atof(argv[2]); ang = atof(argv[3]);
	memset(&g, 0, sizeof g);
	g.scene.map.width = 10; g.scene.map.height = 5;
	g.scene.map.grid = malloc(sizeof(char *) * 5);
	for (i = 0; i < 5; i++) g.scene.map.grid[i] = strdup(rows[i]);
	for (i = 0; i < 4; i++) { tex[i].width = 64; tex[i].height = 64; g.texture[i] = &tex[i]; }
	g.player.x = px; g.player.y = py;
	g.player.dir_x = 1; g.player.dir_y = 0;           /* spawn facing E */
	g.player.plane_x = -g.player.dir_y * CAMERA_PLANE;
	g.player.plane_y =  g.player.dir_x * CAMERA_PLANE;
	player_rotate(&g, ang);                            /* real rotation code */
	printf("dir %.9f %.9f plane %.9f %.9f\n", g.player.dir_x, g.player.dir_y, g.player.plane_x, g.player.plane_y);
	for (i = 0; i < 9; i++) {
		ray_init(&g, &r, xs[i]); ray_dda(&g, &r); ray_project(&r); ray_set_texture(&g, &r);
		printf("x %4d cam %.6f rdir %.9f %.9f map %d %d side %d wall_dist %.9f lh %d ds %d de %d tex_x %d tex %d\n",
			xs[i], r.camera_x, r.dir_x, r.dir_y, r.map_x, r.map_y, r.side, r.wall_dist,
			r.line_height, r.draw_start, r.draw_end, r.texture_x, (int)(r.texture - &tex[0]));
	}
	return 0;
}
