import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_pack import (AuditError, Conflict, build_pack, canonical, delta,
                               element_index, file_info, model_hash, model_summary,
                               read_json, verify_pack, wall_geometry, assert_public,
                               public_value, scan_public_pack, semantic_delta)


def wall(guid, begin, end):
    return {'guid': guid, 'type': 'Wall', 'homeStory': 0,
            'placement': {'referenceGeometry': {'begin': {'x': begin, 'y': 0},
                'end': {'x': end, 'y': 0}, 'arcAngle': 0, 'height': 3,
                'thickness': 0.2, 'bottomOffsetFromHomeStory': 0}},
            'properties': {'fireRating': 'fixture-only'},
            'materialBindings': {'structureType': 0}, 'bodies': []}


class AuditPackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source, self.first, self.second = wall('A', 0, 1), wall('B', 1, 2), wall('C', 2, 2.5)
        self.before = {'elements': [self.source], 'materials': [], 'stories': [], 'counts': {'elements': 1}}
        self.after = {**self.before, 'elements': [self.source, self.first], 'counts': {'elements': 2}}
        self.final = {**self.before, 'elements': [self.source, self.first, self.second], 'counts': {'elements': 3}}
        self.specs = []
        for name, data in [('initial', self.before), ('before', self.before), ('after', self.after)]:
            self.write(name+'.json', data)
            self.specs.append({'id': name, **file_info(self.root, name+'.json')})
        self.write('compact.json', {'sourceGuid': 'A', 'createdGuid': 'B', 'length': 1.0,
                                  'jointDistance': 0.0, 'elementCountBefore': 1, 'elementCountAfter': 2})
        self.contract = {'schemaVersion': 1, 'goalId': 'fixture-goal', 'modelIdentity': 'fixture',
            'initial': 'initial', 'snapshots': self.specs,
            'iterations': [{'iteration': 1, 'before': 'before', 'after': 'after',
                'sourceGuid': 'A', 'createdGuid': 'B', 'expectedLength': 1,
                'expectedAddedCount': 1, 'compactEvidence': [file_info(self.root, 'compact.json')]}],
            'requireDependency': True}

    def write(self, name, data):
        (self.root/name).write_bytes(canonical(data)+b'\n')

    def build(self, name='pack'):
        build_pack(self.root, self.contract, self.root/name)
        return self.root/name

    def update_after(self, data):
        self.write('after.json', data)
        self.contract['snapshots'][-1].update(file_info(self.root, 'after.json'))

    def add_second(self):
        for name, data in [('before2', self.after), ('after2', self.final)]:
            self.write(name+'.json', data)
            self.specs.append({'id': name, **file_info(self.root, name+'.json')})
        self.contract['iterations'].append({'iteration': 2, 'before': 'before2', 'after': 'after2',
            'sourceGuid': 'B', 'createdGuid': 'C', 'expectedLength': 0.5, 'expectedAddedCount': 1})

    def test_deterministic_extraction_all_bytes(self):
        a, b = self.build('a'), self.build('b')
        self.assertEqual({p.relative_to(a): p.read_bytes() for p in a.rglob('*.json')},
                         {p.relative_to(b): p.read_bytes() for p in b.rglob('*.json')})

    def test_summary_counts_and_totals(self):
        summary, _ = model_summary(self.after, 'fixture')
        self.assertEqual(summary['elementCount'], 2)
        self.assertEqual(summary['typeCounts'], {'Wall': 2})
        self.assertEqual(summary['materialsCount'], 0)

    def test_whole_model_index_hashes_existing_groups_only(self):
        rows = element_index(self.after)
        self.assertEqual([r['guid'] for r in rows], ['A', 'B'])
        self.assertIn('propertiesHash', rows[0])
        self.assertIn('geometryHash', rows[0])
        self.assertNotIn('bbox', rows[0])
        absent = copy.deepcopy(self.before)
        del absent['elements'][0]['properties']
        self.assertNotIn('propertiesHash', element_index(absent)[0])

    def test_exact_added_guid(self):
        d = delta(element_index(self.before), element_index(self.after))
        self.assertEqual(d['added'], ['B'])
        self.assertEqual(d['unchangedCount'], 1)

    def test_removed_detection(self):
        self.assertEqual(delta(element_index(self.after), element_index(self.before))['removed'], ['B'])

    def test_changed_detection_includes_property_change(self):
        changed = copy.deepcopy(self.after)
        changed['elements'][0]['properties']['fireRating'] = 'changed'
        self.assertEqual(delta(element_index(self.after), element_index(changed))['changed'], ['A'])

    def test_exact_full_objects_extracted(self):
        p = self.build()
        self.assertEqual(read_json(p/'iteration-1/source-wall.json'), self.source)
        self.assertEqual(read_json(p/'iteration-1/created-wall.json'), self.first)

    def test_wall_geometry_recomputed(self):
        g = wall_geometry(self.source, self.first)
        self.assertEqual(g['length'], 1)
        self.assertTrue(g['computedFromDump'])
        self.assertTrue(g['sameDirection'])
        self.assertEqual(g['createdFields']['height'], 3)

    def test_joint_distance_computation(self):
        g = wall_geometry(self.source, wall('B', 1.25, 2.25))
        self.assertEqual(g['jointDistance'], 0.25)

    def test_dependency_equality(self):
        self.add_second()
        p = self.build()
        d = read_json(p/'dependency-check.json')
        self.assertTrue(d['equal'])
        self.assertEqual(d['dependencies'][0]['iteration2SourceGuid'], 'B')

    def test_dependency_mismatch_fails(self):
        self.add_second()
        self.contract['iterations'][1]['sourceGuid'] = 'A'
        with self.assertRaises(Conflict):
            self.build()

    def test_source_sha_mismatch_modified_value(self):
        modified = copy.deepcopy(self.after)
        modified['elements'][1]['placement']['referenceGeometry']['height'] = 4
        self.write('after.json', modified)
        with self.assertRaisesRegex(AuditError, 'SHA/size mismatch'):
            self.build()
        self.assertFalse((self.root/'pack/source.json').exists())

    def test_tampered_audit_file(self):
        p = self.build()
        (p/'iteration-1/created-wall.json').write_bytes(b'{}\n')
        with self.assertRaisesRegex(AuditError, 'manifest SHA/size mismatch'):
            verify_pack(self.root, p)

    def test_self_consistent_tampered_file_recomputed(self):
        p = self.build()
        name = 'iteration-1/created-wall.json'
        (p/name).write_bytes(b'{}\n')
        m = read_json(p/'audit-pack-manifest.json')
        for e in m['files']:
            if e['path'] == name:
                e.update(file_info(p, name))
        (p/'audit-pack-manifest.json').write_bytes(canonical(m)+b'\n')
        with self.assertRaises(Conflict):
            verify_pack(self.root, p)

    def test_wrong_created_guid(self):
        self.contract['iterations'][0]['createdGuid'] = 'ABSENT'
        with self.assertRaisesRegex(AuditError, 'GUID absent'):
            self.build()

    def test_two_unexpected_additions(self):
        data = copy.deepcopy(self.after)
        data['elements'].append(wall('EXTRA', 9, 10))
        data['counts']['elements'] = 3
        self.update_after(data)
        with self.assertRaisesRegex(Conflict, 'exactly one'):
            self.build()

    def test_compact_full_conflict(self):
        self.write('compact.json', {'length': 99})
        self.contract['iterations'][0]['compactEvidence'] = [file_info(self.root, 'compact.json')]
        with self.assertRaisesRegex(Conflict, 'Compact/full mismatch'):
            self.build()

    def test_manifest_verification_all_files(self):
        p = self.build()
        self.assertEqual(verify_pack(self.root, p)['status'], 'PASS')
        m = read_json(p/'audit-pack-manifest.json')
        for e in m['files']:
            self.assertEqual(e['sha256'], hashlib.sha256((p/e['path']).read_bytes()).hexdigest())
            self.assertTrue(e['sourceDumpRefs'])

    def test_unlisted_extra_file_fails(self):
        p = self.build()
        (p/'extra.json').write_text('{}')
        with self.assertRaisesRegex(AuditError, 'file set mismatch'):
            verify_pack(self.root, p)

    def test_duplicate_guids_fail_closed(self):
        with self.assertRaises(AuditError):
            element_index({'elements': [self.source, self.source]})

    def test_duplicate_json_keys_fail_closed(self):
        self.write('bad.json', {})
        (self.root/'bad.json').write_text('{"elements":[],"elements":[1]}')
        with self.assertRaises(AuditError):
            read_json(self.root/'bad.json')

    def test_model_hash_compatible_order_timing_rule(self):
        changed = copy.deepcopy(self.after)
        changed['elements'].reverse()
        # Timing was absent in the original and is excluded in both inputs.
        changed['nativeSeconds'] = 999
        self.assertEqual(model_hash(changed), model_hash(self.after))

    def test_index_deduplicated_between_identical_snapshots(self):
        p = self.build()
        before = read_json(p/'before/model-summary.json')
        initial = read_json(p/'initial/model-summary.json')
        self.assertEqual(before['elementIndex'], initial['elementIndex'])

    def test_nonempty_output_not_overwritten(self):
        self.build()
        with self.assertRaises(AuditError):
            self.build()

    def test_path_traversal_rejected(self):
        self.contract['snapshots'][0]['path'] = '../outside.json'
        with self.assertRaises(AuditError):
            self.build()

    def test_changed_neighbour_full_records(self):
        neighbour = {'guid': 'N', 'type': 'Object', 'properties': {'value': 1}}
        self.before['elements'].append(neighbour)
        self.before['counts']['elements'] = 2
        self.after['elements'].append({**neighbour, 'properties': {'value': 2}})
        self.after['counts']['elements'] = 3
        for spec, data in zip(self.specs, [self.before, self.before, self.after]):
            self.write(spec['path'], data)
            spec.update(file_info(self.root, spec['path']))
        self.contract['iterations'][0]['compactEvidence'] = []
        p = self.build()
        records = read_json(p/'iteration-1/changed-elements.json')
        self.assertEqual(records[0]['before'], neighbour)
        self.assertEqual(records[0]['after']['properties']['value'], 2)
        fields = read_json(p/'iteration-1/changed-fields.json')
        self.assertEqual(fields['elements'][0]['changedPaths'], ['properties.value'])
        self.assertFalse(fields['onlyNativeBodyIndexChanges'])

    def test_reported_count_conflict(self):
        self.after['counts']['elements'] = 99
        self.update_after(self.after)
        with self.assertRaises(Conflict):
            self.build()

    def test_fingerprint_conflict(self):
        self.write('fingerprint.json', {'modelIdentity': 'fixture', 'modelHash': 'wrong', 'elementCount': 1})
        self.specs[0]['fingerprint'] = file_info(self.root, 'fingerprint.json')
        with self.assertRaisesRegex(Conflict, 'fingerprint mismatch'):
            self.build()

    def test_readback_conflict(self):
        self.contract['historicalStage'] = 3
        self.write('readback.json', self.before)
        self.specs.append({'id': 'observation-003', **file_info(self.root, 'readback.json')})
        with self.assertRaisesRegex(Conflict, 'Read-back differs'):
            self.build()

    def test_manifest_tampering_recomputed(self):
        p = self.build()
        m = read_json(p/'audit-pack-manifest.json')
        m['files'][0]['sourceDumpRefs'] = ['wrong-source.json']
        (p/'audit-pack-manifest.json').write_bytes(canonical(m)+b'\n')
        with self.assertRaises(Conflict):
            verify_pack(self.root, p)

    def test_invalid_contract_lengths(self):
        for value in (True, 0, -1, float('nan'), float('inf')):
            with self.subTest(value=value):
                self.contract['iterations'][0]['expectedLength'] = value
                with self.assertRaises(AuditError):
                    self.build()

    def test_typed_action_conflict(self):
        self.write('compact.json', {'typedRequest': {'sourceGuid': 'WRONG', 'length': 1}})
        self.contract['iterations'][0]['compactEvidence'] = [file_info(self.root, 'compact.json')]
        with self.assertRaises(Conflict):
            self.build()


    def test_public_scan_missing_or_empty_pack_fails(self):
        for p in (self.root/'missing', self.root/'empty'):
            if p.name == 'empty':
                p.mkdir()
            with self.assertRaises(AuditError):
                scan_public_pack(p)

    def test_public_scan_keys_fail_closed(self):
        with self.assertRaises(AuditError):
            assert_public({'/tmp/private': 'value'})

    def test_public_scan_windows_paths(self):
        for value in (r'C:\Users\Alice\model.pln', 'D:/archive/model.pln', 'see C:/tmp/x'):
            with self.subTest(value=value), self.assertRaises(AuditError):
                assert_public({'source': value})

    def test_public_scan_unix_paths(self):
        for value in ('/home/alice/model.pln', '/tmp/model.pln', 'archive: /var/data/x'):
            with self.subTest(value=value), self.assertRaises(AuditError):
                assert_public(value)

    def test_public_scan_unc_and_rooted_windows(self):
        for value in (r'\\host\share\model.pln', '//host/share/model.pln', r'\Users\Alice\x', r'\archive\x'):
            with self.subTest(value=value), self.assertRaises(AuditError):
                assert_public(value)

    def test_public_scan_relative_user_and_home_paths(self):
        for value in ('Users/Alice/model.pln', 'home/alice/model.pln', '~/x', '%USERPROFILE%/x', '$HOME/x'):
            with self.subTest(value=value), self.assertRaises(AuditError):
                assert_public(value)

    def test_public_safe_relative_paths_and_url(self):
        assert_public({'source': 'outputs/stage/model.json', 'url': 'https://github.com/owner/repo'})

    def test_public_identity_provenance_round_trip(self):
        identity = 'C:/Users/Alice/model.pln'
        self.contract['modelIdentity'] = identity
        self.write('identity.json', {'result': {'addOnCommandResponse': {'projectPath': identity}}})
        self.contract['identityEvidence'] = file_info(self.root, 'identity.json')
        p = self.build()
        c = read_json(p/'source.json')['contract']
        self.assertEqual(c['modelIdentity'], public_value(identity))
        self.assertEqual(c['identityEvidence'], self.contract['identityEvidence'])
        self.assertEqual(verify_pack(self.root, p)['status'], 'PASS')
        self.assertEqual(scan_public_pack(p)['status'], 'PASS')

    def test_public_identity_mismatch_still_fails(self):
        self.contract['modelIdentity'] = 'C:/Users/Alice/model.pln'
        self.write('identity.json', {'result': {'addOnCommandResponse': {'projectPath': 'D:/other.pln'}}})
        self.contract['identityEvidence'] = file_info(self.root, 'identity.json')
        with self.assertRaises(Conflict):
            self.build()

    def test_nested_source_metadata_and_properties_sanitized(self):
        self.contract['metadata'] = {'source': ['/home/alice/archive']}
        self.first['properties']['sourcePath'] = 'C:/Users/Alice/x'
        self.update_after(self.after)
        p = self.build()
        self.assertEqual(scan_public_pack(p)['status'], 'PASS')
        self.assertEqual(read_json(p/'iteration-1/created-wall.json')['properties']['sourcePath'],
                         public_value('C:/Users/Alice/x'))
        self.assertEqual(verify_pack(self.root, p)['status'], 'PASS')

    def test_verifier_rejects_escaped_json_local_path(self):
        p = self.build()
        (p/'iteration-1/created-wall.json').write_text(json.dumps({'source': '/tmp/x'}))
        with self.assertRaisesRegex(AuditError, 'local user path'):
            verify_pack(self.root, p)

    def test_semantic_native_body_index_only_is_noise(self):
        c = {'changed': ['N'], 'unchangedCount': 2}
        semantic_delta(c, [{'guid': 'N', 'changedPaths': ['bodies[0].nativeBodyIndex', 'bodies[12].nativeBodyIndex']}])
        self.assertEqual(c['rawChanged'], ['N'])
        self.assertEqual(c['semanticChanged'], [])
        self.assertEqual(c['technicalNoiseChanged'], ['N'])
        self.assertEqual(c['semanticUnchangedCount'], 3)

    def test_semantic_mixed_and_nonbody_index_remain_changes(self):
        for paths in (['bodies[0].nativeBodyIndex', 'properties.value'],
                      ['properties.nativeBodyIndex'], ['bodies[0].nested.nativeBodyIndex'],
                      ['bodies'], ['bodies[0].vertices[0].x']):
            with self.subTest(paths=paths):
                c = {'changed': ['N'], 'unchangedCount': 0}
                semantic_delta(c, [{'guid': 'N', 'changedPaths': paths}])
                self.assertEqual(c['semanticChanged'], ['N'])
                self.assertEqual(c['rawChanged'], ['N'])

    def test_semantic_delta_published_end_to_end(self):
        neighbour = {'guid': 'N', 'type': 'Object', 'bodies': [{'nativeBodyIndex': 1, 'vertices': [1, 2]}]}
        self.before['elements'].append(neighbour)
        self.before['counts']['elements'] = 2
        changed = copy.deepcopy(neighbour)
        changed['bodies'][0]['nativeBodyIndex'] = 7
        self.after['elements'].append(changed)
        self.after['counts']['elements'] = 3
        for spec, data in zip(self.specs, [self.before, self.before, self.after]):
            self.write(spec['path'], data)
            spec.update(file_info(self.root, spec['path']))
        self.contract['iterations'][0]['compactEvidence'] = []
        p = self.build()
        d = read_json(p/'iteration-1/before-after-delta.json')
        self.assertEqual(d['changed'], ['N'])
        self.assertEqual(d['rawChanged'], ['N'])
        self.assertEqual(d['semanticChanged'], [])
        self.assertEqual(read_json(p/'iteration-1/changed-elements.json')[0]['before'], neighbour)
        self.assertEqual(verify_pack(self.root, p)['status'], 'PASS')

    def test_published_historical_packs_have_no_local_paths(self):
        root = Path(__file__).resolve().parents[1]
        for pack in ('outputs/closed-loop-stage1/audit-pack', 'outputs/closed-loop-stage3/run-002/audit-pack'):
            self.assertEqual(scan_public_pack(root/pack)['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
