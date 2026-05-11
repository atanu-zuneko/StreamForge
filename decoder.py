import subprocess
import numpy as np
import time

from settings import *


class FFmpegDecoder:

    def __init__(self, stream_url):

        self.frame_interval = 1.0 / FPS

        self.process = subprocess.Popen(
            [
                "ffmpeg",
                "-stream_loop",
                "-1",
                "-i",
                stream_url,
                "-vf",
                f"scale={WIDTH}:{HEIGHT}",
                "-r",
                str(FPS),
                "-f",
                "rawvideo",
                "-pix_fmt",
                "bgr24",
                "-",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=FRAME_SIZE,
        )

        self._next_frame_time = time.monotonic()

    def read_frame(self):

        raw_frame = self.process.stdout.read(FRAME_SIZE)

        if len(raw_frame) != FRAME_SIZE:
            return None

        frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((HEIGHT, WIDTH, 3))

        now = time.monotonic()
        wait = self._next_frame_time - now
        if wait > 0:
            time.sleep(wait)

        self._next_frame_time = time.monotonic() + self.frame_interval

        return frame
