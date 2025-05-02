from .global_object import GlobalObject

# Must be executed before any other imports
global_object = GlobalObject()
global_object.instantiate_stack()
global_object.stack.enabled = False


from .__version__ import __version__ as __version__  # noqa: E402
from .base_collection import BaseCollection  # noqa: E402
from .fitting.available_minimizers import AvailableMinimizers  # noqa: E402
from .interface_factory import InterfaceFactory  # noqa: E402

__all__ = [
    __version__,
    AvailableMinimizers,
    global_object,
    BaseCollection,
    InterfaceFactory,
]
