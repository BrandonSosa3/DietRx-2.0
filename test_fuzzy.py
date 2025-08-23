#!/usr/bin/env python3
"""Quick test for fuzzy matching"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.fuzzy_matcher import FuzzyMatcher

def test_fuzzy():
    matcher = FuzzyMatcher()
    
    candidates = ["Ibuprofen", "Acetaminophen", "Aspirin", "Grapefruit", "Spinach"]
    
    test_cases = [
        "ibuprofin",
        "asprin", 
        "grapfruit",
        "spinage"
    ]
    
    for query in test_cases:
        print(f"\nTesting: {query}")
        matches = matcher.find_best_matches(query, candidates, limit=3)
        for match, score in matches:
            print(f"  • {match} (Score: {score})")

if __name__ == "__main__":
    test_fuzzy()