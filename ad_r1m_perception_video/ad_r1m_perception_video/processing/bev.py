import math
import time
import cv2
import numpy as np


class BEV:
    def __init__(self, cameras_cfg, bev_size=800, ground_range=5.0, feather_band=30):
        self.bev_size = bev_size
        self.ground_range = ground_range
        self.feather_band = feather_band
        self.cam_keys = list(cameras_cfg.keys())

        self.gpu_maps = {}
        self.cpu_maps = {}
        self.masks = {}

        for cam_key, cam_data in cameras_cfg.items():
            cfg = cam_data['config']
            calib = cam_data['calibration']

            cap_w = cfg['capture_width']
            cap_h = cfg['capture_height']
            work_w = cfg['work_width']
            work_h = cfg['work_height']

            calib_w = calib['calibration_width']
            calib_h = calib['calibration_height']

            K = np.array(calib['camera_matrix'], dtype=np.float64).reshape(3, 3)
            D = np.array(calib['distortion_coeffs'], dtype=np.float64)

            sx = cap_w / calib_w
            sy = cap_h / calib_h
            K_full = K.copy()
            K_full[0, 0] *= sx
            K_full[0, 2] *= sx
            K_full[1, 1] *= sy
            K_full[1, 2] *= sy

            new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
                K_full, D, (cap_w, cap_h), np.eye(3), balance=0.0
            )

            H = self._compute_homography(new_K, calib['height'], calib['pitch'], calib['yaw'], calib['offset'])

            map_x, map_y, mask = self._precompute_fused_map(
                K_full, D, new_K, H, cap_w, cap_h, work_w, work_h
            )

            gpu_map_x = cv2.cuda_GpuMat()
            gpu_map_x.upload(map_x)
            gpu_map_y = cv2.cuda_GpuMat()
            gpu_map_y.upload(map_y)

            self.gpu_maps[cam_key] = (gpu_map_x, gpu_map_y)
            self.cpu_maps[cam_key] = (map_x, map_y)
            self.masks[cam_key] = mask

        self.blend_weights = self._compute_blend_weights()
        self.gains = {k: 1.0 for k in self.cam_keys}
        self.calibrated = False

    def _compute_homography(self, new_K, height, pitch_deg, yaw_deg, offset):
        theta = math.radians(pitch_deg)
        psi = math.radians(yaw_deg)

        R = np.array([
            [math.cos(psi), math.sin(psi), 0],
            [math.sin(theta) * math.sin(psi), -math.sin(theta) * math.cos(psi), -math.cos(theta)],
            [-math.cos(theta) * math.sin(psi), math.cos(theta) * math.cos(psi), -math.sin(theta)],
        ], dtype=np.float64)

        cam_pos = np.array([offset[0], offset[1], height], dtype=np.float64)
        t = -R @ cam_pos

        H_ground_to_image = new_K @ np.column_stack([R[:, 0], R[:, 1], t])

        T_bev_to_ground = np.array([
            [self.ground_range / self.bev_size, 0, -self.ground_range / 2],
            [0, -self.ground_range / self.bev_size, self.ground_range / 2],
            [0, 0, 1],
        ], dtype=np.float64)

        return H_ground_to_image @ T_bev_to_ground

    def _precompute_fused_map(self, K_full, D, new_K, H, cap_w, cap_h, work_w, work_h):
        map1_f, map2_f = cv2.fisheye.initUndistortRectifyMap(
            K_full, D, np.eye(3), new_K, (cap_w, cap_h), cv2.CV_32FC1
        )

        u_bev = np.arange(self.bev_size, dtype=np.float32)
        v_bev = np.arange(self.bev_size, dtype=np.float32)
        uu_bev, vv_bev = np.meshgrid(u_bev, v_bev)

        w = H[2, 0] * uu_bev + H[2, 1] * vv_bev + H[2, 2]
        u_und = ((H[0, 0] * uu_bev + H[0, 1] * vv_bev + H[0, 2]) / w).astype(np.float32)
        v_und = ((H[1, 0] * uu_bev + H[1, 1] * vv_bev + H[1, 2]) / w).astype(np.float32)

        combined_map_x = cv2.remap(map1_f, u_und, v_und, cv2.INTER_LINEAR,
                                   borderMode=cv2.BORDER_CONSTANT, borderValue=-1)
        combined_map_y = cv2.remap(map2_f, u_und, v_und, cv2.INTER_LINEAR,
                                   borderMode=cv2.BORDER_CONSTANT, borderValue=-1)

        scale_x = work_w / cap_w
        scale_y = work_h / cap_h
        combined_map_x = combined_map_x * scale_x
        combined_map_y = combined_map_y * scale_y

        valid = (w > 0) & (combined_map_x >= 0) & (combined_map_x < work_w) \
                & (combined_map_y >= 0) & (combined_map_y < work_h)

        return combined_map_x, combined_map_y, valid.astype(np.bool_)

    def _compute_blend_weights(self):
        weights = {}
        for cam_key in self.cam_keys:
            mask = self.masks[cam_key].astype(np.uint8)
            dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
            weights[cam_key] = dist.astype(np.float32)

        total = np.zeros((self.bev_size, self.bev_size), dtype=np.float32)
        for w in weights.values():
            total += w
        total[total == 0] = 1.0

        for cam_key in self.cam_keys:
            weights[cam_key] /= total

        return weights

    def calibrate(self, frames, num_frames=10):
        gpu_frame = cv2.cuda_GpuMat()
        accum = {k: np.zeros((self.bev_size, self.bev_size, 3), dtype=np.float64) for k in self.cam_keys}
        count = 0

        for _ in range(num_frames + 5):
            all_ready = all(f is not None for f in frames.values())
            if not all_ready:
                time.sleep(0.1)
                continue

            for cam_key in self.cam_keys:
                gpu_map_x, gpu_map_y = self.gpu_maps[cam_key]
                gpu_bev = cv2.cuda.remap(frames[cam_key], gpu_map_x, gpu_map_y,
                                         interpolation=cv2.INTER_LINEAR,
                                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
                bev = gpu_bev.download()
                accum[cam_key] += bev.astype(np.float64)

            count += 1
            if count >= num_frames:
                break
            time.sleep(0.05)

        if count == 0:
            self.calibrated = True
            return

        bev_images = {k: (v / count).astype(np.uint8) for k, v in accum.items()}

        self.gains = self._compute_gains(bev_images)

        for cam_key in self.cam_keys:
            bev_images[cam_key] = np.clip(
                bev_images[cam_key].astype(np.float32) * self.gains[cam_key], 0, 255
            ).astype(np.uint8)

        self.blend_weights = self._find_seam_and_feather(bev_images)
        self.calibrated = True

    def _compute_gains(self, bev_images):
        gains = {k: 1.0 for k in self.cam_keys}
        mean_intensities = {}

        for cam_key in self.cam_keys:
            overlap = np.zeros((self.bev_size, self.bev_size), dtype=bool)
            for other_key in self.cam_keys:
                if other_key != cam_key:
                    overlap |= self.masks[other_key]
            overlap &= self.masks[cam_key]

            if overlap.sum() > 100:
                mean_intensities[cam_key] = bev_images[cam_key][overlap].mean()

        if len(mean_intensities) < 2:
            return gains

        global_mean = np.mean(list(mean_intensities.values()))
        for cam_key in mean_intensities:
            if mean_intensities[cam_key] > 0:
                gains[cam_key] = global_mean / mean_intensities[cam_key]

        return gains

    def _find_seam_and_feather(self, bev_images):
        cam_pairs = list(zip(self.cam_keys, self.cam_keys[1:] + [self.cam_keys[0]]))

        seam_mask = {k: self.masks[k].copy() for k in self.cam_keys}

        for cam_a, cam_b in cam_pairs:
            overlap = self.masks[cam_a] & self.masks[cam_b]
            if overlap.sum() < 50:
                continue

            diff = np.zeros((self.bev_size, self.bev_size), dtype=np.float32)
            img_a = bev_images[cam_a].astype(np.float32)
            img_b = bev_images[cam_b].astype(np.float32)
            color_diff = np.sqrt(np.sum((img_a - img_b) ** 2, axis=2))
            diff[overlap] = color_diff[overlap]

            dist_a = cv2.distanceTransform(self.masks[cam_a].astype(np.uint8), cv2.DIST_L2, 5)
            dist_b = cv2.distanceTransform(self.masks[cam_b].astype(np.uint8), cv2.DIST_L2, 5)

            cost_a = dist_a.copy()
            cost_b = dist_b.copy()
            cost_a[overlap] -= color_diff[overlap] * 0.1
            cost_b[overlap] += color_diff[overlap] * 0.1

            a_wins = overlap & (cost_a >= cost_b)
            b_wins = overlap & ~a_wins

            seam_mask[cam_a][b_wins] = False
            seam_mask[cam_b][a_wins] = False

        weights = {}
        for cam_key in self.cam_keys:
            mask = seam_mask[cam_key].astype(np.uint8)
            dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
            dist = np.minimum(dist, self.feather_band).astype(np.float32)
            weights[cam_key] = dist

        total = np.zeros((self.bev_size, self.bev_size), dtype=np.float32)
        for w in weights.values():
            total += w
        total[total == 0] = 1.0

        for cam_key in self.cam_keys:
            weights[cam_key] /= total

        return weights

    def stitch(self, frames, floor_masks=None):
        canvas = np.zeros((self.bev_size, self.bev_size, 3), dtype=np.float32)

        for cam_key in self.cam_keys:
            gpu_map_x, gpu_map_y = self.gpu_maps[cam_key]
            gpu_bev = cv2.cuda.remap(frames[cam_key], gpu_map_x, gpu_map_y,
                                     interpolation=cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            bev = gpu_bev.download().astype(np.float32) * self.gains[cam_key]
            canvas += bev * self.blend_weights[cam_key][:, :, np.newaxis]

        bev_canvas = np.clip(canvas, 0, 255).astype(np.uint8)

        if floor_masks is not None:
            floor_bev = np.zeros((self.bev_size, self.bev_size), dtype=np.uint8)
            for cam_key in self.cam_keys:
                if cam_key not in floor_masks:
                    continue
                map_x, map_y = self.cpu_maps[cam_key]
                mask_in_bev = cv2.remap(floor_masks[cam_key], map_x, map_y,
                                        cv2.INTER_NEAREST, borderValue=0)
                floor_bev[self.masks[cam_key] & (mask_in_bev > 0)] = 1

            floor_visible = (floor_bev > 0) & np.any(bev_canvas > 0, axis=2)
            bev_canvas[floor_visible] = (
                bev_canvas[floor_visible] * 0.85 + np.array([0, 180, 0]) * 0.15
            ).astype(np.uint8)

        return bev_canvas
