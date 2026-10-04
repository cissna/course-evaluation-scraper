import unittest
from unittest.mock import patch
from backend.instructor_names import recorded_instructor_names
from backend.result_service import cached_professor_result, cached_course_result
from backend.percentiles import build_benchmark
from backend.app import app


class ResultTests(unittest.TestCase):
    def test_recorded_names_keep_variants_and_support_explicit_team_lists(self):
        self.assertEqual(recorded_instructor_names({'instructor_name': 'Jane Smith & J. Smith'}), ['J. Smith', 'Jane Smith'])
        self.assertEqual(recorded_instructor_names({'instructor_name': 'Smith, Jane'}), ['Smith, Jane'])
        self.assertEqual(recorded_instructor_names({'instructor_names': ['Jane Smith', 'J. Smith', 'Jane Smith']}), ['J. Smith', 'Jane Smith'])

    @patch('backend.result_service.course_refresh_status', side_effect=lambda code: {'course_code': code})
    @patch('backend.result_service.db_utils.get_professor_records')
    def test_professor_scope_excludes_other_teachers_even_when_courses_are_grouped(self, records, status):
        records.return_value = [
            ('EN.601.415.01.SP25', 'EN.601.415', {'instructor_name': 'Jane Smith', 'course_name': 'Databases'}),
            ('EN.601.615.01.SP25', 'EN.601.615', {'instructor_name': 'J. Smith', 'course_name': 'Databases'}),
            ('EN.601.415.01.FA25', 'EN.601.415', {'instructor_name': 'Jane Smith & Dana Lee', 'course_name': 'Databases'}),
        ]
        result = cached_professor_result('Jane Smith')
        instances = result['raw_data']['instances']
        self.assertEqual(len(instances), 2)
        self.assertNotIn('EN.601.615.01.SP25', instances)
        self.assertEqual(result['refresh']['courses'], [{'course_code': 'EN.601.415'}])
        self.assertEqual(instances['EN.601.415.01.FA25']['source_evaluation_id'], 'EN.601.415.01.FA25')

    @patch('backend.result_service.course_refresh_status', side_effect=lambda code: {'course_code': code})
    @patch('backend.result_service.db_utils.get_records_for_courses')
    def test_cached_course_preserves_source_ids_and_grouping(self, records, status):
        records.return_value = [
            ('EN.553.431.01.SP25', 'EN.553.431', {'course_name': 'Honors Mathematical Statistics'}),
            ('EN.553.631.01.SP25', 'EN.553.631', {'course_name': 'Mathematical Statistics'}),
        ]
        result = cached_course_result('EN.553.431')['raw_data']
        self.assertTrue(result['grouping_metadata']['is_grouped'])
        self.assertEqual(result['metadata']['current_name'], 'Honors Mathematical Statistics')
        self.assertEqual(list(result['instances']), ['EN.553.431.01.SP25', 'EN.553.631.01.SP25'])

    def test_benchmark_weights_responses_within_course_groups_and_courses_equally(self):
        records = [
            ('EN.553.431.01.SP20', 'EN.553.431', {'overall_quality_frequency': {'Excellent': 1}}),
            ('EN.553.631.01.SP25', 'EN.553.631', {'overall_quality_frequency': {'Poor': 3}}),
            ('AS.180.101.01.SP25', 'AS.180.101', {'overall_quality_frequency': {'Good': 100, 'N/A': 40}}),
        ]
        result = build_benchmark(records, generated_at='test')
        self.assertEqual(result['metrics']['overall_quality']['scores'], [2, 4])
        self.assertEqual(result['years'], [2020, 2025])
        self.assertEqual(result['metrics']['workload']['scores'], [])

    @patch('backend.app.find_professors_by_name_db', return_value={'results': [{'name': 'Jane Smith'}], 'total_count': 1})
    @patch('backend.app.find_courses_by_name_with_details', return_value={'results': [{'course_code': 'AS.180.101'}], 'total_count': 1})
    def test_search_keeps_counts_for_both_types(self, courses, professors):
        response = app.test_client().get('/api/search?q=Smith&limit=20')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['courses']['total_count'] + response.json['professors']['total_count'], 2)

    def test_invalid_course_cannot_trigger_scrape(self):
        with patch('backend.app.refresh_course') as refresh:
            self.assertEqual(app.test_client().post('/api/recheck/not-a-code').status_code, 400)
            refresh.assert_not_called()


if __name__ == '__main__':
    unittest.main()
