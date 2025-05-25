
### third-party imports

from pygame import (

    QUIT,

    KEYUP,
    K_ESCAPE, K_RETURN, K_BACKSPACE,

    TEXTINPUT,

    Surface,
    quit as quit_pygame,

)

from pygame.event import get as get_events

from pygame.display import update

from pygame.draw import (
    rect as draw_rect,
    circle as draw_circle,
    line as draw_line,
)


### local imports

from .pygameconstants import (
    FPS,
    SCREEN,
    SCREEN_RECT,
    BG_COLOR,
    maintain_fps,
    fill_screen,
    blit_on_screen,
    screen_colliderect,
)

from .rendertext import render_text



DIGIT_TO_CORNER = { # like digits on the numpad
    1: 'bottomleft',
    2: 'midbottom',
    3: 'bottomright',
    4: 'midleft',
    5: 'center',
    6: 'midright',
    7: 'topleft',
    8: 'midtop',
    9: 'topright',
}

CORNER_TO_DIGIT = {
    corner: digit
    for digit, corner in DIGIT_TO_CORNER.items()
}

CHAR_MAP = {}



class RectPosNameForm:

    def __init__(self):

        self.type_prompt_surf = (

            render_text(
                "Press number from desired pos",
                False,
                'white',
                'blue',
            )

        )

        corner_rect = SCREEN_RECT.copy()
        corner_rect.w *= .5
        corner_rect.h *= .5

        corner_surf = Surface(corner_rect.size).convert()
        corner_surf.fill('blue')
        draw_rect(corner_surf, 'white', corner_rect, 4)
        draw_line(corner_surf, 'white', corner_rect.midtop, corner_rect.midbottom, 4)
        draw_line(corner_surf, 'white', corner_rect.midleft, corner_rect.midright, 4)

        padded_corner_rect = corner_rect.inflate(-6, -6)

        for corner_name, digit in CORNER_TO_DIGIT.items():

            corner_pos = getattr(padded_corner_rect, corner_name)

            digit_surf = render_text(str(digit), False, 'purple')
            digit_rect = digit_surf.get_rect()

            setattr(digit_rect, corner_name, corner_pos)
            draw_circle(corner_surf, 'white', digit_rect.center, 13)
            corner_surf.blit(digit_surf, digit_rect)

        corner_rect.center = SCREEN_RECT.center

        self.corner_surf = corner_surf
        self.corner_rect = corner_rect

    def get_rect_pos_name(self):

        self.running = True
        self.value = None

        while self.running:

            maintain_fps(FPS)

            self.control()
            self.draw()

        return self.value

    def control(self):

        for event in get_events():

            if event.type == TEXTINPUT:

                if (
                    event.text.isdigit()
                    and int(event.text) in DIGIT_TO_CORNER
                ):
                    digit = int(event.text)
                    self.value = DIGIT_TO_CORNER[digit]
                    self.running = False

            elif event.type == KEYUP:

                if event.key == K_ESCAPE:
                    self.running = False

            elif event.type == QUIT:

                quit_pygame()
                quit()

    def draw(self):

        fill_screen('blue')

        blit_on_screen(self.type_prompt_surf, (4, 4))
        blit_on_screen(self.corner_surf, self.corner_rect)

        update()


class LabelTextForm:

    def __init__(self):

        self.type_prompt_surf = (

            render_text(
                "Type label's text; press Enter/Return to confirm;",
                False,
                'white',
                'blue',
            )

        )

    def get_label_text(self):

        self.running = True
        self.value = ''

        while self.running:

            maintain_fps(FPS)

            self.control()
            self.draw()

        return self.value

    def control(self):

        for event in get_events():

            if event.type == TEXTINPUT:
                self.value = self.value + event.text

            elif event.type == KEYUP:

                if event.key in (K_ESCAPE, K_RETURN):
                    self.running = False

                elif event.key == K_BACKSPACE:
                    self.value = self.value[:-1]

            elif event.type == QUIT:

                quit_pygame()
                quit()

    def draw(self):

        fill_screen('blue')

        blit_on_screen(self.type_prompt_surf, (4, 4))

        y = 40
        x = 5

        for char in self.value:

            try:
                char_surf = CHAR_MAP[char]

            except KeyError:

                char_surf = render_text(char, False, 'white', 'blue')
                CHAR_MAP[char] = char_surf

            ###

            blit_on_screen(char_surf, (x, y))
            x += char_surf.get_width()

        update()


get_rect_pos_name = RectPosNameForm().get_rect_pos_name
get_label_text = LabelTextForm().get_label_text

