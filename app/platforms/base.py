from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePlatform(ABC):
    name: str = "Base"

    @abstractmethod
    async def post(self, message: str) -> Dict[str, Any]:
        pass
