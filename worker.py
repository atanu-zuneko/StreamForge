from threading import Thread
from queue import Queue, Empty
import pickle

from zmq_utils import create_pull_connect, create_push_bind

from settings import *
# from inference import inferences

from modules.sample import LineModule, BWModule

line_module = LineModule()
bw_module  = BWModule()

CAMERA_MODULES = {
    0: [bw_module, line_module],
    1: [line_module],
}


def ai_worker(worker_id, recv_queue, send_queue):

    print(f"worker {worker_id}")

    while True:

        try:

            data = recv_queue.get()

            packet = pickle.loads(data)

            cam_id = packet["cam_id"]
            frame = packet["frame"]

            for module in CAMERA_MODULES.get(cam_id, []):
                frame = module.process(frame)

            while not send_queue.empty():
                try:
                    send_queue.get_nowait()
                except Empty:
                    break
            
            out_packet = {"cam_id": cam_id, "frame": frame}
            send_queue.put(pickle.dumps(out_packet))

        except Exception as e:
            print(f"worker {worker_id}", e)


def recv_loop(recv_socket, recv_queue):
    while True:
        try:
            data = recv_socket.recv()

            while not recv_queue.empty():
                try:
                    recv_queue.get_nowait()
                except Empty:
                    break

            recv_queue.put(data)

        except Exception as e:
            print("recv_loop", e)


def send_loop(send_socket, send_queue):
    while True:
        try:
            data = send_queue.get()
            send_socket.send(data)
        except Exception as e:
            print("send_loop", e)


if __name__ == "__main__":

    recv_socket = create_pull_connect(DECODE_PORT)
    send_socket = create_push_bind(ENCODE_PORT)

    recv_queue = Queue()
    send_queue = Queue()

    Thread(target=recv_loop, args=(recv_socket, recv_queue), daemon=True).start()
    Thread(target=send_loop, args=(send_socket, send_queue), daemon=True).start()

    threads = []

    for i in range(4):
        t = Thread(target=ai_worker, args=(i, recv_queue, send_queue), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
