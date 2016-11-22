import socket
import logging
import asynchat
import asyncore

import time # TODO

from game import Game


class Match(object):
    def __init__(self, name, random_seed):
        self.name = name
        self.connected = False
        self.port = None
        self.server = None
        self.client = None
        self.clients = {}
        assert type(random_seed) == str
        self.game = Game(random_seed)
        self.other_game = Game(random_seed)
        
    def join(self, remote_ip, remote_port):
        self.port = remote_port
        def callback(seed):
            self.game.random.seed(seed)
            self.other_game.random.seed(seed)
            self.handle_connect()
        self.client = ChatHandler(self.other_game, self.name,
                dest=(remote_ip, remote_port),
                clients=self.clients,
                random_callback=callback)

    def serve(self, port=7375):
        self.port = port
        def callback():
            self.handle_connect()
        self.server = Server(port, self.clients, self.other_game,
                attach_callback=callback)

    def handle_connect(self):
        self.connected = True
        self.game.start()
        self.other_game.start()
        
    def send_message(self, msg):
        if self.server:
            self.server.push_all(msg + '\n')
        if self.client:
            self.client.push(msg + '\n')

    def user_input(self, command_name):
        if self.connected:
            self.game.user_command(command_name)
            self.send_message('X' + str(self.game.current_frame))
            self.send_message(command_name)

    def handle_network(self):
        # Send/receive network messages
        if self.client:
            asyncore.loop(map=self.clients, timeout=0, count=20)
        if self.server:
            asyncore.loop(map=self.clients, timeout=0, count=20)

    def next_frame(self):
        if self.connected:
            self.game.next_frame()
            self.other_game.next_frame()


match = None
def send_message(msg):
    if match:
        match.send_message(msg)


class ChatHandler(asynchat.async_chat):
    def __init__(self, game, name, sock=None, dest=None, clients=None,
            random_callback=None):
        if sock is None:
            asynchat.async_chat.__init__(self, map=clients)
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect((dest))
        else:
            asynchat.async_chat.__init__(self, sock=sock, map=clients)
        self.set_terminator('\n')
        self.buffer = []
        self.handlers = {
            'H': self.receive_hello,
            'L': self.receive_left,
            'R': self.receive_right,
            'D': self.receive_down,
            'W': self.receive_cw,
            'C': self.receive_ccw,
            'X': self.receive_next,
            'N': self.receive_random,
        }
        self.frames_ahead = 0
        self.game = game
        self.name = name
        self.random_callback = random_callback
        self.opponent = None

        # Tell the other player who we are
        self.push('H' + self.name + '\n')

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        msg = ''.join(self.buffer)
        logging.info('Received: {0}'.format(msg))  # TODO
        print('Received: {0}'.format(msg))  # TODO
        if msg[0] in self.handlers:
            self.handlers[msg[0]](msg)
        else:
            logging.warning('No handler for message: {0}'.format(msg))
        self.buffer = []
        
    def receive_hello(self, msg):
        """
        Hello - H{name}
            Where {name} is the name of the player sending the message
        """
        self.opponent = msg[1:]
        logging.info('Player {0} joined!'.format(self.opponent))

    def receive_left(self, msg):
        """ L """
        self.game.user_left()

    def receive_right(self, msg):
        """ R """
        self.game.user_right()

    def receive_down(self, msg):
        """ D """
        self.game.user_down()

    def receive_cw(self, msg):
        """ W """
        self.game.clockwise()

    def receive_ccw(self, msg):
        """ C """
        self.game.counterclockwise()

    def receive_next(self, msg):
        """ X{current_frame} """
        target_frame = int(msg[1:])
        # Catch up to 1 before the target frame (that way we don't overshoot it)
        while self.game.current_frame < target_frame - 1:
            self.game.next_frame()
        #  Record how far ahead we are
        if self.game.current_frame > target_frame:
            self.frames_ahead = self.game.current_frame - target_frame

    def receive_random(self, msg):
        """ N{random_seed} """
        print('Random! {}'.format(time.time()))
        #self.game.random.seed(msg[1:])
        if self.random_callback:
            self.random_callback(msg[1:])


class Server(asyncore.dispatcher):
    def __init__(self, port, clients, game, name='host', attach_callback=None):
        asyncore.dispatcher.__init__(self, map=clients)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('', port))
        self.listen(1)
        self.clients = clients
        self.game = game
        self.name = name
        self.attach_callback = attach_callback

    def handle_accept(self):
        pair = self.accept()
        if pair:
            sock, addr = pair
            logging.info('Connection from {0}'.format(addr))
            handler = ChatHandler(self.game, self.name, sock=sock, clients=self.clients)
            handler.push('N' + self.game.random_seed + '\n')
            if self.attach_callback:
                self.attach_callback()

    def push_all(self, data):
        for c in self.clients.values():
            if c is not self:
                c.push(data)

