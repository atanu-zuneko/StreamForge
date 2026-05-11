import subprocess
import threading

from settings import *


class RTSPEncoder:

    def __init__(self, stream_name):

        self.output_url = f"rtsp://localhost:8554/{stream_name}"

        self.process = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "bgr24",
                "-video_size",
                f"{WIDTH}x{HEIGHT}",
                "-framerate",
                str(FPS),
                "-i",
                "-",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-tune",
                "zerolatency",
                "-pix_fmt",
                "yuv420p",
                "-g",
                "10",
                "-f",
                "rtsp",
                "-rtsp_transport",
                "tcp",
                self.output_url,
            ],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

        # FIX: log stderr in background so we can see exactly why ffmpeg exits
        threading.Thread(target=self._log_stderr, daemon=True).start()

    def _log_stderr(self):
        for line in self.process.stderr:
            print(f"[ffmpeg {self.output_url}]", line.decode(errors="ignore").strip())
        print(
            f"[ffmpeg {self.output_url}] process exited with code {self.process.returncode}"
        )

    def write_frame(self, frame):

        try:

            self.process.stdin.write(frame.tobytes())

        except Exception as e:

            print("encoder write", e)

            err = self.process.stderr.readline()
            print(err.decode(errors="ignore"))
