#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame as pg
from pygame import sprite
from itertools import cycle
from random import randint

SPRITES_FILENAME = './media/sprites_hq_.png'

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

DEMO_FIELD = """###############
                #P+___________#
                #+#_#_#_#_#_#_#
                #_____________#
                #_#_#_#_#_#_#_#
                #_____________#
                #_#_#_++++#_#_#_#_#
                #_____++++________#
                #_#_#_++++#_#_#_#_#
                #_____________#
                #_#_#_#_#_#_#_#
                #_____________#
                ###############"""


def get_closer_center(x, y):
    """returns closer block coordinates for place objects"""
    return round(x / BLOCK_WIDTH) * BLOCK_WIDTH, \
        round(y / BLOCK_HEIGHT) * BLOCK_HEIGHT


class Block(sprite.Sprite):
    """abstract class for static objects"""
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
    """indestructible block"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = kwargs["sprites_tile"][3][3]

    def __repr__(self):
        return f"X{self.rect.x // BLOCK_WIDTH, self.rect.y // BLOCK_HEIGHT}"


class BrickBlock(Block):
    """destructible block"""
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
    """bomb class for placing by Player()"""
    def __init__(self, x, y, sprites_tile, timer=1, radius=1):
        super().__init__(x, y)
        self.sprites_tile = sprites_tile
        self.image = sprites_tile[3][0]
        self.countdown = timer
        self.radius = radius
        self.animation_rate = ANIMATION_RATE / (self.countdown + .55)
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
    """Explosion class.
    Objects placed by Bomb class after timeout.
    Destroy objects by .exploded() method"""
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
        """make images lists for animations of death-rays"""
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

            # making death-rays of a given length
            for distance in range(self.radius):
                # rays bodies
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

            # rays ends
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
        """returns ShiftableSpriteGroup() group of death-rays"""
        return self.splash_group

    def fired(self):
        """is explosion ends?"""
        return not self.anim_center

    def get_direction_and_distance(self, sprite):
        """calculate distance and direction of collision"""
        delta_x = self.rect.x - sprite.rect.x
        delta_y = self.rect.y - sprite.rect.y

        direction = -1
        if delta_x > 0:
            direction = 0
        elif delta_x < 0:
            direction = 1
        elif delta_y > 0:
            direction = 2
        elif delta_y < 0:
            direction = 3

        distance = max(abs(delta_x), abs(delta_y)) // BLOCK_WIDTH
        
        return direction, distance

    def get_rays_lengths(self, groups, maxlen=0):
        """calculate maximum rays lengths to sprites from collection of groups
        returns tuple of distances (left, right, up, down)
        directions:
        0 - left
        1 - right
        2 - up
        3 - down"""


    def collide(self, list_of_sprites_group):
        """processing of death-rays touching
        by sprites in collection of groups"""
        collisions = []
        for sprites_group in list_of_sprites_group:
            collisions += sprite.groupcollide(sprites_group,
                                              self.splash_group,
                                              False,
                                              False)
        for collision in collisions:
            # trying to destroy collided sprites
            collision.exploded()
            if isinstance(collision, WallBlock) or isinstance(collision, BrickBlock):
                direction, distance = self.get_direction_and_distance(collision)
                print(direction, distance)


class Actor(sprite.Sprite):
    """abstract class for moving objects"""
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
        """death-ray of Explosion() touched here"""
        # self.alive = False

    def get_center_position(self):
        """return self center point for camera movement"""
        return self.rect.x + self.rect.w // 2, \
            self.rect.y + self.rect.h // 2


class Player(Actor):
    """main character class"""
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
            self.anim_died = sprites_tile[20][:2] +\
                sprites_tile[20][3:5] +\
                sprites_tile[20][6:7]
            self.anim_died = cycle(self.anim_died + self.anim_died[::-1])
        self.bomb_timer = 0
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
                    self.image = next(self.anim_died)
                    # self.kill()
                    # self = Player(100, 100, sprites_tile=self.sprites_tile)
                    # self = BrickBlock(100,100,sprites_tile=self.sprites_tile)

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
        """static objects collisions processing
        moving through walls here"""
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

    def draw(self, surface):
        """draw himself onto the surface"""
        surface.blit(self.image, self.rect)

    def is_alive(self):
        """check sprite not collided with death-ray from Explosion()"""
        return self.alive


class SpriteSheet:
    """single-file sprites loader class"""
    def __init__(self, filename):
        try:
            self.sheet = pg.image.load(filename).convert()
        except pg.error as message:
            print('Unable to load spritesheet image:', filename)
            raise SystemExit(message)

    def image_at(self, rectangle, colorkey=None):
        """loads image from x, y, x + offset, y + offset"""
        rect = pg.Rect(rectangle)
        image = pg.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is None:
            colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pg.RLEACCEL)
        elif isinstance(colorkey, pg.Color):
            image.set_colorkey(colorkey, pg.RLEACCEL)
        return image

    def images_at(self, rects, colorkey=None):
        """loads multiple images, supply a list of coordinates"""
        return [self.image_at(rect, colorkey) for rect in rects]

    def load_strip(self, rect, image_count, colorkey=None):
        """loads a strip of images and returns them as a list"""
        tups = [(rect[0] + rect[2] * x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)

    def load_table(self, rect, rows, cols, colorkey=None):
        """loads cols*rows of sprites"""
        ret = []
        for i in range(rows):
            tups = [(rect[0] + rect[2] * x,
                     rect[1] + rect[3] * i,
                     rect[2], rect[3])
                    for x in range(cols)]
            ret.append(self.images_at(tups, colorkey))
        return ret


class ShiftableSpriteGroup(sprite.Group):
    """modified sprite.Group with screen shift option
    for camera movement imitation"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view_shift = 0, 0

    def set_view_shift(self, x, y):
        """set shift of "camera" """
        self.view_shift = x, y

    def draw(self, surface):
        """draw all sprites onto the surface"""
        # super().draw(surface)
        sprites = self.sprites()
        surface_blit = surface.blit
        for spr in sprites:
            rect = spr.rect.copy()
            rect.x += self.view_shift[0]
            rect.y += self.view_shift[1]
            self.spritedict[spr] = surface_blit(spr.image, rect)
        self.lostsprites = []

    def contains_sprite_of_class(self, cls):
        """check cls-type sprite in group"""
        for sprite in self:
            if isinstance(sprite, cls):
                return True
        return False


def main():
    pg.init()
    timer = pg.time.Clock()
    screen = pg.display.set_mode(DISPLAY)

    backgroud_surface = pg.Surface(pg.display.list_modes()[0])
    backgroud_surface.fill(pg.Color(BACKGROUND_COLOR))

    font = pg.font.Font(None, 100)
    win_screen = font.render(
                        "WIN!", True, (50, 255, 50))
    fail_screen = font.render(
                        "YOU FAILED!", True, (255, 50, 50))

    ss = SpriteSheet(SPRITES_FILENAME)
    sprites_tile = ss.load_table((0, 0, BLOCK_WIDTH, BLOCK_HEIGHT),
                                 22, 14,
                                 colorkey=pg.Color("#388700"))

    pg.display.set_caption("Demolition expert")
    pg.display.set_icon(sprites_tile[0][5])
    anim_icon = cycle(sprites_tile[2][:7])

    blocks_group = ShiftableSpriteGroup()
    bombs_group = ShiftableSpriteGroup()
    explosions_group = ShiftableSpriteGroup()
    actors_group = ShiftableSpriteGroup()

    player = None
    field_width = field_height = 0
    for row in DEMO_FIELD.replace('\r', '').split('\n'):
        field_width = 0
        for cell in row.strip():
            block = None
            if cell == '#':
                block = WallBlock(field_width,
                                  field_height,
                                  sprites_tile=sprites_tile)
            elif cell == 'B':
                block = BrickBlock(field_width,
                                   field_height,
                                   sprites_tile=sprites_tile)
            elif cell == '_' and not randint(0, 2):
                block = BrickBlock(field_width,
                                   field_height,
                                   sprites_tile=sprites_tile)
            elif cell == 'P' and not player:
                player = Player(field_width,
                                field_height,
                                sprites_tile=sprites_tile)
            if block:
                blocks_group.add(block)
            field_width += BLOCK_WIDTH
        field_height += BLOCK_HEIGHT

    field_center = (field_width // 2 - BLOCK_WIDTH // 2,
                    field_height // 2 - BLOCK_HEIGHT // 2)

    if player is None:
        player = Player(*field_center, sprites_tile=sprites_tile)
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
                    if pg.display.Info().current_w == WIN_WIDTH and \
                       pg.display.Info().current_h == WIN_HEIGHT:
                            pg.display.set_mode(pg.display.list_modes()[0])
                            pg.display.toggle_fullscreen()
                    else:
                        pg.display.toggle_fullscreen()
                        pg.display.set_mode(DISPLAY)
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

        screen.blit(backgroud_surface, cam_shift)

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

        if not player.is_alive():
            screen.blit(fail_screen,
                        (display_w // 2 - fail_screen.get_width() // 2,
                         display_h // 2 - fail_screen.get_height() // 2))

        elif not blocks_group.contains_sprite_of_class(BrickBlock):
            screen.blit(win_screen,
                        (display_w // 2 - win_screen.get_width() // 2,
                         display_h // 2 - win_screen.get_height() // 2))

        pg.display.update()


if __name__ == "__main__":
    main()
