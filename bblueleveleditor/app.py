"""Facility with function to run the app."""

### standard library imports

from types import SimpleNamespace

from itertools import chain, product

from ast import literal_eval

from collections import deque

from pprint import pformat


### third-party imports

from pygame import (

    QUIT,

    MOUSEMOTION,
    MOUSEBUTTONUP,
    MOUSEBUTTONDOWN,

    KEYDOWN, K_ESCAPE, K_HOME,

    K_w, K_a, K_s, K_d,

    K_q, K_e, K_x, K_r, K_v, K_g,

    Rect, Surface,
    quit as quit_pygame,

)

from pygame.event import get as get_events

from pygame.display import update

from pygame.key import get_pressed as get_pressed_states

from pygame.math import Vector2

from pygame.mouse import get_pos as get_mouse_pos

from pygame.draw import rect as draw_rect, circle as draw_circle

from pygame.image import load as load_image

from pygame.font import Font


### local imports

from .config import (
    FONTS_DIR,
    LEVELS_DIR,
    COLORKEY_ASSETS_DIR,
    NO_COLORKEY_ASSETS_DIR,
)

from .pygameconstants import (
    FPS, SCREEN, SCREEN_RECT,
    maintain_fps, blit_on_screen, screen_colliderect,
)

from .grid import ScrollableGrid



scrolling = Vector2()

unit_rect = Rect(0, 0, 16, 16)

unit_grid   = ScrollableGrid(SCREEN, 1, (255,255,255), unit_rect, area_rect=SCREEN_RECT)
screen_grid = ScrollableGrid(SCREEN, 1, (0,0,0), SCREEN_RECT, area_rect=SCREEN_RECT)

bg = SCREEN.copy()
bg.fill('lightblue')

BACK_PROPS = set()
MIDDLE_PROPS = set()
BLOCKS = set()
ACTORS = set()

BACK_PROPS_ON_SCREEN = set()
MIDDLE_PROPS_ON_SCREEN = set()
BLOCKS_ON_SCREEN = set()
ACTORS_ON_SCREEN = set()

SETS = [
    BACK_PROPS,
    MIDDLE_PROPS,
    BLOCKS,
    ACTORS,
]

get_layer_from_name = {

  'backprops': BACK_PROPS,
  'middleprops': MIDDLE_PROPS,
  'blocks': BLOCKS,
  'actors': ACTORS,

}.__getitem__


SETS_ON_SCREEN = [
    BACK_PROPS_ON_SCREEN,
    MIDDLE_PROPS_ON_SCREEN,
    BLOCKS_ON_SCREEN,
    ACTORS_ON_SCREEN,
]

def do_nothing(): pass

###

render_text = Font(str(FONTS_DIR / 'minimal_5x7.ttf'), 28).render

LETTER_E = render_text('e', False, 'black').convert()

_br = LETTER_E.get_bounding_rect()
LETTER_E = LETTER_E.subsurface(_br)
_bg = LETTER_E.copy()
_bg.fill('white')
_bg.blit(LETTER_E, (0,0))
LETTER_E = _bg


###
SEAMLESS_SURFS_MAP = {}

###

REFS = SimpleNamespace()

REFS.draw_unit_grid = unit_grid.draw
REFS.draw_screen_grid = screen_grid.draw

REFS.is_deleting = False

REFS.mouse_pressed_routine = do_nothing
REFS.seamless_area_drawing_routine = do_nothing

###


_dx_map = (

    dict.fromkeys(

        product(
            *((True, False) for _ in range(2))
        ),

        0,

    )

)

_dx_map[(True, False)] =  1
_dx_map[(False, True)] = -1

_dy_map = _dx_map.copy()

abs_delta = 4

DELTA_MAP = {

    (x_key + y_key) : (x_value * abs_delta, y_value * abs_delta)

    for x_key, x_value in _dx_map.items()
    for y_key, y_value in _dy_map.items()

}

###

###

COLOR_KEY = (192, 192, 192)

asset_data_map = {}

for image_path in chain(
    COLORKEY_ASSETS_DIR.iterdir(),
    NO_COLORKEY_ASSETS_DIR.iterdir()
):

    ###

    suffix = image_path.suffix.lower()

    if suffix != '.png':
        continue

    layer_name, is_seamless, pos_name, _ = image_path.suffixes

    ###

    surf = load_image(str(image_path)).convert()

    if image_path.parent.name == 'colorkey':
        surf.set_colorkey(COLOR_KEY)

    name = image_path.name

    asset_name = name[:name.index('.')]

    asset_data_map[asset_name] = {
        'name' : asset_name,
        'layer_name' : layer_name[1:],
        'pos_name': pos_name[1:],
        'is_seamless': literal_eval(is_seamless[1:]),
        'surf' : surf,
    }

asset_name_deque = deque(sorted(asset_data_map))

seamless_drawing_rect = unit_rect.copy()

def track_and_show_seamless_area():
    seamless_drawing_rect.topleft = unit_rect.topleft
    REFS.seamless_area_drawing_routine = draw_seamless_area

def draw_seamless_area():

    draw_rect(
        SCREEN,
        'fuchsia',
        unit_rect.union(seamless_drawing_rect),
    )

def add_seamless_asset():

    REFS.seamless_area_drawing_routine = do_nothing

    union = unit_rect.union(seamless_drawing_rect)

    asset_name = REFS.current_asset
    pos_name = asset_data_map[asset_name]['pos_name']

    scrolled_pos = getattr(union, pos_name)

    unscrolled_pos = tuple(map(int, scrolled_pos - scrolling))

    layer_name = asset_data_map[asset_name]['layer_name']

    layer = get_layer_from_name(layer_name)

    for obj in layer:

        if (
            obj.name == asset_name
            and obj.rect.colliderect(union)
        ):
            return

    obj_list = layered_objects.setdefault(layer_name, [])

    data = {
        'name': asset_name,
        'size': union.size,
        'pos': unscrolled_pos,
    }

    obj_list.append(data)

    layer = get_layer_from_name(layer_name)

    layer.add(
      Object2D(data, pos_name, scrolled_pos)
    )

    list_objects_on_screen()

def add_asset():

    asset_name = REFS.current_asset
    pos_name = asset_data_map[asset_name]['pos_name']

    scrolled_pos = getattr(unit_rect, pos_name)

    unscrolled_pos = tuple(map(int, scrolled_pos - scrolling))

    layer_name = asset_data_map[asset_name]['layer_name']

    obj_list = layered_objects.setdefault(layer_name, [])

    layer = get_layer_from_name(layer_name)

    for obj_data in obj_list:

        if (
            obj_data['pos'] == unscrolled_pos
            and obj_data['name'] == asset_name
        ):
            return

    data = {
        'name': asset_name,
        'pos': unscrolled_pos,
    }

    obj_list.append(data)

    layer.add(
      Object2D(data, pos_name, scrolled_pos)
    )

    list_objects_on_screen()

def begin_adding_assets():
    REFS.mouse_pressed_routine = add_asset

def stop_adding_assets():
    REFS.mouse_pressed_routine = do_nothing


class Object2D:

    def __init__(self, data, pos_name, pos):

        self.data = data

        name = self.name = data['name']

        if 'size' in data:

            size = data['size']
            key = name, size

            try:
                self.image = SEAMLESS_SURFS_MAP[key]

            except KeyError:

                unit_surf = asset_data_map[name]['surf']

                image = new_seamless_image(unit_surf, size)
                self.image = SEAMLESS_SURFS_MAP[key] = image

        else:
            self.image = asset_data_map[name]['surf']

        self.rect = self.image.get_rect()

        setattr(self.rect, pos_name, pos)

    def draw(self):
        blit_on_screen(self.image, self.rect)

    def draw_outlined(self):
        self.draw()
        draw_rect(SCREEN, 'black', self.rect, 1)

def new_seamless_image(surf, size):

    rect = surf.get_rect()
    area = Rect(0, 0, *size)

    area_surf = Surface(size).convert()

    if surf.get_colorkey():

        area_surf.fill(COLOR_KEY)
        area_surf.set_colorkey(COLOR_KEY)

    blit_on_area = area_surf.blit

    while rect.top < area.bottom:

        blit_on_area(surf, rect)

        rect.left = rect.right

        if rect.left > area.right:

            rect.top = rect.bottom
            rect.left = 0

    return area_surf


def update_asset_refs():

    asset_name = REFS.current_asset = asset_name_deque[0]

    REFS.asset_surf = asset_data_map[asset_name]['surf']

    if asset_data_map[asset_name]['is_seamless']:

        REFS.on_mouse_click   = track_and_show_seamless_area
        REFS.on_mouse_release = add_seamless_asset

    else:

        REFS.on_mouse_click   = begin_adding_assets
        REFS.on_mouse_release = stop_adding_assets


update_asset_refs()

###

def begin_deleting_assets():
    REFS.mouse_pressed_routine = delete_asset

def finish_deleting_assets():
    REFS.mouse_pressed_routine = do_nothing

def delete_asset():

    mouse_pos = get_mouse_pos()

    for_deletion = []

    for a_set in SETS_ON_SCREEN:

        for obj in a_set:

            if obj.rect.collidepoint(mouse_pos):
                for_deletion.append((a_set, obj))

    if not for_deletion: return

    for a_set, obj in for_deletion:

        a_set.remove(obj)

        layer_name = asset_data_map[obj.name]['layer_name']
        layer = get_layer_from_name(layer_name)
        layer.remove(obj)

        layered_objects[layer_name].remove(obj.data)

def toggle_eraser():

    if REFS.on_mouse_click != begin_deleting_assets:

        REFS.on_mouse_click = begin_deleting_assets
        REFS.on_mouse_release = finish_deleting_assets

        REFS.asset_surf = LETTER_E

    else:
        update_asset_refs()


###

try:

    level_path = next(
        path
        for path in LEVELS_DIR.iterdir()
        if path.suffix == '.lvl'
    )

except StopIteration:

    level_path = LEVELS_DIR / 'level.lvl'

    level_data = {
      'layered_objects': {}
    }

else:
    level_data = literal_eval(level_path.read_text(encoding='utf-8'))

layered_objects = level_data['layered_objects']

for layer_name, obj_list in layered_objects.items():

    get_layer_from_name(layer_name).update(

        Object2D(
            obj_data,
            asset_data_map[obj_data['name']]['pos_name'],
            obj_data['pos']
        )

        for obj_data in obj_list

    )

###

def run_app():
    """Run the app's mainloop."""

    list_objects_on_screen()

    while True:

        maintain_fps(FPS)

        control()
        update_app()
        draw()

def control():

    for event in get_events():

        if event.type == QUIT:

            quit_pygame()
            quit()

        elif event.type == MOUSEBUTTONDOWN:

            if event.button == 1:
                REFS.on_mouse_click()

        elif event.type == MOUSEBUTTONUP:

            if event.button == 1:
                REFS.on_mouse_release()

        elif event.type == MOUSEMOTION:
            update_unit_rect_topleft()

        elif event.type == KEYDOWN:

            if event.key in (K_q, K_e):

                asset_name_deque.rotate(
                    -1 if event.key == K_e else 1
                )

                update_asset_refs()

            elif event.key == K_HOME:

                dx, dy = -scrolling
                scroll(dx, dy)

            elif event.key == K_x:
                toggle_eraser()

            elif event.key == K_r:

                REFS.draw_objects = (
                    outline_draw_objects
                    if REFS.draw_objects == normal_draw_objects
                    else normal_draw_objects
                )

            elif event.key == K_g:

                if REFS.draw_unit_grid == do_nothing:

                    REFS.draw_unit_grid = unit_grid.draw
                    REFS.draw_screen_grid = screen_grid.draw

                else:

                    REFS.draw_unit_grid = do_nothing
                    REFS.draw_screen_grid = do_nothing

            elif event.key == K_v:
                level_path.write_text(pformat(level_data), encoding='utf-8')

            elif event.key == K_ESCAPE:

                quit_pygame()
                quit()

    ###

    pressed_states = get_pressed_states()

    dx, dy = DELTA_MAP[

        pressed_states[K_a],
        pressed_states[K_d],
        pressed_states[K_w],
        pressed_states[K_s],

    ]

    if dx or dy:
        scroll(dx, dy)

def update_app():
    REFS.mouse_pressed_routine()

def draw():

    blit_on_screen(bg, (0, 0))
    REFS.draw_objects()

    REFS.seamless_area_drawing_routine()

    REFS.draw_unit_grid()
    REFS.draw_screen_grid()

    asset_data = asset_data_map[REFS.current_asset]

    blit_on_screen(REFS.asset_surf, tuple(v + 6 for v in get_mouse_pos()))

    draw_rect(SCREEN, 'blue', unit_rect, 1)

    draw_circle(
        SCREEN,
        'blue',
        getattr(unit_rect, asset_data['pos_name']),
        4,
    )

    update()

###

def update_unit_rect_topleft():

    horiz_scrolling, vert_scrolling = scrolling

    h_scrolling_rest = horiz_scrolling % 16
    v_scrolling_rest = vert_scrolling % 16

    mx, my = get_mouse_pos()

    x_rest = (mx - h_scrolling_rest) % 16
    y_rest = (my - v_scrolling_rest) % 16

    x = mx - x_rest
    y = my - y_rest

    unit_rect.topleft = x, y

def scroll(dx, dy):

    unit_grid.scroll(dx, dy)
    screen_grid.scroll(dx, dy)

    seamless_drawing_rect.move_ip(dx, dy)

    for prop in BACK_PROPS:
        prop.rect.move_ip(dx, dy)

    for prop in MIDDLE_PROPS:
        prop.rect.move_ip(dx, dy)

    for block in BLOCKS:
        block.rect.move_ip(dx, dy)

    for actor in ACTORS:
        actor.rect.move_ip(dx, dy)

    list_objects_on_screen()

    scrolling.x += dx
    scrolling.y += dy

    update_unit_rect_topleft()

def list_objects_on_screen():

    for layer, on_screen in zip(SETS, SETS_ON_SCREEN):

        on_screen.clear()

        on_screen.update(
            obj
            for obj in layer
            if screen_colliderect(obj.rect)
        )

def normal_draw_objects():

    for prop in BACK_PROPS_ON_SCREEN:
        prop.draw()

    for prop in MIDDLE_PROPS_ON_SCREEN:
        prop.draw()

    for block in BLOCKS_ON_SCREEN:
        block.draw()

    for actor in ACTORS_ON_SCREEN:
        actor.draw()

def outline_draw_objects():

    for prop in BACK_PROPS_ON_SCREEN:
        prop.draw_outlined()

    for prop in MIDDLE_PROPS_ON_SCREEN:
        prop.draw_outlined()

    for block in BLOCKS_ON_SCREEN:
        block.draw_outlined()

    for actor in ACTORS_ON_SCREEN:
        actor.draw_outlined()

REFS.draw_objects = normal_draw_objects
