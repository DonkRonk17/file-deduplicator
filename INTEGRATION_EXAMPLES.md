# File Deduplicator - Integration Examples

## Basic Usage
```python
from deduplicator import FileDeduplicator

dedup = FileDeduplicator()
duplicates = dedup.scan_directory('/path')
dedup.export_json(duplicates, 'report.json')
```

## With Filtering
```python
dedup = FileDeduplicator(
    min_size=1024,
    extensions=['.jpg', '.png'],
    exclude_dirs=['node_modules']
)
duplicates = dedup.scan_directory('/path')
```

## Automated Cleanup
```bash
#!/bin/bash
python deduplicator.py ~/Downloads --action delete --min-size 1MB --dry-run
```
