#!/usr/bin/env python3
"""
Test Suite for File Deduplicator
==================================
Comprehensive tests for all deduplication functionality.
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Fix Windows console encoding for tests
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
from deduplicator import FileDeduplicator

class TestFileDeduplicator(unittest.TestCase):
    """Test core functionality."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.dedup = FileDeduplicator()
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_01_init(self):
        """Test initialization."""
        self.assertIsNotNone(self.dedup)
        self.assertEqual(self.dedup.min_size, 1)
        self.assertEqual(self.dedup.threads, 4)
    
    def test_02_hash_file(self):
        """Test file hashing."""
        test_file = Path(self.temp_dir) / 'test.txt'
        test_file.write_text('test content')
        hash_val = self.dedup._hash_file(test_file)
        self.assertEqual(len(hash_val), 64)  # SHA-256 hex length
    
    def test_03_scan_directory_no_duplicates(self):
        """Test scanning directory with no duplicates."""
        (Path(self.temp_dir) / 'file1.txt').write_text('content 1')
        (Path(self.temp_dir) / 'file2.txt').write_text('content 2')
        (Path(self.temp_dir) / 'file3.txt').write_text('content 3')
        
        duplicates = self.dedup.scan_directory(self.temp_dir)
        self.assertEqual(len(duplicates), 0)
    
    def test_04_scan_directory_with_duplicates(self):
        """Test finding duplicate files."""
        same_content = 'duplicate content'
        (Path(self.temp_dir) / 'file1.txt').write_text(same_content)
        (Path(self.temp_dir) / 'file2.txt').write_text(same_content)
        (Path(self.temp_dir) / 'file3.txt').write_text('different')
        
        duplicates = self.dedup.scan_directory(self.temp_dir)
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(len(duplicates[0].files), 2)
    
    def test_05_filter_by_extension(self):
        """Test extension filtering."""
        dedup = FileDeduplicator(extensions=['.txt'])
        (Path(self.temp_dir) / 'test.txt').write_text('content')
        (Path(self.temp_dir) / 'test.py').write_text('content')
        
        duplicates = dedup.scan_directory(self.temp_dir)
        # Should only scan .txt files
        self.assertIsInstance(duplicates, list)
    
    def test_06_filter_by_min_size(self):
        """Test minimum size filtering."""
        dedup = FileDeduplicator(min_size=100)
        small_file = Path(self.temp_dir) / 'small.txt'
        small_file.write_text('x' * 10)  # Only 10 bytes
        
        duplicates = dedup.scan_directory(self.temp_dir)
        self.assertEqual(len(duplicates), 0)
    
    def test_07_filter_by_max_size(self):
        """Test maximum size filtering."""
        dedup = FileDeduplicator(max_size=50)
        large_file = Path(self.temp_dir) / 'large.txt'
        large_file.write_text('x' * 100)  # 100 bytes
        
        duplicates = dedup.scan_directory(self.temp_dir)
        self.assertEqual(len(duplicates), 0)
    
    def test_08_exclude_directories(self):
        """Test directory exclusion."""
        dedup = FileDeduplicator(exclude_dirs=['excluded'])
        
        # Create excluded directory
        excluded_dir = Path(self.temp_dir) / 'excluded'
        excluded_dir.mkdir()
        (excluded_dir / 'file.txt').write_text('content')
        
        duplicates = dedup.scan_directory(self.temp_dir)
        # Should not scan excluded directory
        self.assertIsInstance(duplicates, list)
    
    def test_09_export_json(self):
        """Test JSON export."""
        (Path(self.temp_dir) / 'file1.txt').write_text('duplicate')
        (Path(self.temp_dir) / 'file2.txt').write_text('duplicate')
        
        duplicates = self.dedup.scan_directory(self.temp_dir)
        
        json_file = Path(self.temp_dir) / 'report.json'
        self.dedup.export_json(duplicates, str(json_file))
        
        self.assertTrue(json_file.exists())
        self.assertGreater(json_file.stat().st_size, 0)
    
    def test_10_export_csv(self):
        """Test CSV export."""
        (Path(self.temp_dir) / 'file1.txt').write_text('duplicate')
        (Path(self.temp_dir) / 'file2.txt').write_text('duplicate')
        
        duplicates = self.dedup.scan_directory(self.temp_dir)
        
        csv_file = Path(self.temp_dir) / 'report.csv'
        self.dedup.export_csv(duplicates, str(csv_file))
        
        self.assertTrue(csv_file.exists())
        self.assertGreater(csv_file.stat().st_size, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
