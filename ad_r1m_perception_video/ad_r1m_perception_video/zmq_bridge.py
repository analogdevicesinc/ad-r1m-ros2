import json

import numpy as np
import zmq

DEFAULT_ENDPOINT = 'ipc:///tmp/perception.ipc'
TOPIC = b'perception'


class FramePublisher:
    def __init__(self, endpoint=DEFAULT_ENDPOINT, sndhwm=2):
        self._ctx = zmq.Context.instance()

        self._sock.setsockopt(zmq.SNDHWM, sndhwm)
        self._sock.bind(endpoint)

    def publish(self, frames, meta=None):
        names = list(frames.keys())
        header = {
            'meta': meta or {},
            'frames': [],
        }
        buffers = []
        for name in names:
            arr = np.ascontiguousarray(frames[name])
            header['frames'].append({
                'name': name,
                'shape': list(arr.shape),
                'dtype': str(arr.dtype),
            })
            buffers.append(arr)

        parts = [TOPIC, json.dumps(header).encode('utf-8')]
        parts.extend(buffers)
        self._sock.send_multipart(parts, copy=False)

    def close(self):
        self._sock.close(linger=0)


class FrameSubscriber:
    def __init__(self, endpoint=DEFAULT_ENDPOINT, rcvhwm=2):
        self._ctx = zmq.Context.instance()
        self._sock = self._ctx.socket(zmq.SUB)
        self._sock.setsockopt(zmq.RCVHWM, rcvhwm)
        self._sock.setsockopt(zmq.SUBSCRIBE, TOPIC)
        self._sock.connect(endpoint)

    def recv(self, timeout_ms=0):
        if timeout_ms:
            if not self._sock.poll(timeout_ms, zmq.POLLIN):
                return None

        latest = None
        while True:
            try:
                latest = self._sock.recv_multipart(zmq.NOBLOCK, copy=False)
            except zmq.Again:
                break

        if latest is None:
            return None

        return self._parse(latest)

    @staticmethod
    def _parse(parts):
        header = json.loads(bytes(parts[1]))
        specs = header['frames']
        frames = {}
        for spec, buf in zip(specs, parts[2:]):
            arr = np.frombuffer(bytes(buf), dtype=np.dtype(spec['dtype']))
            frames[spec['name']] = arr.reshape(spec['shape'])
        return header.get('meta', {}), frames

    def close(self):
        self._sock.close(linger=0)
