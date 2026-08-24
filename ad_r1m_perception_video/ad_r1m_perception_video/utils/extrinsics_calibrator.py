import os
import cv2
import numpy as np
import yaml
import math
import threading

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config', 'pipeline.yaml')

# Checkerboard (for height + pitch per camera)
CHECKER_INNER_CORNERS = (4, 3)
CHECKER_SQUARE_SIZE = 0.05  # meters

# ChArUco board (for inter-camera translation)
CHARUCO_SQUARES_X = 7
CHARUCO_SQUARES_Y = 5
CHARUCO_SQUARE_SIZE = 0.0395  # meters
CHARUCO_MARKER_SIZE = 0.030   # meters
CHARUCO_DICT = cv2.aruco.DICT_4X4_50

CAMS_TO_CALIBRATE = ['rear', 'left', 'front', 'right']


CAPTURE_W = 1640
CAPTURE_H = 1232

EXPOSURE_TIME_NS = 20000000  # 20ms — slightly bright for indoor calibration
GAIN = 2.0
ISP_DIGITAL_GAIN = 2.0

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        cfg = yaml.safe_load(f)
    params = cfg['perception_node']['ros__parameters']

    cameras = {}
    for cam_key, cam_data in params['cameras'].items():
        config = cam_data['config']
        calib = cam_data['calibration']
        name = config['name']
        K = np.array(calib['camera_matrix'], dtype=np.float64).reshape(3, 3)
        D = np.array(calib['distortion_coeffs'], dtype=np.float64)
        cameras[name] = {
            'sensor_id': config['sensor_id'],
            'K': K,
            'D': D,
            'width': calib['calibration_width'],
            'height': calib['calibration_height'],
        }
    return cameras


def open_camera(cam):
    pipeline = (
        f"nvarguscamerasrc sensor_id={cam['sensor_id']} sensor_mode=1 "
        f"exposuretimerange=\"{EXPOSURE_TIME_NS} {EXPOSURE_TIME_NS}\" "
        f"gainrange=\"{GAIN} {GAIN}\" "
        f"ispdigitalgainrange=\"{ISP_DIGITAL_GAIN} {ISP_DIGITAL_GAIN}\" ! "
        f"video/x-raw(memory:NVMM), width={CAPTURE_W},height={CAPTURE_H},framerate=30/1,format=NV12 ! "
        "nvvidconv ! video/x-raw,format=BGRx ! "
        "videoconvert ! video/x-raw,format=BGR ! appsink drop=1"
    )
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        print(f"[ERROR] Failed to open sensor_id={cam['sensor_id']}")
        return None
    print(f"[OK] Opened sensor_id={cam['sensor_id']}")
    return cap

def precompute_undistort_maps(cam):
    K_full = cam['K'].copy()
    D_full = cam['D'].copy()
    sx = CAPTURE_W / cam['width']
    sy = CAPTURE_H / cam['height']
    K_full[0, 0] *= sx
    K_full[0, 2] *= sx
    K_full[1, 1] *= sy
    K_full[1, 2] *= sy

    new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
        K_full, D_full, (CAPTURE_W, CAPTURE_H), np.eye(3), balance=0.0
    )
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(
        K_full, D_full, np.eye(3), new_K, (CAPTURE_W, CAPTURE_H), cv2.CV_16SC2
    )
    return map1, map2, new_K


def make_object_points():
    cols, rows = CHECKER_INNER_CORNERS
    objp = np.zeros((cols * rows, 3), dtype=np.float64)
    for i in range(rows):
        for j in range(cols):
            objp[i * cols + j] = [j * CHECKER_SQUARE_SIZE, i * CHECKER_SQUARE_SIZE, 0.0]
    return objp


def extract_height_and_pitch(rvec, tvec):
    R, _ = cv2.Rodrigues(rvec)
    cam_pos_in_board = -R.T @ tvec.flatten()
    height = abs(cam_pos_in_board[2])

    ground_normal_in_cam = R[:, 2]
    if ground_normal_in_cam[1] > 0:
        ground_normal_in_cam = -ground_normal_in_cam
    pitch = math.degrees(math.atan2(-ground_normal_in_cam[2], -ground_normal_in_cam[1]))

    return height, pitch


BEV_SIZE = 600
BEV_GROUND_RANGE = 5.0


def create_charuco_board():
    aruco_dict = cv2.aruco.getPredefinedDictionary(CHARUCO_DICT)
    board = cv2.aruco.CharucoBoard(
        (CHARUCO_SQUARES_X, CHARUCO_SQUARES_Y),
        CHARUCO_SQUARE_SIZE,
        CHARUCO_MARKER_SIZE,
        aruco_dict,
    )
    return board, aruco_dict


def detect_charuco_pose(gray, K, board, aruco_dict):
    detector = cv2.aruco.ArucoDetector(aruco_dict)
    corners, ids, _ = detector.detectMarkers(gray)
    if ids is None or len(ids) < 4:
        return None, None
    _, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(
        corners, ids, gray, board
    )
    if charuco_ids is None or len(charuco_ids) < 4:
        return None, None
    success, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(
        charuco_corners, charuco_ids, board, K, None, None, None
    )
    if success:
        return rvec, tvec
    return None, None


def compute_relative_pose(rvec_a, tvec_a, rvec_b, tvec_b, ref_yaw_deg, ref_pitch_deg):
    """Compute position and relative yaw of camera B relative to camera A in world frame."""
    R_a, _ = cv2.Rodrigues(rvec_a)
    R_b, _ = cv2.Rodrigues(rvec_b)

    # Camera positions in board frame
    pos_a = -R_a.T @ tvec_a.flatten()
    pos_b = -R_b.T @ tvec_b.flatten()
    delta_board = pos_b - pos_a

    # Build world-to-camera rotation for reference camera (same as in compute_bev_homography)
    theta = math.radians(ref_pitch_deg)
    psi = math.radians(ref_yaw_deg)
    R_world_to_cam = np.array([
        [math.cos(psi), math.sin(psi), 0],
        [math.sin(theta) * math.sin(psi), -math.sin(theta) * math.cos(psi), -math.cos(theta)],
        [-math.cos(theta) * math.sin(psi), math.cos(theta) * math.cos(psi), -math.sin(theta)],
    ], dtype=np.float64)


    R_board_to_world = R_world_to_cam.T @ R_a

    # Transform delta from board frame to world frame
    delta_world = R_board_to_world @ delta_board

    # Relative rotation for yaw: R_b_from_a = R_b @ R_a^T (in camera frame)
    # Transform to world frame to get yaw around Z axis
    R_rel_cam = R_b @ R_a.T
    R_rel_world = R_world_to_cam.T @ R_rel_cam @ R_world_to_cam
    rel_yaw = -math.degrees(math.atan2(R_rel_world[1, 0], R_rel_world[0, 0]))

    return delta_world, rel_yaw


def compute_bev_homography(new_K, height, pitch_deg, yaw_deg=0.0, cam_offset_xy=(0.0, 0.0)):
    """Compute homography mapping BEV pixels to camera image pixels.

    BEV is vehicle-centered: X=right, Y=forward, vehicle at center.
    Each camera faces yaw_deg from vehicle forward, pitched down by pitch_deg.
    cam_offset_xy: (x, y) position of this camera in the vehicle ground frame.
    """
    theta = math.radians(pitch_deg)
    psi = math.radians(yaw_deg)

    R = np.array([
        [math.cos(psi), math.sin(psi), 0],
        [math.sin(theta) * math.sin(psi), -math.sin(theta) * math.cos(psi), -math.cos(theta)],
        [-math.cos(theta) * math.sin(psi), math.cos(theta) * math.cos(psi), -math.sin(theta)],
    ], dtype=np.float64)

    cam_pos = np.array([cam_offset_xy[0], cam_offset_xy[1], height], dtype=np.float64)
    t = -R @ cam_pos

    H_ground_to_image = new_K @ np.column_stack([R[:, 0], R[:, 1], t])

    T_bev_to_ground = np.array([
        [BEV_GROUND_RANGE / BEV_SIZE, 0, -BEV_GROUND_RANGE / 2],
        [0, -BEV_GROUND_RANGE / BEV_SIZE, BEV_GROUND_RANGE / 2],
        [0, 0, 1],
    ], dtype=np.float64)

    return H_ground_to_image @ T_bev_to_ground


CAM_YAWS = {'front': 0.0, 'rear': 180.0, 'left': 90.0, 'right': -90.0}


class CameraThread:
    def __init__(self, name, cam):
        self.name = name
        self.cap = open_camera(cam)
        self.map1, self.map2, self.new_K = precompute_undistort_maps(cam)
        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                undistorted = cv2.remap(frame, self.map1, self.map2, cv2.INTER_LINEAR)
                with self.lock:
                    self.frame = undistorted

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.running = False
        self.thread.join()
        self.cap.release()


def get_charuco_frame(frame, ref_half):
    """Crop frame to left or right half for charuco detection when two identical boards may be visible."""
    if ref_half == 'left':
        return frame[:, :frame.shape[1] // 2]
    elif ref_half == 'right':
        return frame[:, frame.shape[1] // 2:]
    return frame


def get_charuco_K(new_K, ref_half, frame_width):
    """Adjust intrinsics for a half-frame crop."""
    if ref_half is None:
        return new_K
    K = new_K.copy()
    if ref_half == 'right':
        K[0, 2] -= frame_width // 2
    return K


def calibrate_pair(pair, ref_cam, frames, cam_threads, obj_points, charuco_board, aruco_dict,
                   cam_heights, cam_pitches, cam_offsets, cam_yaws, bev_Hs,
                   ref_half=None, target_half=None):
    """ref_half/target_half: 'left' or 'right' to crop the camera's frame for charuco detection,
    avoiding confusion when two identical boards are visible. None = use full frame."""
    target_cam = [n for n in pair if n != ref_cam][0]
    print(f"\n  --- Calibrating pair: {pair}, ref={ref_cam}"
          f"{f' (ref {ref_half} half)' if ref_half else ''}"
          f"{f' (target {target_half} half)' if target_half else ''} ---")

    for name in pair:
        gray = cv2.cvtColor(frames[name], cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(
            gray, CHECKER_INNER_CORNERS,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK
        )
        if not found:
            print(f"  [{name}] Checkerboard: not detected")
            continue
        corners = cv2.cornerSubPix(
            gray, corners, (11, 11), (-1, -1),
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        )
        success, rvec, tvec = cv2.solvePnP(
            obj_points, corners, cam_threads[name].new_K, None, flags=cv2.SOLVEPNP_IPPE
        )
        if success:
            h, p = extract_height_and_pitch(rvec, tvec)
            if h > 0.40 or abs(p) > 20.0:
                print(f"  [{name}] Checkerboard: REJECTED (height={h*100:.1f}cm pitch={p:.1f}deg) — likely charuco misdetection")
                continue
            cam_heights[name] = h
            cam_pitches[name] = p
            print(f"  [{name}] Checkerboard: height={h*100:.2f}cm pitch={p:.2f}deg")
        else:
            print(f"  [{name}] Checkerboard: solvePnP failed")

    charuco_poses = {}
    for name in pair:
        half = None
        if name == ref_cam:
            half = ref_half
        elif name == target_cam:
            half = target_half

        if half is not None:
            cropped = get_charuco_frame(frames[name], half)
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            K = get_charuco_K(cam_threads[name].new_K, half, frames[name].shape[1])
        else:
            gray = cv2.cvtColor(frames[name], cv2.COLOR_BGR2GRAY)
            K = cam_threads[name].new_K
        rvec, tvec = detect_charuco_pose(gray, K, charuco_board, aruco_dict)
        if rvec is not None:
            charuco_poses[name] = (rvec, tvec)
            print(f"  [{name}] ChArUco: detected")
        else:
            print(f"  [{name}] ChArUco: not detected")

    if len(charuco_poses) >= 2 and ref_cam in charuco_poses:
        rvec_ref, tvec_ref = charuco_poses[ref_cam]
        ref_yaw = cam_yaws[ref_cam]
        ref_pitch = cam_pitches[ref_cam] if cam_pitches[ref_cam] is not None else 5.0
        for name in pair:
            if name == ref_cam:
                continue
            if name in charuco_poses:
                rvec_n, tvec_n = charuco_poses[name]
                delta, rel_yaw = compute_relative_pose(
                    rvec_ref, tvec_ref, rvec_n, tvec_n, ref_yaw, ref_pitch
                )
                cam_offsets[name] = (cam_offsets[ref_cam][0] + delta[0],
                                     cam_offsets[ref_cam][1] + delta[1])
                cam_yaws[name] = ref_yaw + rel_yaw
                print(f"  [{name}] Offset from {ref_cam}: dX={delta[0]*100:.1f}cm dY={delta[1]*100:.1f}cm dZ={delta[2]*100:.1f}cm")
                print(f"  [{name}] Absolute: X={cam_offsets[name][0]*100:.1f}cm Y={cam_offsets[name][1]*100:.1f}cm Yaw={cam_yaws[name]:.1f}deg")

    for name in pair:
        if cam_heights[name] is not None and cam_pitches[name] is not None:
            bev_Hs[name] = compute_bev_homography(
                cam_threads[name].new_K,
                cam_heights[name],
                cam_pitches[name],
                cam_yaws[name],
                cam_offsets[name],
            )
    print("  [BEV updated]")


def main():
    cameras = load_config()
    obj_points = make_object_points()
    charuco_board, aruco_dict = create_charuco_board()

    cam_threads = {}
    for name in CAMS_TO_CALIBRATE:
        ct = CameraThread(name, cameras[name])
        if ct.cap is None:
            print(f"[ERROR] Could not open {name}, aborting")
            return
        cam_threads[name] = ct

    bev_Hs = {name: None for name in CAMS_TO_CALIBRATE}
    cam_heights = {name: None for name in CAMS_TO_CALIBRATE}
    cam_pitches = {name: None for name in CAMS_TO_CALIBRATE}
    cam_offsets = {name: (0.0, 0.0) for name in CAMS_TO_CALIBRATE}
    cam_yaws = {name: CAM_YAWS.get(name, 0.0) for name in CAMS_TO_CALIBRATE}

    print(f"Calibrating: {CAMS_TO_CALIBRATE}")
    print("SPACE = rear<->left + rear<->right, C = left<->front + right<->front (averaged), Q = quit")

    while True:
        frames = {}
        for name, ct in cam_threads.items():
            f = ct.get_frame()
            if f is not None:
                frames[name] = f

        if len(frames) < len(cam_threads):
            cv2.waitKey(1)
            continue

        displays = []
        for name in CAMS_TO_CALIBRATE:
            disp = cv2.resize(frames[name], (410, 308))
            cv2.putText(disp, name, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            displays.append(disp)

        pov_row = np.hstack(displays)

        bev_canvas = np.zeros((BEV_SIZE, BEV_SIZE, 3), dtype=np.uint8)
        for name in CAMS_TO_CALIBRATE:
            if bev_Hs[name] is not None:
                H = bev_Hs[name]
                bev = cv2.warpPerspective(frames[name], H, (BEV_SIZE, BEV_SIZE),
                                          flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
                us = np.arange(BEV_SIZE)
                vs = np.arange(BEV_SIZE)
                uu, vv = np.meshgrid(us, vs)
                w = H[2, 0] * uu + H[2, 1] * vv + H[2, 2]
                valid = w > 0
                bev[~valid] = 0
                mask = valid & bev.any(axis=2)
                bev_canvas[mask] = bev[mask]

        bev_display = cv2.resize(bev_canvas, (pov_row.shape[1], pov_row.shape[0]))
        combined = np.vstack([pov_row, bev_display])
        cv2.imshow("Calibration", combined)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):

            calibrate_pair(['rear', 'left'], 'rear', frames, cam_threads, obj_points,
                           charuco_board, aruco_dict, cam_heights, cam_pitches,
                           cam_offsets, cam_yaws, bev_Hs, ref_half='right')
            calibrate_pair(['rear', 'right'], 'rear', frames, cam_threads, obj_points,
                           charuco_board, aruco_dict, cam_heights, cam_pitches,
                           cam_offsets, cam_yaws, bev_Hs, ref_half='left')
        elif key == ord('c'):

            calibrate_pair(['left', 'front'], 'left', frames, cam_threads, obj_points,
                           charuco_board, aruco_dict, cam_heights, cam_pitches,
                           cam_offsets, cam_yaws, bev_Hs, target_half='left')
            front_via_left = (cam_offsets['front'], cam_yaws['front'])

            calibrate_pair(['right', 'front'], 'right', frames, cam_threads, obj_points,
                           charuco_board, aruco_dict, cam_heights, cam_pitches,
                           cam_offsets, cam_yaws, bev_Hs, target_half='right')
            front_via_right = (cam_offsets['front'], cam_yaws['front'])

            avg_x = (front_via_left[0][0] + front_via_right[0][0]) / 2.0
            avg_y = (front_via_left[0][1] + front_via_right[0][1]) / 2.0
            avg_yaw = (front_via_left[1] + front_via_right[1]) / 2.0
            cam_offsets['front'] = (avg_x, avg_y)
            cam_yaws['front'] = avg_yaw
            if cam_heights['front'] is not None and cam_pitches['front'] is not None:
                bev_Hs['front'] = compute_bev_homography(
                    cam_threads['front'].new_K, cam_heights['front'],
                    cam_pitches['front'], cam_yaws['front'], cam_offsets['front'])
            print(f"  [front] Averaged: X={avg_x*100:.1f}cm Y={avg_y*100:.1f}cm Yaw={avg_yaw:.1f}deg")
            print(f"    via left:  X={front_via_left[0][0]*100:.1f}cm Y={front_via_left[0][1]*100:.1f}cm Yaw={front_via_left[1]:.1f}deg")
            print(f"    via right: X={front_via_right[0][0]*100:.1f}cm Y={front_via_right[0][1]*100:.1f}cm Yaw={front_via_right[1]:.1f}deg")
        elif key == ord('q'):
            break

    for ct in cam_threads.values():
        ct.stop()
    cv2.destroyAllWindows()
    
    
    
if __name__ == '__main__':
    main()
