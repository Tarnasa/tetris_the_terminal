#!/usr/bin/env python3

import sys
import os
import select
import time

from graphics import ESC
from game import Game


FRAMERATE = 30

game = Game()
game.start()
game.draw()
sys.stdout.flush()

# Don't wait for newlines to grab input
# Don't echo their input to the screen
os.system('stty -icanon echo')
quit = False
try:
    while not quit:
        while select.select([sys.stdin,], [], [], 0.0)[0]:
            c = sys.stdin.read(1)
            print('select ' + c)
            if c == 'z':
                quit = True
            if c == 'a':
                game.user_left()
            if c == 'd':
                game.user_right()
            if c == 's':
                game.user_down()
            if c == 'q':
                game.counterclockwise()
            if c == 'e':
                game.clockwise()
        game.next_frame()
        game.draw()
        sys.stdout.flush()
        time.sleep(1.0 / FRAMERATE)
except Exception as e:
    print(ESC + 'c')
    import traceback
    traceback.print_exc()
else:
    print(ESC + 'c')
finally:
    os.system('stty icanon echo')

