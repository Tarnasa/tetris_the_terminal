# TODO: Add correct delays
# Line clear delay = 41
# DAS = 14
# Lock = 30
# ARE = 30
# TODO: Scoring
# TODO: Use TGM randomizer with history = 4

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
    def __init__(self):
        self.width = 10
        self.height = 22
        self.hidden_rows = 2  # Don't show t
        self.lock_delay = 30
        self.lock_left = self.lock_delay
        self.cumulative_gravity = 0  # Piece moves down when this reaches 256
        self.current = None
        self.blocks = [[0] * self.width for _ in range(self.height)]
        self.screen = Screen(self.width*2+2, self.height+2)
        self.next_tetrominos = []
        self.paint_border()
        self.level = 0

    def paint_border(self):
        mx = self.width*2+1
        my = self.height+1
        for y in range(self.height+2):
            self.screen.pixels[y][0] = Pixel('|', 7, 0)
            self.screen.pixels[y][mx] = Pixel('|', 7, 0)
        for x in range(self.width*2+2):
            self.screen.pixels[0][x] = Pixel('=', 7, 0)
            self.screen.pixels[my][x] = Pixel('=', 7, 0)
        for x, y in [(0, 0), (mx, 0), (0, my), (mx, my)]:
            self.screen.pixels[y][x] = Pixel('#', 7, 0)

    @property
    def gravity(self):
        pos = bisect_left(GRAVITY_TABLE, (self.level, 0))
        return GRAVITY_TABLE[pos-1][1]

    def start(self):
        self.next_tetrominos = [random.choice('IJLT')]  # "To avoid a forced overhang"
        self.spawn_next()

    def next_tetromino(self):
        if not self.next_tetrominos:
            self.next_tetrominos = list(ALL_PIECES)
            random.shuffle(self.next_tetrominos)
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

    def unpaint_piece(self):
        for x, y in self.current.yield_occupied():
            self.screen.pixels[y+1][x*2+1] = Pixel(' ', 7, 0)
            self.screen.pixels[y+1][x*2+2] = Pixel(' ', 7, 0)

    def paint_piece(self):
        c = self.current.color
        for x, y in self.current.yield_occupied():
            self.screen.pixels[y+1][x*2+1] = Pixel(' ', 7, c)
            self.screen.pixels[y+1][x*2+2] = Pixel(' ', 7, c)

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





