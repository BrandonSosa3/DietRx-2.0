#!/usr/bin/env python3
"""Debug script for fuzzy matching"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.fuzzy_matcher import FuzzyMatcher

def debug_fuzzy_matching():
    """Debug what find_best_matches returns"""
    
    matcher = FuzzyMatcher()
    candidates = ["Ibuprofen", "Acetaminophen", "Aspirin"]
    
    print("🔍 Testing fuzzy matching...")
    print(f"Candidates: {candidates}")
    
    # Test exact match
    print(f"\n1. Query: 'ibuprofen'")
    matches = matcher.find_best_matches("ibuprofen", candidates)
    print(f"   Matches: {matches}")
    
    # Test typo with different thresholds
    print(f"\n2. Query: 'ibuprofin' (typo)")
    
    # Try with default threshold (80)
    typo_matches_80 = matcher.find_best_matches("ibuprofin", candidates, score_cutoff=80)
    print(f"   Matches (threshold 80): {typo_matches_80}")
    
    # Try with lower threshold (60)
    typo_matches_60 = matcher.find_best_matches("ibuprofin", candidates, score_cutoff=60)
    print(f"   Matches (threshold 60): {typo_matches_60}")
    
    # Try with very low threshold (30)
    typo_matches_30 = matcher.find_best_matches("ibuprofin", candidates, score_cutoff=30)
    print(f"   Matches (threshold 30): {typo_matches_30}")
    
    # Test partial match
    print(f"\n3. Query: 'ibu' (partial)")
    partial_matches = matcher.find_best_matches("ibu", candidates, score_cutoff=50)
    print(f"   Matches (threshold 50): {partial_matches}")
    
    return matches

if __name__ == "__main__":
    debug_fuzzy_matching()