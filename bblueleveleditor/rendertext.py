
from pygame.font import Font

from .config import FONTS_DIR



render_text = Font(str(FONTS_DIR/'minimal_5x7.ttf'), 28).render
render_big_text = Font(str(FONTS_DIR/'minimal_5x7.ttf'), 68).render
