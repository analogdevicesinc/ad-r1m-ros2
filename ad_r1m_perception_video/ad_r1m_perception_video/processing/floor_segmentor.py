import math
import threading
import cv2
import numpy as np
from ultralytics import FastSAM


def compute_prompt_points(calib, K, D, calib_w, calib_h, work_w, work_h):
    height = calib['height']
    pitch_deg = calib['pitch']
    yaw_deg = calib['yaw']
    offset = calib['offset']

    theta = math.radians(pitch_deg)
    psi = math.radians(yaw_deg)

    R = np.array([
        [math.cos(psi), math.sin(psi), 0],
        [math.sin(theta) * math.sin(psi), -math.sin(theta) * math.cos(psi), -math.cos(theta)],
        [-math.cos(theta) * math.sin(psi), math.cos(theta) * math.cos(psi), -math.sin(theta)],
    ], dtype=np.float64)

    cam_pos = np.array([offset[0], offset[1], height], dtype=np.float64)
    t = -R @ cam_pos

    rvec, _ = cv2.Rodrigues(R)
    tvec = t.reshape(3, 1)

    K_proc = K.copy()
    sx = work_w / calib_w
    sy = work_h / calib_h
    K_proc[0, 0] *= sx
    K_proc[0, 2] *= sx
    K_proc[1, 1] *= sy
    K_proc[1, 2] *= sy

    ground_pts = []
    for x in np.arange(-0.4, 0.5, 0.2):
        for y in np.arange(-0.4, 0.5, 0.2):
            dist = math.sqrt((x - offset[0])**2 + (y - offset[1])**2)
            if 0.15 < dist < 0.5:
                ground_pts.append([x, y, 0.0])
    ground_pts = np.array(ground_pts, dtype=np.float64) if ground_pts else np.zeros((0, 3))

    def project_and_filter(pts_3d):
        img_pts, _ = cv2.fisheye.projectPoints(
            pts_3d.reshape(-1, 1, 3), rvec, tvec, K_proc, D
        )
        img_pts = img_pts.reshape(-1, 2)
        margin = 20
        valid = (img_pts[:, 0] >= margin) & (img_pts[:, 0] < work_w - margin) & \
                (img_pts[:, 1] >= margin) & (img_pts[:, 1] < work_h - margin)
        return img_pts[valid]

    pos_pts = project_and_filter(ground_pts) if len(ground_pts) > 0 else np.zeros((0, 2))

    if len(pos_pts) > 0:
        pos_pts = pos_pts[pos_pts[:, 1] > work_h * 0.4]

    if len(pos_pts) > 5:
        indices = np.linspace(0, len(pos_pts) - 1, 5, dtype=int)
        pos_pts = pos_pts[indices]

    neg_pts = np.array([
        [work_w * 0.1, work_h * 0.1],
        [work_w * 0.3, work_h * 0.12],
        [work_w * 0.5, work_h * 0.08],
        [work_w * 0.7, work_h * 0.12],
        [work_w * 0.9, work_h * 0.1],
    ], dtype=np.float64)

    return pos_pts, neg_pts


class FloorSegmentor:
    def __init__(self, model_path, cameras_cfg, cam_keys=None, model_size=384, confidence=0.7):
        self.model = FastSAM(model_path)
        self.model_size = model_size
        self.confidence = confidence
        self.cam_keys = cam_keys if cam_keys else list(cameras_cfg.keys())

        self.prompts = {}
        self.prompts_raw = {}
        self._masks = {}
        self._work_sizes = {}

        for cam_key in self.cam_keys:
            cam_data = cameras_cfg[cam_key]
            cfg = cam_data['config']
            calib = cam_data['calibration']

            work_w = cfg['work_width']
            work_h = cfg['work_height']
            calib_w = calib['calibration_width']
            calib_h = calib['calibration_height']

            K = np.array(calib['camera_matrix'], dtype=np.float64).reshape(3, 3)
            D = np.array(calib['distortion_coeffs'], dtype=np.float64)

            pos, neg = compute_prompt_points(calib, K, D, calib_w, calib_h, work_w, work_h)
            self.prompts_raw[cam_key] = (pos, neg)

            sx, sy = model_size / work_w, model_size / work_h
            points = [[p[0] * sx, p[1] * sy] for p in pos] + \
                     [[p[0] * sx, p[1] * sy] for p in neg]
            labels = [1] * len(pos) + [0] * len(neg)
            self.prompts[cam_key] = (points, labels)
            self._masks[cam_key] = np.zeros((work_h, work_w), dtype=np.uint8)
            self._work_sizes[cam_key] = (work_w, work_h)

        self._lock = threading.Lock()
        self._input_frames = None
        self._running = True
        self._event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self._running:
            self._event.wait()
            self._event.clear()
            if not self._running:
                break

            with self._lock:
                frames = self._input_frames
                self._input_frames = None

            if frames is None:
                continue

            batch = []
            batch_keys = []
            for cam_key in self.cam_keys:
                if cam_key not in frames:
                    continue
                resized = cv2.resize(frames[cam_key], (self.model_size, self.model_size))
                batch.append(resized)
                batch_keys.append(cam_key)

            if not batch:
                continue

            for i, cam_key in enumerate(batch_keys):
                points, labels = self.prompts[cam_key]
                if not points:
                    continue

                results = self.model(
                    batch[i], imgsz=self.model_size, verbose=False,
                    points=points, labels=labels
                )

                if len(results) > 0 and results[0].masks is not None and len(results[0].masks.data) > 0:
                    confs = results[0].boxes.conf.cpu().numpy()
                    masks_data = results[0].masks.data.cpu().numpy()
                    high_conf = np.where(confs >= self.confidence)[0][:3]
                    if len(high_conf) > 0:
                        mask_data = np.any(masks_data[high_conf], axis=0).astype(np.float32)
                    else:
                        mask_data = masks_data[0]

                    work_w, work_h = self._work_sizes[cam_key]
                    mask = cv2.resize(mask_data, (work_w, work_h))
                    with self._lock:
                        self._masks[cam_key] = (mask > 0.5).astype(np.uint8)

    def submit_batch(self, frames):
        with self._lock:
            self._input_frames = frames.copy()
        self._event.set()

    def get_mask(self, cam_key):
        with self._lock:
            return self._masks[cam_key]

    def get_all_masks(self):
        with self._lock:
            return {k: v for k, v in self._masks.items()}

    def stop(self):
        self._running = False
        self._event.set()
        self._thread.join()
