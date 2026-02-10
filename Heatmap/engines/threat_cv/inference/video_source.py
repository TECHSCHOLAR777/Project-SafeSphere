import cv2
import numpy as np
from typing import Iterator, Optional, Union


class VideoSource:
    def __init__(self, source: Union[int, str] = 0, width: Optional[int] = None, height: Optional[int] = None, fps: Optional[float] = None) -> None:
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None

    def open(self) -> None:
        self.cap = cv2.VideoCapture(self.source)
        if self.width is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(self.width))
        if self.height is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self.height))
        if self.fps is not None:
            self.cap.set(cv2.CAP_PROP_FPS, float(self.fps))

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def is_open(self) -> bool:
        return self.cap is not None and self.cap.isOpened()

    def frames(self) -> Iterator[np.ndarray]:
        if not self.is_open():
            self.open()
        while True:
            assert self.cap is not None
            ok, frame = self.cap.read()
            if not ok:
                break
            yield frame

    def __enter__(self) -> "VideoSource":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
