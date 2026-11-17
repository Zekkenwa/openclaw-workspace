import os, heapq, json, time
from collections import defaultdict
from pathlib import Path

ROOT = Path('C:/')
TOP_FILES = 80
largest = []
root_sizes = defaultdict(int)
user_sizes = defaultdict(int)
ext_sizes = defaultdict(int)
errors = 0
files = 0
start = time.time()

stack = [ROOT]
while stack:
    folder = stack.pop()
    try:
        with os.scandir(folder) as it:
            for entry in it:
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        size = entry.stat(follow_symlinks=False).st_size
                        files += 1
                        p = Path(entry.path)
                        parts = p.parts
                        if len(parts) > 1:
                            root_sizes[parts[1]] += size
                        if len(parts) > 3 and parts[1].lower() == 'users':
                            user_sizes[f'{parts[2]}\\{parts[3]}'] += size
                        suffix = p.suffix.lower() or '[no extension]'
                        ext_sizes[suffix] += size
                        item = (size, str(p))
                        if len(largest) < TOP_FILES:
                            heapq.heappush(largest, item)
                        elif size > largest[0][0]:
                            heapq.heapreplace(largest, item)
                except (OSError, PermissionError):
                    errors += 1
    except (OSError, PermissionError):
        errors += 1

result = {
    'elapsed_seconds': round(time.time()-start, 1),
    'files_scanned': files,
    'errors': errors,
    'root_folders': sorted(({'path': f'C:\\{k}', 'bytes': v} for k,v in root_sizes.items()), key=lambda x:x['bytes'], reverse=True),
    'user_level_folders': sorted(({'path': f'C:\\Users\\{k}', 'bytes': v} for k,v in user_sizes.items()), key=lambda x:x['bytes'], reverse=True)[:50],
    'extensions': sorted(({'extension': k, 'bytes': v} for k,v in ext_sizes.items()), key=lambda x:x['bytes'], reverse=True)[:30],
    'largest_files': [{'path': p, 'bytes': s} for s,p in sorted(largest, reverse=True)],
}
print(json.dumps(result, indent=2))
