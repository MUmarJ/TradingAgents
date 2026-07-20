# TradingAgents/graph/__init__.py
# Lazy imports to avoid pulling in optional dependencies (e.g., ace)
# when only signal_processing is needed.


def __getattr__(name):
    if name == "TradingAgentsGraph":
        from .trading_graph import TradingAgentsGraph
        return TradingAgentsGraph
    if name == "ConditionalLogic":
        from .conditional_logic import ConditionalLogic
        return ConditionalLogic
    if name == "GraphSetup":
        from .setup import GraphSetup
        return GraphSetup
    if name == "Propagator":
        from .propagation import Propagator
        return Propagator
    if name == "Reflector":
        from .reflection import Reflector
        return Reflector
    if name == "SignalProcessor":
        from .signal_processing import SignalProcessor
        return SignalProcessor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "TradingAgentsGraph",
    "ConditionalLogic",
    "GraphSetup",
    "Propagator",
    "Reflector",
    "SignalProcessor",
]
