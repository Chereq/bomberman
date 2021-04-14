#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame as pg
from pygame import sprite
from pprint import pprint
from itertools import cycle


# for field
BLOCK_WIDTH = 64
BLOCK_HEIGHT = 64
WIN_WIDTH = BLOCK_WIDTH * 5#13
WIN_HEIGHT = BLOCK_HEIGHT * 5#13
DISPLAY = (WIN_WIDTH, WIN_HEIGHT)
BACKGROUND_COLOR = "#388700"  #"#101010"
BLOCK_COLOR = "#b0b0b0"

# for player
MOVE_SPEED = BLOCK_WIDTH // 8
WIDTH = BLOCK_WIDTH
HEIGHT = BLOCK_HEIGHT
COLOR =  "#888888"
ANIMATION_RATE = 10

# 29 * 13

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
    return round(x / BLOCK_WIDTH) * BLOCK_WIDTH, round(y / BLOCK_HEIGHT) * BLOCK_HEIGHT

class Block(sprite.Sprite):
    def __init__(self, x, y, sprites_tile=None):
        # sprite.Sprite.__init__(self)
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sprites_tile = kwargs["sprites_tile"]
        self.image = kwargs["sprites_tile"][3][0]
        self.countdown = 1
        self.radius = 2
        self.animation_rate = ANIMATION_RATE / (self.countdown + .5)
        self.animation_timeout = 0
        self.anim_static = cycle(kwargs["sprites_tile"][3][0:3] + kwargs["sprites_tile"][3][2:-1:-1])
        self.anim_die = kwargs["sprites_tile"][3][5:11]

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
        return Explosion(*self.get_epicenter(), sprites_tile=self.sprites_tile, radius=self.radius)


class Explosion(Block):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.radius = 1
        if "radius" in kwargs:
            self.radius = kwargs["radius"]
        self.blast_speed = 10
        self.ray_power = 1
        self.time = 0

        self.anim_static = [kwargs["sprites_tile"][6][2],
                            kwargs["sprites_tile"][6][7],
                            kwargs["sprites_tile"][11][2],
                            kwargs["sprites_tile"][11][7]]

        self.anim_static += self.anim_static[::-1]
        self.image = self.static_image = kwargs["sprites_tile"][6][2]

        self.anim_static, self.images_inner, self.images_otter = self.get_rays_images(kwargs["sprites_tile"])

        self.splash_group = sprite.Group()

    def get_rays_images(self, sprites_tile):
        centers = (6,2),(6,7),(11,2),(11,7)
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

        if not self.anim_static:
            self.image = self.static_image
            self.splash_group.empty()
            return

        if self.time / 1000 >= 1 / self.blast_speed:
            self.time = 0
            self.image = self.anim_static.pop()

            images_otter = self.images_otter.pop()
            images_inner = self.images_inner.pop()

            self.splash_group.empty()

            for distance in range(self.radius):
                sprite_left = sprite.Sprite()
                sprite_left.image = images_inner[0]
                sprite_left.rect = self.rect.x - BLOCK_WIDTH * distance, self.rect.y, BLOCK_WIDTH, BLOCK_HEIGHT
                self.splash_group.add(sprite_left)
                sprite_right = sprite.Sprite()
                sprite_right.image = images_inner[1]
                sprite_right.rect = self.rect.x + BLOCK_WIDTH * distance, self.rect.y, BLOCK_WIDTH, BLOCK_HEIGHT
                self.splash_group.add(sprite_right)
                sprite_up = sprite.Sprite()
                sprite_up.image = images_inner[2]
                sprite_up.rect = self.rect.x, self.rect.y - BLOCK_HEIGHT * distance, BLOCK_WIDTH, BLOCK_HEIGHT
                self.splash_group.add(sprite_up)
                sprite_down = sprite.Sprite()
                sprite_down.image = images_inner[3]
                sprite_down.rect = self.rect.x, self.rect.y + BLOCK_HEIGHT * distance, BLOCK_WIDTH, BLOCK_HEIGHT
                self.splash_group.add(sprite_down)

            sprite_left = sprite.Sprite()
            sprite_left.image = images_otter[0]
            sprite_left.rect = self.rect.x - BLOCK_WIDTH * self.radius, self.rect.y, BLOCK_WIDTH, BLOCK_HEIGHT
            self.splash_group.add(sprite_left)
            sprite_right = sprite.Sprite()
            sprite_right.image = images_otter[1]
            sprite_right.rect = self.rect.x + BLOCK_WIDTH * self.radius, self.rect.y, BLOCK_WIDTH, BLOCK_HEIGHT
            self.splash_group.add(sprite_right)
            sprite_up = sprite.Sprite()
            sprite_up.image = images_otter[2]
            sprite_up.rect = self.rect.x, self.rect.y - BLOCK_HEIGHT * self.radius, BLOCK_WIDTH, BLOCK_HEIGHT
            self.splash_group.add(sprite_up)
            sprite_down = sprite.Sprite()
            sprite_down.image = images_otter[3]
            sprite_down.rect = self.rect.x, self.rect.y + BLOCK_HEIGHT * self.radius, BLOCK_WIDTH, BLOCK_HEIGHT
            self.splash_group.add(sprite_down)


    def get_splash_group(self):
        return self.splash_group

    def fired(self):
        return not self.anim_static

    def collide(self, list_of_sprites_group):

        death_note = set()
        collisions = []
        for sprites_group in list_of_sprites_group:
            collisions += sprite.groupcollide(sprites_group, self.splash_group, False, False)
        for collision in collisions:
            collision.exploded()
        # for sprite_group in list_of_sprites_group:
        #     for sprite_ext in sprite_group:
        #             collisions = sprite.spritecollide(sprite_ext, self.splash_group, False)
        #             if collisions:
        #                 print(collisions)
        # print(list_of_sprites_group)
        # for sprites_group in list_of_sprites_group:
            # print(123, self.splash_group, sprites_group)
            # print(self.splash_group)
            # print(sprites_group)
            # sprite.groupcollide(self.splash_group, sprites_group, False, False)
            # collide_list = sprite.groupcollide(self.splash_group, sprites_group, False, False)
            # for collision in collide_list:
                # print(collision)
        # raise SystemExit


class Actor(sprite.Sprite):
    def __init__(self, x, y, sprites_tile=None):
        super().__init__()
        self.xvel = self.yvel = 0
        self.anim_right = self.anim_left = self.anim_up = self.anim_down = self.anim_die = self.static_image = None
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.image.fill(pg.Color(COLOR))
        self.rect = pg.Rect(x, y, WIDTH, HEIGHT)
        self.animation_timeout = 0
        self.alive = True

    def exploded(self):
        self.alive = False


class Player(Actor):
    def __init__(self, x, y, sprites_tile=None):
        super().__init__(x, y)
        if sprites_tile:
            self.image = self.static_image = sprites_tile[0][4]
            self.anim_right = cycle(sprites_tile[1][0:3])
            self.anim_left = cycle(sprites_tile[0][0:3])
            self.anim_up = cycle(sprites_tile[1][3:6])
            self.anim_down = cycle(sprites_tile[0][3:6])
            self.anim_die = cycle(sprites_tile[2][:7])

    def update(self, time, horizontal=0, vertical=0, action=False, blocks=[]):

        # if self.alive:
        self.xvel = horizontal
        self.yvel = vertical
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

        self.rect.y += self.yvel * MOVE_SPEED
        self.rect.x += self.xvel * MOVE_SPEED
        self.collide(blocks)

        if action:
            x, y = get_closer_center(self.rect.x, self.rect.y)
            return x, y


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
        "Loads cols*rows sprites"
        ret = []
        for i in range(rows):
            tups = [(rect[0] + rect[2] * x, rect[1] + rect[3] * i, rect[2], rect[3])
                for x in range(cols)]
            ret.append(self.images_at(tups, colorkey))
        return ret


demo_field = [
    [["#"]] * 11,
    [["#"]] + [["B"]] * 9 + [["#"]],
    [["#"], []] * 5 + [["#"]],
    [["#"]] + [[]] * 9 + [["#"]],
    [["#"], []] * 5 + [["#"]],
    [["#"]] + [[]] * 9 + [["#"]],
    [["#"], []] * 5 + [["#"]],
    [["#"]] + [[]] * 9 + [["#"]],
    [["#"], []] * 5 + [["#"]],
    [["#"]] + [[]] * 9 + [["#"]],
    [["#"]] * 11
              ]


def main():
    pg.init()
    timer = pg.time.Clock()
    screen = pg.display.set_mode(DISPLAY)
    pg.display.set_caption("Demolition expert")
    bg = pg.Surface((WIN_WIDTH, WIN_HEIGHT))

    ss = SpriteSheet('./media/sprites_hq.png')
    sprites_tile = ss.load_table((0, 0, BLOCK_WIDTH, BLOCK_HEIGHT), 14, 12)

    bg.fill(pg.Color(BACKGROUND_COLOR))

    blocks_group = sprite.Group()
    bombs_group = sprite.Group()
    explosions_group = sprite.Group()
    actors_group = sprite.Group()
    # test_group = sprite.Group()
    # blocks = []
    x = y = BLOCK_WIDTH
    for row in demo_field:
        for cell in row:
            if cell:
                block = WallBlock(x, y, sprites_tile=sprites_tile)
                if cell[0] == 'B':
                    block = BrickBlock(x, y, sprites_tile=sprites_tile)
                blocks_group.add(block)
                # blocks.append(block)
            x += BLOCK_WIDTH
        y += BLOCK_HEIGHT
        x = BLOCK_WIDTH
    player = Player(BLOCK_WIDTH * 6, BLOCK_HEIGHT * 6.5, sprites_tile=sprites_tile)

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


        ret = player.update(milliseconds, horizontal, vertical, action, (blocks_group, bombs_group, actors_group))
        blocks_group.update(milliseconds)
        bombs_group.update(milliseconds)
        explosions_group.update(milliseconds, (blocks_group, actors_group))
        # actors_group.update(milliseconds)

        screen.blit(bg, (0, 0))

        if ret:# and not bombs_group:
            bomb = Bomb(*ret, sprites_tile=sprites_tile)
            bombs_group.add(bomb)

        for bomb in bombs_group:
            if bomb.is_exploded():
                explosion = bomb.get_explosion()
                # epicenter = bomb.get_epicenter()
                bomb.kill()
                # explosion = Explosion(*epicenter, sprites_tile=sprites_tile)
                explosions_group.add(explosion)

        for explosion in explosions_group:
            splash_group = explosion.get_splash_group()
            splash_group.draw(screen)

            # for splash_sprite in splash_group:
                # explosions_group.add(splash_sprite)
            if explosion.fired():
                explosion.kill()

        action = False

        blocks_group.draw(screen)
        bombs_group.draw(screen)
        explosions_group.draw(screen)
        actors_group.draw(screen)
        # player.draw(screen)


        # for i, strip in enumerate(sprites_tile):
        #     for j, image in enumerate(strip):
        #         screen.blit(image, (j*BLOCK_WIDTH, i*BLOCK_HEIGHT))

        pg.display.update()
        

if __name__ == "__main__":
    main()