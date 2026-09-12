#!/usr/bin/env python3
"""Render the checked-in examples as static HTML; no browser fetch or build dependency."""
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '    <!-- BEGIN VIDEO EXAMPLES -->'
END = '    <!-- END VIDEO EXAMPLES -->'


def clock(seconds):
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours}:{minutes:02}:{seconds:02}' if hours else f'{minutes}:{seconds:02}'


def render():
    data = json.loads((ROOT / 'examples/videos.json').read_text())
    lines = [BEGIN, '    <section id="use" aria-label="Real video examples">']
    for category, heading in [('technical', 'For builders'), ('business', 'For business')]:
        lines += [f'      <section class="video-group" aria-labelledby="{category}-title">',
                  f'        <h2 id="{category}-title">{heading}</h2>', '        <div class="video-grid">']
        for video in data['videos']:
            if video['category'] != category:
                continue
            key = escape(video['id'])
            url = 'https://www.youtube.com/watch?v=' + key
            lines += [f'          <article class="video" aria-labelledby="task-{key}">',
                      f'            <a class="thumbnail" href="{url}" aria-label="Watch {escape(video["title"])} on YouTube">',
                      f'              <img src="./assets/videos/{key}.jpg" width="320" height="180" loading="lazy" decoding="async" alt="">',
                      '              <svg class="play" viewBox="0 0 32 32" width="32" height="32" aria-hidden="true"><path d="M12 8l13 8-13 8z"/></svg>',
                      f'              <span class="duration" aria-hidden="true">{clock(video["duration_s"])}</span>', '            </a>',
                      f'            <p class="byline">{escape(video["byline"])}</p>',
                      f'            <h3 id="task-{key}">{escape(video["task"])}</h3>',
                      f'            <p class="result">{escape(video["result"])}</p>',
                      f'            <details class="plan" id="plan-{key}">',
                      '              <summary>See the plan &amp; sources</summary>',
                      '              <p class="plan-label">Suggested next steps</p>', '              <ol>']
            lines += [f'                <li>{escape(step)}</li>' for step in video['plan']]
            lines += ['              </ol>', f'              <div class="evidence" id="evidence-{key}" tabindex="-1">',
                      f'                <p class="source-title"><a href="{url}">{escape(video["title"])}</a></p>']
            for excerpt in video['evidence']:
                time = clock(excerpt['start'])
                lines += [f'                <blockquote><p><q>{escape(excerpt["quote"])}</q> <a class="citation" href="{url}&amp;t={int(excerpt["start"])}s" aria-label="Watch source at {time}">{time}</a></p></blockquote>']
            caption = 'Automatic captions; may contain errors.' if video['captions'] == 'auto' else 'Creator-provided captions; may contain errors.'
            lines += [f'                <p class="coverage">{escape(video["coverage"])} {caption}</p>',
                      '              </div>', '            </details>', '          </article>']
        lines += ['        </div>', '      </section>']
    lines += [f'      <p class="example-note">{escape(data["note"])}</p>', '    </section>', END]
    return '\n'.join(lines)


if __name__ == '__main__':
    output = render()
    if '--check' in sys.argv:
        html = (ROOT / 'site/index.html').read_text()
        if output not in html:
            raise SystemExit('Video examples are stale. Render tools/render_examples.py and replace the marked block.')
        print('Static video examples match examples/videos.json')
    elif '--write' in sys.argv:
        path = ROOT / 'site/index.html'
        html = path.read_text()
        start = html.index(BEGIN)
        end = html.index(END, start) + len(END)
        path.write_text(html[:start] + output + html[end:])
        print('Updated the static video examples block')
    else:
        print(output)
