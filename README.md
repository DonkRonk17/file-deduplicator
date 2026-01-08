# 🔍 Universal File Deduplicator

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Find and manage duplicate files across any directory. Fast, accurate, and safe.**

Created by [Metaphy LLC](https://metaphysicsandcomputing.com)

---

## ✨ Features

- 🚀 **Fast** - Multi-threaded hashing with smart pre-filtering
- 🎯 **Accurate** - SHA-256 verification ensures true duplicates only
- 🛡️ **Safe** - Dry-run mode, interactive confirmation, move-to-trash option
- 📊 **Flexible Output** - Text report, JSON, or CSV export
- 🔧 **Customizable** - Filter by size, extension, exclude directories
- 📦 **Zero Dependencies** - Uses only Python standard library

---

## 📥 Installation

### Option 1: Clone from GitHub

```bash
git clone https://github.com/DonkRonk17/file-deduplicator.git
cd file-deduplicator
```

### Option 2: Download directly

Download `deduplicator.py` and run it directly with Python 3.8+.

### Requirements

- **Python 3.8 or higher** (uses walrus operator and dataclasses)
- No external dependencies required!

---

## 🚀 Quick Start

### Basic Scan

```bash
# Scan current directory
python deduplicator.py .

# Scan a specific folder
python deduplicator.py /path/to/folder

# Scan with verbose output (shows all file paths)
python deduplicator.py /path/to/folder -v
```

### Filter Files

```bash
# Only scan images
python deduplicator.py /photos --ext jpg png gif webp

# Only scan large files (>1MB)
python deduplicator.py /data --min-size 1048576

# Exclude specific directories
python deduplicator.py /project --exclude node_modules .git dist
```

### Export Results

```bash
# Export to JSON
python deduplicator.py /data --json duplicates.json

# Export to CSV (for Excel/spreadsheets)
python deduplicator.py /data --csv duplicates.csv
```

### Remove Duplicates

```bash
# ALWAYS do a dry run first!
python deduplicator.py /data --delete --dry-run

# Delete duplicates (keeps oldest file by default)
python deduplicator.py /data --delete --keep oldest

# Delete with interactive confirmation
python deduplicator.py /data --delete -i

# Move duplicates to trash folder instead of deleting
python deduplicator.py /data --move ./duplicates_trash
```

---

## 📖 Command Reference

```
usage: deduplicator.py [-h] [-v] [-r] [--min-size MIN_SIZE] [--max-size MAX_SIZE]
                       [--ext EXT [EXT ...]] [--exclude DIR [DIR ...]]
                       [--threads THREADS] [--json FILE] [--csv FILE]
                       [--delete] [--move FOLDER] [--keep {oldest,newest,first}]
                       [--dry-run] [--interactive] [--version]
                       directory

Arguments:
  directory             Directory to scan

Options:
  -h, --help            Show help message
  -v, --verbose         Show all file paths in report
  -r, --no-recursive    Do not scan subdirectories
  --min-size SIZE       Minimum file size in bytes (default: 1)
  --max-size SIZE       Maximum file size in bytes
  --ext EXT [EXT ...]   Only scan files with these extensions
  --exclude DIR [DIR ...] Directory names to exclude
  --threads N           Number of threads for hashing (default: 4)

Output:
  --json FILE           Export results to JSON file
  --csv FILE            Export results to CSV file

Actions:
  --delete              Delete duplicate files
  --move FOLDER         Move duplicates to specified folder
  --keep {oldest,newest,first}
                        Which file to keep (default: oldest)
  --dry-run             Simulate actions without making changes
  -i, --interactive     Confirm each deletion
```

---

## 📊 Example Output

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     🔍 UNIVERSAL FILE DEDUPLICATOR v1.0.0                     ║
║                         Metaphy LLC - 2025                                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝

🔍 Scanning: /home/user/Documents
   Options: min_size=1, recursive=True

📁 Phase 1: Collecting files...
   Found 15,432 files

⚡ Phase 2: Quick hash filtering...
   1,247 files need full hash verification

🔐 Phase 3: Full hash verification...

📊 Phase 4: Building duplicate groups...

══════════════════════════════════════════════════════════════════════════
                    📋 DUPLICATE FILE REPORT
══════════════════════════════════════════════════════════════════════════

🔴 Found 23 groups of duplicate files
   Total duplicates: 47
   Wasted space: 1.23 GB

----------------------------------------------------------------------

📁 Group 1: 156.78 MB × 3 files
   Hash: a1b2c3d4e5f6g7h8...
   Wasted: 313.56 MB
   🟢 /home/user/Documents/backup/video.mp4
   🔴 /home/user/Documents/projects/video.mp4
   🔴 /home/user/Downloads/video.mp4

📁 Group 2: 45.32 MB × 2 files
   Hash: 9f8e7d6c5b4a3210...
   Wasted: 45.32 MB
   🟢 /home/user/Documents/photos/vacation.jpg
   🔴 /home/user/Documents/photos/vacation_copy.jpg

----------------------------------------------------------------------
📊 SCAN STATISTICS
----------------------------------------------------------------------
   Files scanned:    15,432
   Files hashed:     1,247
   Data scanned:     24.56 GB
   Duplicates found: 47
   Wasted space:     1.23 GB
   Scan time:        12.34 seconds
══════════════════════════════════════════════════════════════════════════
```

---

## 🔒 Safety Features

### 1. Dry Run Mode
Always use `--dry-run` first to see what would be deleted:
```bash
python deduplicator.py /data --delete --dry-run
```

### 2. Interactive Mode
Confirm each file before deletion:
```bash
python deduplicator.py /data --delete -i
```

### 3. Move Instead of Delete
Move duplicates to a folder for manual review:
```bash
python deduplicator.py /data --move ./review_these
```

### 4. Keep Strategy
Choose which file to keep:
- `--keep oldest` - Keep the file with oldest modification date (default)
- `--keep newest` - Keep the most recently modified file
- `--keep first` - Keep the first file found during scan

---

## 🛠️ How It Works

1. **Phase 1: Size Grouping** - Files are grouped by size. Files with unique sizes can't be duplicates.

2. **Phase 2: Quick Hash** - Files of same size get a quick hash (first 4KB + last 4KB + size). This eliminates most non-duplicates quickly.

3. **Phase 3: Full Hash** - Only files with matching quick hashes get full SHA-256 verification.

4. **Phase 4: Report** - True duplicates are grouped and sorted by wasted space.

This multi-phase approach makes scanning fast even for large directories.

---

## 💡 Tips

### Cleaning Up Downloads
```bash
# Find duplicate downloads
python deduplicator.py ~/Downloads --min-size 1048576 -v

# Move duplicates for review
python deduplicator.py ~/Downloads --move ~/Downloads/duplicates
```

### Photo Library Cleanup
```bash
# Find duplicate photos
python deduplicator.py ~/Photos --ext jpg jpeg png heic --json photo_dupes.json

# Review the JSON, then delete
python deduplicator.py ~/Photos --ext jpg jpeg png heic --delete --dry-run
```

### Developer Project Cleanup
```bash
# Exclude build artifacts
python deduplicator.py ~/projects --exclude node_modules .git __pycache__ dist build
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

---

## 📬 Contact

- **Author:** Logan Smith
- **Company:** [Metaphy LLC](https://metaphysicsandcomputing.com)
- **Email:** logan@metaphysicsandcomputing.com

---

Made with ❤️ by Team Brain @ Metaphy LLC
