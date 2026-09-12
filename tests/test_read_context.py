from contextlib import redirect_stdout, redirect_stderr
import base64
import io
import json
import shlex
import warnings
from unittest.mock import patch

from test_ytmd import Isolated, KEY, row, y


class ReadingAndEvidence(Isolated):
    def seed(self, cues=None):
        record = row(cues)
        record['chapters_json'] = json.dumps([dict(start=0, end=60, title='Introduction'), dict(start=60, end=130, title='Technique')])
        y.save(self.db(), record)
        return record

    def call(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', ResourceWarning)
            with redirect_stdout(out), redirect_stderr(err), patch.object(y, 'fetch', side_effect=AssertionError('network fetch')), patch.object(y, 'run_ytdlp', side_effect=AssertionError('yt-dlp invoked')):
                code = y.main([*args, '--json'])
        return code, out.getvalue(), err.getvalue()

    def data(self, *args):
        code, out, err = self.call(*args)
        self.assertEqual(code, 0, err)
        self.assertEqual(err, '')
        return json.loads(out)

    def test_chapter_read_has_outline_provenance_and_honest_scope(self):
        self.seed()
        data = self.data('read', KEY, '--chapter', '2')
        self.assertEqual(data['scope'], dict(start=60, end=130, chapter=2))
        self.assertEqual([p['start'] for p in data['passages']], [60, 120])
        self.assertEqual(data['chapters'][1]['number'], 2)
        self.assertEqual(data['captions'], 'manual')
        self.assertEqual(data['lang'], 'en')
        self.assertEqual(len(data['source_snapshot']), 64)
        self.assertFalse(data['has_more'])
        self.assertIsNone(data['next_cursor'])
        self.assertTrue(data['omissions']['outside_scope'])
        self.assertEqual(data['budget']['used_chars'], sum(len(p['text']) for p in data['passages']))
        self.assertTrue(all(p['url'].startswith(y.url_for(KEY)) for p in data['passages']))

    def test_pagination_is_lossless_even_for_oversized_unicode_passages(self):
        cues = [dict(start=0, end=1, text='Intro'), dict(start=60, end=100, text='Cache café 日本語. ' * 150), dict(start=120, end=125, text='End')]
        self.seed(cues)
        data = self.data('read', KEY, '--max-chars', '256')
        chunks, tokens = [], set()
        for _ in range(50):
            self.assertLessEqual(sum(len(p['text']) for p in data['passages']), 256)
            chunks.extend(p['text'] for p in data['passages'])
            if not data['has_more']:
                break
            token = data['next_cursor']
            self.assertNotIn(token, tokens)
            tokens.add(token)
            self.assertEqual(self.data('read', KEY, '--cursor', token, '--max-chars', '256'), self.data('read', KEY, '--cursor', token, '--max-chars', '256'))
            data = self.data(*shlex.split(data['next_command'])[1:-1])
            self.assertTrue(data['omissions']['before_page'])
        else:
            self.fail('Pagination did not terminate')
        self.assertEqual(''.join(chunks), ''.join(p['text'] for p in y.passages(cues)))
        self.assertGreater(len(tokens), 1)

    def test_stale_or_wrong_video_cursor_does_not_silently_resume(self):
        record = self.seed([dict(start=0, end=5, text='cache ' * 100)])
        token = self.data('read', KEY, '--max-chars', '256')['next_cursor']
        other = dict(record, id='dQw4w9WgXcQ', url=y.url_for('dQw4w9WgXcQ'))
        y.save(self.db(), other)
        code, out, err = self.call('read', other['id'], '--cursor', token)
        self.assertEqual(json.loads(err)['error']['code'], 'invalid_cursor')
        y.save(self.db(), dict(record, title='Changed metadata'))
        code, out, err = self.call('read', KEY, '--cursor', token)
        self.assertEqual(code, 1)
        self.assertEqual(out, '')
        self.assertEqual(json.loads(err)['error']['code'], 'stale_cursor')

    def test_invalid_scope_budget_and_cursor_do_not_create_a_library(self):
        invalid = [
            ('read', KEY, '--chapter', '0'), ('read', KEY, '--max-chars', '255'),
            ('read', KEY, '--max-chars', '100001'), ('read', KEY, '--chapter', '1', '--from', '0'),
            ('read', KEY, '--from', '10', '--to', '5'), ('read', KEY, '--cursor', 'bad!'),
            ('read', KEY, '--cursor', 'a' * 4097), ('read', KEY, '--cursor', 'abc', '--chapter', '1'),
            ('context', KEY), ('context', KEY, '--query', '!!!'), ('context', KEY, '--query', 'x' * 201),
            ('context', KEY, *['--query', 'cache'] * 9),
        ]
        for args in invalid:
            with self.subTest(args=args):
                code, out, err = self.call(*args)
                self.assertIn(code, (1, 2))
                self.assertEqual(out, '')
                self.assertIn('error', json.loads(err))
                self.assertFalse(y.library().exists())

    def test_cursor_defensively_rejects_bad_types_and_large_numbers(self):
        valid = dict(v=1, id=KEY, source='x', scope=dict(start=0, end=None, chapter=None), position=[0, 0])
        cases = [dict(valid, v=True), dict(valid, position=[True, 0]), dict(valid, position=[-1, 0]),
                 dict(valid, scope=dict(start=10**500, end=None, chapter=None)),
                 dict(valid, scope=dict(start=0, end=float('nan'), chapter=None)),
                 dict(valid, scope=dict(start=0, end=None, chapter='1'))]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(y.Error) as raised:
                y.decode_cursor(y.encode_cursor(value))
            self.assertEqual(raised.exception.code, 'invalid_cursor')
        token = base64.urlsafe_b64encode(('[' * 1200 + ']' * 1200).encode()).decode().rstrip('=')
        with self.assertRaises(y.Error):
            y.decode_cursor(token)

    def test_out_of_range_chapter_and_tampered_position(self):
        self.seed([dict(start=0, end=5, text='cache ' * 100)])
        code, out, err = self.call('read', KEY, '--chapter', '3')
        self.assertEqual(json.loads(err)['error']['code'], 'invalid_chapter')
        data = self.data('read', KEY, '--max-chars', '256')
        cursor = y.decode_cursor(data['next_cursor'])
        cursor['position'] = [999, 0]
        code, out, err = self.call('read', KEY, '--cursor', y.encode_cursor(cursor))
        self.assertEqual(json.loads(err)['error']['code'], 'invalid_cursor')

    def test_empty_time_window_is_not_a_whole_video_review(self):
        self.seed()
        data = self.data('read', KEY, '--from', '200', '--to', '300')
        self.assertEqual(data['passages'], [])
        self.assertFalse(data['has_more'])
        self.assertEqual(data['returned_ranges'], [])
        self.assertTrue(data['omissions']['outside_scope'])

    def test_context_multiquery_deduplicates_and_retains_query_provenance(self):
        self.seed()
        data = self.data('context', KEY, '--query', 'cache', '--query', 'invalidation', '--query', 'unicorn')
        self.assertEqual([p['start'] for p in data['evidence']], [60, 120])
        self.assertEqual(data['omissions']['unmatched_queries'], ['unicorn'])
        self.assertFalse(data['omissions']['selection_is_exhaustive'])
        self.assertEqual(len(data['retrieval_hits']), 2)
        self.assertTrue(all(set(h['queries']) == {'cache', 'invalidation'} for h in data['retrieval_hits']))
        self.assertEqual(data['evidence'][0]['chapters'], [2])
        self.assertEqual(data['budget']['used_chars'], sum(len(p['text']) for p in data['evidence']))

    def test_context_budget_explicitly_marks_clipped_and_omitted_evidence(self):
        self.seed([dict(start=0, end=5, text='cache ' * 100), dict(start=60, end=65, text='cache tail')])
        data = self.data('context', KEY, '--query', 'cache', '--max-chars', '256')
        self.assertEqual(data['budget']['used_chars'], 256)
        self.assertTrue(data['omissions']['budget_exhausted'])
        self.assertGreaterEqual(data['omissions']['partial_passages'], 1)
        self.assertTrue(any(p['partial'] for p in data['evidence']))
        self.assertIn('--max-chars 256', data['next_command'])
        self.assertIn('not necessarily included', data['coverage_note'])

    def test_context_no_matches_is_honest_and_does_not_fabricate_a_summary(self):
        self.seed()
        data = self.data('context', KEY, '--query', 'unicorn')
        self.assertEqual(data['evidence'], [])
        self.assertEqual(data['retrieval_hits'], [])
        self.assertEqual(data['omissions']['unmatched_queries'], ['unicorn'])
        self.assertIsNone(data['next_command'])
        self.assertNotIn('summary', data)

    def test_zero_duration_context_and_repeated_speech_survive(self):
        self.seed([dict(start=0, end=0, text='cache'), dict(start=60, end=60, text='cache')])
        data = self.data('context', KEY, '--query', 'cache', '--context', '0')
        self.assertEqual([p['text'] for p in data['evidence']], ['cache', 'cache'])

    def test_context_detects_concurrent_replacement(self):
        record = self.seed()
        original = y.search_results
        def replace(args):
            result = original(args)
            y.save(self.db(), dict(record, title='Replaced'))
            return result
        with patch.object(y, 'search_results', side_effect=replace):
            code, out, err = self.call('context', KEY, '--query', 'cache')
        self.assertEqual(code, 1)
        self.assertEqual(out, '')
        self.assertEqual(json.loads(err)['error']['code'], 'source_changed')

    def test_explicit_wide_scope_does_not_claim_omitted_source_text(self):
        self.seed()
        data = self.data('read', KEY, '--from', '0', '--to', '1000')
        self.assertFalse(data['omissions']['outside_scope'])
        self.assertFalse(data['has_more'])

    def test_chapter_boundary_labels_do_not_include_a_touching_next_chapter(self):
        record = self.seed([dict(start=0, end=60, text='Intro'), dict(start=60, end=70, text='Technique')])
        units = y.cited_passages(record, json.loads(record['cues_json']))
        self.assertEqual(units[0]['chapters'], [1])
        self.assertEqual(units[1]['chapters'], [2])

    def test_budget_can_change_on_resume_without_losing_text(self):
        text = 'café ' * 100
        self.seed([dict(start=0, end=10, text=text)])
        first = self.data('read', KEY, '--max-chars', '256')
        last = self.data('read', KEY, '--cursor', first['next_cursor'], '--max-chars', '1000')
        self.assertFalse(last['has_more'])
        self.assertEqual(''.join(p['text'] for p in first['passages'] + last['passages']), text)
        self.assertTrue(last['passages'][0]['partial'])
        self.assertEqual(last['passages'][0]['text_from'], 256)

    def test_context_matching_modes_stay_explicit(self):
        self.seed()
        self.assertEqual(self.data('context', KEY, '--query', 'cache unicorn')['evidence'], [])
        self.assertTrue(self.data('context', KEY, '--query', 'cache unicorn', '--match', 'any')['evidence'])
        self.assertTrue(self.data('context', KEY, '--query', 'cache invalidation', '--match', 'phrase')['evidence'])

    def test_invalid_stored_id_cannot_become_a_continuation_command(self):
        for key in (None, 'x; echo unsafe', y.url_for(KEY)):
            with self.subTest(key=key), self.assertRaises(y.Error) as raised:
                y.source_metadata(dict(id=key))
            self.assertEqual(raised.exception.code, 'invalid_video')

    def test_human_budgeted_output_labels_partial_text_and_omissions(self):
        self.seed([dict(start=0, end=5, text='cache ' * 100)])
        for args in [('read', KEY), ('context', KEY, '--query', 'cache')]:
            with self.subTest(args=args):
                result = self.cli(*args, '--max-chars', '256')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('partial text 0:256', result.stdout)
                self.assertIn('Omissions:', result.stdout)
                self.assertIn('Next:', result.stdout)

    def test_existing_show_is_still_unpaginated_and_new_commands_parse(self):
        self.seed([dict(start=0, end=5, text='cache ' * 2000)])
        self.assertGreater(len(self.data('show', KEY)['passages'][0]['text']), 8000)
        self.assertTrue(self.data('read', KEY)['has_more'])
        self.assertIn('--chapter', self.cli('help', 'read').stdout)
        self.assertIn('--query', self.cli('help', 'context').stdout)
