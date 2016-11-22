# TODO: Add correct delays
# Line clear delay = 41
# DAS = 14
# Lock = 30
# ARE = 30
# TODO: Scoring
# TODO: Use TGM randomizer with history = 4
# TODO: Hidden lines

import random
from bisect import bisect_left

from tetrominos import Tetromino, ALL_PIECES
from graphics import Screen, Pixel

# http://tetris.wikia.com/wiki/Tetris_The_Grand_Master
S_GRAVITY_TABLE = """
0	4	220	32
30	6	230	64
35	8	233	96
40	10	236	128
50	12	239	160
60	16	243	192
70	32	247	224
80	48	251	256 (1G)
90	64	300	512 (2G)
100	80	330	768 (3G)
120	96	360	1024 (4G)
140	112	400	1280 (5G)
160	128	420	1024 (4G)
170	144	450	768 (3G)
200	4	500	5120 (20G)"""[1:]
lines = S_GRAVITY_TABLE.split('\n')
GRAVITY_TABLE = [None for _ in range(len(lines)*2)]
for y, line in enumerate(lines):
    line = line.strip()
    parts = line.split()
    GRAVITY_TABLE[y] = int(parts[0]), int(parts[1])
    GRAVITY_TABLE[y + len(lines)] = int(parts[2]), int(parts[3])


class Game(object):
    def __init__(self, random_seed=None):
        self.width = 10
        self.height = 22
        self.hidden_rows = 2  # Don't show t
        self.lock_delay = 30
        self.lock_left = self.lock_delay
        self.cumulative_gravity = 0  # Piece moves down when this reaches 256
        self.current = None
        self.blocks = [[0] * self.width for _ in range(self.height)]
        self.screen = Screen(self.width*2+2, self.height+2)
        self.next_screen = Screen(11, 6)
        self.next_tetrominos = []
        self.paint_borders()
        self.current_frame = 0
        self.level = 0
        self.random_seed = random_seed
        self.random = random.Random()
        if random_seed is not None:
            self.random.seed(random_seed)

    def paint_borders(self):
        self.screen.paint_border()
        self.next_screen.paint_border()

    @property
    def gravity(self):
        pos = bisect_left(GRAVITY_TABLE, (self.level, 0))
        return GRAVITY_TABLE[pos-1][1]

    def start(self):
        self.next_tetrominos = [self.random.choice('IJLT')]  # "To avoid a forced overhang"
        self.spawn_next()

    def next_tetromino(self):
        if not self.next_tetrominos or len(self.next_tetrominos) <= 1:
            to_shuffle = list(ALL_PIECES)
            self.random.shuffle(to_shuffle)
            self.next_tetrominos = to_shuffle + self.next_tetrominos
        old = self.next_tetrominos[-1]
        old = Tetromino(old, x=(old!='I'))
        new = self.next_tetrominos[-2]
        new = Tetromino(new, x=(new!='I'))
        self.unpaint_piece_to(old, self.next_screen)
        self.paint_piece_to(new, self.next_screen)
        return self.next_tetrominos.pop()

    def next_frame(self):
        self.cumulative_gravity += self.gravity
        while self.cumulative_gravity > 256:
            self.cumulative_gravity -= 256
            self.down()
        if self.is_touching():
            self.lock_left -= 1
            if self.lock_left <= 0:
                self.settle()
                self.spawn_next()
                self.reset_lock_delay()
        else:
            self.reset_lock_delay()
        self.current_frame += 1

    def spawn_next(self):
        next_name = self.next_tetromino()
        self.current = Tetromino(next_name, y=0)
        self.current.x = 6 - (self.current.width+1) // 2
        self.paint_piece()
        self.level += 1

    def settle(self):
        """ Turns current tetromino into blocks """
        for x, y in self.current.yield_occupied():
            self.blocks[y][x] = self.current.color
            self.screen.pixels[y+1][x*2+1] = Pixel(' ', 0, self.current.color)
            self.screen.pixels[y+1][x*2+2] = Pixel(' ', 0, self.current.color)
        self.clear_lines()

    def clear_lines(self):
        to_delete = []
        for y, row in enumerate(self.blocks):
            if all(row):
                to_delete.append(y)
        self.blocks = [row for y, row in enumerate(self.blocks) if y not in to_delete]
        self.blocks = [[0] * self.width for _ in range(self.height - len(self.blocks))] + self.blocks
        self.repaint_screen()
        self.level += len(to_delete)

    def repaint_screen(self):
        for y in range(self.height):
            for x in range(self.width):
                self.screen.pixels[y+1][x*2+1] = Pixel(' ', 7, self.blocks[y][x])
                self.screen.pixels[y+1][x*2+2] = Pixel(' ', 7, self.blocks[y][x])

    def reset_lock_delay(self):
        self.lock_left = self.lock_delay

    def occupied(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.blocks[y][x] != 0
        return True

    def collides(self, xd=0, yd=0, od=0):
        new_x = self.current.x + xd
        new_y = self.current.y + yd
        new_orientation = (self.current.orientation + od) % 4
        new_tetromino = Tetromino(self.current.name,
                new_x, new_y, new_orientation)
        for x, y in new_tetromino.yield_occupied():
            if self.occupied(x, y):
                return True
        return False

    def unpaint_piece_to(self, t, screen):
        for x, y in t.yield_occupied():
            screen.pixels[y+1][x*2+1] = Pixel(' ', 7, 0)
            screen.pixels[y+1][x*2+2] = Pixel(' ', 7, 0)

    def paint_piece_to(self, t, screen):
        for x, y in t.yield_occupied():
            screen.pixels[y+1][x*2+1] = Pixel(' ', 7, t.color)
            screen.pixels[y+1][x*2+2] = Pixel(' ', 7, t.color)

    def unpaint_piece(self):
        self.unpaint_piece_to(self.current, self.screen)

    def paint_piece(self):
        self.paint_piece_to(self.current, self.screen)

    def user_command(self, command_name):
        {
                'L': self.user_left,
                'R': self.user_right,
                'D': self.user_down,
                'W': self.clockwise,
                'C': self.counterclockwise,
        }[command_name]()

    def user_left(self):
        if not self.collides(xd=-1):
            self.unpaint_piece()
            self.current.x -= 1
            self.paint_piece()
            self.reset_lock_delay()

    def user_right(self):
        if not self.collides(xd=1):
            self.unpaint_piece()
            self.current.x += 1
            self.paint_piece()
            self.reset_lock_delay()
        
    def user_down(self):
        if not self.collides(yd=1):
            self.unpaint_piece()
            self.current.y += 1
            self.paint_piece()
        else:
            self.lock_left = 0

    def down(self):
        if not self.collides(yd=1):
            self.unpaint_piece()
            self.current.y += 1
            self.paint_piece()

    def is_touching(self):
        return self.collides(yd=1)

    def clockwise(self):
        self.unpaint_piece()
        success = True
        """ Try TGM kicks: http://tetris.wikia.com/wiki/TGM_rotation """
        if not self.collides(od=1):
            self.current.clockwise()
        elif not self.collides(xd=1, od=1):
            self.current.x += 1
            self.current.clockwise()
        elif not self.collides(xd=-1, od=1):
            self.current.x -= 1
            self.current.clockwise()
        else:
            success = False
        if success:
            self.reset_lock_delay()
        self.paint_piece()

    def counterclockwise(self):
        self.unpaint_piece()
        success = True
        """ Try TGM kicks: http://tetris.wikia.com/wiki/TGM_rotation """
        if not self.collides(od=-1):
            self.current.counterclockwise()
        elif not self.collides(xd=1, od=-1):
            self.current.x += 1
            self.current.counterclockwise()
        elif not self.collides(xd=-1, od=-1):
            self.current.x -= 1
            self.current.counterclockwise()
        else:
            success = False
        if success:
            self.reset_lock_delay()
        self.paint_piece()

    def draw(self, xoff=0, yoff=0):
        self.screen.draw(xoff, yoff)

    def draw_next_piece(self, xoff=0, yoff=0):
        self.next_screen.draw(xoff, yoff)

