"""
Registry for tracking parablock-decorated functions.
"""
import hashlib
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class FunctionMetadata:
    """Metadata for a registered function."""
    func: Callable
    name: str
    module: str
    source: str
    docstring: str
    signature: inspect.Signature
    frozen: bool
    implementation: Optional[str] = None
    
    def get_full_name(self) -> str:
        """Get the full name of the function (module.name)."""
        return f"{self.module}.{self.name}"
    
    def get_hash(self) -> str:
        """Generate a hash of the function's docstring and signature."""
        hash_input = f"{self.docstring}|{str(self.signature)}"
        return hashlib.md5(hash_input.encode()).hexdigest()


class FunctionRegistry:
    """Registry for parablock-decorated functions."""
    
    _registry: Dict[str, FunctionMetadata] = {}
    _implementations: Dict[str, str] = {}
    _needs_generation: Dict[str, bool] = {}
    
    @classmethod
    def register(
        cls,
        func: Callable,
        name: str,
        module: str,
        source: str,
        docstring: str,
        signature: inspect.Signature,
        frozen: bool,
    ) -> None:
        """Register a function with the registry."""
        full_name = f"{module}.{name}"
        cls._registry[full_name] = FunctionMetadata(
            func=func,
            name=name,
            module=module,
            source=source,
            docstring=docstring,
            signature=signature,
            frozen=frozen,
        )
    
    @classmethod
    def get_all(cls) -> List[FunctionMetadata]:
        """Get all registered functions."""
        return list(cls._registry.values())
    
    @classmethod
    def get(cls, full_name: str) -> Optional[FunctionMetadata]:
        """Get a registered function by its full name."""
        return cls._registry.get(full_name)
    
    @classmethod
    def store_implementation(cls, full_name: str, implementation: str) -> None:
        """Store an implementation for a function."""
        if full_name in cls._registry:
            cls._registry[full_name].implementation = implementation
        cls._implementations[full_name] = implementation
    
    @classmethod
    def get_implementation(cls, full_name: str) -> Optional[str]:
        """Get the implementation for a function."""
        if full_name in cls._implementations:
            return cls._implementations[full_name]
        if full_name in cls._registry and cls._registry[full_name].implementation:
            return cls._registry[full_name].implementation
        return None
    
    @classmethod
    def needs_generation(cls, full_name: str, cached_hash: Optional[str]) -> bool:
        """Check if a function needs generation or regeneration."""
        # Check if we've already determined this
        if full_name in cls._needs_generation:
            return cls._needs_generation[full_name]
            
        if full_name not in cls._registry:
            cls._needs_generation[full_name] = False
            return False
        
        metadata = cls._registry[full_name]
        
        # If frozen, don't regenerate
        if metadata.frozen:
            cls._needs_generation[full_name] = False
            return False
        
        # If no cached hash, needs generation
        if cached_hash is None:
            cls._needs_generation[full_name] = True
            return True
        
        # If hash doesn't match, needs regeneration
        result = metadata.get_hash() != cached_hash
        cls._needs_generation[full_name] = result
        return result
    
    @classmethod
    def clear_module(cls, module_name: str) -> None:
        """
        Clear all registry entries for a specific module.
        
        Args:
            module_name: Name of the module to clear
        """
        # Remove functions that belong to this module
        cls._registry = {
            full_name: metadata
            for full_name, metadata in cls._registry.items()
            if not metadata.module.startswith(module_name)
        }
        
        # Clear implementations for this module
        cls._implementations = {
            full_name: impl
            for full_name, impl in cls._implementations.items()
            if not full_name.startswith(module_name)
        }
        
        # Clear generation flags
        cls._needs_generation = {
            full_name: flag
            for full_name, flag in cls._needs_generation.items()
            if not full_name.startswith(module_name)
        }