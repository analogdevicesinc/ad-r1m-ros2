from abc import ABC, abstractmethod


class Camera(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def get_frame(self):
        pass

    @abstractmethod
    def stop(self):
        pass
