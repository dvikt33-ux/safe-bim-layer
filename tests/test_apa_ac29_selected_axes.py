"""Sparse named-axis placements use the existing original native route."""
import copy,unittest
from test_apa_ac29_mass_request import M,A,request,router

def task():
    t=request(False);t['request']='Распределить копии по выбранным пересечениям осей'
    t['placements']=dict(mode='AXIS_INTERSECTIONS',sourceRef=t['sourceRef'],
        X=[dict(id='1',coordinate=10),dict(id='2',coordinate=23),dict(id='3',coordinate=47)],
        Y=[dict(id='А',coordinate=8),dict(id='Б',coordinate=19)],
        reference=dict(x=0,y=0,z=0),requiresNativeAxisObjects=False,
        selectedIntersections=[dict(X='3',Y='Б'),dict(X='1',Y='А'),dict(X='2',Y='Б')])
    return t

class SelectedAxesTests(unittest.TestCase):
    def test_sparse_selection_preserves_requested_order_labels_and_nonuniform_coordinates(self):
        t=task();before=copy.deepcopy(t)
        result=A.prepare_auto_optimized_native_task(router(),t)
        ops=result['selectedNativeTaskPreview']['workflow']['graph']['operations']
        self.assertEqual(len(ops),1);self.assertEqual(ops[0]['command'],'MoveElements')
        rows=ops[0]['params']['elementsWithMoveVectors']
        # The strategy may canonicalize operation order. Match exact vector set.
        self.assertEqual({(r['moveVector']['x'],r['moveVector']['y']) for r in rows},{(47,19),(10,8),(23,19)})
        self.assertTrue(all(r['copy'] for r in rows))
        refs=result['placementReferences']
        self.assertEqual([(r['X'],r['Y']) for r in refs['intersections']],[('3','Б'),('1','А'),('2','Б')])
        self.assertFalse(refs['nativeAxisObjectsCreated']);self.assertEqual(t,before)

    def test_unknown_duplicate_empty_and_malformed_pairs_fail(self):
        for pairs in ([],None,[dict(X='missing',Y='А')],[dict(X='1',Y='А')]*2,
                      [dict(X='1',Y='А',Z='bad')],[dict(X=1,Y='А')]):
            with self.subTest(pairs=pairs):
                t=task();t['placements']['selectedIntersections']=pairs
                with self.assertRaises(ValueError):M.normalize_mass_request(t)

    def test_sparse_subset_of_large_grid_does_not_generate_unrequested_copies(self):
        t=task();t['placements']['X']=[dict(id=str(i),coordinate=100+i*7) for i in range(32)]
        t['placements']['Y']=[dict(id=str(i),coordinate=200+i*11) for i in range(32)]
        t['placements']['selectedIntersections']=[dict(X='1',Y='2'),dict(X='31',Y='30')]
        self.assertEqual(len(M.normalize_mass_request(t)['targets']),2)
        del t['placements']['selectedIntersections']
        with self.assertRaisesRegex(ValueError,'CAPACITY'):M.normalize_mass_request(t)

    def test_all_intersections_and_axis_line_are_existing_compatible_modes(self):
        t=task();del t['placements']['selectedIntersections']
        self.assertEqual(len(M.normalize_mass_request(t)['targets']),6)
        t['placements']['Y']=t['placements']['Y'][:1]
        self.assertEqual(len(M.normalize_mass_request(t)['targets']),3)

    def test_native_axis_creation_and_unverified_reference_still_fail(self):
        t=task();t['placements']['requiresNativeAxisObjects']=True
        with self.assertRaisesRegex(ValueError,'OWN_VERIFIER'):M.normalize_mass_request(t)
        t=task();t['placements']['reference']['x']=1
        with self.assertRaisesRegex(ValueError,'REFERENCE_MUST_MATCH'):M.normalize_mass_request(t)

    def test_ambiguous_axis_labels_and_duplicate_coordinates_rejected(self):
        for row in (dict(id=' 1 ',coordinate=11),dict(id='1',coordinate=11),dict(id='other',coordinate=10)):
            t=task();t['placements']['X'].append(row)
            with self.assertRaisesRegex(ValueError,'UNIQUE'):M.normalize_mass_request(t)

if __name__=='__main__':unittest.main()
