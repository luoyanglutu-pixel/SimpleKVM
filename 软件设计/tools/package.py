"""Package only verified build artifacts and a source snapshot."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.1.1'


def check_hashes(base,hashes):
    for name,digest in hashes.items():
        assert hashlib.sha256((base/name).read_bytes()).hexdigest()==digest, 'Stale build/test: '+name


def zip_files(path,items):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for arc,source in sorted(items):
            info=zipfile.ZipInfo(arc,(2026,10,21,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,source.read_bytes())


def main():
    vendor=ROOT/'firmware/Vendor/WCH'
    provenance=json.loads((vendor/'provenance.json').read_text('utf-8'))
    check_hashes(vendor,{x['path']:x['sha256'] for x in provenance['files']})
    tests=json.loads((ROOT/'build/host/test-result.json').read_text('utf-8'))
    assert tests['passed'] and not tests['failures'] and not tests['errors']
    check_hashes(ROOT,tests['source_sha256'])
    pins=json.loads((ROOT/'build/hardware-pin-check.json').read_text('utf-8'))
    assert pins['passed']
    dest=ROOT/'releases'/('v'+VERSION);dest.mkdir(parents=True,exist_ok=True)
    for profile in ['bringup','dev','release']:
        folder=ROOT/'build'/profile
        manifest=json.loads((folder/f'simplekvm_{profile}.json').read_text('utf-8'))
        check_hashes(ROOT/'firmware',manifest['source_sha256'])
        check_hashes(folder,manifest['artifacts_sha256'])
        assert manifest['tim2_vector_verified'] and manifest['version']==VERSION
        assert manifest['host_test_result']==tests
        target=dest/profile;target.mkdir(exist_ok=True)
        for p in folder.glob('simplekvm_'+profile+'.*'):
            shutil.copy2(p,target/p.name)
        for p in folder.glob('*.su'):shutil.copy2(p,target/p.name)
        shutil.copy2(folder/'build-log.json',target/'build-log.json')
    for name in ['test-result.json','hardware-pin-check.json']:
        src=ROOT/('build/host/test-result.json' if name=='test-result.json' else 'build/hardware-pin-check.json')
        shutil.copy2(src,dest/name)
    readme='''# SimpleKVM v0.1.1 样板验证包

硬件：2026-10-21下午版，CH32V003F4P6 + CH444G + CH334P。
电脑端23项实际C逻辑测试和三种交叉编译已通过；尚未上板验收。

## 先选文件

- bringup/simplekvm_bringup.hex：四键四灯检查，USB数据始终断开，看门狗关闭。全部释放后逐键按下才亮灯。
- dev/simplekvm_dev.hex：首次完整功能联调。默认电脑4，20ms消抖，先断后接，看门狗关闭。
- release/simplekvm_release.hex：相同功能，加约1秒目标超时看门狗；配置名称不表示量产放行。

首次USB功能联调选择dev，不要把bringup无法枚举误判为坏板。

## 烧录

WCH-LinkE，RISC-V/SDI模式。本板自供电，H1：1 SWIO、2 NRST、3 GND；下载器5V/3V3和SWCLK不接。
优先载入HEX，选CH32V003，编程并校验后复位。HEX携带地址，ELF链接原点为0x00000000；不要套用其它芯片BIN地址。
按键只改变数据通路；LED代表已选通道，不能确认主机在线或枚举完成。

各配置含HEX/BIN/ELF/map/反汇编/构建清单、校验值和栈用量文件。源代码在sources.zip。
完整上板步骤与未测项目见源码包的软件设计/02_编译与烧录.md、03_测试与构建记录.md。
SHA256SUMS.txt覆盖本目录文件，顶层压缩包另外记录哈希。
'''
    (dest/'README.md').write_text(readme,encoding='utf-8')
    source_items=[]
    for folder in ['firmware','tools','tests']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.name!='local_config.json':
                source_items.append(('软件设计/'+p.relative_to(ROOT).as_posix(),p))
    for p in ROOT.glob('*.md'): source_items.append(('软件设计/'+p.name,p))
    source_items.append(('软件设计/.gitignore',ROOT/'.gitignore'))
    # Include the immutable schematic inputs needed by pin verification.
    hw=ROOT.parent/'硬件设计/原理图/新方案'
    for name in ['SCH_SCH_new_2026-10-21-2.pdf','Netlist_SCH_new_2026-10-21-2.enet',
                 'BOM_SimpleKVM_new_SCH_new_2026-10-21-2.xlsx','13_原理图复查_2026-10-21-2.md',
                 '08_下载接口与烧录指南.md']:
        source_items.append(('硬件设计/原理图/新方案/'+name,hw/name))
    zip_files(dest/'sources.zip',source_items)
    sums=[]
    for p in sorted(dest.rglob('*')):
        if p.is_file() and p.name!='SHA256SUMS.txt':
            sums.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(dest).as_posix())
    (dest/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
    bundle=dest.parent/('simplekvm_v'+VERSION+'_样板验证包.zip')
    zip_files(bundle,[(p.relative_to(dest).as_posix(),p) for p in dest.rglob('*') if p.is_file()])
    summary={'version':VERSION,'archive':bundle.name,'bytes':bundle.stat().st_size,
             'sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),
             'host_tests':tests['tests'],'bench_tested':False}
    (dest.parent/('package-v'+VERSION+'.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__': main()
