from fractions import Fraction
import math
import time

import cv2
import numpy as np

from aiortc import VideoStreamTrack
from av import VideoFrame


class CompositeTrack(VideoStreamTrack):
    def __init__(self, track, peer_data, pc_id):
        super().__init__()
        self.track = track
        self.peer_data = peer_data
        self.pc_id = pc_id
        self.full_height = 1000
        self.full_width = 1000

    def send_frame(self):
        ...

    async def recv(self):
        frames = []

        if len(self.peer_data) == 1:
            # frame.to_ndarray(format="bgr24")
            frame = await self.track.recv()
            # frame = self.peer_data[self.pc_id]["latest_frame"]
            return frame

            # img = self.peer_data[self.pc_id]["latest_frame"]
            # new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            # return new_frame


        for pc_id, pdata in list(self.peer_data.items()):   

            if self.pc_id == pc_id:
                continue

            track = pdata.tracks.video
            if track is None:
                continue
            try:
                frame = await track.recv()
                # frame = self.peer_data[pc_id]["latest_frame"]
                img = frame.to_ndarray(format="bgr24")
                if img is None:
                    continue

                cv2.putText(
                    img, 
                    pdata.name,
                    (40, 40),                       # position
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1.2,                            # size
                    (0, 255, 0),                    # color (green)
                    3
                )

                frames.append(img)
            except Exception as e:
                pass

        if not frames:
            # return a black frame
            black = np.zeros((480, 640, 3), dtype=np.uint8)
            out = VideoFrame.from_ndarray(black, format="bgr24")
            out.pts = int(time.time() * 90000)
            out.time_base = Fraction(1, 90000)
            return out

        try:
            num_clients = len(frames)
            cols = math.ceil(math.sqrt(num_clients))
            rows = math.ceil(num_clients / cols)
            cell_width = self.full_width // cols
            cell_height = self.full_height // rows

            # Resize frames
            resized_frames = [cv2.resize(f, (cell_width, cell_height)) for f in frames]

            # Build the grid row by row
            grid_rows = []
            for r in range(rows):
                row_frames = []
                for c in range(cols):
                    idx = r * cols + c
                    if idx < num_clients:
                        row_frames.append(resized_frames[idx])
                    else:
                        # empty cell
                        row_frames.append(np.zeros((cell_height, cell_width, 3), dtype=np.uint8))
                grid_rows.append(cv2.hconcat(row_frames))

            combined = cv2.vconcat(grid_rows)

            # Convert to VideoFrame
            new_frame = VideoFrame.from_ndarray(combined, format="bgr24")
            new_frame.pts = int(time.time() * 90000)
            new_frame.time_base = Fraction(1, 90000)
            return new_frame
        except Exception as e:
            return None


class LabelVideoStream(VideoStreamTrack):
    def __init__(self, source_track, username, pc_id):
        super().__init__()
        self.source = source_track
        self.username = username
        self.pc_id = pc_id


    async def recv(self):
        # Get next frame from incoming track
        frame = await self.source.recv()

        # Convert to numpy for processing
        img = frame.to_ndarray(format="bgr24")
        # Add text overlay
        cv2.putText(
            img, 
            self.username,
            (40, 40),                      # position
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.2,                            # size
            (0, 255, 0),                    # color (green)
            3
        )

        # Convert back to VideoFrame
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame
