from ad_r1m_perception_video.capture.camera import Camera


def create_camera(config: dict) -> Camera:
    cam_type = config.get('type', 'gstreamer')

    if cam_type == 'gstreamer':
        from ad_r1m_perception_video.capture.gstreamer_camera import GstreamerCamera
        return GstreamerCamera(config)
    else:
        raise ValueError(f"Unknown camera type: {cam_type}")
