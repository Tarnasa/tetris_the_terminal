I = """
....
xxxx
....
....

..x.
..x.
..x.
..x.

....
xxxx
....
....

..x.
..x.
..x.
..x."""[1:]

O = """
xx
xx

xx
xx

xx
xx

xx
xx"""[1:]

T = """
...
.x.
xxx

.x.
.xx
.x.

...
xxx
.x.

.x.
xx.
.x."""[1:]

S = """
...
.xx
xx.

x..
xx.
.x.

...
.xx
xx.

x..
xx.
.x."""[1:]

Z = """
...
xx.
.xx

..x
.xx
.x.

...
xx.
.xx

..x
.xx
.x."""[1:]

J = """
...
x..
xxx

.xx
.x.
.x.

...
xxx
..x

.x.
.x.
xx."""[1:]

L = """
...
..x
xxx

.x.
.x.
.xx

...
xxx
x..

xx.
.x.
.x."""[1:]

import re

ALL_PIECES = 'IOTSZJL'
COLORS = {
        'O': 11, # Yellow
        'I': 9,  # Red
        'T': 14, # Cyan
        'S': 2,  # Green
        'Z': 13, # Magenta
        'J': 12, # Blue
        'L': 208 # Orange
}

shape_data = dict()
for c in ALL_PIECES:
    data = eval(c)
    data = re.sub(r' |\n|\r', '', data)
    width = int((len(data)/4)**0.5)
    step = width*width
    shape_data[c] = [data[i:i+step] for i in range(0, len(data), step)], width


class Tetromino(object):
    def __init__(self, name, x=0, y=0, orientation=0):
        self.name = name
        self.x = x
        self.y = y
        self.orientation = orientation % 4
        self.data, self.width = shape_data[self.name]
        self.color = COLORS[self.name]

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.width

    def is_inside(self, x, y):
        return self.left <= x <= self.right and self.top <= y <= self.bottom

    def is_occupied(self, x, y):
        if self.inside(x, y):
            return self.data[self.orientation][x - self.left + (y - self.top) * self.width] == 'x'
        return False

    def yield_occupied(self):
        for i, c in enumerate(self.data[self.orientation]):
            if c == 'x':
                yield (self.x + i % self.width, self.y + i // self.width)

    def clockwise(self):
        self.orientation = (self.orientation + 1) % 4

    def counterclockwise(self):
        self.orientation = (self.orientation - 1) % 4

