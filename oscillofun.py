from scipy.io import wavfile
import numpy as np
import pygame
import math
import time
from pprint import pprint
from random import randint


clock = pygame.time.Clock()

window_size = 800, 800
STEPSIZE = 512
invert_list = [1, 0]
volume = .15

pygame.mixer.init(44100, -16, 2, STEPSIZE)

color = pygame.Color(100, 255, 100, 255)
# color = pygame.Color(255, 200, 100, 255)
background_color = pygame.Color(0, 0, 0, 100 if STEPSIZE < 1000 else 180)

pygame.init()
pygame.display.set_caption("Sine Wave")

screen = pygame.display.set_mode(window_size)
screen.fill(background_color)

surface = surface_w = pygame.Surface(window_size, pygame.SRCALPHA)
surface_w.fill(background_color)

surface_f = pygame.Surface(pygame.display.list_modes()[0], pygame.SRCALPHA)
surface_f.fill(background_color)

fs, audio_data = wavfile.read('oscillofun.wav')
# fs, audio_data = wavfile.read('The Alpha Molecule.wav')
# fs, audio_data = wavfile.read('Oscilloscope Music Kickstarter (June 2015).wav')
# fs, audio_data = wavfile.read('How To Draw Mushrooms On An Oscilloscope With Sound.wav')
# fs, audio_data = wavfile.read('Jerobeam Fenderson - How To Draw Mushrooms On An Oscilloscope With Sound.wav')

draw_data = audio_data / 2 ** 16 + .5
deltas = np.diff(draw_data, axis=0)
lengths = np.hypot(deltas[:,0], deltas[:,1])
alphas = np.exp(lengths)
alphas = np.interp(lengths, (lengths.min(), lengths.max()), (0, 255))

alphas = np.clip(alphas * 20, 0, 255)

alphas = np.interp(alphas, (alphas.min(), alphas.max()), (255, 0))
thickness = np.interp(alphas, (alphas.min(), alphas.max()), (0, 3))

alphas = np.expand_dims(alphas, axis=1)

thickness = np.expand_dims(thickness, axis=1)

audio_data = audio_data[1:]
draw_data = draw_data[1:]

draw_data = np.append(draw_data, alphas, axis=1)
draw_data = np.append(draw_data, thickness, axis=1)
data_len = len(audio_data)
rewinding_step = data_len // STEPSIZE // 25

position = 0
prev = audio_data[0]

min_dim = min(pygame.display.Info().current_w, pygame.display.Info().current_h)

running = True
paused = False
one_line = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_F7:
                running = False
            if event.key == pygame.K_SPACE:
                paused = not paused
            if event.key == pygame.K_UP:
                volume = min(1, volume * 1.1)
            if event.key == pygame.K_DOWN:
                volume *= .9
            if event.key == pygame.K_LEFT:
                position = max((position - rewinding_step, 0))
            if event.key == pygame.K_RIGHT:
                position = min((position + rewinding_step, data_len))
            if event.key == pygame.K_END:
                position = 3686400 // STEPSIZE
            if event.key == pygame.K_r:
                invert_list[0] = 0 if invert_list[0] else 1
            if event.key == pygame.K_l:
                invert_list[1] = 0 if invert_list[1] else 1
            if event.key == pygame.K_f:
                if pygame.display.Info().current_w == pygame.display.Info().current_h:
                    pygame.display.set_mode(pygame.display.list_modes()[0])
                    pygame.display.toggle_fullscreen()
                    surface = surface_f
                else:
                    pygame.display.toggle_fullscreen()
                    pygame.display.set_mode(window_size)
                    surface = surface_w
                min_dim = min(pygame.display.Info().current_w, pygame.display.Info().current_h)
            if event.key == pygame.K_s:
                one_line = False if one_line else True
        # elif event.type == pygame.MOUSEWHEEL:
            # volume = min(1, volume * (1 + event.y * 0.1))


    
    if not paused:

        frame_data_slice = audio_data[position * STEPSIZE:position * STEPSIZE + STEPSIZE]
        music = pygame.sndarray.make_sound(frame_data_slice).play()
        music.set_volume(volume)

        surface.fill(background_color)

        draw_data_slice = draw_data[position * STEPSIZE:position * STEPSIZE + STEPSIZE].copy()
        draw_data_slice[:,(0,1)] = abs(invert_list - draw_data_slice[:,(0,1)])
        draw_data_slice[:,(0,1)] *= min_dim
        draw_data_slice[:,(0,1)] += [(pygame.display.Info().current_w - min_dim) // 2, (pygame.display.Info().current_h - min_dim) // 2]

        # if draw_data_slice[0][0] > 1000:
        #     paused = True

        if one_line:
            pygame.draw.aalines(surface, color, False, draw_data_slice[:,(0,1)])
        else:
            for pixel in draw_data_slice:
                *pixel, alpha, thickness = pixel
                color.a = int(alpha)
                thickness = int(thickness)
                pygame.draw.line(surface, color, prev, pixel, thickness)
                prev = pixel

        position += 1
        if position * STEPSIZE >= data_len:
            position = 0
            running = False

        screen.blit(surface, (0, 0))
        while music.get_busy():
            pass
    pygame.display.flip()
    clock.tick(44100 / STEPSIZE)