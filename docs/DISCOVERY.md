# Help the right people discover ytmd

## Position around the job

**Use what you learn from YouTube.**

Supporting explanation: **Timestamped evidence and chapter reads for understanding, learning,
and applying videos with your existing Pi, Codex, or Claude Code agent.**

Keep the technical keywords people actually search for—YouTube captions/transcripts, agent skill,
CLI, local Markdown—but do not lead with storage as the benefit. Do not imply ytmd independently
produces AI answers or supports caption-less videos.

## Baseline observed before the v0.5 release

The public GitHub API reported the description “YouTube → local transcript. One CLI, markdown +
SQLite, built for coding agents.”, a correct homepage URL, no repository topics, zero stars, and
zero forks. Those are a point-in-time observation, not proof of demand or user count. Release
payload downloads are not unique installations, and stars aren't activation.

The existing site already had static agent instructions, pinned installation, copy buttons,
canonical/share metadata, and GitHub Pages. The largest gaps were the outcome-led message,
end-to-end examples, and distribution—not another install command.

## What v0.5 prepares

- Outcome-led README, site, and share descriptions.
- A copyable video + task prompt, rather than only “save this transcript”.
- Three concrete workflows (understand, learn, apply), explicitly labelled synthetic reference responses.
- Goal-aware agent skill and plain-text guide, with citations, depth, and omissions explained.
- Evaluation commands plus an honest distinction between retrieval checks and unscored agent quality.
- Homepage sitemap and structured software metadata. These help machines understand the page;
  they do not guarantee indexing, rich results, or discovery. GitHub project-page robots rules
  are controlled at the origin root; no misleading project-local robots.txt is added.

## Highest-impact next distribution work

| Priority | Action | Why / measure |
| --- | --- | --- |
| 1 | Update GitHub About to “Use YouTube videos with your agent: local captions, chapter reads, and timestamped evidence for understanding and action.” | Match the repo's first impression to the site. Check homepage/description consistency. |
| 1 | Add accurate repository topics: youtube, transcript, ai-agents, agent-skills, claude-code, codex, cli, sqlite, python | Make intent and compatibility searchable. Avoid irrelevant tags. |
| 1 | Record one 60–90 second real-task demo: video + goal → evidence → useful explanation/action plan → timestamp check | Show usefulness, not terminal scrolling. Use material you may share and remove private project details. |
| 2 | Publish three short walkthroughs, one per intent, with an actual supported video and a concrete task | Give people a page they can find and copy. Synthetic examples demonstrate shape but aren't proof of real-video performance. |
| 2 | Share each walkthrough with the relevant agent community and explain limitations | Earn adoption through a working workflow. Follow community promotion rules; don't mass-post. |
| 2 | Check compatible agent-skill directories and submit the skill with its CLI prerequisites clearly stated | Target people who already have an agent. Verify each directory's current submission/install requirements first. |
| 3 | Offer a friend a cold install and task; observe where they stop | Measure first successful cited answer, time-to-useful-output, errors, and whether they return for a second video. |
| 3 | Submit the canonical site/sitemap in an owner-controlled search console | Only after ownership verification; don't promise search rankings. |

GitHub metadata edits, directory submissions, recordings, and social posts are follow-up actions,
not silently performed by the release. A browser UI for people without an agent is a separate
product decision; validate the current agent-native workflow before building it.

## Suggested demo script

1. “I want to use this talk to improve X—not just summarize it.”
2. Paste one video URL and one concrete goal into an existing agent.
3. Briefly show the outline and bounded evidence. Don't make the audience watch every CLI call.
4. Show prerequisites, an actionable recommendation, and an important exception.
5. Open one cited timestamp and verify the claim.
6. Show one labelled adaptation and one missing detail the agent did not invent.
7. End with the website's copyable setup/task prompt and the available-captions limitation.

Do not present an authored or synthetic response as a measured agent result. A compelling demo
can also show an honest “the video doesn't specify that”.

## A small launch experiment

Over one week, invite a handful of relevant users to try the three workflows. Track voluntarily
reported: install completed, first cited answer, task accomplished, missing detail, and repeat use.
Use GitHub's aggregate traffic/referrers and release download counts as directional evidence only.
No telemetry or analytics is installed by v0.5. Ask before adding it and minimize collection.

The main metric is **a user does something useful with a video's information at the depth they need**.
Acquisition without that activation is not product progress.
