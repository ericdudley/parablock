from parablock import parablock
    
@parablock
def hello_world():
    """
    Greet the world, the way that programmers always have.
    """

@parablock
def get_greeting(name: str) -> str:
    """
    Make a personalized greeting for the user.
    """
    
@parablock
def get_goodbye(name: str, fn) -> str:
    """
    Make a personalized goodbye for the user.
    """
    assert "Susan" in fn("Susan") # <-- fn is the implementation of this parablock

def run_demo():
    hello_world()
    
    print(get_greeting("Tom"))
    
    print(get_goodbye("Tom"))
    
    hello_world.peek()
