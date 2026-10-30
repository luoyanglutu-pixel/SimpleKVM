"""Run actual C key/switch/health code via a host DLL.

No target MMIO, USB host, or physical time is simulated by these tests.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'firmware/App'
LIB = None
GAP, SETTLE, ACTIVE, FAULT = range(4)
NONE = 255
DEFAULT = 3


def load_core(clang):
    out = ROOT / 'build/host'
    out.mkdir(parents=True, exist_ok=True)
    dll = out / 'kvm_core.dll'
    sources = [APP / x for x in ['key.c', 'switch_ctrl.c', 'health.c', 'runtime.c']]
    if Path(clang).name.lower() == 'tcc.exe':
        # Keep command arguments ASCII: TinyCC 0.9.27 uses ANSI file APIs.
        cmd = [clang, '-shared', '-Wall', '-Werror', '-I', 'firmware/App',
               *[x.relative_to(ROOT).as_posix() for x in sources],
               'tests/mock_board.c', '-o', 'build/host/kvm_core.dll']
    else:
        cmd = [clang, '--target=x86_64-pc-windows-msvc', '-fuse-ld=lld', '-shared',
               '-nostdlib', '-O2', '-std=c11', '-Wall', '-Wextra', '-Werror',
               '-fno-builtin', '-fno-stack-protector', '-I', str(APP),
               *map(str, sources), str(ROOT/'tests/mock_board.c'),
               '-Wl,/noentry', '-o', str(dll)]
    subprocess.run(cmd, check=True, cwd=ROOT)
    lib = ctypes.CDLL(str(dll))
    for name, count in [('test_reset',1), ('test_tick',2), ('test_request',2),
                        ('test_poll',1), ('test_corrupt',3),
                        ('test_inject_failure',1), ('test_get',1),
                        ('test_event',2), ('test_health',3), ('test_clear_events',0)]:
        fn = getattr(lib, name)
        fn.argtypes = [ctypes.c_uint32] * count
        fn.restype = ctypes.c_uint32 if name in {
            'test_tick','test_request','test_get','test_event','test_health'} else None
    return lib, cmd


class Behavior(unittest.TestCase):
    def setUp(self):
        LIB.test_reset(0)

    def get(self, field): return LIB.test_get(field)

    def tick_range(self, start, stop, mask):
        return [LIB.test_tick(t & 0xffffffff, mask) for t in range(start, stop+1)]

    def ready(self):
        self.tick_range(0, 103, 0)
        self.assertEqual((self.get(0), self.get(1), self.get(8)),
                         (ACTIVE, DEFAULT, DEFAULT))

    def events(self):
        return [tuple(LIB.test_event(i, f) for f in range(3))
                for i in range(self.get(9))]

    def tearDown(self):
        self.assertEqual(self.get(10), 0, 'mock observed unsafe select/enable or log overflow')

    def test_boot_disconnect_select_settle_connect_order(self):
        LIB.test_poll(100)
        self.assertEqual((self.get(0), self.get(6), self.get(8)), (GAP, 1, NONE))
        LIB.test_poll(101)
        self.assertEqual((self.get(0), self.get(6)), (SETTLE, 1))
        LIB.test_poll(102)
        self.assertEqual(self.get(6), 1)
        LIB.test_poll(103)
        self.assertEqual((self.get(0), self.get(1), self.get(8)),
                         (ACTIVE, DEFAULT, DEFAULT))
        self.assertEqual(self.events(), [(0,1,1),(0,2,NONE),
                         (101,3,DEFAULT),(103,4,DEFAULT),(103,2,DEFAULT)])

    def test_all_twelve_directed_transitions(self):
        for source in range(4):
            for target in range(4):
                if source == target: continue
                LIB.test_reset(0)
                LIB.test_request(1, source)
                LIB.test_poll(102); LIB.test_poll(104)
                LIB.test_clear_events()
                LIB.test_request(200, target)
                LIB.test_poll(300)
                self.assertEqual(self.get(6), 1)
                LIB.test_poll(301); LIB.test_poll(303)
                self.assertEqual((self.get(1), self.get(8)), (target,target))
                self.assertEqual(self.events(), [(200,1,1),(200,2,NONE),
                    (301,3,target),(303,4,target),(303,2,target)])

    def test_duplicate_active_target_never_toggles_data(self):
        self.ready(); LIB.test_clear_events()
        self.assertEqual(LIB.test_request(104,DEFAULT), 1)
        LIB.test_poll(500)
        self.assertEqual(self.events(), [])
        self.assertEqual(self.get(4), 1)

    def test_keys_each_map_to_target_once(self):
        for target in range(4):
            LIB.test_reset(0); self.ready()
            events = self.tick_range(104, 140, 1 << target)
            self.assertEqual([e for e in events if e != NONE], [target])
            self.tick_range(141, 250, 1 << target)
            self.assertEqual((self.get(1),self.get(8)),(target,target))

    def test_twenty_ms_threshold_and_bounce(self):
        self.ready()
        for t in range(104,124):
            self.assertEqual(LIB.test_tick(t, 2 if t % 2 == 0 else 0), NONE)
        self.tick_range(124,143,2)
        self.assertEqual(self.get(2), DEFAULT)
        self.assertEqual(LIB.test_tick(144,2),1)

    def test_short_pulse_ignored(self):
        self.ready()
        self.assertTrue(all(e == NONE for e in self.tick_range(104,122,8)))
        self.tick_range(123,150,0)
        self.assertEqual(self.get(4), 1)

    def test_long_press_ten_seconds_does_not_repeat(self):
        self.ready()
        events = self.tick_range(104,10104,4)
        self.assertEqual([e for e in events if e != NONE],[2])
        self.assertEqual((self.get(4),self.get(1)),(2,2))

    def test_release_requires_full_stable_interval(self):
        self.ready(); self.tick_range(104,124,2)
        self.tick_range(125,143,0)
        self.assertTrue(all(e==NONE for e in self.tick_range(144,190,8)))
        self.tick_range(191,211,0)
        self.assertEqual(LIB.test_tick(212,8), NONE)
        self.assertEqual(LIB.test_tick(232,8), NONE)  # gap invalidates stability
        self.assertTrue(all(e==NONE for e in self.tick_range(233,252,8)))
        self.tick_range(253,273,0)
        self.assertEqual(self.tick_range(274,294,8)[-1],3)

    def test_held_during_boot_is_not_a_request(self):
        self.tick_range(0,200,2)
        self.assertEqual((self.get(1),self.get(4)),(DEFAULT,1))
        self.tick_range(201,221,0)
        self.assertEqual(self.tick_range(222,242,2)[-1],1)

    def test_multikey_overlap_locks_until_all_released(self):
        self.ready()
        LIB.test_tick(104,2); LIB.test_tick(105,6)
        self.assertTrue(all(e==NONE for e in self.tick_range(106,150,2)))
        self.assertEqual(self.get(2),DEFAULT)
        self.tick_range(151,171,0)
        self.assertEqual(self.tick_range(172,192,4)[-1],2)

    def test_second_key_after_first_event_does_not_fire(self):
        self.ready(); self.tick_range(104,124,2)
        self.tick_range(125,140,6)
        self.assertTrue(all(e==NONE for e in self.tick_range(141,180,4)))
        self.assertEqual(self.get(2),1)

    def test_sample_gap_never_fabricates_stability(self):
        self.ready(); LIB.test_tick(104,8)
        self.assertEqual(LIB.test_tick(200,8),NONE)
        self.assertTrue(all(e==NONE for e in self.tick_range(201,240,8)))
        self.tick_range(241,261,0)
        self.assertEqual(self.tick_range(262,282,8)[-1],3)

    def test_gap_request_overrides_old_pending(self):
        self.ready(); LIB.test_clear_events()
        LIB.test_request(200,1); LIB.test_request(300,3)
        LIB.test_poll(301); self.assertEqual(self.get(0),GAP)
        LIB.test_poll(401); LIB.test_poll(403)
        self.assertEqual([e[2] for e in self.events() if e[1]==4],[3])

    def test_settle_request_overrides_old_pending(self):
        self.ready(); LIB.test_clear_events()
        LIB.test_request(200,1); LIB.test_poll(301)
        LIB.test_request(302,2); LIB.test_poll(303)
        self.assertEqual(self.get(6),1)
        LIB.test_poll(403); LIB.test_poll(405)
        self.assertEqual([e[2] for e in self.events() if e[1]==4],[2])

    def test_key_event_wins_on_old_settle_deadline(self):
        self.ready(); self.tick_range(104,123,0)
        LIB.test_request(124,1)
        self.tick_range(124,206,0)
        self.tick_range(207,226,8)  # request matures at 227, old SETTLE deadline
        self.assertEqual(self.get(0),SETTLE)
        LIB.test_clear_events()
        self.assertEqual(LIB.test_tick(227,8),3)
        self.assertEqual((self.get(0),self.get(6),self.get(2)),(GAP,1,3))
        self.assertFalse(any(e[1]==4 for e in self.events()))

    def test_overdue_poll_cannot_skip_settle(self):
        LIB.test_poll(5000)
        self.assertEqual((self.get(0),self.get(6)),(SETTLE,1))
        LIB.test_poll(5000); LIB.test_poll(5001)
        self.assertEqual(self.get(6),1)
        LIB.test_poll(5002); self.assertEqual(self.get(6),0)

    def test_timer_wrap_switch_and_key(self):
        origin = 0xfffffff0
        LIB.test_reset(origin)
        self.tick_range(origin,origin+103,0)
        self.assertEqual((self.get(0),self.get(1)),(ACTIVE,DEFAULT))
        self.assertEqual(self.tick_range(origin+104,origin+124,8)[-1],3)
        self.tick_range(origin+125,origin+227,8)
        self.assertEqual(self.get(1),3)

    def test_invalid_target_fault_is_sticky(self):
        self.ready(); self.assertEqual(LIB.test_request(200,4),0)
        self.assertEqual((self.get(0),self.get(6),self.get(8)),(FAULT,1,NONE))
        self.assertEqual(self.get(3),1)
        self.assertEqual(LIB.test_request(201,0),0)
        LIB.test_poll(1000); self.assertEqual(self.get(6),1)
        self.assertEqual(self.get(3),1)

    def test_corrupted_states_cannot_connect(self):
        for state,pending,active in [(99,0,NONE),(GAP,4,NONE),
                                     (SETTLE,255,NONE),(ACTIVE,1,0)]:
            LIB.test_reset(0); LIB.test_corrupt(state,pending,active)
            LIB.test_poll(200)
            self.assertEqual((self.get(0),self.get(6),self.get(8)),(FAULT,1,NONE))

    def test_hardware_refusal_is_safe(self):
        for failure in (1,2):
            LIB.test_reset(0); LIB.test_inject_failure(failure)
            LIB.test_poll(101); LIB.test_poll(103)
            self.assertEqual((self.get(0),self.get(6),self.get(8),self.get(3)),
                             (FAULT,1,NONE,3))

    def test_watchdog_requires_new_tick_and_both_tasks(self):
        self.assertEqual(LIB.test_health(0,1,1),0)
        self.assertEqual(LIB.test_health(1,0,1),0)
        self.assertEqual(LIB.test_health(1,1,0),0)
        self.assertEqual(LIB.test_health(1,1,1),1)
        self.assertEqual(LIB.test_health(1,1,1),0)
        self.assertEqual(LIB.test_health(2,1,1),1)
        LIB.test_reset(0xffffffff)
        self.assertEqual(LIB.test_health(0,1,1),1)

    def test_no_watchdog_approval_after_fault(self):
        self.ready(); LIB.test_request(104,99)
        previous=self.get(11)
        self.tick_range(104,150,0)
        self.assertEqual(self.get(11),previous)

    def test_random_trace_preserves_disconnect_before_select(self):
        rng=random.Random(0x334444)
        for now in range(1,10001):
            LIB.test_clear_events()
            if rng.randrange(8)==0: LIB.test_request(now,rng.randrange(4))
            LIB.test_tick(now,rng.randrange(16))
            self.assertNotEqual(self.get(0),FAULT)
            if self.get(0)==ACTIVE:
                self.assertEqual((self.get(6),self.get(8)),(0,self.get(1)))
            else:
                self.assertEqual((self.get(6),self.get(8)),(1,NONE))


def main():
    global LIB
    parser=argparse.ArgumentParser()
    config=ROOT/'tools/local_config.json'
    local=json.loads(config.read_text('utf-8')) if config.exists() else {}
    parser.add_argument('--clang','--cc',dest='clang',default=os.environ.get('KVM_HOST_CC') or local.get('host_cc') or shutil.which('clang'))
    args=parser.parse_args()
    if not args.clang: parser.error('Provide --clang PATH (Windows clang + lld required)')
    LIB,command=load_core(args.clang)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Behavior)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    record={'tests':result.testsRun,'passed':result.wasSuccessful(),
            'failures':len(result.failures),'errors':len(result.errors),
            'compiler_command':command,'scope':'actual C core behavior; no target MMIO or USB hardware validation'}
    tracked=[APP/x for x in ['key.c','key.h','switch_ctrl.c','switch_ctrl.h',
                              'health.c','health.h','app_config.h','board.h','runtime.c']]
    tracked += [ROOT/'tests/mock_board.c', Path(__file__).resolve()]
    record['source_sha256']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in tracked}
    (ROOT/'build/host/test-result.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    return 0 if result.wasSuccessful() else 1

if __name__=='__main__': sys.exit(main())
