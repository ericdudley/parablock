"""
Runtime executor for parablock functions.
"""

import functools
import inspect
from typing import Any, Callable, TypeVar
import textwrap
from .registry import FunctionRegistry
from .utils import Cache

# Generic type variable for function return
T = TypeVar("T")


def pararun(func: Callable[..., T]) -> Callable[..., T]:
    """
    Execute a parablock-decorated function.

    This function retrieves the generated implementation for a
    parablock-decorated function and creates a new function that
    executes that implementation.

    Args:
        func: The parablock-decorated function

    Returns:
        A new function that executes the generated implementation

    Raises:
        RuntimeError: If no implementation is available for the function
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Get the full name of the function
        full_name = f"{func.__module__}.{func.__name__}"
        module_name = func.__module__

        # Ensure cache is loaded for this module
        # This will also populate the registry with implementations from cache
        Cache.load(module_name)

        # Get the implementation from the registry
        implementation = FunctionRegistry.get_implementation(full_name)

        if not implementation:
            # Try checking parent modules if the direct module doesn't have it
            parent_module = ".".join(module_name.split(".")[:-1])
            if parent_module:
                Cache.load(parent_module)
                implementation = FunctionRegistry.get_implementation(full_name)

        if not implementation:
            raise RuntimeError(
                f"No implementation available for {full_name}. "
                f"Run 'make process' to generate an implementation."
            )

        # Create a new function with the implementation
        exec_globals = {}
        exec_locals = {}

        # Create function signature without the 'fn' parameter
        signature = inspect.signature(func)
        param_names = [p for p in signature.parameters if p != "fn"]
        params_str = ", ".join(param_names)

        # Create a new function with the implementation
        # TODO These template strings are not very intuitive and a big source of bugs with indent issues.
        func_source = f"""
def implementation_func({params_str}):
{textwrap.indent(implementation, '   ')}
"""

        # Execute the function source to define implementation_func
        exec(func_source, exec_globals, exec_locals)

        # Get the implementation function
        implementation_func = exec_locals["implementation_func"]

        # Call the implementation function with the arguments
        return implementation_func(*args, **kwargs)

    return wrapper
