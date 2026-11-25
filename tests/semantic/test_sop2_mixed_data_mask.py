"""A SOP2 data result reads a compare mask as a complete scalar word."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from support import rdna2spirv, translate_lines
from spirv_mini_interp import run_workgroup

FIXTURE = HERE / "fixtures" / "sop2_mixed_data_mask.asm"


class TestSop2MixedDataMask(unittest.TestCase):
    def check_result(self, size, wave, op, data, mask, expected, emulate=False):
        compare_dst = "s20" if wave == 32 else "s[20:21]"
        source = FIXTURE.read_text(encoding="utf-8").replace("v_cmp_eq_u32_e64 s20,", f"v_cmp_eq_u32_e64 {compare_dst},")
        source = source.replace("s_or_b32 s30, s4, s20", f"{op} s30, s4, {mask}")
        lines = source.splitlines()
        if wave == 64:
            lines.insert(0, "s_mov_b64 exec, -1")
        header = bytes(0x138) + struct.pack("<4I", 0x8090, size, 1, 1)
        with patch.object(rdna2spirv, "WAVE64_EMULATE", emulate):
            module = translate_lines("cs_sop2_mixed_data_mask", lines, fssm=header)
            self.assertEqual(rdna2spirv.translate.last_gen.wave64, wave == 64)
            self.assertEqual(rdna2spirv.translate.last_gen.emulate, emulate)
        subgroup = 32 if emulate else wave
        mem = run_workgroup(
            module, size, subgroup,
            inputs_for=lambda i: {"%wg_id": (0, 0, 0), "%local_id": (i, 0, 0), "%sg_lane": i % subgroup},
            push_constants=[0, 0, 0xFFFFFFFF, 0x31016FAC, data] + [0] * 27,
            memory={},
        )
        self.assertEqual([(mem[8 * i], mem[8 * i + 4]) for i in range(size)],
                         [(expected, 7 if expected else 0)] * size)

    def test_wave32_reads_the_mask_word_for_scalar_bitwise_ops(self):
        for size in (8, 32):
            for op, data, expected in (("s_or_b32", 0xD4718F66, 0xD4718F67),
                                       ("s_and_b32", 2, 0),
                                       ("s_and_b32", 1, 1)):
                with self.subTest(size=size, op=op, data=data):
                    self.check_result(size, 32, op, data, "s20", expected)

    def test_partial_wave64_data_result_sets_scc_even_with_no_upper_lanes(self):
        self.check_result(20, 64, "s_or_b32", 0x80000000, "s21", 0x80000000)

    def test_emulated_wave64_gathers_the_full_scalar_source(self):
        self.check_result(40, 64, "s_or_b32", 0xD4718F66, "s20", 0xD4718F67, emulate=True)


if __name__ == "__main__":
    unittest.main()
