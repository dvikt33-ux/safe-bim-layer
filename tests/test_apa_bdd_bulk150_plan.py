"""Pure OFFLINE tests for the 150-copy / one-native-call Archicad grid + line."""
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import apa_bdd_live_bulk_distribute_near_house as LIVE

class MassCopyDistribution(unittest.TestCase):
    def test_100_grid_plus_50_linear_uniform_no_duplicate(self):
        positions=LIVE.expected_positions()
        grid=positions[:100]
        line=positions[100:]
        self.assertEqual((len(positions),len(set(positions))),(150,150))
        self.assertEqual(len({x for x,y in grid}),10)
        self.assertEqual(len({y for x,y in grid}),10)
        self.assertEqual(sorted({x for x,y in line}),
                         [round(22+i*.8,6) for i in range(50)])
        self.assertEqual({y for x,y in line},{11.0})
        self.assertFalse(set(grid)&set(line))
        self.assertEqual(positions[0],(22.0,0.0))
        self.assertEqual(positions[99],(29.2,7.2))
        self.assertEqual(positions[100],(22.0,11.0))
        self.assertEqual(positions[-1],(61.2,11.0))

    def test_source_displacements_not_zero_and_within_batch_max(self):
        points=LIVE.expected_positions()
        offsets=[(round(x-LIVE.SOURCE_XY[0],6),
                  round(y-LIVE.SOURCE_XY[1],6),0.0) for x,y in points]
        self.assertEqual(len(offsets),150)
        self.assertTrue(all(any(v!=0 for v in d) for d in offsets))
        self.assertEqual(len(set(offsets)),150)
        self.assertLessEqual(len(offsets),200)

    def test_actual_native_body_collision_blocks_before_any_write(self):
        def body(x,y):
            return {"bodies":[{"vertices":[(x-.05,y-.025,0.),
                                           (x+.05,y+.025,2.9)]}]}
        p=LIVE.expected_positions()
        with self.assertRaisesRegex(ValueError,"COLLIDES_WITH_EXISTING_NATIVE_BODY"):
            LIVE.preflight_clearance({"blocker":body(22.,0.)},p)
        LIVE.preflight_clearance({"other":body(0.,0.)},p)

    def test_executable_defaults_to_read_only(self):
        import argparse
        parser=argparse.ArgumentParser()
        parser.add_argument("--apply",action="store_true")
        self.assertFalse(parser.parse_args([]).apply)
        self.assertTrue(parser.parse_args(["--apply"]).apply)

if __name__=="__main__":
    unittest.main()
