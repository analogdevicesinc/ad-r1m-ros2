import cv2

from ad_r1m_perception_video.capture.camera import Camera

class GstreamerCamera(Camera):
    def start(self):
        
        pipeline = (
            f"nvarguscamerasrc sensor_id={self.config['sensor_id']} sensor_mode={self.config['sensor_mode']} ! "
            f"video/x-raw(memory:NVMM), width={self.config['capture_width']},height={self.config['capture_height']},framerate={self.config['framerate']}/1,format=NV12 ! "
            f"nvvidconv ! video/x-raw,width={self.config['work_width']},height={self.config['work_height']},format=BGRx ! "
            "appsink max-buffers=1 drop=1"
        )
        
        try:
            self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera sensor_id={self.config['sensor_id']}")
        except Exception as e:
            self.cap = None
            raise RuntimeError(f"GStreamer pipeline error: {e}")

    def get_frame(self):
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        return frame if ret else None

    def stop(self):
        if self.cap is not None:
            self.cap.release()
