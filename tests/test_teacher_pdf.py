"""Guard the object and source boundaries of the full-PDF extraction pass."""

import copy
import unittest

from chuchariot.dataset_io import ROOT, read_json
from chuchariot.queries import KnowledgeStore
from chuchariot.preview import preview_data
from chuchariot.validation import validate
from scripts.extract_teacher_pdf_v05 import build


class TeacherPdfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.ontology, cls.summary = build()
        cls.entities = {e['id']: e for e in cls.data['entities']}

    def measurements(self, owner):
        return {e['measurement']['quantity']: e['measurement'] for e in self.data['entities']
                if e['kind'] == 'Measurement' and e['scope_id'] == owner}

    def test_fifth_batch_keeps_previous_records_unchanged(self):
        base = read_json(ROOT / 'data/candidates/wheel-axle.v0.4.json')
        for key in ['entities', 'facts', 'evidence', 'model_mappings']:
            self.assertEqual(self.data[key][:len(base[key])], base[key])
        self.assertEqual(validate(self.data, self.ontology), [])

    def test_same_number_is_not_the_same_artifact(self):
        self.assertNotEqual(self.entities['specimen:ch13-yoke']['id'], self.entities['specimen:002']['id'])
        self.assertEqual(self.measurements('specimen:ch13-yoke')['通宽']['value'], 49)
        self.assertEqual(self.measurements('specimen:002')['通长']['value'], 272)
        self.assertEqual(self.measurements('specimen:ch14-beam')['残长']['value'], 136)
        self.assertEqual(self.measurements('specimen:ch14-trace')['可见部分长']['value'], 177)

    def test_unnumbered_axle_does_not_overwrite_reference_or_target(self):
        self.assertEqual(self.measurements('record:p04-unnumbered-axle')['通长']['value'], 276)
        self.assertEqual(self.measurements('specimen:002')['通长']['value'], 272)
        self.assertEqual(self.measurements('object:001'), {})
        self.assertEqual(self.entities['record:p04-unnumbered-axle']['kind'], 'ReferenceRecord')

    def test_wheel_parts_own_their_dimensions_and_range(self):
        self.assertEqual(self.measurements('component:ch15-rim')['牙高']['value'], 6.7)
        self.assertEqual(self.measurements('component:ch15-spoke-inner')['厚']['value'], 1.4)
        self.assertEqual(self.measurements('component:ch15-spoke-outer')['直径']['value'], 2.9)
        height = self.measurements('component:ch15-hub-ridges')['高']
        self.assertEqual((height['min'], height['max']), (.4, .6))
        self.assertTrue(self.measurements('specimen:ch11-trace')['宽']['approximate'])

    def test_mass_and_statistics_are_not_length_measurements(self):
        self.assertTrue(all(e['measurement']['unit'] == 'cm' for e in self.entities.values() if e['kind'] == 'Measurement'))
        weight = [f for f in self.data['facts'] if f['subject_id'] == 'specimen:003' and f['predicate'] == 'HAS_MASS_RECORD']
        self.assertIn('是否包含所配辖', weight[0]['value'])
        counts = [f for f in self.data['facts'] if f['subject_id'] == 'record:hemp-trace-count' and f['predicate'] == 'HAS_RECORDED_QUANTITY']
        self.assertEqual(counts[0]['value'], '5根')

    def test_joint_and_pin_cannot_cross_specimen_scope(self):
        for predicate in ['TENON_JOINT_WITH', 'HAS_ASSOCIATED_COMPONENT']:
            with self.subTest(predicate=predicate):
                wrong = copy.deepcopy(self.data)
                fact = next(f for f in wrong['facts'] if f['predicate'] == predicate)
                fact['object_id'] = 'component:001'
                errors = validate(wrong, self.ontology)
                self.assertTrue(any('跨标本' in e or '归属于当前标本' in e for e in errors), errors)

    def test_inference_and_heading_only_terms_do_not_become_artifacts(self):
        inferred = [f for f in self.data['facts'] if f['origin'] == 'inferred']
        self.assertTrue(any('推测' in f.get('value', '') for f in inferred))
        self.assertTrue(all(f['rationale'] for f in inferred))
        self.assertEqual([f for f in self.data['facts'] if f['subject_id'] == 'object:001' and f['predicate'] == 'HAS_PART'], [])
        self.assertTrue(all(f['review_status'] == 'pending' for f in self.data['facts']))
        self.assertNotIn('觼軜', [e['label'] for e in self.data['entities']])

    def test_confirmed_projection_hides_new_measurement_values(self):
        snapshot = KnowledgeStore(self.data, self.ontology).snapshot()
        self.assertEqual(snapshot['facts'], [])
        self.assertEqual(snapshot['evidence'], [])
        self.assertTrue(all('measurement' not in e for e in snapshot['entities'] if e['kind'] == 'Measurement'))

    def test_checked_excerpts_cover_all_source_pages_with_explicit_gaps(self):
        self.assertEqual({row['pdf_page'] for row in self.summary['coverage'].values()}, set(range(1, 10)))
        self.assertTrue(any(x['page'] == 10 and x['item'] == '空白页' for x in self.summary['exclusions']))
        old = len(read_json(ROOT / 'data/candidates/wheel-axle.v0.4.json')['evidence'])
        self.assertTrue(all(e['source_id'] == 'source:001' for e in self.data['evidence'][old:]))

    def test_fifth_batch_media_resolves_to_its_own_source_page(self):
        paths = (ROOT/'data/candidates/teacher-pdf.v0.5.json', ROOT/'data/ontology/ontology.v0.3.json')
        snapshot = preview_data(*paths, review=True, media_manifest=ROOT/'data/sources/fusion-media.v0.5.json')
        clip = next(item for item in snapshot['media'] if item['id'] == 'media:pdf-wheel-details')
        self.assertEqual(clip['pdf_page'], 6)
        self.assertIn('component:ch15-hub', clip['entity_ids'])
        self.assertNotIn('object:001', clip['entity_ids'])
        hidden = preview_data(*paths, media_manifest=ROOT/'data/sources/fusion-media.v0.5.json')
        self.assertEqual(hidden['media'], [])


if __name__ == '__main__':
    unittest.main()
