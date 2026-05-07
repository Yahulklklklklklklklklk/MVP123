from abc import ABC, abstractmethod


class BaseSourceAdapter(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def query(self, indicator: str, indicator_type: str) -> dict:
        raise NotImplementedError