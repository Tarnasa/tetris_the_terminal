#!/usr/bin/env python3

import sys
import os
import select
import time
import argparse

from graphics import ESC
from game import Game
import multiplayer


FRAMERATE = 30

# Don't wait for newlines to grab input
# Don't echo their input to the screen
os.system('stty -icanon echo')
os.system('xset r rate 300 25')
quit = False
try:

    parser = argparse.ArgumentParser('Play a game of Tetris in the terminal!')
    parser.add_argument('-s', '--host', action='store_const', const=True, default=False,
            help='Host a multiplayer game')
    parser.add_argument('-j', '--join', type=str, metavar='ADDR',
            help='Specify the remote address to join a multiplayer game')
    parser.add_argument('-p', '--port', type=int, default=7375,
            help='The port to use for multiplayer connections, (default=7375)')
    parser.add_argument('-r', '--seed', type=str, default=str(time.time()),
            help='The seed for the random number generator, defaults to time')

    args = parser.parse_args()

    if not args.host and not args.join:
        game = Game(args.seed)
        game.start()
        game.draw()
        sys.stdout.flush()

        while not quit:
            start_time = time.time()
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
            game.draw_next_piece(6, 0)
            game.draw(0, 6)
            
            sys.stdout.flush()
            time.sleep(1.0 / FRAMERATE - (time.time() - start_time))

    elif args.host:
        match = multiplayer.Match('host', args.seed)
        multiplayer.match = match
        match.serve(args.port)
    elif args.join:
        match = multiplayer.Match('join', args.seed)
        multiplayer.match = match
        match.join(args.join, args.port)

    if multiplayer.match:
        while not quit:
            start_time = time.time()
            # Grab any pending input
            mapping = {
                    'a': 'L',
                    's': 'D',
                    'd': 'R',
                    'q': 'C',
                    'e': 'W',
            }
            while select.select([sys.stdin,], [], [], 0.0)[0]:
                c = sys.stdin.read(1)
                if c == 'z':
                    quit = True
                elif c in mapping and match.connected:
                    #match.game.user_command(mapping[c])
                    match.user_input(mapping[c])
                print('select ' + c)

            match.handle_network()
            match.next_frame()

            match.game.draw_next_piece(6, 0)
            match.game.draw(0, 6)
            match.other_game.draw_next_piece(24+6, 0)
            match.other_game.draw(24, 6)
            sys.stdout.flush()

            match.handle_network()

            sleep_for = max(0, 1./FRAMERATE - (time.time() - start_time))
            time.sleep(sleep_for)

except Exception as e:
    print(ESC + 'c')
    import traceback
    traceback.print_exc()
else:
    print(ESC + 'c')
finally:
    os.system('stty icanon echo')
    os.system('xset r rate 660 25')  # TODO Don't hard code this

    

