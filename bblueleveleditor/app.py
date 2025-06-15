"""Facility with function to run the app."""

### standard library imports

from types import SimpleNamespace

from itertools import chain, repeat, product

from ast import literal_eval

from collections import deque

from pprint import pformat

from math import dist

from warnings import warn


### third-party imports

from pygame import (

    QUIT,

    MOUSEMOTION,
    MOUSEBUTTONUP,
    MOUSEBUTTONDOWN,

    KEYDOWN, K_ESCAPE, K_HOME,

    KMOD_SHIFT,

    K_w, K_a, K_s, K_d,

    K_q, K_e,

    K_f,

    K_x, K_r, K_v, K_g, K_p,

    Rect, Surface,
    quit as quit_pygame,

)

from pygame.event import get as get_events

from pygame.display import update

from pygame.key import get_pressed as get_pressed_states

from pygame.math import Vector2

from pygame.mouse import get_pos as get_mouse_pos

from pygame.draw import (
    rect as draw_rect,
    circle as draw_circle,
    line as draw_line,
)

from pygame.image import load as load_image, save as save_image

from pygame.transform import rotate as rotate_surface, flip as flip_surface


### local imports

from .config import (
    NO_COLORKEY_ASSETS_DIR,
    COLORKEY_ASSETS_DIR,
    LEVELS_DIR,
)

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

from .grid import ScrollableGrid

from .rendertext import render_text, render_big_text

from .labelassist import get_rect_pos_name, get_label_text



### module level objs/constants

## vector representing first point where there's content
## in the level, that is, the topleft of the topleftmost
## object, or (0, 0) if the level is empty
##
## this point is used as the starting point from where to place
## level chunks
content_origin = Vector2()

## vector to keep track of scrolling
scrolling = Vector2()

### reference unit area for placing assets
unit_rect = Rect(0, 0, 16, 16)

### grids

unit_grid   = ScrollableGrid(SCREEN, 1, (255,255,255), unit_rect, area_rect=SCREEN_RECT)
screen_grid = ScrollableGrid(SCREEN, 1, (0,0,0), SCREEN_RECT, area_rect=SCREEN_RECT)


### define a vicinity rect
###
### it is a rect equivalent to the SCREEN after we increase it in all four
### directions by its own dimensions, centered on the screen
###
### it is used to detect chunks of the level adjacent to the screen
### (the screen is the visible area)
###   _________________________________
###  |                ^                |
###  |  VICINITY      |                |
###  |  RECT          |                |
###  |           _____|_____           |
###  |          |           |          |
###  |<---------|  SCREEN   |--------->|
###  |          |   RECT    |          |
###  |          |___________|          |
###  |                |                |
###  |                |                |
###  |                |                |
###  |________________v________________|

VICINITY_RECT = (
    SCREEN_RECT.inflate(SCREEN_RECT.width * 2, SCREEN_RECT.height * 2)
)

VICINITY_WIDTH, VICINITY_HEIGHT = VICINITY_RECT.size
vicinity_colliderect = VICINITY_RECT.colliderect

CHUNKS = set()

CHUNKS_IN = set()
CHUNKS_IN_TEMP = set()

### layers

LAYER_NAMES = (
    'backprops',
    'middleprops',
    'blocks',
    'actors',
    'labels',
)


get_layer_from_name = {
    name: set()
    for name in LAYER_NAMES
}.__getitem__

LAYERS = [get_layer_from_name(name) for name in LAYER_NAMES]

ONSCREEN_LAYERS = [
    set()
    for name in LAYER_NAMES
]

###


def do_nothing(): pass

## letter e icon, for when "erasing" assets on canvas


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

REFS.left_or_right = 'right'


## delta map for scrolling level

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

abs_delta = 8

DELTA_MAP = {

    (x_key + y_key) : (x_value * abs_delta, y_value * abs_delta)

    for x_key, x_value in _dx_map.items()
    for y_key, y_value in _dy_map.items()

}

### loading surfs

COLOR_KEY = (192, 192, 192)

asset_spec_map = {}

for image_path, has_transparency in chain(
    zip(NO_COLORKEY_ASSETS_DIR.iterdir(), repeat(False)),
    zip(COLORKEY_ASSETS_DIR.iterdir(), repeat(True)),
):

    ###

    suffix = image_path.suffix.lower()

    if suffix != '.png':

        warn("Non-PNG image asset ignored.", RuntimeWarning)
        continue

    layer_name, is_seamless, orientation, pos_name, _ = image_path.suffixes

    ###
    surf = load_image(str(image_path)).convert()

    if has_transparency:
        surf.set_colorkey(COLOR_KEY)

    name = image_path.name

    asset_name = name[:name.index('.')]

    asset_spec_map[asset_name] = {
        'name' : asset_name,
        'layer_name' : layer_name[1:],
        'pos_name': pos_name[1:],
        'is_seamless': literal_eval(is_seamless[1:]),
        'surf' : surf,
    }

    if orientation[1:] == 'lr':
        asset_spec_map[asset_name]['surf_left'] = flip_surface(surf, True, False)

asset_name_deque = deque(sorted(asset_spec_map))

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
    pos_name = asset_spec_map[asset_name]['pos_name']

    scrolled_pos = getattr(union, pos_name)

    unscrolled_pos = tuple(map(int, scrolled_pos - scrolling))

    layer_name = asset_spec_map[asset_name]['layer_name']

    layer = get_layer_from_name(layer_name)

    for obj in layer:

        if (
            obj.name == asset_name
            and obj.rect.colliderect(union)
        ):
            return

    obj_list = (
        level_data['layered_objects']
        .setdefault(layer_name, [])
    )

    data = {
        'name': asset_name,
        'size': union.size,
        'pos': unscrolled_pos,
    }

    obj_list.append(data)

    ###
    obj = Object2D.from_asset_spec_map(
        data,
        layer_name,
        pos_name,
        scrolled_pos,
    )

    ### if an existing chunk collides add obj to that chunk

    for chunk in chain(CHUNKS_IN, CHUNKS):

        if chunk.rect.colliderect(union):

            chunk.add_obj(obj)
            layer.add(obj)
            break

    ### otherwise create a new chunk

    else:
        
        ## note: we don't need to add the object to the layer here,
        ## because it will be added for us when this new chunk is added
        ## to the set of chunks in vicinity (CHUNKS_IN) inside
        ## update_chunks_and_layers()

        chunk_anchor_pos = union.center
        unscrolled_anchor_pos = chunk_anchor_pos - scrolling
        pos_from_origin = unscrolled_anchor_pos - content_origin

        left_multiplier = pos_from_origin.x // VICINITY_WIDTH
        top_multiplier = pos_from_origin.y // VICINITY_HEIGHT

        left = left_multiplier * VICINITY_WIDTH
        top = top_multiplier * VICINITY_HEIGHT

        VICINITY_RECT.topleft = (
            (left, top)
            + scrolling
            + content_origin
        )

        CHUNKS.add(LevelChunk(VICINITY_RECT, {obj}))

        VICINITY_RECT.center = SCREEN_RECT.center

    update_chunks_and_layers()


def add_asset():

    asset_name = REFS.current_asset
    pos_name = asset_spec_map[asset_name]['pos_name']

    scrolled_pos = getattr(unit_rect, pos_name)

    unscrolled_pos = tuple(map(int, scrolled_pos - scrolling))

    layer_name = asset_spec_map[asset_name]['layer_name']

    obj_list = level_data['layered_objects'].setdefault(layer_name, [])

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

    if (
        'surf_left' in asset_spec_map[asset_name]
        and REFS.left_or_right == 'right'
    ):
        data['facing_right'] = True

    obj_list.append(data)

    ###

    obj = Object2D.from_asset_spec_map(
        data,
        layer_name,
        pos_name,
        scrolled_pos,
    )

    ###

    layer = get_layer_from_name(layer_name)

    ### if an existing chunk collides add obj to that chunk

    rect = obj.rect

    for chunk in chain(CHUNKS_IN, CHUNKS):

        if chunk.rect.colliderect(rect):

            chunk.add_obj(obj)
            layer.add(obj)
            break

    ### otherwise create a new chunk

    else:

        ## note: we don't need to add the object to the layer here,
        ## because it will be added for us when this new chunk is added
        ## to the set of chunks in vicinity (CHUNKS_IN) inside
        ## update_chunks_and_layers()

        chunk_anchor_pos = rect.center
        unscrolled_anchor_pos = chunk_anchor_pos - scrolling
        pos_from_origin = unscrolled_anchor_pos - content_origin

        left_multiplier = pos_from_origin.x // VICINITY_WIDTH
        top_multiplier = pos_from_origin.y // VICINITY_HEIGHT

        left = left_multiplier * VICINITY_WIDTH
        top = top_multiplier * VICINITY_HEIGHT

        VICINITY_RECT.topleft = (
            (left, top)
            + scrolling
            + content_origin
        )

        CHUNKS.add(LevelChunk(VICINITY_RECT, {obj}))

        VICINITY_RECT.center = SCREEN_RECT.center

    update_chunks_and_layers()

def add_label():

    pos_name = get_rect_pos_name()

    if pos_name is None:
        return

    label_text = get_label_text()

    if not label_text:
        return

    scrolled_pos = getattr(unit_rect, pos_name)

    unscrolled_pos = tuple(map(int, scrolled_pos - scrolling))

    layer_name = 'labels'

    obj_list = level_data['layered_objects'].setdefault(layer_name, [])

    for obj_data in obj_list:

        if (
            obj_data['pos'] == unscrolled_pos
            and obj_data['name'] == 'label'
        ):
            return

    data = {
        'name': 'label',
        'text': label_text,
        'pos_name': pos_name,
        'pos': unscrolled_pos,
    }

    obj_list.append(data)
    ###

    obj = Object2D.from_text(data, layer_name, pos_name, scrolled_pos)
    ###

    layer = get_layer_from_name(layer_name)

    ### if an existing chunk collides add obj to that chunk

    rect = obj.rect

    for chunk in chain(CHUNKS_IN, CHUNKS):

        if chunk.rect.colliderect(rect):

            chunk.add_obj(obj)
            layer.add(obj)
            break

    ### otherwise create a new chunk

    else:

        ## note: we don't need to add the object to the layer here,
        ## because it will be added for us when this new chunk is added
        ## to the set of chunks in vicinity (CHUNKS_IN) inside
        ## update_chunks_and_layers()

        chunk_anchor_pos = rect.center
        unscrolled_anchor_pos = chunk_anchor_pos - scrolling
        pos_from_origin = unscrolled_anchor_pos - content_origin

        left_multiplier = pos_from_origin.x // VICINITY_WIDTH
        top_multiplier = pos_from_origin.y // VICINITY_HEIGHT

        left = left_multiplier * VICINITY_WIDTH
        top = top_multiplier * VICINITY_HEIGHT

        VICINITY_RECT.topleft = (
            (left, top)
            + scrolling
            + content_origin
        )

        CHUNKS.add(LevelChunk(VICINITY_RECT, {obj}))

        VICINITY_RECT.center = SCREEN_RECT.center

    update_chunks_and_layers()

def begin_adding_assets():
    REFS.mouse_pressed_routine = add_asset

def stop_adding_assets():
    REFS.mouse_pressed_routine = do_nothing


class Object2D:

    def __init__(self, data, layer_name, pos_name, pos, surf):

        self.data = data
        self.layer_name = layer_name

        name = self.name = data['name']

        ###
        self.image = surf
        ###

        self.rect = self.image.get_rect()

        setattr(self.rect, pos_name, pos)

    @classmethod
    def from_asset_spec_map(cls, data, layer_name, pos_name, pos):

        name = data['name']

        if 'size' in data:

            size = data['size']
            key = name, size

            try:
                surf = SEAMLESS_SURFS_MAP[key]

            except KeyError:

                unit_surf = asset_spec_map[name]['surf']

                surf = new_seamless_image(unit_surf, size)
                SEAMLESS_SURFS_MAP[key] = surf

        else:

            surf = (

                asset_spec_map[name]['surf_left']
                if (
                    'surf_left' in asset_spec_map[name]
                    and not data.get('facing_right', False)
                )

                else asset_spec_map[name]['surf']

            )

        return cls(
            data,
            layer_name,
            pos_name,
            pos,
            surf,
        )

    @classmethod
    def from_text(cls, data, layer_name, pos_name, pos):

        return cls(
            data,
            'labels',
            pos_name,
            pos,
            get_label_surface(data['text'], pos_name),
        )

    def draw(self):
        blit_on_screen(self.image, self.rect)

    def draw_outlined(self):
        self.draw()
        draw_rect(SCREEN, 'black', self.rect, 1)


def get_label_surface(text, pos_name):

    full_text_surf = render_text(text, False, 'white')

    horiz_infl = 2
    vert_infl = 10

    if pos_name == 'midtop':
        full_text_surf = rotate_surface(full_text_surf, -90)

    elif pos_name == 'midbottom':
        full_text_surf = rotate_surface(full_text_surf, 90)

    else:
        horiz_infl, vert_infl = vert_infl, horiz_infl

    text_rect = full_text_surf.get_bounding_rect()
    text_surf = full_text_surf.subsurface(text_rect)

    irect = text_rect.inflate(horiz_infl, vert_infl)

    surf = Surface(irect.size).convert()
    surf.fill('black')

    irect.topleft = (0, 0)

    draw_circle(
        surf,
        'yellow',
        getattr(irect.inflate(-2, -2), pos_name),
        4,
    )

    ###

    text_rect.center = irect.center

    if 'left' in pos_name:
        text_rect.right = irect.right - 2

    elif 'right' in pos_name:
        text_rect.left = irect.left + 2

    elif 'top' in pos_name:
        text_rect.bottom = irect.bottom - 2

    elif 'bottom' in pos_name:
        text_rect.top = irect.top + 2

    surf.blit(text_surf, text_rect)

    ###

    return surf

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
    is_seamless = asset_spec_map[asset_name]['is_seamless']


    if is_seamless:
        REFS.asset_surf = asset_spec_map[asset_name]['surf']

    else:

        REFS.asset_surf = (

            asset_spec_map[asset_name]['surf_left']
            if (
                'surf_left' in asset_spec_map[asset_name]
                and REFS.left_or_right == 'left'
            )

            else asset_spec_map[asset_name]['surf']

        )

    if is_seamless:

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

    for on_screen_layer in ONSCREEN_LAYERS:

        for obj in on_screen_layer:

            if obj.rect.collidepoint(mouse_pos):
                for_deletion.append((on_screen_layer, obj))

    if not for_deletion: return

    layered_objects = level_data['layered_objects']

    for on_screen_layer, obj in for_deletion:

        ### remove object from live layers

        on_screen_layer.remove(obj)
        layer = get_layer_from_name(obj.layer_name)
        layer.remove(obj)

        ### remove object from chunk
        obj.chunk.remove_obj(obj)

        ### remove object's data from level data
        layered_objects[obj.layer_name].remove(obj.data)

def toggle_eraser():

    if REFS.on_mouse_click != begin_deleting_assets:

        REFS.on_mouse_click = begin_deleting_assets
        REFS.on_mouse_release = finish_deleting_assets

        REFS.asset_surf = LETTER_E

    else:
        update_asset_refs()


### loading/creating level data

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



class LevelChunk:

    def __init__(self, rect, objs):

        ### instantiate rect
        self.rect = rect.copy()

        ### store objs
        self.objs = objs

        ### create and store layers

        for layer_name in LAYER_NAMES:
            setattr(self, layer_name, set())

        ### create and store center map, a map to store the
        ### center of each object relative to this chunk's topleft
        ###
        ### also create a local reference to it and an attribute
        ### referencing its item getter method

        center_map = self.center_map = {}
        self.get_center = center_map.__getitem__

        ### iterate over objects...
        ###
        ### - storing them in layers
        ### - storing objects centers relative to level's topleft

        topleft = self.rect.topleft

        for obj in objs:

            obj.chunk = self

            getattr(self, obj.layer_name).add(obj)

            center_map[obj] = tuple(
                chunk_pos - obj_center_pos
                for chunk_pos, obj_center_pos in zip(topleft, obj.rect.center)
            )

    def position_objs(self):

        get_center = self.get_center

        topleft = self.rect.topleft

        for obj in self.objs:

            obj.rect.center = tuple(
                chunk_pos - obj_center_offset
                for chunk_pos, obj_center_offset in zip(topleft, get_center(obj))
            )

    def add_obj(self, obj):

        obj.chunk = self

        self.objs.add(obj)

        getattr(self, obj.layer_name).add(obj)

        self.center_map[obj] = tuple(
            chunk_pos - obj_center_pos
            for chunk_pos, obj_center_pos in zip(self.rect.topleft, obj.rect.center)
        )

    def remove_obj(self, obj):

        self.objs.remove(obj)
        getattr(self, obj.layer_name).remove(obj)
        self.center_map.pop(obj)


def instantiate_and_group_objects():

    layered_objects = level_data['layered_objects']

    ### instantiate all objects

    objs = [

        Object2D.from_text(
            obj_data,
            'labels',
            obj_data['pos_name'],
            obj_data['pos'],
        )
        if layer_name == 'labels'

        else (
            Object2D.from_asset_spec_map(
                obj_data,
                layer_name,
                asset_spec_map[obj_data['name']]['pos_name'],
                obj_data['pos']
            )
        )

        for layer_name, objs in layered_objects.items()
        for obj_data in objs

    ]

    n = len(objs)

    if n == 1:

        obj = objs[0]

        VICINITY_RECT.topleft = obj.topleft
        content_origin.update(obj.topleft)

        CHUNKS.add(LevelChunk(VICINITY_RECT, objs))

    elif n > 1:

        ### XXX idea, not sure if worth pursuing (certainly not now,
        ### probably never): make it so assets that collide with more than
        ### one chunk are added to the one that gets more area after cliping
        ### the asset's rect with the chunk's rect

        ## define a union rect

        first_obj, *other_objs = objs

        union_rect = first_obj.rect.unionall(

            [
                obj.rect
                for obj in other_objs
            ]

        )

        content_origin.update(union_rect.topleft)

        ## prepare to loop while evaluating whether objects
        ## and the union rect collide with the vicinity

        union_left, _ = VICINITY_RECT.topleft = union_rect.topleft

        obj_set = set(objs)

        ## while looping indefinitely

        while True:

            ## if there are objs colliding with the vicinity,
            ## store them in their own level chunk and remove
            ## them from the set of objects

            colliding_objs = {
                obj
                for obj in obj_set
                if vicinity_colliderect(obj.rect)
            }

            if colliding_objs:

                obj_set -= colliding_objs
                CHUNKS.add(LevelChunk(VICINITY_RECT, colliding_objs))

            ## if there's no obj left in the set, break out of loop

            if not obj_set:
                break

            ## reposition vicinity horizontally, as though the union
            ## rect was a table and we were moving the vicinity to the
            ## column to the right
            VICINITY_RECT.x += VICINITY_WIDTH

            ## if vicinity in new position doesn't touch the union
            ## anymore, keep thinking of the union rect as a table and
            ## reposition the vicinity at the beginning of the next
            ## imaginary row

            if not vicinity_colliderect(union_rect):

                VICINITY_RECT.left = union_left
                VICINITY_RECT.y += VICINITY_HEIGHT

instantiate_and_group_objects()

###

def run_app():
    """Run the app's mainloop."""

    VICINITY_RECT.center = SCREEN_RECT.center

    update_chunks_and_layers()

    while True:

        maintain_fps(FPS)

        control()
        update_app()
        draw()


def control():

    for event in get_events():

        if event.type == MOUSEBUTTONDOWN:

            if event.button == 1:
                REFS.on_mouse_click()

        elif event.type == MOUSEBUTTONUP:

            if event.button == 1:
                REFS.on_mouse_release()

        elif event.type == MOUSEMOTION:
            update_unit_rect_topleft()

        elif event.type == KEYDOWN:

            if event.key in (K_q, K_e):

                if event.mod & KMOD_SHIFT:

                    REFS.left_or_right = (
                        'right'
                        if REFS.left_or_right == 'left'
                        else 'left'
                    )

                else:
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

            elif event.key == K_p:

                mark_areas = event.mod & KMOD_SHIFT
                save_level_as_png(mark_areas)

            elif event.key == K_f:
                add_label()

            elif event.key == K_ESCAPE:

                quit_pygame()
                quit()

        elif event.type == QUIT:

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

    fill_screen(BG_COLOR)

    REFS.draw_objects()

    REFS.seamless_area_drawing_routine()

    REFS.draw_unit_grid()
    REFS.draw_screen_grid()

    asset_data = asset_spec_map[REFS.current_asset]

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

    for chunk in CHUNKS:
        chunk.rect.move_ip(dx, dy)

    ###
    update_chunks_and_layers()
    ###

    scrolling.x += dx
    scrolling.y += dy

    update_unit_rect_topleft()

def update_chunks_and_layers():

    ### check current chunks in vicinity

    CHUNKS_IN_TEMP.update(
        chunk
        for chunk in CHUNKS
        if vicinity_colliderect(chunk.rect)
    )

    ### if it is different from previous chunks in vicinity...

    if CHUNKS_IN != CHUNKS_IN_TEMP:

        ### for the chunks leaving vicinity, remove their objects
        ### from the layers

        for chunk in (CHUNKS_IN - CHUNKS_IN_TEMP):

            for layer_name in LAYER_NAMES:

                get_layer_from_name(layer_name).difference_update(
                    getattr(chunk, layer_name)
                )


        ### for the chunks entering vicinity, add their objects to the layers

        for chunk in (CHUNKS_IN_TEMP - CHUNKS_IN):

            for layer_name in LAYER_NAMES:

                get_layer_from_name(layer_name).update(
                    getattr(chunk, layer_name)
                )


        ### update the set of chunks in vicinity

        CHUNKS_IN.clear()
        CHUNKS_IN.update(CHUNKS_IN_TEMP)

    ### for each chunk in vicinity, reposition their objects

    for chunk in CHUNKS_IN:
        chunk.position_objs()

    ### clear temporary chunks collection
    CHUNKS_IN_TEMP.clear()

    ### list objects on screen

    for layer, on_screen in zip(LAYERS, ONSCREEN_LAYERS):

        on_screen.clear()

        on_screen.update(
            obj
            for obj in layer
            if screen_colliderect(obj.rect)
        )

def normal_draw_objects():

    for on_screen_layer in ONSCREEN_LAYERS:
        for prop in on_screen_layer:
            prop.draw()

def outline_draw_objects():

    for on_screen_layer in ONSCREEN_LAYERS:
        for prop in on_screen_layer:
            prop.draw_outlined()


REFS.draw_objects = normal_draw_objects

def save_level_as_png(mark_areas):

    ### position objs relative to their chunks

    for chunk in CHUNKS:
        chunk.position_objs()

    ### create rect union from them

    one, *rest = (
        obj
        for chunk in CHUNKS
        for obj in chunk.objs
    )

    union = one.rect.unionall([obj.rect for obj in rest])

    ### create surface from that rect union and fill it

    s = Surface(union.size).convert()
    s.fill(BG_COLOR)

    ### blit objects in it, layer by layer, as we offset
    ### their rects by the union's topleft

    offset_x, offset_y = (-coord for coord in union.topleft)

    blit_on_surf = s.blit

    for layer_name in LAYER_NAMES:

        for chunk in CHUNKS:

            for obj in getattr(chunk, layer_name):

                blit_on_surf(obj.image, obj.rect.move(offset_x, offset_y))

    ### if we must mark area, draw outline of chunks and screens

    if mark_areas:

        screen_width, screen_height = SCREEN_RECT.size

        ###

        for chunk in CHUNKS:

            offset_chunk_rect = chunk.rect.move(offset_x, offset_y)

            draw_rect(
                s,
                'purple',
                offset_chunk_rect,
                1,
            )

            h1 = Vector2(offset_chunk_rect.topleft)
            h2 = Vector2(offset_chunk_rect.bottomleft)

            for i in range(1, 3):

                draw_line(
                    s,
                    'white',
                    h1 + (screen_width * i, 0),
                    h2 + (screen_width * i, 0),
                    1,
                )

            v1 = Vector2(offset_chunk_rect.topleft)
            v2 = Vector2(offset_chunk_rect.topright)

            for i in range(1, 3):

                draw_line(
                    s,
                    'white',
                    v1 + (0, screen_height * i),
                    v2 + (0, screen_height * i),
                    1,
                )
        
        ###
        level_width, level_height = union.size

        number_of_horiz_sections, remainder = divmod(level_width, screen_width)

        if remainder:
            number_of_horiz_sections += 1

        max_horiz_digits = len(str(number_of_horiz_sections))

        single_digit = render_big_text('0', False, 'white', 'black')

        padding = 10

        left_increment = single_digit.get_width() * max_horiz_digits + (padding * 2)
        top_increment = single_digit.get_height() + (padding * 2)
        increments = (left_increment, top_increment)

        new_surf = Surface(
            tuple(
                dimension + increment
                for dimension, increment in zip(union.size, increments)
            )
        ).convert()

        new_surf.fill('black')
        new_surf.blit(s, increments)

        new_surf_width, new_surf_height = new_surf.get_size()

        x = left_increment + padding
        y = padding
        section_index = 0

        while True:

            digits_surf = (
                render_big_text(
                    str(section_index).rjust(max_horiz_digits, '0'),
                    False,
                    'white',
                    'black',
                )
            )

            new_surf.blit(digits_surf, (x, y))
            x += screen_width
            section_index += 1

            if x > new_surf_width:
                break

        x = padding
        y = top_increment + padding
        section_index = 0

        while True:

            digits_surf = (
                render_big_text(
                    str(section_index).rjust(max_horiz_digits, '0'),
                    False,
                    'white',
                    'black',
                )
            )

            new_surf.blit(digits_surf, (x, y))
            y += screen_height
            section_index += 1

            if y > new_surf_height:
                break

        s = new_surf

    ### save layer on disk as image
    save_image(s, str(LEVELS_DIR / 'level.png'))
