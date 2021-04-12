#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame as pg
from pprint import pprint


WIN_WIDTH = 32*11
WIN_HEIGHT = 32*11
DISPLAY = (WIN_WIDTH, WIN_HEIGHT)
BACKGROUND_COLOR = "#388700"
PLATFORM_WIDTH = 32
PLATFORM_HEIGHT = 32
PLATFORM_COLOR = "#b0b0b0"

# 29 * 13

class Block(pg.sprite.Sprite):
    def __init__(self, x, y, undercover=None):
        pg.sprite.Sprite.__init__(self)
        # super().__init__()
        self.undercover = undercover
        self.image = pg.Surface((PLATFORM_WIDTH, PLATFORM_HEIGHT))
        self.image.fill(pg.Color(PLATFORM_COLOR))
        self.rect = pg.Rect(x, y, PLATFORM_WIDTH, PLATFORM_HEIGHT)

    def place(self, x, y):
        pass

    def __repr__(self):
        return "O"

class WallBlock(Block):
    def __repr__(self):
        return "X"

class BrickBlock(Block):
    def __repr__(self):
        return "#"


MOVE_SPEED = 7
WIDTH = 22
HEIGHT = 32
COLOR =  "#888888"
class Player(pg.sprite.Sprite):
    def __init__(self, x, y):
        pg.sprite.Sprite.__init__(self)
        self.xvel = 0   #скорость перемещения. 0 - стоять на месте
        self.startX = x # Начальная позиция Х, пригодится когда будем переигрывать уровень
        self.startY = y
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.image.fill(pg.Color(COLOR))
        self.rect = pg.Rect(x, y, WIDTH, HEIGHT) # прямоугольный объект

    def update(self, horizontal, vertical):
        self.xvel = horizontal
        self.yvel = vertical

        self.rect.x += self.xvel
        self.rect.y += self.yvel

    # def draw(self, screen): # Выводим себя на экран
    #     screen.blit(self.image, (self.rect.x,self.rect.y))

    def collide(self, xvel, yvel, blocks):
        for block in blocks:
            if pg.sprite.collide_rect(self, block):
                if xvel > 0:
                    self.rect.right = p.rect.left # то не движется вправо

                if xvel < 0:                      # если движется влево
                    self.rect.left = p.rect.right # то не движется влево

                if yvel > 0:                      # если падает вниз
                    self.rect.bottom = p.rect.top # то не падает вниз
                    self.onGround = True          # и становится на что-то твердое
                    self.yvel = 0                 # и энергия падения пропадает

                if yvel < 0:                      # если движется вверх
                    self.rect.top = p.rect.bottom # то не движется вверх
                    self.yvel = 0                 # и энергия прыжка пропадает



demo_field = [
    [["#"]] * 11,
    [["#"]] + [[]] * 9 + [["#"]],
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

    bg.fill(pg.Color(BACKGROUND_COLOR))

    sprites_group = pg.sprite.Group()
    x = y = 0
    for row in demo_field:
        for cell in row:
            if cell:
                block = WallBlock(x, y)
                if cell[0] == '#':
                    pass
                sprites_group.add(block)
            x += PLATFORM_WIDTH
        y += PLATFORM_HEIGHT
        x = 0

    player = Player(PLATFORM_WIDTH * 5, PLATFORM_HEIGHT * 5)
    sprites_group.add(player)

    horizontal = vertical = 0

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
            if event.type == pg.KEYUP:
                if event.key == pg.K_LEFT or event.key == pg.K_RIGHT:
                    horizontal = 0
                if event.key == pg.K_UP or event.key == pg.K_DOWN:
                    vertical = 0


        player.update(horizontal, vertical)
        screen.blit(bg, (0, 0))
        sprites_group.draw(screen)

        pg.display.update()
        timer.tick(30)
        

if __name__ == "__main__":
    main()