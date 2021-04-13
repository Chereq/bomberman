#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame as pg
from pygame import sprite
from pprint import pprint


# for field
BLOCK_WIDTH = 64
BLOCK_HEIGHT = 64
WIN_WIDTH = BLOCK_WIDTH * 13
WIN_HEIGHT = BLOCK_HEIGHT * 15
DISPLAY = (WIN_WIDTH, WIN_HEIGHT)
BACKGROUND_COLOR = "#101010"#"#388700"
BLOCK_COLOR = "#b0b0b0"

# for player
MOVE_SPEED = BLOCK_WIDTH // 8
WIDTH = BLOCK_WIDTH
HEIGHT = BLOCK_HEIGHT
COLOR =  "#888888"

# 29 * 13

def get_closer_center(x, y):
    return round(x / BLOCK_WIDTH) * BLOCK_WIDTH, round(y / BLOCK_HEIGHT) * BLOCK_HEIGHT

class Block(sprite.Sprite):
    def __init__(self, x, y, sprites=None, sprite_tile=None):
        sprite.Sprite.__init__(self)
        # super().__init__()
        self.image = pg.Surface((BLOCK_WIDTH, BLOCK_HEIGHT))
        self.image.fill(pg.Color(BLOCK_COLOR))
        self.rect = pg.Rect(x, y, BLOCK_WIDTH, BLOCK_HEIGHT)

    def __repr__(self):
        return "O"

class WallBlock(Block):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.image = ss.image_at((BLOCK_WIDTH * 3,
        #                             BLOCK_HEIGHT * 3,
        #                             BLOCK_WIDTH,
        #                             BLOCK_HEIGHT))

    def __repr__(self):
        return f"X{self.rect.x // BLOCK_WIDTH, self.rect.y // BLOCK_HEIGHT}"

class BrickBlock(Block):
    def __repr__(self):
        return f"#{self.rect.x // BLOCK_WIDTH, self.rect.y // BLOCK_HEIGHT}"

class Bomb(Block):
    pass
        


class Player(sprite.Sprite):
    def __init__(self, x, y, image=None):
        sprite.Sprite.__init__(self)
        self.xvel = self.yvel = 0
        if image is None:
            self.image = pg.Surface((WIDTH, HEIGHT))
            self.image.fill(pg.Color(COLOR))
        elif isinstance(image, pg.Surface):
            self.image = image
        else:
            pass
        self.rect = pg.Rect(x, y, WIDTH, HEIGHT)

    def update(self, horizontal, vertical):
        self.xvel = horizontal
        self.yvel = vertical

        self.rect.x += self.xvel * MOVE_SPEED
        self.rect.y += self.yvel * MOVE_SPEED

    def update(self, horizontal, vertical, action, blocks):
        # if not vertical:
        self.xvel = horizontal
        self.yvel = vertical

        # if self.xvel > 0:
        #     self.image.fill(pg.Color(COLOR))
        #     self.bolt_anim_right.blit(self.image, (0, 0))
        # elif self.xvel < 0:
        #     self.image.fill(pg.Color(COLOR))
        #     self.bolt_anim_left.blit(self.image, (0, 0))
        # elif self.yvel > 0:
        #     self.image.fill(pg.Color(COLOR))
        #     self.bolt_anim_up.blit(self.image, (0, 0))
        # elif self.yvel < 0:
        #     self.image.fill(pg.Color(COLOR))
        #     self.bolt_anim_down.blit(self.image, (0, 0))

        self.rect.y += self.yvel * MOVE_SPEED
        self.rect.x += self.xvel * MOVE_SPEED
        self.collide(blocks)

        if action:
            x, y = get_closer_center(self.rect.x, self.rect.y)
            bomb = Bomb(x, y)
            return bomb


    def collide(self, blocks):
        collide_list = sprite.spritecollide(self, blocks, False)

        move_h = move_v = 0
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
        screen.blit(self.image, (self.rect.x,self.rect.y))


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
    sprite_images = ss.load_table((0, 0, BLOCK_WIDTH, BLOCK_HEIGHT), 14, 12)

    bg.fill(pg.Color(BACKGROUND_COLOR))

    sprites_group = sprite.Group()
    blocks = []
    x = y = BLOCK_WIDTH
    for row in demo_field:
        for cell in row:
            if cell:
                block = WallBlock(x, y, sprites=None)
                if cell[0] == 'B':
                    block = BrickBlock(x, y, sprites=None)
                sprites_group.add(block)
                blocks.append(block)
            x += BLOCK_WIDTH
        y += BLOCK_HEIGHT
        x = BLOCK_WIDTH
    player = Player(BLOCK_WIDTH * 6, BLOCK_HEIGHT * 5, image=ss.image_at((BLOCK_WIDTH * 4,
                                                                                   BLOCK_HEIGHT * 0,
                                                                                   BLOCK_WIDTH,
                                                                                   BLOCK_HEIGHT)))
    sprites_group.add(player)

    horizontal = vertical = 0
    action = False

    while True:
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


        ret = player.update(horizontal, vertical, action, blocks)
        if ret:
            sprites_group.add(ret)
            blocks.append(ret)

        action = False

        player.draw(screen)
        screen.blit(bg, (0, 0))
        sprites_group.draw(screen)

        # for i, strip in enumerate(sprite_images):
        #     for j, image in enumerate(strip):
        #         screen.blit(image, (j*BLOCK_WIDTH, i*BLOCK_HEIGHT))

        # screen.blit(sprite_images[0][5], (0, 0))

        pg.display.update()
        timer.tick(30)
        

if __name__ == "__main__":
    main()