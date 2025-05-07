"""
Test runner for verifying generated implementations.
"""
import ast
import inspect
import textwrap
import traceback
from typing import Any, Callable, Dict, Optional, Tuple
from rich.console import Console

console = Console()

class TestRunner:
    """
    Runs tests against generated implementations to verify they work.
    """
    
    @staticmethod
    def extract_test_code(source: str) -> str:
        """
        Extract the test code from a function's source.
        
        Args:
            source: Function source code
            
        Returns:
            The extracted test code
        """
        tree = ast.parse(source)
        function_def = tree.body[0]
        
        if not isinstance(function_def, ast.FunctionDef):
            return ""
        
        # Get the function body, excluding docstring
        body = function_def.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Str):
            body = body[1:]
        
        if not body:
            return ""
        
        # Convert the body back to source code
        body_source = ""
        for node in body:
            body_source += ast.unparse(node) + "\n"
        
        return body_source
    
    @staticmethod
    def run_test(
        func: Callable,
        implementation: str,
        test_code: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Run tests against the implementation.
        
        Args:
            func: Original function
            implementation: Generated implementation code
            test_code: Test code extracted from the function body
            
        Returns:
            Tuple of (success, error_message)
        """
        # First, dedent both the implementation and test_code
        implementation = textwrap.dedent(implementation)
        test_code = textwrap.dedent(test_code)
        
        # Extract parameter names from the function
        signature = inspect.signature(func)
        param_names = [p for p in signature.parameters if p != "fn"]
        params_str = ", ".join(param_names)
        fn_params_str = ", ".join(["None"] + [p for p in param_names])
        
        # Prepare the template
        # TODO Another awkward template string
        template = f"""
def test_implementation(fn, {params_str}):
    def implementation_func({params_str}):
{{implementation}}
        
    return implementation_func({params_str})

def run_test():
    # Define a mock fn function that calls the implementation
    def fn({params_str}):
        return test_implementation({fn_params_str})
    
    # Run the test code
{{test_code}}
    
    return True  # If we got here, tests passed
"""

        implementation_indented = textwrap.indent(implementation, '        ')
        test_code_indented = textwrap.indent(test_code, '    ')
        
        # Construct the final source
        test_func_source = template.format(
            implementation=implementation_indented,
            test_code=test_code_indented
        )
        
        # Compile and execute the test
        try:
            test_globals: Dict[str, Any] = {}
            exec(test_func_source, test_globals)
            
            # Run the test
            test_globals["run_test"]()
            return True, None
        except Exception as e:
            error_msg = traceback.format_exc()
            return False, error_msg