import zmq

context = zmq.Context()


def create_push_connect(port):
    socket = context.socket(zmq.PUSH)
    socket.setsockopt(zmq.SNDHWM, 1)
    socket.connect(f"tcp://localhost:{port}")
    return socket


def create_push_bind(port):
    socket = context.socket(zmq.PUSH)
    socket.setsockopt(zmq.SNDHWM, 1)
    socket.bind(f"tcp://*:{port}")
    return socket


def create_pull_connect(port):
    socket = context.socket(zmq.PULL)
    socket.setsockopt(zmq.RCVHWM, 1)
    socket.connect(f"tcp://localhost:{port}")
    return socket


def create_pull_bind(port):
    socket = context.socket(zmq.PULL)
    socket.setsockopt(zmq.RCVHWM, 1)
    socket.bind(f"tcp://*:{port}")
    return socket
