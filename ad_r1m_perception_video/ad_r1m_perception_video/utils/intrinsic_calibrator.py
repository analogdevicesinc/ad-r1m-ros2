import argparse
import cv2
import os
import glob
import numpy as np

class IntrinsicCalibrator():
    def __init__(self, camera_capture):
        self.camera_capture = camera_capture
        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
        self.board = cv2.aruco.CharucoBoard((7, 5), 0.0395, 0.03,self.dictionary)
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, cv2.aruco.DetectorParameters())

    def capture_images(self):
        frame_number = 0
        while(self.camera_capture.isOpened()):
            ret, frame = self.camera_capture.read()
            if ret:
                display = frame.copy()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                markerCorners, markerIds, _ = self.detector.detectMarkers(gray)
                n_charuco = 0
                if markerCorners:
                    cv2.aruco.drawDetectedMarkers(display, markerCorners, markerIds)
                    retval, charucoCorners, charucoIds = cv2.aruco.interpolateCornersCharuco(
                        markerCorners, markerIds, gray, self.board
                    )
                    if retval and retval > 0:
                        cv2.aruco.drawDetectedCornersCharuco(display, charucoCorners, charucoIds)
                        n_charuco = retval

                status = f"Corners: {n_charuco}/24"
                color = (0, 255, 0) if n_charuco > 5 else (0, 0, 255)
                cv2.putText(display, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                cv2.putText(display, f"Captured: {frame_number}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(display, "SPACE=capture  Q=quit", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                cv2.imshow('current_frame', display)
                key = cv2.waitKey(1) & 0xFF
                if key == ord(' '):
                    if(not os.path.exists('calibration_data_set')):
                        os.mkdir('calibration_data_set')
                    cv2.imwrite(f'calibration_data_set/frame_{frame_number}.png', frame)
                    print(f"[CAPTURED] frame_{frame_number}.png ({n_charuco} charuco corners detected)")
                    frame_number = frame_number + 1
                elif key == ord('q'):
                    break
            else:
                print("Problem with camera capture")
                break
               
def calibrate_camera():
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
    board = cv2.aruco.CharucoBoard((7, 5), 0.0395, 0.03,dictionary)
    params = cv2.aruco.DetectorParameters()
    arucoDetector = cv2.aruco.ArucoDetector(dictionary, params)

    allObjectPoints = []
    allImagePoints = []
    imageSize = None

    boardCorners = board.getChessboardCorners()

    images = glob.glob('calibration_data_set/*.png')
    debug_dir = 'calibration_debug'
    os.makedirs(debug_dir, exist_ok=True)

    print(f"Found {len(images)} images")
    for iname in images:
        img = cv2.imread(iname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        debug_img = img.copy()

        markerCorners, markerIds, _ = arucoDetector.detectMarkers(gray)
        n_markers = len(markerCorners) if markerCorners is not None else 0

        n_charuco = 0
        if n_markers > 0:
            cv2.aruco.drawDetectedMarkers(debug_img, markerCorners, markerIds)

            retval, charucoCorners, charucoIds = cv2.aruco.interpolateCornersCharuco(
                markerCorners, markerIds, gray, board
            )
            n_charuco = retval if retval is not None else 0
            if retval is not None and retval > 5:
                cv2.aruco.drawDetectedCornersCharuco(debug_img, charucoCorners, charucoIds)

                objPts = boardCorners[charucoIds.flatten()].reshape(-1, 1, 3).astype(np.float64)
                imgPts = charucoCorners.reshape(-1, 1, 2).astype(np.float64)

                allObjectPoints.append(objPts)
                allImagePoints.append(imgPts)
                imageSize = gray.shape[::-1]

        print(f"  {os.path.basename(iname)}: {n_markers} markers, {n_charuco} charuco corners")
        cv2.imwrite(f"{debug_dir}/{os.path.basename(iname)}", debug_img)

    print(f"Images with detected board: {len(allObjectPoints)}/{len(images)}")

    if len(allObjectPoints) > 10:
        K = np.zeros((3, 3))
        D = np.zeros((4, 1))

        calibration_flags = (
            cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC
            + cv2.fisheye.CALIB_FIX_SKEW
        )

        try:
            ret, K, D, rvecs, tvecs = cv2.fisheye.calibrate(
                allObjectPoints,
                allImagePoints,
                imageSize,
                K, D,
                None, None,
                calibration_flags,
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-6)
            )
        except cv2.error as e:
            print(f"Calibration failed: {e}")
            print("Try capturing more images with the board at varied angles and positions.")
            return

        print(f"Reprojection error: {ret:.4f} pixels")
        print("Camera Matrix:\n", K)
        print("Distortion Coefficients (k1, k2, k3, k4):\n", D.flatten())

        h, w = img.shape[:2]
        newK = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
            K, D, (w, h), np.eye(3), balance=0.0
        )
        map1, map2 = cv2.fisheye.initUndistortRectifyMap(
            K, D, np.eye(3), newK, (w, h), cv2.CV_16SC2
        )
        und = cv2.remap(img, map1, map2, cv2.INTER_LINEAR)
        cv2.imwrite('calibresult.png', und)
        
        rescale_params(K, D, imageSize, (820, 616))

    else:
        print("Not enough images for calibration")


def rescale_params(K, D, original_size, target_size):
    sx = target_size[0] / original_size[0]
    sy = target_size[1] / original_size[1]

    K_scaled = K.copy()
    K_scaled[0, 0] *= sx
    K_scaled[0, 2] *= sx
    K_scaled[1, 1] *= sy
    K_scaled[1, 2] *= sy

    print(f"\nRescaled to {target_size[0]}x{target_size[1]}:")
    print("Camera Matrix:\n", K_scaled)
    print("Distortion Coefficients (unchanged):\n", D.flatten())

    return K_scaled, D

def main():
    parser = argparse.ArgumentParser(description='Intrinsic camera calibration')
    parser.add_argument('--sensor', type=int, default=2, help='Argus sensor_id to open')
    args = parser.parse_args()

    gstreamer_pipeline = (
        f"nvarguscamerasrc sensor_id={args.sensor} sensor_mode=1 ! "
        f"video/x-raw(memory:NVMM), width={1640},height={1232},framerate={30}/1,format=NV12 ! "
        "nvvidconv ! "
        "video/x-raw,format=BGRx ! "
        "videoconvert ! "
        "video/x-raw,format=BGR ! "
        "appsink drop=1"
    )
    camera_capture = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)
    calibrator = IntrinsicCalibrator(camera_capture=camera_capture)

    calibrator.capture_images()

    camera_capture.release()
    calibrate_camera()
    
    

if __name__ == '__main__':
    main()




##7x5 39.2 square
