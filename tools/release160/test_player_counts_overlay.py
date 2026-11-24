#!/usr/bin/env python3
import pathlib, tempfile, shutil, sys, hashlib
from apply_player_counts import apply, BASE, MAIN
source=pathlib.Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix='counts-overlay-proof-') as tmp:
    root=pathlib.Path(tmp)
    for rel in [BASE+'configs/CoreConfig.java',MAIN]:
        target=root/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/rel,target)
    apply(root)
    files=[root/(BASE+'configs/CoreConfig.java'),root/MAIN,root/(BASE+'PlayerCountCache.java')]
    before=[f.read_bytes() for f in files];apply(root);assert before==[f.read_bytes() for f in files]
    files[1].write_text(files[1].read_text()+'\n// unreviewed drift\n')
    before=[f.read_bytes() for f in files]
    try:apply(root);raise AssertionError('source drift accepted')
    except ValueError:pass
    assert before==[f.read_bytes() for f in files], 'partial mutation on failed preflight'
print('Counts overlay PASS: exact source, idempotence and refusal of unreviewed drift before writes')
