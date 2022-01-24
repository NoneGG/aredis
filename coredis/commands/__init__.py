from abc import ABC, abstractmethod
from typing import Any


class CommandMixin(ABC):
    @abstractmethod
    def execute_command(self, command: str, *args: Any) -> Any:
        pass
