import hashlib
import inspect
import json
import os
from pathlib import Path
from typing import Dict, Optional, Set

from rich.console import Console

console = Console()


class Cache:
    """
    Cache system for storing generated implementations.
    """
    
    _cache_dir = Path(".parablock") / "cache"
    _cache: Dict[str, Dict[str, str]] = {}
    _loaded_modules: Set[str] = set()
    
    @classmethod
    def module_name_to_cache_file(cls, module_name: str) -> str:
        """Convert a module name to a cache file name."""
        return module_name.replace(".", "_") + ".json"
    
    @classmethod
    def _ensure_cache_dir(cls) -> None:
        """Ensure the cache directory exists."""
        os.makedirs(cls._cache_dir, exist_ok=True)
    
    @classmethod
    def _get_cache_file(cls, module_name: str) -> Path:
        """Get the cache file path for a module."""
        cls._ensure_cache_dir()
        return cls._cache_dir / f"{Cache.module_name_to_cache_file(module_name)}"
    
    @classmethod
    def load(cls, module_name: str) -> None:
        """
        Load cache data for a module and populate the registry with implementations.
        
        This method loads cached implementations from disk and updates the registry,
        ensuring implementations are available at runtime.
        """
        if module_name in cls._loaded_modules:
            return
        
        from .registry import FunctionRegistry
        
        cache_file = cls._get_cache_file(module_name)
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    module_cache = json.load(f)
                    
                    # Update the in-memory cache
                    cls._cache.update(module_cache)
                    
                    # Populate the registry with implementations from cache
                    for func_name, cache_data in module_cache.items():
                        if "implementation" in cache_data:
                            # Store the implementation in the registry
                            FunctionRegistry.store_implementation(
                                func_name, 
                                cache_data["implementation"]
                            )
                    
                    console.print(f"[green]Loaded cache for module: {module_name}[/]")
            except Exception as e:
                console.print(f"[yellow]Error loading cache for {module_name}: {str(e)}[/]")
        else:
            console.print(f"[yellow]No cache file found for module: {module_name}[/]")
        
        cls._loaded_modules.add(module_name)
    
    @classmethod
    def save(cls, module_name: str) -> None:
        """
        Save cache data for a module.
        
        This method saves only the implementations relevant to the specified module,
        creating a module-specific cache file.
        """
        cls._ensure_cache_dir()
        cache_file = cls._get_cache_file(module_name)
        
        # Filter cache to only include functions from this module
        module_cache = {
            func_name: data 
            for func_name, data in cls._cache.items()
            if func_name.startswith(f"{module_name}.")
        }
        
        try:
            with open(cache_file, "w") as f:
                json.dump(module_cache, f, indent=2)
                console.print(f"[green]Saved cache for module: {module_name}[/]")
        except Exception as e:
            console.print(f"[yellow]Error saving cache for {module_name}: {str(e)}[/]")
    
    @classmethod
    def get(cls, func_name: str) -> Optional[Dict[str, str]]:
        """Get cached data for a function."""
        return cls._cache.get(func_name)
    
    @classmethod
    def store(cls, func_name: str, func_hash: str, implementation: str) -> None:
        """Store an implementation in the cache."""
        if func_name not in cls._cache:
            cls._cache[func_name] = {}
        
        cls._cache[func_name] = {
            "hash": func_hash,
            "implementation": implementation,
        }


def get_function_hash(docstring: str, signature: inspect.Signature) -> str:
    """Generate a hash for a function based on its docstring and signature."""
    hash_input = f"{docstring}|{str(signature)}"
    return hashlib.md5(hash_input.encode()).hexdigest()


def get_modified_files(watched_files: Set[str], event_path: str) -> Set[str]:
    """Get the set of files that need to be processed based on a file change."""
    # For now, just return the changed file if it's in the watched files
    if event_path in watched_files:
        return {event_path}
    return set()