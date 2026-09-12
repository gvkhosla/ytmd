#!/usr/bin/env python3
"""Offline retrieval checks. Does not run or grade a model's answer quality."""
from importlib.machinery import SourceFileLoader
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def evaluate():
    loader = SourceFileLoader('ytmd_eval', str(ROOT / 'ytmd'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    cli = importlib.util.module_from_spec(spec)
    loader.exec_module(cli)
    cases = json.loads((ROOT / 'evals/cases.json').read_text())
    video = cases['video']
    reports = []
    with tempfile.TemporaryDirectory(prefix='ytmd-eval-') as tmp:
        # Only this module's library function is redirected; the user's environment/library stays untouched.
        cli.library = lambda: Path(tmp)
        conn = cli.connect()
        try:
            cli.save(conn, dict(id=video['id'], title=video['title'], channel=video['channel'],
                url=cli.url_for(video['id']), uploaded_at='', duration_s=video['duration_s'],
                description='Synthetic evaluation, not a real video.', captions='manual', lang='en',
                ingested_at='2026-01-01T00:00:00Z', transcript=cli.transcript(video['cues']),
                cues_json=json.dumps(video['cues']), raw_captions=json.dumps(video['cues']),
                caption_format='json3', chapters_json=json.dumps(video['chapters'])))
        finally:
            conn.close()
        for task in cases['tasks']:
            command = [sys.executable, str(ROOT / 'ytmd'), 'context', video['id'], '--max-chars', '4000', '--json']
            for query in task['queries']:
                command += ['--query', query]
            result = subprocess.run(command, capture_output=True, text=True, env=dict(os.environ, YTMD_DIR=tmp))
            data = json.loads(result.stdout) if result.returncode == 0 else {}
            quotes = data.get('evidence', [])
            text = '\n'.join(q['text'] for q in quotes)
            missing = [phrase for phrase in task['required_evidence'] if phrase not in text]
            faithful = all(any(q['text'] == cue['text'][q['text_from']:q['text_to']] and q['start'] == cue['start'] and q['end'] == cue['end'] and q['url'] == cli.url_for(video['id'], cue['start']) for cue in video['cues']) for q in quotes)
            unmatched = data.get('omissions', {}).get('unmatched_queries', [])
            passed = result.returncode == 0 and not missing and faithful and sum(len(q['text']) for q in quotes) <= 4000 and all(q in unmatched for q in task.get('unmatched_queries', []))
            reports.append(dict(task=task['id'], retrieval_passed=passed, missing_evidence=missing,
                                faithful_quotes=faithful, excerpt_chars=sum(len(q['text']) for q in quotes),
                                retrieval_calls=1, agent_answer_quality='not_evaluated', error=result.stderr))
    return reports


if __name__ == '__main__':
    reports = evaluate()
    print(json.dumps(dict(fixture='synthetic', results=reports, agent_answer_quality='not_evaluated'), indent=2))
    sys.exit(0 if all(r['retrieval_passed'] for r in reports) else 1)
