"""Finite-line placement contract and original selector integration; no native writes."""
import copy,unittest
from test_apa_ac29_mass_request import request,router,M,A


def task():
    t=request(False)
    t['request']='Распределить колонны по конечной линии'
    t['placements']=dict(mode='LINE_SEGMENT',count=3,start=dict(x=10,y=20,z=0),
                         end=dict(x=30,y=40,z=0),reference=dict(x=0,y=0,z=0))
    return t


class SegmentTests(unittest.TestCase):
    def test_diagonal_includes_both_endpoints_with_equal_intervals(self):
        t=task();original=copy.deepcopy(t)
        result=A.prepare_auto_optimized_native_task(router(),t)
        ops=result['selectedNativeTaskPreview']['workflow']['graph']['operations']
        self.assertEqual(len(ops),1)
        self.assertEqual(ops[0]['command'],'MoveElements')
        rows=ops[0]['params']['elementsWithMoveVectors']
        self.assertEqual(len(rows),3)
        self.assertEqual([r['moveVector'] for r in rows],
                         [dict(x=10,y=20,z=0),dict(x=20,y=30,z=0),dict(x=30,y=40,z=0)])
        self.assertTrue(all(r['copy'] is True for r in rows))
        self.assertEqual(t,original)

    def test_reverse_direction_and_fractional_pitch(self):
        t=task();t['placements'].update(count=4,start=dict(x=11,y=0,z=0),end=dict(x=1,y=0,z=0))
        self.assertEqual([r['dx'] for r in M.placement_offsets(t['placements'])],[11,7.666667,4.333333,1])

    def test_count_is_new_positions_not_source_plus_copies(self):
        t=task();t['placements'].update(count=2)
        result=M.normalize_mass_request(t)
        self.assertEqual(len(result['targets']),2)
        self.assertEqual(result['targets'][0]['anchor'],dict(x=10,y=20,z=0))

    def test_source_reference_must_be_actual_first_prototype(self):
        t=task();t['placements']['reference']['x']=1
        with self.assertRaisesRegex(ValueError,'REFERENCE_MUST_MATCH'):M.normalize_mass_request(t)

    def test_invalid_layouts_fail_closed(self):
        for change in (
            dict(count=True),dict(count=1),dict(count=201),dict(start=dict(x=float('nan'),y=0,z=0)),
            dict(end=dict(x=10,y=20,z=0)),dict(end=dict(x=20,y=30,z=1)),
            dict(start=dict(x=0,y=0,z=0)),dict(extra='inferred'),dict(reference=dict(x=10001,y=0,z=0))):
            with self.subTest(change=change):
                t=task();t['placements'].update(change)
                with self.assertRaises(ValueError):M.normalize_mass_request(t)

    def test_existing_group_line_uses_one_native_group_command(self):
        t=request(True);t['placements']=task()['placements']
        result=A.prepare_auto_optimized_native_task(router(),t)
        self.assertEqual(result['requiredRuntimeCommands'],['AddOn.TapirCommand.CloneNativeGroupV1'])
        self.assertEqual(result['groupedTargetCount'],6)
        self.assertEqual(result['nativeCallCountIfAuthorized'],1)


if __name__=='__main__':unittest.main()
