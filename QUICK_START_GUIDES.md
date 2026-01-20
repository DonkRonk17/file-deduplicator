# File Deduplicator - Quick Start

## 30-Second Setup
1. Clone repository
2. Run: python deduplicator.py /path/to/scan
3. Review results
4. Use --action delete to remove duplicates

## For Developers
```python
from deduplicator import FileDeduplicator
dedup = FileDeduplicator(min_size=1024)
results = dedup.scan_directory('/path')
```

## For CLI Users
```bash
python deduplicator.py ~/Downloads --dry-run
python deduplicator.py ~/Downloads --action delete
```
