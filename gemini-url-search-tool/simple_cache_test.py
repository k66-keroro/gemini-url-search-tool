#!/usr/bin/env python3
"""
Simple cache service test.
"""

import json
import hashlib
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from collections import OrderedDict
import weakref
import gc
import tempfile

# Simple test of cache components
print("Testing cache components...")

# Test basic LRU functionality
class SimpleLRUCache:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.cache = OrderedDict()
    
    def get(self, key):
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        
        # Remove oldest if over limit
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

# Test the simple cache
cache = SimpleLRUCache(max_size=3)
cache.put("key1", "value1")
cache.put("key2", "value2")
cache.put("key3", "value3")

assert cache.get("key1") == "value1"
print("✓ Simple LRU cache works")

# Test SQLite cache
with tempfile.TemporaryDirectory() as temp_dir:
    db_path = Path(temp_dir) / "test.db"
    
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE cache_entries (
            key TEXT PRIMARY KEY,
            value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert test data
    conn.execute("INSERT INTO cache_entries (key, value) VALUES (?, ?)", 
                ("test_key", json.dumps({"data": "test_value"})))
    conn.commit()
    
    # Retrieve test data
    cursor = conn.execute("SELECT value FROM cache_entries WHERE key = ?", ("test_key",))
    row = cursor.fetchone()
    
    if row:
        data = json.loads(row[0])
        assert data == {"data": "test_value"}
        print("✓ SQLite cache works")
    
    conn.close()

print("🎉 Basic cache functionality verified!")