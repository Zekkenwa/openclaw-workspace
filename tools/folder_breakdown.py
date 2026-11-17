import os, json, sys, time
from pathlib import Path

roots = [Path(p) for p in sys.argv[1:]]
result = []
for root in roots:
    sizes = {}
    errors = 0
    start = time.time()
    try:
        children = list(os.scandir(root))
    except OSError as e:
        result.append({'root':str(root),'error':str(e)})
        continue
    for child in children:
        if child.is_symlink():
            continue
        total = 0
        if child.is_file(follow_symlinks=False):
            try: total = child.stat(follow_symlinks=False).st_size
            except OSError: errors += 1
        elif child.is_dir(follow_symlinks=False):
            stack = [child.path]
            while stack:
                d = stack.pop()
                try:
                    with os.scandir(d) as it:
                        for e in it:
                            try:
                                if e.is_symlink(): continue
                                if e.is_dir(follow_symlinks=False): stack.append(e.path)
                                elif e.is_file(follow_symlinks=False): total += e.stat(follow_symlinks=False).st_size
                            except OSError: errors += 1
                except OSError: errors += 1
        sizes[child.name] = total
    result.append({'root':str(root),'elapsed_seconds':round(time.time()-start,1),'errors':errors,'children':[
        {'path':str(root / k),'bytes':v} for k,v in sorted(sizes.items(), key=lambda x:x[1], reverse=True)
    ]})
print(json.dumps(result, indent=2))
