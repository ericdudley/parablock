# ParaBlock

A Python library for natural language defined functions. Parablock enables developers to define functionality through natural language descriptions rather than explicit code.

## Features

- Define Python functions where the implementation is generated from the docstring
- Process these functions during a pre-processing step to generate actual code implementations
- Run tests against the generated implementations until they pass
- Cache successful implementations to avoid unnecessary regeneration
- Lookup generated implementations at runtime and execute instead of the body of @parablock functions.

## Installation

```bash
cd parablock
poetry install
```


See [README.md](../README.md)