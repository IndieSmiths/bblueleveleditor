"""Facility for function to initialize game."""

### standard library imports

from contextlib import redirect_stdout

from io import StringIO


### third-party imports

## our first pygame import has the stdout redirected,
## to prevent the default message to be printed on the
## screen;
##
## don't worry, we proudly credit the usage of pygame in
## prominent spots in our apps/games/tools

with StringIO() as temp_stream:
    with redirect_stdout(temp_stream):
        from pygame.mixer import pre_init as pre_init_mixer

from pygame.locals import SCALED

from pygame.display import set_mode, set_caption, init as init_display

from pygame.font import init as init_font

from pygame.time import Clock



pre_init_mixer(frequency=44100)

init_display()
init_font()

set_caption("Scaled Level Editor", "SLE")

SCREEN = set_mode((320, 180), SCALED, 32)

SCREEN_RECT = SCREEN.get_rect()
blit_on_screen = SCREEN.blit
fill_screen = SCREEN.fill
BG_COLOR = 'lightblue'

SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_RECT.size

screen_colliderect = SCREEN_RECT.colliderect

FPS = 30
MSECS_PER_FRAME = 1000 / FPS
maintain_fps = Clock().tick
