from .registry import IndicatorRegistry, IndicatorNotFoundError

registry = IndicatorRegistry()
register = registry.register

__all__ = ["registry", "register", "IndicatorNotFoundError"]
