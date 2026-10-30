"""Reproducible bare-metal CH32V003 build; no IDE or make dependency."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FW = ROOT/'firmware'
VERSION = '0.1.1'
PROFILES = {'bringup': (0,1), 'dev': (0,0), 'release': (1,0)}


def run(cmd, log, echo=True):
    p=subprocess.run(list(map(str,cmd)),cwd=FW,stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT,encoding='utf-8',errors='replace')
    log.append({'command':list(map(str,cmd)), 'output':p.stdout,'exit_code':p.returncode})
    if p.stdout and echo: print(p.stdout,end='')
    if p.returncode: raise RuntimeError(f'Command failed ({p.returncode}): {cmd[0]}')
    return p.stdout


def resolve_gcc(value):
    config=ROOT/'tools/local_config.json'
    local=json.loads(config.read_text('utf-8')) if config.exists() else {}
    candidate=value or os.environ.get('KVM_GCC') or local.get('gcc')
    if not candidate:
        candidate=shutil.which('riscv-none-embed-gcc') or shutil.which('riscv-none-elf-gcc')
    if not candidate: raise RuntimeError('Provide --gcc PATH, KVM_GCC, or run tools/bootstrap_tools.py')
    p=Path(candidate).resolve()
    if not p.is_file(): raise RuntimeError(f'Compiler not found: {p}')
    # MRS GCC8 uses ANSI paths. Installation must have an ASCII path.
    if not str(p).isascii(): raise RuntimeError('Install/copy MRS toolchain under an ASCII path first')
    return p


def build(profile,gcc):
    out=ROOT/'build'/profile
    out.mkdir(parents=True,exist_ok=True)
    log=[]
    stem='simplekvm_'+profile
    relout='../build/'+profile
    app=[str(x.relative_to(FW)).replace('\\','/') for x in sorted((FW/'App').glob('*.c'))]
    vendor=['Vendor/WCH/Peripheral/src/ch32v00x_'+x+'.c' for x in ['gpio','rcc','tim','iwdg','misc']]
    sources=app+vendor+['Project/system_ch32v00x.c','Vendor/WCH/Startup/startup_ch32v00x.S']
    arch=['-march=rv32ec','-mabi=ilp32e','-msmall-data-limit=8','-mno-save-restore']
    flags=arch+['-Os','-g3','-ffunction-sections','-fdata-sections','-fno-common',
                '-fno-builtin','-fno-stack-protector','-fstack-usage',
                '-IApp','-IProject','-IVendor/WCH/Core','-IVendor/WCH/Peripheral/inc',
                '-DKVM_WATCHDOG='+str(PROFILES[profile][0]),
                '-DKVM_BRINGUP='+str(PROFILES[profile][1])]
    compiler=run([gcc,'--version'],log).splitlines()[0]
    objects=[]
    try:
        for index,source in enumerate(sources):
            obj=f'{relout}/{index:02d}_{Path(source).stem}.o'
            opts=['-std=c11','-Wall','-Wextra','-Werror'] if source.startswith('App/') else []
            run([gcc,*flags,*opts,'-c',source,'-o',obj],log)
            objects.append(obj)
        elf=f'{relout}/{stem}.elf'
        run([gcc,*arch,'-nostdlib','-nostartfiles','-TProject/Link.ld',
             '-Wl,--gc-sections,--print-memory-usage',f'-Wl,-Map={relout}/{stem}.map',
             *objects,'-lgcc','-o',elf],log)
        prefix=gcc.name.removesuffix('gcc.exe').removesuffix('gcc')
        suffix='.exe' if gcc.suffix.lower()=='.exe' else ''
        tool=lambda name: gcc.with_name(prefix+name+suffix)
        for fmt,extension in [('ihex','hex'),('binary','bin')]:
            run([tool('objcopy'),'-O',fmt,elf,f'{relout}/{stem}.{extension}'],log)
        sizes=run([tool('size'),'-A',elf],log)
        (out/(stem+'.sections.txt')).write_text(sizes,encoding='utf-8')
        headers=run([tool('readelf'),'-h',elf],log)
        (out/(stem+'.elf-header.txt')).write_text(headers,encoding='utf-8')
        syms=run([tool('nm'),'-n',elf],log,echo=False)
        (out/(stem+'.symbols.txt')).write_text(syms,encoding='utf-8')
        disassembly=run([tool('objdump'),'-d',elf],[],echo=False)
        (out/(stem+'.lst')).write_text(disassembly,encoding='utf-8')
        symbols={m[3]:int(m[1],16) for line in syms.splitlines()
                 if (m:=re.fullmatch(r'([0-9a-fA-F]+)\s+([A-Za-z])\s+(\S+)',line))}
        binary=(out/(stem+'.bin')).read_bytes()
        assert int.from_bytes(binary[38*4:39*4],'little')==symbols['TIM2_IRQHandler'], 'TIM2 vector not bound'
        assert symbols['_start']==0 and 'RISC-V' in headers
        assert 'RVE' in headers, 'Not RV32E ABI'
        sections={m[1]:int(m[2]) for line in sizes.splitlines()
                  if (m:=re.fullmatch(r'(\.[\w.]+)\s+(\d+)\s+(?:0x[0-9a-fA-F]+|\d+)',line.strip()))}
        static_ram=sum(sections.get(s,0) for s in ['.data','.bss','.highcode'])
        assert len(binary)<=8192, 'Project Flash goal exceeded'
        assert static_ram<=512, 'Project static RAM goal exceeded'
        assert sections['.stack']==512
        assert symbols['_ebss']<=0x20000800-sections['.stack']
        assert symbols['_eusrstack']==0x20000800
        hashes={p.relative_to(FW).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(FW.rglob('*')) if p.is_file()}
        test_path=ROOT/'build/host/test-result.json'
        manifest={'version':VERSION,'profile':profile,'watchdog_enabled':bool(PROFILES[profile][0]),
                  'data_path_permanently_disabled':bool(PROFILES[profile][1]),
                  'compiler':compiler,'compiler_path':str(gcc),
                  'architecture':'rv32ec','abi':'ilp32e','flash_origin':'0x00000000',
                  'flash_image_bytes':len(binary),'static_ram_bytes':static_ram,
                  'reserved_stack_bytes':sections['.stack'],
                  'tim2_vector_verified':True,'sdk_commit':'4e1b7437ada5d3ae8831a6f4b811a6320e4e23c7',
                  'hardware_netlist_sha256':'b54f1f99c8de1449b985926847d8d976c1113d993f46d08a57aa5d76fe3327fa',
                  'host_test_result':json.loads(test_path.read_text('utf-8')) if test_path.exists() else None,
                  'bench_tested':False,'source_sha256':hashes,
                  'artifacts_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in out.glob(stem+'.*') if p.suffix!='.json'}}
        (out/(stem+'.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:manifest[k] for k in ['profile','flash_image_bytes','static_ram_bytes','reserved_stack_bytes','tim2_vector_verified','bench_tested']}))
    finally:
        (out/'build-log.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--profile',choices=[*PROFILES,'all'],default='dev')
    p.add_argument('--gcc')
    args=p.parse_args()
    gcc=resolve_gcc(args.gcc)
    for profile in PROFILES if args.profile=='all' else [args.profile]:
        build(profile,gcc)

if __name__=='__main__':
    try:main()
    except (RuntimeError,AssertionError) as exc:
        print('BUILD FAILED:',exc,file=sys.stderr)
        sys.exit(1)
