#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     🔍 UNIVERSAL FILE DEDUPLICATOR                            ║
║                         Metaphy LLC - 2025                                     ║
║                                                                                ║
║  Find and manage duplicate files across any directory.                         ║
║  Fast, accurate, and safe - with multiple action modes.                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Author: Logan Smith / Metaphy LLC
Repository: https://github.com/DonkRonk17/file-deduplicator
License: MIT
"""

import os
import sys
import hashlib
import argparse
import json
import shutil
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import concurrent.futures
from dataclasses import dataclass, asdict

# Version
__version__ = "1.0.0"

# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FileInfo:
    """Information about a file."""
    path: str
    size: int
    hash: str
    modified: float
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class DuplicateGroup:
    """A group of duplicate files."""
    hash: str
    size: int
    files: List[FileInfo]
    wasted_space: int
    
    def to_dict(self) -> dict:
        return {
            'hash': self.hash,
            'size': self.size,
            'count': len(self.files),
            'wasted_space': self.wasted_space,
            'files': [f.to_dict() for f in self.files]
        }

# ═══════════════════════════════════════════════════════════════════════════════
# CORE DEDUPLICATOR CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class FileDeduplicator:
    """
    Universal File Deduplicator - Find and manage duplicate files.
    
    Features:
    - Fast hashing with size pre-filtering
    - Multi-threaded scanning for speed
    - Safe deletion with confirmation
    - Multiple output formats (text, JSON, CSV)
    - Dry-run mode for safety
    """
    
    def __init__(self, 
                 min_size: int = 1,
                 max_size: Optional[int] = None,
                 extensions: Optional[List[str]] = None,
                 exclude_dirs: Optional[List[str]] = None,
                 threads: int = 4):
        """
        Initialize the deduplicator.
        
        Args:
            min_size: Minimum file size in bytes (default: 1)
            max_size: Maximum file size in bytes (default: None = unlimited)
            extensions: List of file extensions to include (default: all)
            exclude_dirs: List of directory names to exclude
            threads: Number of threads for parallel hashing
        """
        self.min_size = min_size
        self.max_size = max_size
        self.extensions = [ext.lower().lstrip('.') for ext in (extensions or [])]
        self.exclude_dirs = set(exclude_dirs or ['.git', '__pycache__', 'node_modules', '.venv', 'venv'])
        self.threads = threads
        
        # Statistics
        self.stats = {
            'files_scanned': 0,
            'files_hashed': 0,
            'bytes_scanned': 0,
            'duplicates_found': 0,
            'wasted_space': 0,
            'scan_time': 0
        }
    
    def _should_include_file(self, path: Path) -> bool:
        """Check if a file should be included in the scan."""
        try:
            # Check if file exists and is accessible
            if not path.is_file():
                return False
            
            # Check size constraints
            size = path.stat().st_size
            if size < self.min_size:
                return False
            if self.max_size and size > self.max_size:
                return False
            
            # Check extension filter
            if self.extensions:
                ext = path.suffix.lower().lstrip('.')
                if ext not in self.extensions:
                    return False
            
            return True
        except (PermissionError, OSError):
            return False
    
    def _should_exclude_dir(self, path: Path) -> bool:
        """Check if a directory should be excluded."""
        return path.name in self.exclude_dirs
    
    def _hash_file(self, path: Path, chunk_size: int = 65536) -> Optional[str]:
        """
        Calculate SHA-256 hash of a file.
        
        Uses chunked reading for memory efficiency on large files.
        """
        try:
            hasher = hashlib.sha256()
            with open(path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (PermissionError, OSError, IOError):
            return None
    
    def _quick_hash(self, path: Path) -> Optional[str]:
        """
        Quick hash using first and last 4KB + file size.
        Used for initial grouping before full hash.
        """
        try:
            size = path.stat().st_size
            hasher = hashlib.md5()
            hasher.update(str(size).encode())
            
            with open(path, 'rb') as f:
                # Read first 4KB
                hasher.update(f.read(4096))
                
                # Read last 4KB if file is larger
                if size > 8192:
                    f.seek(-4096, 2)
                    hasher.update(f.read(4096))
            
            return hasher.hexdigest()
        except (PermissionError, OSError, IOError):
            return None
    
    def scan_directory(self, directory: str, recursive: bool = True) -> List[DuplicateGroup]:
        """
        Scan a directory for duplicate files.
        
        Args:
            directory: Path to directory to scan
            recursive: Whether to scan subdirectories (default: True)
            
        Returns:
            List of DuplicateGroup objects
        """
        start_time = datetime.now()
        directory = Path(directory).resolve()
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")
        
        print(f"🔍 Scanning: {directory}")
        print(f"   Options: min_size={self.min_size}, recursive={recursive}")
        
        # Phase 1: Collect all files and group by size
        print("\n📁 Phase 1: Collecting files...")
        size_groups: Dict[int, List[Path]] = defaultdict(list)
        
        def walk_directory(dir_path: Path):
            """Walk directory and collect files."""
            try:
                for entry in dir_path.iterdir():
                    if entry.is_dir():
                        if not self._should_exclude_dir(entry) and recursive:
                            walk_directory(entry)
                    elif self._should_include_file(entry):
                        size = entry.stat().st_size
                        size_groups[size].append(entry)
                        self.stats['files_scanned'] += 1
                        self.stats['bytes_scanned'] += size
            except PermissionError:
                pass
        
        walk_directory(directory)
        
        # Filter to only sizes with potential duplicates
        potential_duplicates = {
            size: files for size, files in size_groups.items() 
            if len(files) > 1
        }
        
        print(f"   Found {self.stats['files_scanned']:,} files")
        print(f"   {len(potential_duplicates):,} size groups with potential duplicates")
        
        # Phase 2: Quick hash for initial grouping
        print("\n⚡ Phase 2: Quick hash filtering...")
        quick_hash_groups: Dict[str, List[Path]] = defaultdict(list)
        
        for size, files in potential_duplicates.items():
            for file_path in files:
                qhash = self._quick_hash(file_path)
                if qhash:
                    quick_hash_groups[f"{size}_{qhash}"].append(file_path)
        
        # Filter to only groups with potential duplicates
        potential_duplicates_2 = {
            key: files for key, files in quick_hash_groups.items()
            if len(files) > 1
        }
        
        files_to_hash = sum(len(files) for files in potential_duplicates_2.values())
        print(f"   {files_to_hash:,} files need full hash verification")
        
        # Phase 3: Full hash verification
        print("\n🔐 Phase 3: Full hash verification...")
        full_hash_groups: Dict[str, List[FileInfo]] = defaultdict(list)
        
        def hash_file_info(path: Path) -> Optional[Tuple[str, FileInfo]]:
            """Hash a file and return FileInfo."""
            file_hash = self._hash_file(path)
            if file_hash:
                try:
                    stat = path.stat()
                    return (file_hash, FileInfo(
                        path=str(path),
                        size=stat.st_size,
                        hash=file_hash,
                        modified=stat.st_mtime
                    ))
                except (PermissionError, OSError):
                    pass
            return None
        
        # Use thread pool for parallel hashing
        all_files = [f for files in potential_duplicates_2.values() for f in files]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            results = list(executor.map(hash_file_info, all_files))
        
        for result in results:
            if result:
                file_hash, file_info = result
                full_hash_groups[file_hash].append(file_info)
                self.stats['files_hashed'] += 1
        
        # Phase 4: Build duplicate groups
        print("\n📊 Phase 4: Building duplicate groups...")
        duplicate_groups: List[DuplicateGroup] = []
        
        for file_hash, files in full_hash_groups.items():
            if len(files) > 1:
                size = files[0].size
                wasted = size * (len(files) - 1)
                
                duplicate_groups.append(DuplicateGroup(
                    hash=file_hash,
                    size=size,
                    files=files,
                    wasted_space=wasted
                ))
                
                self.stats['duplicates_found'] += len(files) - 1
                self.stats['wasted_space'] += wasted
        
        # Sort by wasted space (largest first)
        duplicate_groups.sort(key=lambda g: g.wasted_space, reverse=True)
        
        # Calculate scan time
        self.stats['scan_time'] = (datetime.now() - start_time).total_seconds()
        
        return duplicate_groups
    
    def print_report(self, groups: List[DuplicateGroup], verbose: bool = False):
        """Print a human-readable report of duplicates."""
        print("\n" + "═" * 70)
        print("                    📋 DUPLICATE FILE REPORT")
        print("═" * 70)
        
        if not groups:
            print("\n✅ No duplicate files found!")
            self._print_stats()
            return
        
        print(f"\n🔴 Found {len(groups)} groups of duplicate files")
        print(f"   Total duplicates: {self.stats['duplicates_found']:,}")
        print(f"   Wasted space: {self._format_size(self.stats['wasted_space'])}")
        
        print("\n" + "-" * 70)
        
        for i, group in enumerate(groups, 1):
            print(f"\n📁 Group {i}: {self._format_size(group.size)} × {len(group.files)} files")
            print(f"   Hash: {group.hash[:16]}...")
            print(f"   Wasted: {self._format_size(group.wasted_space)}")
            
            if verbose or len(groups) <= 10:
                for j, file_info in enumerate(group.files):
                    marker = "🟢" if j == 0 else "🔴"
                    print(f"   {marker} {file_info.path}")
        
        self._print_stats()
    
    def _print_stats(self):
        """Print scan statistics."""
        print("\n" + "-" * 70)
        print("📊 SCAN STATISTICS")
        print("-" * 70)
        print(f"   Files scanned:    {self.stats['files_scanned']:,}")
        print(f"   Files hashed:     {self.stats['files_hashed']:,}")
        print(f"   Data scanned:     {self._format_size(self.stats['bytes_scanned'])}")
        print(f"   Duplicates found: {self.stats['duplicates_found']:,}")
        print(f"   Wasted space:     {self._format_size(self.stats['wasted_space'])}")
        print(f"   Scan time:        {self.stats['scan_time']:.2f} seconds")
        print("═" * 70)
    
    def export_json(self, groups: List[DuplicateGroup], output_path: str):
        """Export results to JSON file."""
        data = {
            'generated': datetime.now().isoformat(),
            'stats': self.stats,
            'groups': [g.to_dict() for g in groups]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Exported to: {output_path}")
    
    def export_csv(self, groups: List[DuplicateGroup], output_path: str):
        """Export results to CSV file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("group,hash,size,path,modified\n")
            for i, group in enumerate(groups, 1):
                for file_info in group.files:
                    mod_date = datetime.fromtimestamp(file_info.modified).isoformat()
                    # Escape path for CSV
                    path = file_info.path.replace('"', '""')
                    f.write(f'{i},"{group.hash}",{file_info.size},"{path}",{mod_date}\n')
        
        print(f"✅ Exported to: {output_path}")
    
    def delete_duplicates(self, groups: List[DuplicateGroup], 
                         keep: str = 'oldest',
                         dry_run: bool = True,
                         interactive: bool = False) -> int:
        """
        Delete duplicate files, keeping one copy.
        
        Args:
            groups: List of duplicate groups
            keep: Which file to keep ('oldest', 'newest', 'first')
            dry_run: If True, only simulate deletion
            interactive: If True, confirm each deletion
            
        Returns:
            Number of files deleted (or would be deleted in dry run)
        """
        if dry_run:
            print("\n⚠️  DRY RUN - No files will be deleted")
        
        deleted_count = 0
        freed_space = 0
        
        for group in groups:
            # Sort files based on keep strategy
            files = list(group.files)
            if keep == 'oldest':
                files.sort(key=lambda f: f.modified)
            elif keep == 'newest':
                files.sort(key=lambda f: f.modified, reverse=True)
            # 'first' keeps original order
            
            # Keep the first file, delete the rest
            keeper = files[0]
            to_delete = files[1:]
            
            print(f"\n📁 Group: {group.hash[:16]}...")
            print(f"   Keeping: {keeper.path}")
            
            for file_info in to_delete:
                if interactive and not dry_run:
                    response = input(f"   Delete {file_info.path}? [y/N]: ")
                    if response.lower() != 'y':
                        print(f"   ⏭️  Skipped: {file_info.path}")
                        continue
                
                if dry_run:
                    print(f"   🔴 Would delete: {file_info.path}")
                else:
                    try:
                        os.remove(file_info.path)
                        print(f"   ✅ Deleted: {file_info.path}")
                        deleted_count += 1
                        freed_space += file_info.size
                    except (PermissionError, OSError) as e:
                        print(f"   ❌ Failed: {file_info.path} - {e}")
        
        print("\n" + "═" * 70)
        if dry_run:
            print(f"📊 DRY RUN SUMMARY: Would delete {deleted_count} files")
            print(f"   Would free: {self._format_size(freed_space)}")
        else:
            print(f"📊 DELETION SUMMARY: Deleted {deleted_count} files")
            print(f"   Space freed: {self._format_size(freed_space)}")
        print("═" * 70)
        
        return deleted_count
    
    def move_duplicates(self, groups: List[DuplicateGroup],
                       destination: str,
                       keep: str = 'oldest',
                       dry_run: bool = True) -> int:
        """
        Move duplicate files to a destination folder (safer than delete).
        
        Args:
            groups: List of duplicate groups
            destination: Folder to move duplicates to
            keep: Which file to keep ('oldest', 'newest', 'first')
            dry_run: If True, only simulate
            
        Returns:
            Number of files moved
        """
        dest_path = Path(destination)
        
        if not dry_run:
            dest_path.mkdir(parents=True, exist_ok=True)
        
        if dry_run:
            print(f"\n⚠️  DRY RUN - Files would be moved to: {destination}")
        else:
            print(f"\n📦 Moving duplicates to: {destination}")
        
        moved_count = 0
        
        for group in groups:
            files = list(group.files)
            if keep == 'oldest':
                files.sort(key=lambda f: f.modified)
            elif keep == 'newest':
                files.sort(key=lambda f: f.modified, reverse=True)
            
            keeper = files[0]
            to_move = files[1:]
            
            for file_info in to_move:
                src = Path(file_info.path)
                dst = dest_path / src.name
                
                # Handle name conflicts
                counter = 1
                while dst.exists():
                    dst = dest_path / f"{src.stem}_{counter}{src.suffix}"
                    counter += 1
                
                if dry_run:
                    print(f"   Would move: {src} → {dst}")
                else:
                    try:
                        shutil.move(str(src), str(dst))
                        print(f"   ✅ Moved: {src.name}")
                        moved_count += 1
                    except (PermissionError, OSError) as e:
                        print(f"   ❌ Failed: {src} - {e}")
        
        print(f"\n📊 {'Would move' if dry_run else 'Moved'}: {moved_count} files")
        return moved_count
    
    @staticmethod
    def _format_size(size: int) -> str:
        """Format size in human-readable form."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main CLI entry point."""
    # Fix Windows console encoding
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except AttributeError:
            pass  # Python < 3.7
    
    parser = argparse.ArgumentParser(
        description="🔍 Universal File Deduplicator - Find and manage duplicate files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan current directory
  python deduplicator.py .
  
  # Scan with verbose output
  python deduplicator.py /path/to/folder -v
  
  # Scan only images
  python deduplicator.py /photos --ext jpg png gif
  
  # Export results to JSON
  python deduplicator.py /data --json duplicates.json
  
  # Delete duplicates (dry run first!)
  python deduplicator.py /data --delete --dry-run
  python deduplicator.py /data --delete --keep oldest
  
  # Move duplicates to trash folder
  python deduplicator.py /data --move ./duplicates_trash

Author: Logan Smith / Metaphy LLC
Repository: https://github.com/DonkRonk17/file-deduplicator
        """
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show all file paths')
    parser.add_argument('-r', '--no-recursive', action='store_true',
                       help='Do not scan subdirectories')
    parser.add_argument('--min-size', type=int, default=1,
                       help='Minimum file size in bytes (default: 1)')
    parser.add_argument('--max-size', type=int, default=None,
                       help='Maximum file size in bytes')
    parser.add_argument('--ext', nargs='+', metavar='EXT',
                       help='Only scan files with these extensions')
    parser.add_argument('--exclude', nargs='+', metavar='DIR',
                       help='Directory names to exclude')
    parser.add_argument('--threads', type=int, default=4,
                       help='Number of threads for hashing (default: 4)')
    
    # Output options
    parser.add_argument('--json', metavar='FILE',
                       help='Export results to JSON file')
    parser.add_argument('--csv', metavar='FILE',
                       help='Export results to CSV file')
    
    # Action options
    parser.add_argument('--delete', action='store_true',
                       help='Delete duplicate files')
    parser.add_argument('--move', metavar='FOLDER',
                       help='Move duplicates to specified folder')
    parser.add_argument('--keep', choices=['oldest', 'newest', 'first'],
                       default='oldest',
                       help='Which file to keep (default: oldest)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate actions without making changes')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Confirm each deletion')
    
    parser.add_argument('--version', action='version',
                       version=f'File Deduplicator v{__version__}')
    
    args = parser.parse_args()
    
    # Print banner
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     🔍 UNIVERSAL FILE DEDUPLICATOR v1.0.0                     ║
║                         Metaphy LLC - 2025                                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Create deduplicator
    dedup = FileDeduplicator(
        min_size=args.min_size,
        max_size=args.max_size,
        extensions=args.ext,
        exclude_dirs=args.exclude,
        threads=args.threads
    )
    
    try:
        # Scan directory
        groups = dedup.scan_directory(
            args.directory,
            recursive=not args.no_recursive
        )
        
        # Print report
        dedup.print_report(groups, verbose=args.verbose)
        
        # Export if requested
        if args.json:
            dedup.export_json(groups, args.json)
        if args.csv:
            dedup.export_csv(groups, args.csv)
        
        # Perform actions if requested
        if args.delete:
            if not args.dry_run:
                print("\n⚠️  WARNING: This will permanently delete files!")
                response = input("Are you sure? Type 'yes' to confirm: ")
                if response.lower() != 'yes':
                    print("❌ Aborted.")
                    return
            
            dedup.delete_duplicates(
                groups,
                keep=args.keep,
                dry_run=args.dry_run,
                interactive=args.interactive
            )
        
        elif args.move:
            dedup.move_duplicates(
                groups,
                destination=args.move,
                keep=args.keep,
                dry_run=args.dry_run
            )
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        sys.exit(130)

if __name__ == '__main__':
    main()
