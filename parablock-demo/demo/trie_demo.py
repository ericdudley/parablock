from typing import List, Any
from parablock import parablock

@parablock
def build_prefix_tree(fn, words: List[str]) -> Any:
    """
    Build a prefix tree (trie) from a list of words.
    Returns an instance of a class that exposes the following methods:
    - insert(word: str): Insert a word into the trie.
    - search(word: str): Search for a word in the trie.
    - starts_with(prefix: str): Check if any word in the trie starts with the given prefix.
    - get_autocomplete_suggestions(prefix: str, max_suggestions: int): Get autocomplete suggestions for a prefix.
    """
    test_words = [
        "apple",
        "application",
        "apply",
        "apt",
        "banana",
        "band",
        "bandwidth",
    ]
    
    assert fn(test_words) is not None, "Trie should not be None"
    assert fn(test_words).search("apple") is True, "Should find 'apple'"
    assert fn(test_words).search("app") is False, "Should not find 'app'"
    assert fn(test_words).starts_with("app") is True, "Should start with 'app'"
    assert fn(test_words).starts_with("bat") is False, "Should not start with 'bat'"
    assert fn(test_words).get_autocomplete_suggestions("ap", 3) == [
        "apple",
        "application",
        "apply",
    ], "Should return autocomplete suggestions for 'ap'"
    assert fn(test_words).get_autocomplete_suggestions("b", 2) == [
        "banana",
        "band",
    ], "Should return autocomplete suggestions for 'b'"

def run_trie_demo():
    dictionary = [
        "telescope",
        "technology",
        "technique",
        "temperature",
        "dolphin",
        "document",
        "downtown",
        "dinosaur",
    ]
    trie = build_prefix_tree(dictionary)
    
    prefixes = ["te", "do", "tec", "p"]
    for prefix in prefixes:
        suggestions = trie.get_autocomplete_suggestions(prefix, max_suggestions=5)
        print(f"\nAutocomplete suggestions for '{prefix}':")
        for suggestion in suggestions:
            print(f"  - {suggestion}")