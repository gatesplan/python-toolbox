from typing import Callable, List, Dict


class IndicatorNotFoundError(KeyError):
    pass


class IndicatorRegistry:
    def __init__(self):
        self._registry: Dict[str, Callable] = {}

    def register(self, name: str) -> Callable[[Callable], Callable]:
        def decorator(func: Callable) -> Callable:
            self._registry[name] = func
            return func
        return decorator

    def get(self, name: str) -> Callable:
        if name not in self._registry:
            raise IndicatorNotFoundError(f"Indicator '{name}' not found in registry")
        return self._registry[name]

    def has(self, name: str) -> bool:
        return name in self._registry

    def list_all(self) -> List[str]:
        return sorted(self._registry.keys())
