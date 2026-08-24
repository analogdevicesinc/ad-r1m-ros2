import cv2
import numpy as np
import threading
import queue
from datetime import datetime


class Display:
    def __init__(self, floor_seg=None, cameras_cfg=None, record_path="/ros2_ws/src/ad_r1m_perception_video"):
        self.floor_seg = floor_seg
        self.cameras_cfg = cameras_cfg
        self.record_path = record_path

        self._record_queue = queue.Queue(maxsize=60)
        self._recording = False
        self._writer = None
        self._record_thread = None

    def show(self, bev_canvas, frames):
        cv2.imshow("BEV", bev_canvas)

        debug_grid = self._build_debug_grid(frames)
        if debug_grid is not None:
            cv2.imshow("Floor Masks", debug_grid)

        if self._recording:
            self._queue_frame(bev_canvas, debug_grid)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('v'):
            self._toggle_recording(bev_canvas, debug_grid)

    def _build_debug_grid(self, frames):
        if self.floor_seg is None:
            return None

        seg_keys = self.floor_seg.cam_keys
        thumb_w, thumb_h = 300, 225
        cols = 2
        rows = (len(seg_keys) + 1) // 2
        grid = np.zeros((thumb_h * rows, thumb_w * cols, 3), dtype=np.uint8)

        for i, cam_key in enumerate(seg_keys):
            frame_cpu = frames[cam_key].download() if hasattr(frames[cam_key], 'download') else frames[cam_key]
            overlay = frame_cpu.copy()
            mask = self.floor_seg.get_mask(cam_key)
            overlay[mask > 0] = (overlay[mask > 0] * 0.85 + np.array([0, 180, 0]) * 0.15).astype(np.uint8)
            small = cv2.resize(overlay, (thumb_w, thumb_h))

            work_w = self.cameras_cfg[cam_key]['config']['work_width']
            work_h = self.cameras_cfg[cam_key]['config']['work_height']
            pos_pts, neg_pts = self.floor_seg.prompts_raw[cam_key]
            for p in pos_pts:
                cx = int(p[0] * thumb_w / work_w)
                cy = int(p[1] * thumb_h / work_h)
                cv2.circle(small, (cx, cy), 3, (0, 255, 0), -1)
            for p in neg_pts:
                cx = int(p[0] * thumb_w / work_w)
                cy = int(p[1] * thumb_h / work_h)
                cv2.circle(small, (cx, cy), 3, (0, 0, 255), -1)

            name = self.cameras_cfg[cam_key]['config'].get('name', cam_key)
            cv2.putText(small, name, (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            row, col = divmod(i, 2)
            grid[row*thumb_h:(row+1)*thumb_h, col*thumb_w:(col+1)*thumb_w] = small

        return grid

    def _queue_frame(self, bev_canvas, debug_grid):
        if debug_grid is not None:
            bev_h = bev_canvas.shape[0]
            grid_h = debug_grid.shape[0]
            if grid_h < bev_h:
                pad = np.zeros((bev_h - grid_h, debug_grid.shape[1], 3), dtype=np.uint8)
                debug_padded = np.vstack([debug_grid, pad])
            else:
                debug_padded = debug_grid[:bev_h]
            record_frame = np.hstack([bev_canvas, debug_padded])
        else:
            record_frame = bev_canvas
        try:
            self._record_queue.put_nowait(record_frame)
        except queue.Full:
            pass

    def _toggle_recording(self, bev_canvas, debug_grid):
        if not self._recording:
            h = bev_canvas.shape[0]
            w = bev_canvas.shape[1]
            if debug_grid is not None:
                w += debug_grid.shape[1]
            filename = f"{self.record_path}/bev_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
            self._writer = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'XVID'), 30, (w, h))
            self._recording = True
            self._record_thread = threading.Thread(target=self._write_loop, daemon=True)
            self._record_thread.start()
            print(f'[REC] Recording started: {filename}')
        else:
            self._recording = False
            self._record_queue.put(None)
            self._record_thread.join()
            self._writer.release()
            self._writer = None
            print('[REC] Recording stopped')

    def _write_loop(self):
        while True:
            frame = self._record_queue.get()
            if frame is None:
                break
            self._writer.write(frame)

    def stop(self):
        if self._recording:
            self._recording = False
            self._record_queue.put(None)
            self._record_thread.join()
            self._writer.release()
            self._writer = None
