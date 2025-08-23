#!/usr/bin/env python3
"""Test script to verify Phase 1 implementation"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing Module Imports...")
    try:
        import config
        from data.database import DatabaseManager
        from data.api_clients import APIManager
        from utils.fuzzy_matcher import FuzzyMatcher
        from data.cache_manager import CacheManager
        from utils.data_processor import DataProcessor
        print("   ✅ All imports successful")
        return True
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        print("   ⚠️  Module Imports failed!")
        return False

def test_database():
    """Test database functionality"""
    print("🔍 Testing Database Operations...")
    try:
        from data.database import DatabaseManager
        
        # Use a test database
        test_db_path = "test_db.db"
        db = DatabaseManager(test_db_path)
        
        # Test medication insertion
        med_id = db.insert_medication("Test Medication", "generic_test")
        assert med_id > 0, "Failed to insert medication"
        
        # Test food insertion
        food_id = db.insert_food("Test Food", "Test Category")
        assert food_id > 0, "Failed to insert food"
        
        # Test retrieval
        meds = db.get_all_medications()
        foods = db.get_all_foods()
        
        assert len(meds) > 0, "No medications retrieved"
        assert len(foods) > 0, "No foods retrieved"
        
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        print("   ✅ Database tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Database test error: {e}")
        print("   ⚠️  Database Operations failed!")
        return False

def test_fuzzy_matching():
    """Test fuzzy matching functionality"""
    print("🔍 Testing Fuzzy Matching...")
    try:
        from utils.fuzzy_matcher import FuzzyMatcher
        
        matcher = FuzzyMatcher()
        
        # Test basic matching
        candidates = ["Ibuprofen", "Acetaminophen", "Aspirin"]
        matches = matcher.find_best_matches("ibuprofen", candidates)
        
        print(f"   📊 Matches found: {matches}")
        
        assert len(matches) > 0, "No matches found"
        
        # Verify the structure of matches
        first_match = matches[0]
        print(f"   📊 First match details: {first_match}, type: {type(first_match)}")
        
        # Handle both tuple and other possible formats
        if isinstance(first_match, (list, tuple)) and len(first_match) >= 2:
            match_name = first_match[0]
            match_score = first_match[1]
        else:
            raise AssertionError(f"Unexpected match format: {first_match}")
        
        assert match_name == "Ibuprofen", f"Expected 'Ibuprofen', got '{match_name}'"
        assert match_score > 80, f"Expected high score, got {match_score}"
        
        # Test with typos (use lower threshold for typos)
        typo_matches = matcher.find_best_matches("ibuprofin", candidates, score_cutoff=60)
        print(f"   📊 Typo matches found: {typo_matches}")
        
        assert len(typo_matches) > 0, "No matches found for typo even with lower threshold"
        
        if isinstance(typo_matches[0], (list, tuple)) and len(typo_matches[0]) >= 2:
            typo_name = typo_matches[0][0]
            typo_score = typo_matches[0][1]
        else:
            raise AssertionError(f"Unexpected typo match format: {typo_matches[0]}")
        
        assert typo_name == "Ibuprofen", f"Typo matching failed: got '{typo_name}'"
        print(f"   📊 Typo match score: {typo_score}")
        
        # Test case insensitivity
        case_matches = matcher.find_best_matches("IBUPROFEN", candidates)
        assert len(case_matches) > 0, "Case insensitive matching failed"
        assert case_matches[0][0] == "Ibuprofen", "Case insensitive match incorrect"
        
        # Test partial matching
        partial_matches = matcher.find_best_matches("ibu", candidates, score_cutoff=50)
        assert len(partial_matches) > 0, "Partial matching failed"
        
        print("   ✅ Fuzzy matching tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Fuzzy matching test error: {e}")
        print("   ⚠️  Fuzzy Matching failed!")
        import traceback
        traceback.print_exc()
        return False

def test_api_clients():
    """Test API client initialization"""
    print("🔍 Testing API Clients...")
    try:
        from data.api_clients import APIManager
        
        api_manager = APIManager()
        
        # Test that clients are created
        assert api_manager.fda_client is not None, "FDA client not created"
        assert api_manager.rxnav_client is not None, "RxNav client not created"
        assert api_manager.usda_client is not None, "USDA client not created"
        assert api_manager.openfood_client is not None, "OpenFood client not created"
        
        # Test that methods exist
        assert hasattr(api_manager, 'search_all_drugs'), "search_all_drugs method missing"
        assert hasattr(api_manager, 'search_all_foods'), "search_all_foods method missing"
        
        print("   ✅ API client tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ API client test error: {e}")
        print("   ⚠️  API Clients failed!")
        return False

def test_cache_manager():
    """Test cache manager functionality"""
    print("🔍 Testing Cache Manager...")
    try:
        from data.database import DatabaseManager
        from data.cache_manager import CacheManager
        
        # Use test database
        test_db_path = "test_cache_db.db"
        db = DatabaseManager(test_db_path)
        cache_manager = CacheManager(db)
        
        # Test cache key generation
        key = cache_manager.generate_cache_key("test", "arg1", kwarg1="value1")
        assert key is not None, "Cache key generation failed"
        assert len(key) == 32, f"Expected 32-character hash, got {len(key)}"
        
        # Test cache stats
        stats = cache_manager.get_cache_stats()
        assert 'memory_cache_size' in stats, "Cache stats missing memory_cache_size"
        assert 'database_cache_total' in stats, "Cache stats missing database_cache_total"
        
        # Clean up
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        print("   ✅ Cache manager tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Cache manager test error: {e}")
        print("   ⚠️  Cache Manager failed!")
        return False

def test_data_processor():
    """Test data processor functionality"""
    print("🔍 Testing Data Processor...")
    try:
        from data.database import DatabaseManager
        from data.api_clients import APIManager
        from utils.data_processor import DataProcessor
        
        # Use test database
        test_db_path = "test_processor_db.db"
        db = DatabaseManager(test_db_path)
        api_manager = APIManager()
        data_processor = DataProcessor(db, api_manager)
        
        # Test that processor initializes
        assert data_processor.db is not None, "Database not set in processor"
        assert data_processor.api is not None, "API manager not set in processor"
        
        # Test method existence
        assert hasattr(data_processor, 'get_medication_names'), "get_medication_names method missing"
        assert hasattr(data_processor, 'get_food_names'), "get_food_names method missing"
        
        # Clean up
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        print("   ✅ Data processor tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Data processor test error: {e}")
        print("   ⚠️  Data Processor failed!")
        return False

def main():
    """Run all tests"""
    print("🧪 Running Phase 1 Tests...")
    print("-" * 50)
    print()
    
    tests = [
        test_imports,
        test_database,
        test_fuzzy_matching,
        test_api_clients,
        test_cache_manager,
        test_data_processor
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("-" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 1 is ready.")
        print()
        print("🚀 Next steps:")
        print("   1. Run: streamlit run app.py")
        print("   2. Verify the app loads and populates data")
        print("   3. Test the fuzzy matching in the web interface")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues before proceeding.")
        print()
        print("🔧 Common fixes:")
        print("   - Check that all files are in the correct directories")
        print("   - Verify requirements.txt dependencies are installed")
        print("   - Make sure Python path includes the project directory")
        return 1

if __name__ == "__main__":
    sys.exit(main())