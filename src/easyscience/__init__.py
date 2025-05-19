from .global_object import GlobalObject

# Must be executed before any other imports
global_object = GlobalObject()
global_object.instantiate_stack()
global_object.stack.enabled = False


from .__version__ import __version__ as __version__  # noqa: E402
from .base_classes import ObjBase  # noqa: E402
from .fitting import AvailableMinimizers  # noqa: E402
from .fitting import Fitter  # noqa: E402
from .variable import DescriptorNumber  # noqa: E402
from .variable import Parameter  # noqa: E402

__all__ = [
    __version__,
    global_object,
    ObjBase,
    AvailableMinimizers,
    Fitter,
    DescriptorNumber,
    Parameter,
]
