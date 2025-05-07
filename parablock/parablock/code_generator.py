"""
Code generator that interfaces with LLMs to generate implementations.
"""

import inspect
from typing import Any, Dict, List, Optional, Tuple

import openai
from rich.console import Console

console = Console()


class CodeGenerator:
    """
    Generates code implementations using Large Language Models.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the code generator.
        
        Args:
            api_key: OpenAI API key (optional)
        """
        if api_key:
            openai.api_key = api_key
    
    def generate_implementation(
        self,
        name: str,
        docstring: str,
        signature: inspect.Signature,
        test_code: str = "",
        error_feedback: Optional[str] = None,
        max_retries: int = 3,
    ) -> Tuple[bool, str]:
        """
        Generate a function implementation using an LLM.
        
        Args:
            name: Function name
            docstring: Function docstring
            signature: Function signature
            test_code: Test code from the function body
            error_feedback: Feedback from test failures
            max_retries: Maximum number of generation attempts
            
        Returns:
            Tuple of (success, implementation)
        """
        attempts = 0
        success = False
        implementation = ""
        
        # Extract parameter info
        param_info = self._extract_param_info(signature)
        
        while attempts < max_retries and not success:
            attempts += 1
            console.print(f"[bold yellow]Generating implementation for {name}... (Attempt {attempts})[/]")
            
            prompt = self._create_prompt(
                name=name,
                docstring=docstring,
                param_info=param_info,
                return_type=str(signature.return_annotation),
                test_code=test_code,
                error_feedback=error_feedback,
            )
            
            try:
                response = self._call_llm(prompt)
                implementation = self._extract_code(response)
                return True, implementation
            except Exception as e:
                console.print(f"[bold red]Generation error: {str(e)}[/]")
                error_feedback = str(e)
        
        return success, implementation
    
    def _extract_param_info(self, signature: inspect.Signature) -> List[Dict[str, str]]:
        """Extract parameter information from a signature."""
        params = []
        for name, param in signature.parameters.items():
            # Skip the first parameter (assumed to be 'fn')
            if name == 'fn':
                continue
            
            params.append({
                'name': name,
                'type': str(param.annotation),
                'default': str(param.default) if param.default is not inspect.Parameter.empty else None
            })
        
        return params
    
    def _create_prompt(
        self,
        name: str,
        docstring: str,
        param_info: List[Dict[str, str]],
        return_type: str,
        test_code: str,
        error_feedback: Optional[str],
    ) -> str:
        """Create a prompt for the LLM."""
        # TODO This prompt could be greatly improved with some basic prompt engineering techniques.
        prompt = f"""
Generate a Python function implementation based on the following details:

Function Name: {name}

Docstring:
{docstring}

Parameters:
"""
        for param in param_info:
            default_info = f" (default: {param['default']})" if param['default'] else ""
            prompt += f"- {param['name']}: {param['type']}{default_info}\n"
        
        prompt += f"""
Return Type: {return_type}

Test Code:
{test_code}
"""
        
        if error_feedback:
            prompt += f"""
Previous Error:
{error_feedback}

Please fix the issues mentioned in the error.
"""
        
        param_names_str = ", ".join([p["name"] for p in param_info])
        prompt += f"""
Generate only the function implementation code without including the function signature or docstring.
The code should be correct, efficient, and handle edge cases appropriately.
Do not include any comments, explanations, or test code in the implementation.
Only provide the code that will be used as the function body.

IMPORTANT: Your code will be indented and placed inside a function that looks like:
def implementation_func({param_names_str}):
    # YOUR CODE GOES HERE
    
Your implementation should directly use the named parameters ({param_names_str}).
Do not use args or kwargs in your implementation as the parameters will be passed by name.
"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt."""
        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            messages=[
                # TODO Improve system prompt with more guidance
                {"role": "system", "content": "You are a Python expert. Generate clean, correct, and efficient code based on the requirements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000,
        )
        
        return response.choices[0].message["content"]
    
    def _extract_code(self, response: str) -> str:
        """Extract code from the LLM response."""
        # Strip any markdown code block formatting
        code = response.replace("```python", "").replace("```", "").strip()
        
        # If the response starts with 'def', strip the function signature and docstring
        if code.startswith("def "):
            # Find the start of the function body
            lines = code.split("\n")
            start_index = 0
            
            # Skip the function signature
            for i, line in enumerate(lines):
                if line.strip().endswith(":"):
                    start_index = i + 1
                    break
            
            # Skip the docstring if present
            if start_index < len(lines) and '"""' in lines[start_index].strip():
                for i in range(start_index + 1, len(lines)):
                    if '"""' in lines[i]:
                        start_index = i + 1
                        break
            
            # Get the function body, maintaining indentation
            body_lines = lines[start_index:]
            
            # Remove common indentation
            if body_lines:
                min_indent = min(len(line) - len(line.lstrip()) for line in body_lines if line.strip())
                body_lines = [line[min_indent:] if line.strip() else line for line in body_lines]
            
            code = "\n".join(body_lines)
        
        return code