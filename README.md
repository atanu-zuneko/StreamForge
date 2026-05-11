# StreamForge

Real-time multi-camera AI video analysis pipeline. Decodes RTSP/video streams, runs AI inference, and re-publishes annotated streams over RTSP.

---

## How it works

```
Video files / RTSP cameras
        ↓
  FFmpeg decoder          (decoder.py)
        ↓
   ZMQ :5555              (inter-process)
        ↓
   AI inference           (worker.py)
        ↓
   ZMQ :5556              (inter-process)
        ↓
  FFmpeg encoder          (encoder.py)
        ↓
    MediaMTX              (RTSP broker)
        ↓
  VLC / any RTSP player
```

`main.py` and `worker.py` run as separate processes so decoding and inference never block each other.

---

## Requirements

- Python 3.10+
- FFmpeg (must be in PATH)
- MediaMTX - [download here](https://github.com/bluenviron/mediamtx/releases)
- Python packages:

```bash
pip install numpy opencv-python pyzmq
```

---

## Project structure

```
sentinel/
├── main.py          # decoder + encoder process
├── worker.py        # AI inference process
├── modules/sample.py# your AI module logic goes here
├── decoder.py       # FFmpeg decoder wrapper
├── encoder.py       # FFmpeg RTSP encoder wrapper
├── zmq_utils.py     # ZMQ socket helpers
├── streams.py       # camera / video file list
└── settings.py      # resolution, FPS, ports
```

---

## Configuration

**`streams.py`** - add your camera URLs or video files:
```python
STREAMS = [
    "samples/sample1.mp4",
    "samples/sample2.mp4",
    "rtsp://192.168.1.10:554/stream",   # IP camera
]
```

**`settings.py`** - resolution, FPS, ZMQ ports:
```python
WIDTH  = 640
HEIGHT = 360
FPS    = 15

DECODE_PORT = 5555
ENCODE_PORT = 5556
```

**`modules/sample.py`** - put your AI logic here:
```python
class BWModule:
    def process(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        # return the frame
        return frame
```
---

## Running

Start in this order - each in a separate terminal:

```bash
# Terminal 1 - RTSP broker
./mediamtx

# Terminal 2 - AI inference workers
python worker.py

# Terminal 3 - decoder + encoder
python main.py
```

---

## Viewing streams

Open VLC → Media → Open Network Stream:

```
rtsp://localhost:8554/stream0
rtsp://localhost:8554/stream1
rtsp://localhost:8554/stream2
```

Or from command line:
```bash
ffplay rtsp://localhost:8554/stream0
```

---

## Adding AI modules

Each camera can run different modules. Add your logic to `inference.py`:

```python
from modules.ppe  import PPEModule
from modules.zone import ZoneModule

ppe_module  = PPEModule()
zone_module = ZoneModule(polygon=[(100,200),(300,200),(300,400),(100,400)])

CAMERA_MODULES = {
    0: [ppe_module, zone_module],
    1: [ppe_module],
}

def ai_worker(frame, cam_id):
    ...
        for module in CAMERA_MODULES.get(cam_id, []):
            frame = module.process(frame)
    ...
```

Each module is a class with a single `process(self, frame)` method that returns the annotated frame.

---

## Architecture notes

| Component | Role |
|---|---|
| `main.py` | Spawns one decoder thread per camera, runs the encoder loop |
| `worker.py` | 4 inference threads, one ZMQ socket pair |
| ZMQ PUSH/PULL | Passes frames between processes - separate GILs, true parallelism |
| HWM=1 on sockets | Drops stale frames so the stream stays live |
| Lazy encoder init | Encoder only starts when first frame arrives, prevents MediaMTX from dropping the session |
| Frame pacing | Decoder throttles to target FPS to prevent queue buildup |

---

## Known limitations

- No automatic reconnection if a camera stream drops (planned)
- Pickle serialization - not suitable for untrusted frame sources
- Single worker process - for 10+ cameras consider separate worker per module with Redis Streams