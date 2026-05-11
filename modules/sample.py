import cv2

class BWModule:
    def process(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return frame


class LineModule:
    def process(self, frame):
        cv2.line(
            frame,
            (100, 100),
            (500, 100),
            (0, 255, 0),
            3,
        )

        return frame
