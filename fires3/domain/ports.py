from typing import Protocol,List
from .models import Object

class Bucket(Protocol):
    def get(self, key: str):
        ...
    
    def list(self) -> List[Object]:
        ...

    def create(self, key: str, content: bytes) -> Object:
        ...

    def delete(self, key: str) -> bool:
        ...