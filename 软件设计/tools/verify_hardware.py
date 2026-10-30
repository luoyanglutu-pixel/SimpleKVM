"""Check the published hardware baseline and firmware GPIO masks.

The 2026-10-29 release does not include a matching ENET export. The default
check therefore proves file integrity and firmware constants only. Passing a
historical ENET file with --netlist additionally runs the original connectivity
checks, but that result must not be treated as validation of the current PCB.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT.parent / '硬件设计'
CURRENT_BASELINE = {
    'ProPrj_SimpleKVM_2026-10-29.epro2':
        'e9788795cc1f5868b95208a61531f9a7a6e04f5df2975a7832593e5f73e33620',
    'SCH_SCH_new_2026-10-29.pdf':
        '2a0472c722191a3ec380d78114c99a1b42fed6ea0d62099289b459ac37409519',
    'BOM_SimpleKVM_new_SCH_new_2026-10-29.xlsx':
        '8ed492aca8bc979d2edb6fc583e5668d9446db59df8c7a54627b02a527e63dc3',
}
HISTORICAL_NETLIST_SHA256 = (
    'b54f1f99c8de1449b985926847d8d976c1113d993f46d08a57aa5d76fe3327fa'
)
MASKS = {
    'BOARD_LED_MASK': 0x0f,
    'BOARD_SEL0': 0x40,
    'BOARD_SEL1': 0x80,
    'BOARD_EN': 0x04,
    'BOARD_KEY_MASK': 0x78,
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_firmware_masks():
    header = (ROOT / 'firmware/App/board.h').read_text('utf-8')
    for name, value in MASKS.items():
        match = re.search(
            r'#define\s+' + name + r'\s+UINT16_C\((0x[0-9a-fA-F]+)\)',
            header,
        )
        assert match and int(match[1], 16) == value, name


def check_historical_netlist(path):
    digest = sha256(path)
    assert digest == HISTORICAL_NETLIST_SHA256, (
        'Historical hardware export changed; review it before using this check'
    )
    data = json.loads(path.read_text('utf-8-sig'))
    parts = {c['props']['Designator']: c for c in data['components'].values()}

    def net(ref, pin):
        return next(
            item.get('net', '')
            for item in parts[ref]['pinInfoMap'].values()
            if item['number'] == str(pin)
        )

    assert parts['U8']['props']['Manufacturer Part'] == 'CH32V003F4P6'
    assert parts['KEY1']['props']['Manufacturer Part'] == 'CH444G'
    assert parts['U6']['props']['Manufacturer Part'] == 'CH334P'
    for index, pin in enumerate([20, 1, 2, 3]):
        assert net('U8', pin) == net(f'SW{index + 1}', 1) == f'PC{index}_SWI'
        assert net(f'SW{index + 1}', 2) == 'GND'
        assert parts[f'R{index + 1}']['props']['Add into BOM'] == 'no'
        assert net('U8', 10 + index) == net(f'LED{index + 1}', 1) == f'PC{index}_LED'
        assert net(f'LED{index + 1}', 2) == net(f'R{index + 5}', 2)
        assert net(f'R{index + 5}', 1) == 'SYS_5V'
    for mcu, mux, name in [
        (16, 14, 'MUX_SEL0'),
        (17, 2, 'MUX_SEL1'),
        (19, 1, 'MUX_EN_N'),
    ]:
        assert net('U8', mcu) == net('KEY1', mux) == name
    assert net('R9', 1) == 'SYS_5V' and net('R9', 2) == 'MUX_EN_N'
    assert net('U8', 18) == net('H1', 1) == 'SWIO'
    assert net('U8', 4) == net('H1', 2) == 'NRST'
    assert net('H1', 3) == 'GND'
    return digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--netlist',
        help='optional historical 2026-10-21-2 ENET export for connectivity checks',
    )
    args = parser.parse_args()

    file_hashes = {}
    for name, expected in CURRENT_BASELINE.items():
        path = HARDWARE / name
        assert path.is_file(), f'Missing published hardware file: {path}'
        digest = sha256(path)
        assert digest == expected, f'Published hardware file changed: {name}'
        file_hashes[name] = digest

    check_firmware_masks()
    historical_digest = None
    if args.netlist:
        historical_digest = check_historical_netlist(Path(args.netlist))

    result = {
        'passed': True,
        'board': '2026-10-29',
        'published_hardware_sha256': file_hashes,
        'gpio_masks': MASKS,
        'historical_netlist_sha256': historical_digest,
        'scope': (
            'current EDA/PDF/BOM file integrity + firmware mask definitions; '
            'no matching current ENET, PCB DRC, or physical verification'
        ),
    }
    out = ROOT / 'build/hardware-pin-check.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
