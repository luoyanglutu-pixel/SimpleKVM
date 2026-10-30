"""Fetch pinned portable Windows compilers; no system installation or PATH edits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.request
import zipfile

TOOLS={
    'gcc': {
        'url':'https://github.com/ch32-riscv-ug/MounRiver_Studio_Community_miror/releases/download/1.92-toolchain/riscv-none-embed-gcc-8-win-1.92.zip',
        'sha256':'da97b5f50fd20394d844fc02c2bb034f668019b9db62b86a3f15fa277f2831fd',
        'folder':'mrs-gcc8-1.92','exe':'riscv-none-embed-gcc.exe',
        'provenance':'MounRiver 1.92 GCC8 Windows distribution, community split-package mirror'},
    'host_cc': {
        'url':'https://download.savannah.gnu.org/releases/tinycc/tcc-0.9.27-win64-bin.zip',
        'sha256':'34a721949a2583fdff725312da092fa0f5f1f284b702e6f811c6954714faabb2',
        'folder':'tcc-0.9.27','exe':'tcc.exe',
        'provenance':'TinyCC upstream GNU Savannah release'}
}
ROOT=Path(__file__).resolve().parents[1]


def fetch(root,key,meta):
    dest=root/'installed'/meta['folder']
    archive=root/(meta['folder']+'.zip')
    good=archive.exists() and hashlib.sha256(archive.read_bytes()).hexdigest()==meta['sha256']
    if not good:
        req=urllib.request.Request(meta['url'],headers={'User-Agent':'SimpleKVM-build/0.1.0'})
        with urllib.request.urlopen(req,timeout=60) as response,archive.open('wb') as out:
            shutil.copyfileobj(response,out)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=meta['sha256']:
        raise RuntimeError('Download checksum mismatch: '+key)
    dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            if not (dest/info.filename).resolve().is_relative_to(dest.resolve()):
                raise RuntimeError('Unsafe archive path')
        z.extractall(dest)
    candidates=list(dest.rglob(meta['exe']))
    if len(candidates)!=1:raise RuntimeError('Expected exactly one compiler: '+key)
    return str(candidates[0].resolve())


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',default=str(Path(tempfile.gettempdir())/'simplekvm-tools'))
    args=p.parse_args()
    dest=Path(args.root).resolve()
    if os.name!='nt':p.error('This bootstrap contains Windows compilers only')
    if not str(dest).isascii():p.error('--root must be an ASCII installation path')
    dest.mkdir(parents=True,exist_ok=True)
    local={key:fetch(dest,key,meta) for key,meta in TOOLS.items()}
    (ROOT/'tools/local_config.json').write_text(json.dumps(local,indent=2),encoding='utf-8')
    print(json.dumps(local,indent=2))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Tool setup failed:',exc,file=sys.stderr);sys.exit(1)
