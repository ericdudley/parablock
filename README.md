# Parablock

Parablock creates a new way to express software, where the natural language prompt becomes the code itself.

## Core principles

1. Parablock enables software developers to directly express behavior in natural language (aka LLM prompts).
2. Parablock is compatible with existing Python, such that existing Python code bases could be progressively enhanced with Parablock.

## How it works
1. Setup the demo
```sh
cd parablock
poetry install
poetry build

cd ../parablock-demo
make setup
```

This project uses the OpenAI API to generate implementations, you must either have `OPENAI_API_KEY` as an environment variable or pass in `--api-key OPENAI_API_KEY` to the watch process.

2. The watch process runs as an "AI compiler" that watches for changes in your code base as you work, and re-generates the underlying implementations of your functions as you save files.
```sh
cd parablock-demo
make process-watch
```

3. Start writing `@parablock` functions! Follow the guide below to see how you can define behavior with Parablock. At runtime `@parablock` functions can be used just like normal functions.

## @parablock decorator

The `@parablock` decorator tells the watch process that it needs to watch this function and re-generate the implementation when anything changes (prompt, types, tests). At runtime it ensures, that the generated implementation is executed.

### No constraints

You can define `@parablock` functions with no constraints.

```python
@parablock
def hello_world():
    """
    Greet the world, the way that programmers always have.
    """

hello_world()
```

### Type constraints

You can define `@parablock` functions with type constraints for the parameters and return value.

```python
@parablock
def get_greeting(name: str) -> str:
    """
    Make a personalized greeting for the user.
    """

print(get_greeting("Tom"))
```

### Test constraints

The body of the function can be used to define tests on the black box implementation of your function. It is guaranteed that the function will pass these tests. Note: If the function can't be generated to pass the tests, then it won't be generated at all.

```python
@parablock
def get_goodbye(name: str, fn) -> str:
    """
    Make a personalized goodbye for the user.
    """
    assert "Susan" in fn("Susan") # <-- fn is the implementation of this parablock

print(get_goodbye("Tom"))
```

## function.peek()

While the intention is to never have to look at the underlying code, sometime it is useful (or just fun), to see what's going on under the hood.

```python
@parablock
def hello_world():
    """
    Greet the world, the way that programmers always have.
    """

hello_world.peek()
```

Output:
```
╭────────────────────────────── hello_world.peek() ──────────────────────────────╮
│                                   Metadata                                     │
│ ┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓   │
│ ┃ Key       ┃ Value                                                        ┃   │
│ ┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩   │
│ │ Name      │ hello_world                                                  │   │
│ │ Module    │ demo.demo                                                    │   │
│ │ Signature │ ()                                                           │   │
│ │ Docstring │ Greet the world, the way that programmers always have.       │   │
│ │ Source    │   @parablock                                                 │   │
│ │           │   def hello_world():                                         │   │
│ │           │       """                                                    │   │
│ │           │       Greet the world, the way that programmers always have. │   │
│ │           │       """                                                    │   │
│ │           │                                                              │   │
│ │ Frozen    │ False                                                        │   │
│ └───────────┴──────────────────────────────────────────────────────────────┘   │
│ ╭────────────────────────────── Implementation ──────────────────────────────╮ │
│ │   print("Hello, World!")                                                   │ │
│ ╰────────────────────────────────────────────────────────────────────────────╯ │
╰────────────────────────────────────────────────────────────────────────────────╯
```

## Roadmap

This isn't a real roadmap, as much as it is a wish list, right now Parablock is just a fun tech demo.

### Implemented
- @parablock decorator
- Watch process
- Support for dependecy-less and "pure" functions

### Wish list
- @paraclass decorator, allowing for full class definitions
- Dependency support
    - How can we give the ability for parablock functions to use other functions in the code base while still being able to tell when to invalidate the implementation cache? This could lead to long dependency trees and expensive re-generations.
    - How can we utilize external dependencies and make sure they're imported correctly in the implementations?
- "Dynamic" functions
    - Currently, all the implementations are generated at "compile" time, and so you can't ask for truly dynamic behavior. What if you could mark a @parablock as "dynamic" or "aware", and then run the implementation generation logic at runtime, allowing for much more dynamic behavior with the tradeoff of performance.
- Safety
    - Running code blindly is generally a bad idea, and the whole point of Parablock is to blindly run code. How can we put in some protections to prevent accidents? A harder problem would be protecting from malicious exploits.


## Disclaimer and Liability
Warning: Parablock generates and executes code automatically based on natural language prompts. Use at your own risk. This experimental technology is provided "as is" with no warranties or guarantees. Always review generated implementations with function.peek() before running in any environment. The creators and contributors of Parablock accept no liability for any damages or issues resulting from its use.