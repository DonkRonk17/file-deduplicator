# File Deduplicator - Examples

## Quick Start

### Find Duplicates
```bash
python deduplicator.py /path/to/scan
```

### Dry Run (Safe Mode)
```bash
python deduplicator.py /path/to/scan --dry-run
```

### Delete Duplicates
```bash
python deduplicator.py /path/to/scan --action delete
```

### Move to Folder
```bash
python deduplicator.py /path/to/scan --action move --move-to ./duplicates
```

### Filter by Extension
```bash
python deduplicator.py /path/to/scan --extensions .jpg,.png,.gif
```

### Filter by Size
```bash
python deduplicator.py /path/to/scan --min-size 1MB --max-size 100MB
```

### Export Results
```bash
python deduplicator.py /path/to/scan --export json --output report.json
python deduplicator.py /path/to/scan --export csv --output report.csv
```

## Real-World Scenarios

### Clean Downloads Folder
```bash
python deduplicator.py ~/Downloads --action delete --interactive
```

### Photo Library Cleanup
```bash
python deduplicator.py ~/Photos --extensions .jpg,.jpeg,.png --min-size 100KB
```

### Code Repository Cleanup
```bash
python deduplicator.py ~/projects --exclude node_modules,.git,__pycache__ --extensions .py,.js,.ts
```

## Python API

```python
from deduplicator import FileDeduplicator

dedup = FileDeduplicator(min_size=1024, extensions=['.txt', '.pdf'])
duplicates = dedup.scan_directory('/path/to/scan')

for group in duplicates:
    print(f'Found {len(group.files)} duplicates, wasting {group.wasted_space} bytes')
```
