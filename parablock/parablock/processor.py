"""
Parablock processor for scanning and generating implementations.
"""

import argparse
import importlib
import inspect
import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Set

import watchdog.events
import watchdog.observers
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from .code_generator import CodeGenerator
from .registry import FunctionRegistry
from .test_runner import TestRunner
from .utils import Cache, get_function_hash 

console = Console()


# TODO Most of this file was AI generated, it works but is likely doing things inefficiently or re-inventing the wheel.
class Processor:
    """
    Scans for parablock-decorated functions and generates their implementations.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the processor.
        
        Args:
            api_key: OpenAI API key
        """
        self.code_generator = CodeGenerator(api_key=api_key)
        self.test_runner = TestRunner()
        self.watched_files: Set[str] = set()
    
    def process_module(self, module_name: str) -> bool:
        """
        Process all parablock-decorated functions in a module.
        
        Args:
            module_name: Name of the module to process
            
        Returns:
            True if all functions were processed successfully
        """
        console.print(f"[bold blue]Processing module: {module_name}[/]")
        
        try:
            # Import the module to trigger decorators
            importlib.import_module(module_name)
            
            # Add module file to watched files
            module = sys.modules.get(module_name)
            if module and hasattr(module, "__file__"):
                self.watched_files.add(module.__file__)
            
            # Load cache for the module
            Cache.load(module_name)
            
            # Get all functions in the module
            functions = [f for f in FunctionRegistry.get_all() 
                         if f.module == module_name or f.module.startswith(f"{module_name}.")]

            console.print(f"[bold green]Found {len(functions)} functions in {module_name}[/]")
            
            if not functions:
                console.print(f"[yellow]No parablock functions found in {module_name}[/]")
                return True
            
            success = True
            
            with Progress() as progress:
                task = progress.add_task("[green]Processing functions...", total=len(functions))
                
                # Process each function
                for func_metadata in functions:
                    full_name = func_metadata.get_full_name()
                    console.print(f"[bold cyan]Processing function: {full_name}[/]")
                    
                    # Get function hash
                    func_hash = get_function_hash(func_metadata.docstring, func_metadata.signature)
                    
                    # Check cache
                    cache_entry = Cache.get(full_name)
                    cached_hash = cache_entry.get("hash") if cache_entry else None
                    
                    # Check if we need to generate the implementation
                    if not FunctionRegistry.needs_generation(full_name, cached_hash):
                        # Use cached implementation
                        if cache_entry:
                            implementation = cache_entry.get("implementation", "")
                            FunctionRegistry.store_implementation(full_name, implementation)
                            console.print(f"[green]Using cached implementation for {full_name}[/]")
                        else:
                            console.print(f"[yellow]No cached implementation for {full_name}[/]")
                            success = False
                    else:
                        # Generate new implementation
                        console.print(f"[yellow]Generating implementation for {full_name}[/]")
                        
                        # Extract test code
                        test_code = self.test_runner.extract_test_code(func_metadata.source)
                        
                        # Generate and test implementation
                        implementation_success, error_msg = self._generate_and_test(
                            func_metadata.func,
                            func_metadata.name,
                            func_metadata.docstring,
                            func_metadata.signature,
                            test_code,
                        )
                        
                        if implementation_success:
                            console.print(f"[green]Successfully generated implementation for {full_name}[/]")
                            
                            # Get the latest implementation from the registry
                            implementation = FunctionRegistry.get_implementation(full_name)
                            
                            # Store in cache
                            if implementation:
                                Cache.store(full_name, func_hash, implementation)
                                console.print(f"[green]Stored implementation in cache for {full_name}[/]")
                        else:
                            console.print(f"[red]Failed to generate implementation for {full_name}[/]")
                            console.print(Panel(str(error_msg), title="Error", border_style="red"))
                            success = False
                    
                    progress.update(task, advance=1)
            
            # Save cache
            Cache.save(module_name)
            
            return success
        
        except Exception as e:
            console.print(f"[bold red]Error processing module {module_name}: {str(e)}[/]")
            return False
    
    def _generate_and_test(
        self,
        func: callable,
        name: str,
        docstring: str,
        signature: inspect.Signature,
        test_code: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Generate and test an implementation for a function.
        
        Args:
            func: Original function
            name: Function name
            docstring: Function docstring
            signature: Function signature
            test_code: Test code extracted from the function body
            
        Returns:
            Tuple of (success, error_message)
        """
        error_feedback = None
        max_attempts = 3
        
        for attempt in range(max_attempts):
            # Generate implementation
            generation_success, implementation = self.code_generator.generate_implementation(
                name=name,
                docstring=docstring,
                signature=signature,
                test_code=test_code,
                error_feedback=error_feedback,
            )
            
            if not generation_success:
                return False, f"Failed to generate implementation after {attempt + 1} attempts"
            
            # Test implementation
            test_success, test_error = self.test_runner.run_test(
                func=func,
                implementation=implementation,
                test_code=test_code,
            )
            
            if test_success:
                # Store the successful implementation
                full_name = f"{func.__module__}.{name}"
                FunctionRegistry.store_implementation(full_name, implementation)
                return True, None
            
            # Update error feedback for next attempt
            error_feedback = test_error
            console.print(f"[yellow]Test failed on attempt {attempt + 1}, retrying...[/]")
        
        return False, error_feedback
    
    def process_package(self, package_name: str) -> bool:
        """
        Process all modules in a package.
        
        Args:
            package_name: Name of the package to process
            
        Returns:
            True if all modules were processed successfully
        """
        try:
            # Import the package to get its __path__
            package = importlib.import_module(package_name)
            if not hasattr(package, "__path__"):
                console.print(f"[red]{package_name} is not a package[/]")
                return False
            
            package_path = package.__path__[0]
            modules = self._find_modules(package_path, package_name)
            
            success = True
            for module_name in modules:
                if not self.process_module(module_name):
                    success = False
            
            return success
        
        except Exception as e:
            console.print(f"[bold red]Error processing package {package_name}: {str(e)}[/]")
            return False
    
    def _find_modules(self, package_path: str, package_name: str) -> List[str]:
        """Find all modules in a package."""
        modules = []
        
        for root, _, files in os.walk(package_path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    # Convert file path to module name
                    rel_path = os.path.relpath(os.path.join(root, file), package_path)
                    module_path = os.path.splitext(rel_path)[0].replace(os.sep, ".")
                    modules.append(f"{package_name}.{module_path}")
        
        return modules


class FileChangeHandler(watchdog.events.FileSystemEventHandler):
    """Handler for file system events."""
    
    def __init__(self, processor: Processor, package_name: str = None, module_name: str = None):
        """
        Initialize the handler.
        
        Args:
            processor: The processor to use
            package_name: Name of the package to watch (optional)
            module_name: Name of the module to watch (optional)
        """
        self.processor = processor
        self.package_name = package_name
        self.module_name = module_name
        
    def _reload_module(self, module_name: str) -> None:
        """Reload a module to detect new functions"""
        try:
            # Clear registry entries for this module
            FunctionRegistry.clear_module(module_name)
            
            # Reload the module to trigger decorators
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                console.print(f"[green]Reloaded module: {module_name}[/]")
                
            # Process the module
            self.processor.process_module(module_name)
        except Exception as e:
            console.print(f"[red]Error reloading module {module_name}: {str(e)}[/]")
    
    def on_modified(self, event: watchdog.events.FileModifiedEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith('.py'):
            console.print(f"[yellow]File modified: {event.src_path}[/]")
            
            # Find the module name from the file path
            file_path = os.path.abspath(event.src_path)
            module_found = False
            
            for module_name, module in list(sys.modules.items()):
                if hasattr(module, "__file__") and os.path.abspath(module.__file__) == file_path:
                    module_found = True
                    self._reload_module(module_name)
                    break
            
            # If module not found but it's a Python file, try to import it
            if not module_found and self.package_name:
                try:
                    # Convert file path to potential module name
                    package_path = sys.modules[self.package_name].__path__[0]
                    if file_path.startswith(package_path):
                        rel_path = os.path.relpath(file_path, package_path)
                        module_path = os.path.splitext(rel_path)[0].replace(os.sep, ".")
                        potential_module = f"{self.package_name}.{module_path}"
                        
                        # Try to import the module
                        importlib.import_module(potential_module)
                        self.processor.process_module(potential_module)
                        
                        # Add to watched files
                        self.processor.watched_files.add(file_path)
                        console.print(f"[green]Detected new module: {potential_module}[/]")
                except Exception as e:
                    console.print(f"[yellow]Could not import potential new module: {str(e)}[/]")
    
    def on_created(self, event: watchdog.events.FileCreatedEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory and event.src_path.endswith('.py'):
            console.print(f"[yellow]New file created: {event.src_path}[/]")
            # Handle new file the same way as modified files
            self.on_modified(event)

def main() -> None:
    """Main entry point for the processor."""
    parser = argparse.ArgumentParser(description="ParaBlock Processor")
    parser.add_argument("--watch", action="store_true", help="Watch for file changes")
    parser.add_argument("--module", type=str, help="Process a specific module")
    parser.add_argument("--package", type=str, help="Process a package")
    parser.add_argument("--api-key", type=str, help="OpenAI API key")
    args = parser.parse_args()
    
    # Use API key from environment variable if not provided
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        console.print("[bold red]No OpenAI API key provided. Set OPENAI_API_KEY environment variable or use --api-key[/]")
        sys.exit(1)
    
    processor = Processor(api_key=api_key)
    
    # Process module or package
    package_name = None
    module_name = None
    
    if args.module:
        processor.process_module(args.module)
        module_name = args.module
    elif args.package:
        processor.process_package(args.package)
        package_name = args.package
    else:
        # Default to processing the current directory as a package
        cwd = Path.cwd().name
        processor.process_package(cwd)
        package_name = cwd
    
    # Watch for changes if requested
    if args.watch:
        console.print("[bold green]Watching for file changes...[/]")
        handler = FileChangeHandler(processor, package_name, module_name)
        observer = watchdog.observers.Observer()
        
        # Determine directories to watch
        if module_name:
            # Watch module directory
            module = sys.modules.get(module_name)
            if module and hasattr(module, "__file__"):
                watch_dir = os.path.dirname(os.path.abspath(module.__file__))
                observer.schedule(handler, watch_dir, recursive=False)
        elif package_name:
            # Watch package directory recursively
            package = sys.modules.get(package_name)
            if package and hasattr(package, "__path__"):
                watch_dir = package.__path__[0]
                observer.schedule(handler, watch_dir, recursive=True)
        else:
            # Fallback to current working directory
            watch_dir = os.getcwd()
            observer.schedule(handler, watch_dir, recursive=True)
            
        console.print(f"[bold green]Watching directory: {watch_dir}[/]")
        
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

if __name__ == "__main__":
    main()