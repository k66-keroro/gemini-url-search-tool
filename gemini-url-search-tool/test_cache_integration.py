#!/usr/bin/env python3
"""
Simple integration test for cache service.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.core.cache_service import CacheService, LRUCache, PersistentCache
    print("✓ Cache service imports successfully")
    
    # Test LRU Cache
    print("\nTesting LRU Cache...")
    lru_cache = LRUCache(max_size=5, max_memory_mb=1)
    
    # Basic operations
    lru_cache.put("test_key", "test_value")
    result = lru_cache.get("test_key")
    assert result == "test_value", f"Expected 'test_value', got {result}"
    print("✓ LRU Cache basic operations work")
    
    # Test stats
    stats = lru_cache.get_stats()
    assert stats.hits == 1, f"Expected 1 hit, got {stats.hits}"
    assert stats.entry_count == 1, f"Expected 1 entry, got {stats.entry_count}"
    print("✓ LRU Cache statistics work")
    
    # Test Persistent Cache
    print("\nTesting Persistent Cache...")
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_path = Path(temp_dir) / "test_cache.db"
        persistent_cache = PersistentCache(str(cache_path))
        
        # Basic operations
        persistent_cache.put("persistent_key", {"data": "persistent_value"})
        result = persistent_cache.get("persistent_key")
        assert result == {"data": "persistent_value"}, f"Expected dict, got {result}"
        print("✓ Persistent Cache basic operations work")
        
        # Test stats
        stats = persistent_cache.get_stats()
        assert stats['entry_count'] >= 1, f"Expected at least 1 entry, got {stats['entry_count']}"
        print("✓ Persistent Cache statistics work")
    
    # Test Cache Service
    print("\nTesting Cache Service...")
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_path = Path(temp_dir) / "service_cache.db"
        cache_service = CacheService(
            memory_cache_size=10,
            memory_cache_mb=1,
            persistent_cache_path=str(cache_path)
        )
        
        # Test API response caching
        endpoint = "/api/test"
        params = {"query": "test"}
        response = {"results": ["item1", "item2"]}
        
        cache_service.cache_api_response(endpoint, params, response)
        cached_response = cache_service.get_cached_api_response(endpoint, params)
        assert cached_response == response, f"Expected {response}, got {cached_response}"
        print("✓ Cache Service API response caching works")
        
        # Test content analysis caching
        url = "https://example.com"
        analysis = {"summary": "Test summary", "key_points": ["point1"]}
        
        cache_service.cache_content_analysis(url, analysis)
        cached_analysis = cache_service.get_cached_content_analysis(url)
        assert cached_analysis == analysis, f"Expected {analysis}, got {cached_analysis}"
        print("✓ Cache Service content analysis caching works")
        
        # Test cache stats
        stats = cache_service.get_cache_stats()
        assert 'memory_cache' in stats, "Memory cache stats missing"
        assert 'persistent_cache' in stats, "Persistent cache stats missing"
        print("✓ Cache Service statistics work")
    
    print("\n🎉 All cache service tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)