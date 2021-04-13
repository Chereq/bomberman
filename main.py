#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame as pg
from pygame import sprite
from pprint import pprint
from itertools import cycle


# for field
BLOCK_WIDTH = 64
BLOCK_HEIGHT = 64
WIN_WIDTH = BLOCK_WIDTH * 13
WIN_HEIGHT = BLOCK_HEIGHT * 15
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

def get_closer_center(x, y):
    return round(x / BLOCK_WIDTH) * BLOCK_WIDTH, round(y / BLOCK_HEIGHT) * BLOCK_HEIGHT

class Block(sprite.Sprite):
    def __init__(self, x, y, sprites_tile=None):
        # sprite.Sprite.__init__(self)
        super().__init__()
        self.image = pg.Surface((BLOCK_WIDTH, BLOCK_HEIGHT))
        self.image.fill(pg.Color(BLOCK_COLOR))
        self.rect = pg.Rect(x, y, BLOCK_WIDTH, BLOCK_HEIGHT)

    def __repr__(self):
        return "O"

    def update(self, time):
        super().update()

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

class Bomb(Block):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = kwargs["sprites_tile"][3][0]
        self.countdown = 3
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


class Explosion(Block):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.radius = 1
        self.blast_speed = 5
        self.ray_power = 1

    def update(self, time):
        pass


class Actor(sprite.Sprite):
    def __init__(self, x, y, sprites_tile=None):
        self.xvel = self.yvel = 0
        self.anim_right = self.anim_left = self.anim_up = self.anim_down = self.anim_die = self.static_image = None
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.image.fill(pg.Color(COLOR))
        self.rect = pg.Rect(x, y, WIDTH, HEIGHT)
        self.animation_timeout = 0


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

    def update(self, horizontal, vertical, action, blocks, time):

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
    pg.display.set_caption("Bomberman")
    bg = pg.Surface((WIN_WIDTH, WIN_HEIGHT))

    ss = SpriteSheet('./media/sprites_hq.png')
    sprites_tile = ss.load_table((0, 0, BLOCK_WIDTH, BLOCK_HEIGHT), 14, 12)

    bg.fill(pg.Color(BACKGROUND_COLOR))

    sprites_group = sprite.Group()
    bombs_group = sprite.Group()
    explosions_group = sprite.Group()
    actors_group = sprite.Group()
    # blocks = []
    x = y = BLOCK_WIDTH
    for row in demo_field:
        for cell in row:
            if cell:
                block = WallBlock(x, y, sprites_tile=sprites_tile)
                if cell[0] == 'B':
                    block = BrickBlock(x, y, sprites_tile=sprites_tile)
                sprites_group.add(block)
                # blocks.append(block)
            x += BLOCK_WIDTH
        y += BLOCK_HEIGHT
        x = BLOCK_WIDTH
    player = Player(BLOCK_WIDTH * 6, BLOCK_HEIGHT * 5, sprites_tile=sprites_tile)
    # sprites_group.add(player)

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


        ret = player.update(horizontal, vertical, action, (sprites_group, bombs_group, actors_group), time=milliseconds)
        sprites_group.update(milliseconds)
        actors_group.update(milliseconds)
        bombs_group.update(milliseconds)
        explosions_group.update(milliseconds)

        if ret:# and not bombs_group:
            bomb = Bomb(*ret, sprites_tile=sprites_tile)
            bombs_group.add(bomb)

        for bomb in bombs_group:
            if bomb.is_exploded():
                epicenter = bomb.get_epicenter()
                bomb.kill()
                explosion = Explosion(*epicenter)
                explosions_group.add(explosion)

        action = False

        screen.blit(bg, (0, 0))
        sprites_group.draw(screen)
        bombs_group.draw(screen)
        explosions_group.draw(screen)
        player.draw(screen)


        # for i, strip in enumerate(sprites_tile):
        #     for j, image in enumerate(strip):
        #         screen.blit(image, (j*BLOCK_WIDTH, i*BLOCK_HEIGHT))

        screen.blit(sprites_tile[0][5], (0, 0))

        pg.display.update()
        

if __name__ == "__main__":
    main()