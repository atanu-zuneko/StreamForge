from threading import Thread
import pickle
import time

from streams import STREAMS
from settings import *
from decoder import FFmpegDecoder
from encoder import RTSPEncoder
from zmq_utils import (
    create_push_bind,  # bind :5555, worker connects to us
    create_pull_connect,  # connect to worker's bound :5556
)


def decode_worker(stream_url, idx, decode_socket):

    print(f"decoder {idx} started")

    decoder = FFmpegDecoder(stream_url)

    frame_count = 0

    while True:

        try:

            frame = decoder.read_frame()

            if frame is None:
                print(f"decoder {idx} stream ended")
                break

            frame_count += 1

            if frame_count <= 3 or frame_count % 500 == 0:
                print(f"decoder {idx} frame #{frame_count}")

            packet = {"cam_id": idx, "frame": frame}

            decode_socket.send(pickle.dumps(packet))

        except Exception as e:
            print(f"decoder {idx} error: {e}")


if __name__ == "__main__":

    decode_socket = create_push_bind(DECODE_PORT)  # bind :5555
    encode_socket = create_pull_connect(ENCODE_PORT)  # connect to worker's :5556

    print("waiting for worker.py to bind :5556...")
    time.sleep(2)

    threads = []

    for idx, stream in enumerate(STREAMS):
        t = Thread(target=decode_worker, args=(stream, idx, decode_socket), daemon=True)
        t.start()
        threads.append(t)

    print("encoder loop — waiting for first processed frame...")

    encoders = {}
    total_received = 0

    while True:

        try:

            data = encode_socket.recv()

            total_received += 1

            packet = pickle.loads(data)

            cam_id = str(packet["cam_id"])

            frame = packet["frame"]

            if total_received <= 3 or total_received % 500 == 0:
                print(f"encoder loop frame #{total_received} cam {cam_id}")

            if cam_id not in encoders:
                print(f"starting encoder for stream{cam_id}")
                encoders[cam_id] = RTSPEncoder(f"stream{cam_id}")

            encoders[cam_id].write_frame(frame)

        except Exception as e:
            print("encoder loop error:", e)
