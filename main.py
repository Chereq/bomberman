#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame as pg
from pygame import sprite
from pprint import pprint
from itertools import cycle
from random import randint

# for field
BLOCK_WIDTH = 64
BLOCK_HEIGHT = 64
WIN_WIDTH = 800  # BLOCK_WIDTH * 8
WIN_HEIGHT = 600  # BLOCK_HEIGHT * 8
DISPLAY = (WIN_WIDTH, WIN_HEIGHT)
BACKGROUND_COLOR = "#388700"
BLOCK_COLOR = "#b0b0b0"

# for player
MOVE_SPEED = BLOCK_WIDTH // 8
WIDTH = BLOCK_WIDTH
HEIGHT = BLOCK_HEIGHT
COLOR = "#888888"
ANIMATION_RATE = 10


class Camera(object):

    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def update(self, target):
        self.state = self.camera_func(self.state, target.rect)

    def reverse(self, pos):
        return pos[0] - self.state.left, pos[1] - self.state.top

    @classmethod
    def camera_configure(camera, target_rect):
        l, t, _, _ = target_rect
        _, _, w, h = camera
        l, t = -l + WIN_WIDTH / 2, -t + WIN_HEIGHT / 2

        l = min(0, l)
        l = max(-(camera.width - WIN_WIDTH), l)
        t = max(-(camera.height - WIN_HEIGHT), t)
        t = min(0, t)

        return pg.Rect(l, t, w, h)


def get_closer_center(x, y):
    return round(x / BLOCK_WIDTH) * BLOCK_WIDTH, \
            round(y / BLOCK_HEIGHT) * BLOCK_HEIGHT


class Block(sprite.Sprite):
    def __init__(self, x, y, sprites_tile=None):
        super().__init__()
        self.image = pg.Surface((BLOCK_WIDTH, BLOCK_HEIGHT))
        self.image.fill(pg.Color(BLOCK_COLOR))
        self.rect = pg.Rect(x, y, BLOCK_WIDTH, BLOCK_HEIGHT)
        self.alive = True

    def __repr__(self):
        return "O"

    def update(self, time):
        super().update()

    def exploded(self):
        self.alive = False


class WallBlock(Block):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = kwargs["sprites_tile"][3][3]

    def __repr__(self):
        return f"X{self.rect.x // BLOCK_WIDTH, self.rect.y // BLOCK_HEIGHT}"


class BrickBlock(Block):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = kwargs["sprites_tile"][3][4]
        self.anim_die = kwargs["sprites_tile"][3][5:11]

    def __repr__(self):
        return f"#{self.rect.x // BLOCK_WIDTH, self.rect.y // BLOCK_HEIGHT}"

    def update(self, time):
        super().update(time)
        if self.alive:
            return
        self.image = self.anim_die.pop(0)
        if not self.anim_die:
            self.kill()


class Bomb(Block):
    def __init__(self, x, y, sprites_tile, timer=1, radius=1):
        super().__init__(x, y)
        self.sprites_tile = sprites_tile
        self.image = sprites_tile[3][0]
        self.countdown = timer
        self.radius = radius
        self.animation_rate = ANIMATION_RATE / (self.countdown + .5)
        self.animation_timeout = 0
        self.anim_static = cycle(sprites_tile[3][0:3] +
                                 sprites_tile[3][2:-1:-1])
        self.anim_die = sprites_tile[3][5:11]

    def update(self, time):
        self.animation_timeout += time
        self.countdown -= time / 1000
        self.animation_rate = ANIMATION_RATE / (self.countdown + .5)
        if self.animation_timeout / 1000 >= 1 / self.animation_rate:
            self.animation_timeout = 0
            self.image = next(self.anim_static)

    def is_exploded(self):
        return self.countdown <= 0

    def get_epicenter(self):
        return self.rect.x, self.rect.y

    def get_explosion(self):
        self.kill()
        return Explosion(*self.get_epicenter(),
                         sprites_tile=self.sprites_tile,
                         radius=self.radius)


class Explosion(Block):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.radius = 1
        if "radius" in kwargs:
            self.radius = kwargs["radius"]
        self.blast_speed = 10
        self.ray_power = 1
        self.time = 0

        self.anim_center = [kwargs["sprites_tile"][6][2],
                            kwargs["sprites_tile"][6][7],
                            kwargs["sprites_tile"][11][2],
                            kwargs["sprites_tile"][11][7]]

        self.anim_center += self.anim_center[::-1]
        self.image = self.static_image = kwargs["sprites_tile"][6][2]

        self.anim_center, self.images_inner, self.images_otter = \
            self.get_rays_images(kwargs["sprites_tile"])

        self.splash_group = ShiftableSpriteGroup()

    def get_rays_images(self, sprites_tile):
        centers = (6, 2), (6, 7), (11, 2), (11, 7)
        images_inner = []
        images_otter = []
        images_center = []
        for x, y in centers:
            images_center.append(sprites_tile[x][y])
            images_inner.append(
                (sprites_tile[x][y - 1],
                 sprites_tile[x][y + 1],
                 sprites_tile[x - 1][y],
                 sprites_tile[x + 1][y]))

            images_otter.append(
                (sprites_tile[x][y - 2],
                 sprites_tile[x][y + 2],
                 sprites_tile[x - 2][y],
                 sprites_tile[x + 2][y]))

        images_center += images_center[::-1]
        images_inner += images_inner[::-1]
        images_otter += images_otter[::-1]

        return images_center, images_inner, images_otter

    def update(self, time, interact_with=None):
        self.time += time

        self.collide(interact_with)

        if not self.anim_center:
            self.image = self.static_image
            self.splash_group.empty()
            self.kill()
            return

        if self.time / 1000 >= 1 / self.blast_speed:
            self.time = 0
            self.image = self.anim_center.pop()

            images_otter = self.images_otter.pop()
            images_inner = self.images_inner.pop()

            self.splash_group.empty()

            for distance in range(self.radius):
                sprite_left = sprite.Sprite()
                sprite_left.image = images_inner[0]
                sprite_left.rect = pg.Rect(
                                    self.rect.x - BLOCK_WIDTH * distance,
                                    self.rect.y,
                                    BLOCK_WIDTH,
                                    BLOCK_HEIGHT)
                self.splash_group.add(sprite_left)
                sprite_right = sprite.Sprite()
                sprite_right.image = images_inner[1]
                sprite_right.rect = pg.Rect(
                                        self.rect.x + BLOCK_WIDTH * distance,
                                        self.rect.y,
                                        BLOCK_WIDTH,
                                        BLOCK_HEIGHT)
                self.splash_group.add(sprite_right)
                sprite_up = sprite.Sprite()
                sprite_up.image = images_inner[2]
                sprite_up.rect = pg.Rect(
                                    self.rect.x,
                                    self.rect.y - BLOCK_HEIGHT * distance,
                                    BLOCK_WIDTH,
                                    BLOCK_HEIGHT)
                self.splash_group.add(sprite_up)
                sprite_down = sprite.Sprite()
                sprite_down.image = images_inner[3]
                sprite_down.rect = pg.Rect(
                                        self.rect.x,
                                        self.rect.y + BLOCK_HEIGHT * distance,
                                        BLOCK_WIDTH,
                                        BLOCK_HEIGHT)
                self.splash_group.add(sprite_down)

            sprite_left = sprite.Sprite()
            sprite_left.image = images_otter[0]
            sprite_left.rect = pg.Rect(
                                    self.rect.x - BLOCK_WIDTH * self.radius,
                                    self.rect.y,
                                    BLOCK_WIDTH,
                                    BLOCK_HEIGHT)
            self.splash_group.add(sprite_left)
            sprite_right = sprite.Sprite()
            sprite_right.image = images_otter[1]
            sprite_right.rect = pg.Rect(
                                    self.rect.x + BLOCK_WIDTH * self.radius,
                                    self.rect.y,
                                    BLOCK_WIDTH,
                                    BLOCK_HEIGHT)
            self.splash_group.add(sprite_right)
            sprite_up = sprite.Sprite()
            sprite_up.image = images_otter[2]
            sprite_up.rect = pg.Rect(
                                self.rect.x,
                                self.rect.y - BLOCK_HEIGHT * self.radius,
                                BLOCK_WIDTH,
                                BLOCK_HEIGHT)
            self.splash_group.add(sprite_up)
            sprite_down = sprite.Sprite()
            sprite_down.image = images_otter[3]
            sprite_down.rect = pg.Rect(
                                self.rect.x,
                                self.rect.y + BLOCK_HEIGHT * self.radius,
                                BLOCK_WIDTH,
                                BLOCK_HEIGHT)
            self.splash_group.add(sprite_down)

    def get_splash_group(self):
        return self.splash_group

    def fired(self):
        return not self.anim_center

    def collide(self, list_of_sprites_group):

        collisions = []
        for sprites_group in list_of_sprites_group:
            collisions += sprite.groupcollide(sprites_group,
                                              self.splash_group,
                                              False,
                                              False)
        for collision in collisions:
            collision.exploded()


class Actor(sprite.Sprite):
    def __init__(self, x, y, sprites_tile=None):
        super().__init__()
        self.xvel = self.yvel = 0
        self.anim_right = \
            self.anim_left = \
            self.anim_up = \
            self.anim_down = \
            self.anim_die = \
            self.static_image = None
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.image.fill(pg.Color(COLOR))
        self.rect = pg.Rect(x, y, WIDTH, HEIGHT)
        self.animation_timeout = 0
        self.alive = True

    def exploded(self):
        self.alive = False

    def get_center_position(self):
        return self.rect.x + self.rect.w // 2, \
                self.rect.y + self.rect.h // 2


class Player(Actor):
    def __init__(self, x, y, sprites_tile=None):
        super().__init__(x, y)
        self.sprites_tile = sprites_tile
        if sprites_tile:
            self.image = self.static_image = sprites_tile[0][4]
            self.anim_right = cycle(sprites_tile[1][0:3])
            self.anim_left = cycle(sprites_tile[0][0:3])
            self.anim_up = cycle(sprites_tile[1][3:6])
            self.anim_down = cycle(sprites_tile[0][3:6])
            self.anim_die = sprites_tile[2][6::-1]
        self.bomb_timer = 3
        self.bomb_radius = 1

    def update(self,
               time,
               horizontal=0,
               vertical=0,
               action=False,
               blocks=[],
               directcall=False):

        if not directcall:
            return

        if self.alive:
            self.xvel = horizontal
            self.yvel = vertical
        else:
            self.xvel = self.yvel = 0
        self.animation_timeout += time

        if self.animation_timeout / 1000 >= 1 / ANIMATION_RATE:
            self.animation_timeout = 0
            if self.xvel > 0:
                self.image = next(self.anim_right)
            elif self.xvel < 0:
                self.image = next(self.anim_left)
            elif self.yvel > 0:
                self.image = next(self.anim_down)
            elif self.yvel < 0:
                self.image = next(self.anim_up)
            else:
                self.image = self.static_image
            if not self.alive:
                if self.anim_die:
                    self.image = self.anim_die.pop()
                else:
                    self.kill()

        self.rect.y += self.yvel * MOVE_SPEED
        self.rect.x += self.xvel * MOVE_SPEED
        self.collide(blocks)

        if action and self.alive:
            x, y = get_closer_center(self.rect.x, self.rect.y)
            bomb = Bomb(x, y,
                        sprites_tile=self.sprites_tile,
                        timer=self.bomb_timer,
                        radius=self.bomb_radius)
            self.bomb_timer -= 0.1
            self.bomb_radius += 1
            return bomb

    def collide(self, list_of_sprites_group):

        move_h = move_v = 0

        for sprites_group in list_of_sprites_group:

            collide_list = sprite.spritecollide(self, sprites_group, False)
            for collision in collide_list:
                if collision.rect.x < self.rect.x:
                    move_h += 1

                if collision.rect.x > self.rect.x:
                    move_h -= 1

                if collision.rect.y < self.rect.y:
                    move_v += 1

                if collision.rect.y > self.rect.y:
                    move_v -= 1

        if move_h > 0:
            self.rect.x += MOVE_SPEED
        elif move_h < 0:
            self.rect.x -= MOVE_SPEED
        if move_v > 0:
            self.rect.y += MOVE_SPEED
        elif move_v < 0:
            self.rect.y -= MOVE_SPEED

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def is_alive(self):
        return self.alive


class SpriteSheet:
    def __init__(self, filename):
        try:
            self.sheet = pg.image.load(filename).convert()
        except pg.error as message:
            print('Unable to load spritesheet image:', filename)
            raise SystemExit(message)

    def image_at(self, rectangle, colorkey=None):
        "Loads image from x, y, x + offset, y + offset"
        rect = pg.Rect(rectangle)
        image = pg.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is None:
            colorkey = image.get_at((0, 0))
        elif isinstance(colorkey, pg.Color):
            image.set_colorkey(colorkey, pg.RLEACCEL)
        return image

    def images_at(self, rects, colorkey=None):
        "Loads multiple images, supply a list of coordinates"
        return [self.image_at(rect, colorkey) for rect in rects]

    def load_strip(self, rect, image_count, colorkey=None):
        "Loads a strip of images and returns them as a list"
        tups = [(rect[0] + rect[2] * x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)

    def load_table(self, rect, rows, cols, colorkey=None):
        "Loads cols*rows of sprites"
        ret = []
        for i in range(rows):
            tups = [(rect[0] + rect[2] * x,
                     rect[1] + rect[3] * i,
                     rect[2], rect[3])
                    for x in range(cols)]
            ret.append(self.images_at(tups, colorkey))
        return ret


class ShiftableSpriteGroup(sprite.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view_shift = 0, 0

    def set_view_shift(self, x, y):
        self.view_shift = x, y

    def draw(self, surface):
        # super().draw(surface)
        sprites = self.sprites()
        surface_blit = surface.blit
        for spr in sprites:
            rect = spr.rect.copy()
            rect.x += self.view_shift[0]
            rect.y += self.view_shift[1]
            self.spritedict[spr] = surface_blit(spr.image, rect)
        self.lostsprites = []


def main():
    pg.init()
    timer = pg.time.Clock()
    screen = pg.display.set_mode(DISPLAY)
    bg = pg.Surface(pg.display.list_modes()[0])

    ss = SpriteSheet('./media/sprites_hq.png')
    sprites_tile = ss.load_table((0, 0, BLOCK_WIDTH, BLOCK_HEIGHT), 14, 12, 1)

    pg.display.set_caption("Demolition expert")
    pg.display.set_icon(sprites_tile[0][5])
    anim_icon = cycle(sprites_tile[2][:7])

    bg.fill(pg.Color(BACKGROUND_COLOR))

    blocks_group = ShiftableSpriteGroup()
    bombs_group = ShiftableSpriteGroup()
    explosions_group = ShiftableSpriteGroup()
    actors_group = ShiftableSpriteGroup()

    demo_field = """###############
                    #_____________#
                    #_#_#_#_#_#_#_#
                    #_____________#
                    #_#_#_#_#_#_#_#
                    #_____________#
                    #_#_#_#_#_#_#_#
                    #_____________#
                    #_#_#_#_#_#_#_#
                    #_____________#
                    #_#_#_#_#_#_#_#
                    #_____________#
                    ###############"""

    x = y = 0
    for row in demo_field.replace('\r', '').split('\n'):
        x = 0
        for cell in row.strip():
            block = None
            if cell == '#':
                block = WallBlock(x, y, sprites_tile=sprites_tile)
            elif cell == 'B':
                block = BrickBlock(x, y, sprites_tile=sprites_tile)
            elif cell == '_' and not randint(0, 2):
                block = BrickBlock(x, y, sprites_tile=sprites_tile)
            if block:
                blocks_group.add(block)
            x += BLOCK_WIDTH
        y += BLOCK_HEIGHT
    field_width, field_height = x, y
    player = Player(BLOCK_WIDTH * 5,
                    BLOCK_HEIGHT * 5,
                    sprites_tile=sprites_tile)

    actors_group.add(player)

    horizontal = vertical = 0
    action = False

    while True:

        milliseconds = timer.tick(30)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                raise SystemExit
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_q or event.key == pg.K_ESCAPE:
                    raise SystemExit
                if event.key == pg.K_f:
                    if pg.display.Info().current_w == 800 and \
                       pg.display.Info().current_h == 600:
                            pg.display.set_mode(pg.display.list_modes()[0])
                            pg.display.toggle_fullscreen()
                    else:
                        pg.display.toggle_fullscreen()
                        pg.display.set_mode((800, 600))
                if event.key == pg.K_LEFT:
                    horizontal = -1
                if event.key == pg.K_RIGHT:
                    horizontal = 1
                if event.key == pg.K_UP:
                    vertical = -1
                if event.key == pg.K_DOWN:
                    vertical = 1
                if event.key == pg.K_SPACE:
                    action = True
            if event.type == pg.KEYUP:
                if event.key == pg.K_LEFT or event.key == pg.K_RIGHT:
                    horizontal = 0
                if event.key == pg.K_UP or event.key == pg.K_DOWN:
                    vertical = 0

        if not player.is_alive():
            pg.display.set_icon(next(anim_icon))

        ret = player.update(milliseconds,
                            horizontal,
                            vertical,
                            action,
                            (blocks_group, bombs_group, actors_group),
                            directcall=True)
        blocks_group.update(milliseconds)
        bombs_group.update(milliseconds)
        explosions_group.update(milliseconds, (blocks_group, actors_group))
        actors_group.update(milliseconds)

        screen.blit(bg, (0, 0))

        if ret:
            if isinstance(ret, Bomb):
                bombs_group.add(ret)

        cam_shift = [0, 0]
        display_w = pg.display.Info().current_w
        display_h = pg.display.Info().current_h
        player_x, player_y = player.get_center_position()
        if field_width > display_w:
            cam_shift[0] = max(min(display_w // 2 - player_x, 0),
                               -field_width + display_w)
        else:
            cam_shift[0] = display_w // 2 - field_width // 2
        if field_height > display_h:
            cam_shift[1] = max(min(display_h // 2 - player_y, 0),
                               -field_height + display_h)
        else:
            cam_shift[1] = display_h // 2 - field_height // 2

        for bomb in bombs_group:
            if bomb.is_exploded():
                explosion = bomb.get_explosion()
                explosions_group.add(explosion)

        for explosion in explosions_group:
            splash_group = explosion.get_splash_group()
            cam_shift[0] += randint(-1, 1)
            cam_shift[1] += randint(-1, 1)
            splash_group.set_view_shift(*cam_shift)
            splash_group.draw(screen)

        action = False

        blocks_group.set_view_shift(*cam_shift)
        bombs_group.set_view_shift(*cam_shift)
        explosions_group.set_view_shift(*cam_shift)
        actors_group.set_view_shift(*cam_shift)

        blocks_group.draw(screen)
        bombs_group.draw(screen)
        explosions_group.draw(screen)
        actors_group.draw(screen)
        # player.draw(screen)

        pg.display.update()


if __name__ == "__main__":
    main()
