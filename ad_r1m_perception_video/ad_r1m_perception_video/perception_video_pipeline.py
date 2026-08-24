import os
import sys
import time
import threading
import yaml
import cv2

from ad_r1m_perception_video.capture import create_camera
from ad_r1m_perception_video.processing import BEV, FloorSegmentor
from ad_r1m_perception_video.display import Display
from ad_r1m_perception_video.zmq_bridge import FramePublisher


def main(config_path=None):
    if config_path is None:
        if len(sys.argv) > 1:
            config_path = sys.argv[1]
        else:
            pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(pkg_dir, 'config', 'pipeline.yaml')

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    params = config['perception_node']['ros__parameters']
    cameras_cfg = params['cameras']

    frames = {}
    cams = {}
    running = True

    def capture_loop(cam_key, cam):
        while running:
            frame = cam.get_frame()
            if frame is not None:
                gpu_mat = cv2.cuda_GpuMat()
                gpu_mat.upload(frame)
                frames[cam_key] = cv2.cuda.cvtColor(gpu_mat, cv2.COLOR_BGRA2BGR)

    for cam_key, cam_data in cameras_cfg.items():
        cam = create_camera(cam_data['config'])
        cam.start()
        cams[cam_key] = cam
        frames[cam_key] = None
        threading.Thread(target=capture_loop, args=(cam_key, cam), daemon=True).start()
        print(f"Started {cam_key} ({cam_data['config'].get('name', '')})")

    bev_cfg = params.get('bev', {})
    bev = BEV(
        cameras_cfg,
        bev_size=bev_cfg.get('size', 800),
        ground_range=bev_cfg.get('ground_range', 5.0),
        feather_band=bev_cfg.get('feather_band_width', 30),
    )

    floor_cfg = params.get('floor', {})
    floor_seg = None
    if floor_cfg.get('enabled', False) and floor_cfg.get('model_path', ''):
        floor_cams = floor_cfg.get('cameras', list(cameras_cfg.keys()))
        floor_seg = FloorSegmentor(
            floor_cfg['model_path'],
            cameras_cfg,
            cam_keys=floor_cams,
            confidence=floor_cfg.get('confidence_threshold', 0.7),
        )
        print(f'Floor segmentation enabled on: {floor_cams}')

    display = Display(
        floor_seg=floor_seg,
        cameras_cfg=cameras_cfg,
    )

    publisher = FramePublisher()

    try:
        while True:
            if any(f is None for f in frames.values()):
                time.sleep(0.01)
                continue

            if not bev.calibrated:
                bev.calibrate(frames)
                print('BEV calibration done')

            floor_masks = None
            if floor_seg is not None:
                cpu_frames = {k: frames[k].download() for k in floor_seg.cam_keys}
                floor_seg.submit_batch(cpu_frames)
                floor_masks = floor_seg.get_all_masks()

            bev_canvas = bev.stitch(frames, floor_masks)
            display.show(bev_canvas, frames)

            out_frames = {'bev_frame': bev_canvas}
            if floor_masks:
                for cam_key, mask in floor_masks.items():
                    out_frames[f'floor_mask_{cam_key}'] = mask
            publisher.publish(out_frames, meta={'cam_keys': list(cameras_cfg.keys())})

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        running = False
        publisher.close()
        display.stop()
        if floor_seg is not None:
            floor_seg.stop()
        for cam in cams.values():
            cam.stop()


if __name__ == '__main__':
    main()
