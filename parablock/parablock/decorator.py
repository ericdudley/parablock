"""
Decorator module for marking functions for natural language implementation.
"""
import inspect
from functools import wraps
from typing import Any, Callable, Dict, Optional
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
import textwrap


from parablock.utils import Cache
from .registry import FunctionRegistry
from .executor import pararun

def parablock(func: Optional[Callable] = None, *, frozen: bool = False) -> Callable:
    """
    Decorator that marks functions for natural language implementation
    and redirects direct calls to use pararun.
    
    Args:
        func: The function to be decorated
        frozen: If True, don't regenerate even if docstring changes
        
    Returns:
        The decorated function that will use the implementation registry
    """
    def decorator(func: Callable) -> Callable:
        # Get function metadata
        source = inspect.getsource(func)
        docstring = inspect.getdoc(func) or ""
        signature = inspect.signature(func)
        module = inspect.getmodule(func)
        module_name = module.__name__ if module else ""
        
        # Register the function
        FunctionRegistry.register(
            func=func,
            name=func.__name__,
            module=module_name,
            source=source,
            docstring=docstring,
            signature=signature,
            frozen=frozen,
        )
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Dict[str, Any]) -> Any:
            return pararun(func)(*args, **kwargs)
        
        def peek():
            full_name = f"{module_name}.{func.__name__}"
            # Ensure cache is loaded for this module
            # This will also populate the registry with implementations from cache
            Cache.load(module_name)
            # Get the implementation from the registry
            implementation = FunctionRegistry.get_implementation(full_name)
            if not implementation:
                return "Could not find implementation"
            
            # Print the metadata in a table
            console = Console()
            table = Table(title="Metadata")
            table.add_column("Key", justify="left")
            table.add_column("Value", justify="left")
            table.add_row("Name", func.__name__)
            table.add_row("Module", module_name)
            table.add_row("Signature", str(signature))
            table.add_row("Docstring", docstring)
            table.add_row("Source", textwrap.indent(source, "  "))
            table.add_row("Frozen", str(frozen))
            # Print the implementation in its own panel
            implementation_panel = Panel(
                textwrap.indent(implementation, "  "), 
                title="Implementation"
            )
            panel = Panel(Group(table, implementation_panel), title=f"{func.__name__}.peek()")
            console.print(panel)
            
            return implementation
        
        # Add the peek property to the wrapper function
        wrapper.peek = peek
        
        return wrapper
    
    if func is None:
        return decorator
    
    return decorator(func)