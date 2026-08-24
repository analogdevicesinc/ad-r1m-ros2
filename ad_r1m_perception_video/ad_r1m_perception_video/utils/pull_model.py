import argparse
import os
import sys
import urllib.request


FASTSAM_URL = "https://github.com/ultralytics/assets/releases/download/v8.2.0/FastSAM-s.pt"


def main():
    parser = argparse.ArgumentParser(description='Download FastSAM model and optionally export to TensorRT engine')
    parser.add_argument('--engine', action='store_true',
                        help='Also export the model to a TensorRT .engine file')
    parser.add_argument('--imgsz', type=int, default=384,
                        help='Input image size for engine export (default: 384)')
    args = parser.parse_args()

    pkg_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_dir = os.path.join(pkg_dir, 'models', 'floor')
    os.makedirs(model_dir, exist_ok=True)

    pt_path = os.path.join(model_dir, 'FastSAM-s.pt')

    if os.path.exists(pt_path):
        print(f'Model already exists at {pt_path}')
    else:
        print(f'Downloading FastSAM-s.pt...')
        urllib.request.urlretrieve(FASTSAM_URL, pt_path)
        print(f'Saved to {pt_path}')

    if args.engine:
        from ultralytics import FastSAM

        print(f'Exporting to TensorRT engine (imgsz={args.imgsz})...')
        model = FastSAM(pt_path)
        model.export(format='engine', imgsz=args.imgsz)

        base_name = os.path.splitext(os.path.basename(pt_path))[0]
        export_output = os.path.join(model_dir, f'{base_name}.engine')
        final_output = os.path.join(model_dir, f'{base_name}_{args.imgsz}_{args.imgsz}.engine')
        if os.path.exists(export_output):
            os.rename(export_output, final_output)
        print(f'Done: {final_output}')


if __name__ == '__main__':
    main()
