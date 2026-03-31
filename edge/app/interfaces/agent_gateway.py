from abc import ABC, abstractmethod


class AgentGateway(ABC):
    @abstractmethod
    def on_message(self, client, userdata, msg):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass