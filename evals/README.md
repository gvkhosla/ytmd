# Does ytmd help someone do something useful?

There are two different questions. Do not conflate them:

1. **Retrieval correctness:** did the CLI supply relevant, faithful, budgeted source material?
2. **Answer usefulness:** did an agent turn that evidence into the understanding/action the user needs?

## Automated, offline baseline

```bash
python3 evals/run.py
python3 -m unittest discover -s tests -v
```

`cases.json` contains authored **synthetic material**, not a transcript of a real YouTube video.
Its identifiers are fixture IDs. Never fetch them from YouTube or publish an answer implying those
videos exist. No user's private transcript library is copied, indexed, or published by these checks.

The runner seeds a temporary library, retrieves evidence for five tasks (overview, learn, apply,
qualify, unsupported), and checks required passages, literal source quotes, timestamp links,
excerpt budgets, and explicit unmatched queries. It reports call counts and excerpt characters.
It does **not** run an LLM or claim a model-quality score. `agent_answer_quality: not_evaluated`
is intentional. The tests exercise CLI behavior; the curated keyword choices are not a benchmark
of an agent's ability to formulate queries.

## Manual agent evaluation

For each task in `cases.json`, give an agent the goal, the synthetic source material, and the current
skill. Let it choose its retrieval route; record its commands, returned evidence, and final answer.
For a real-video evaluation, use captions you are allowed to use, review the full relevant source
first, and keep private videos, transcripts, and project details local. Do not publish them by default.

Record agent/model/version, skill commit, task, source snapshot, commands/calls, excerpt characters,
answer, and reviewer comments. Score each dimension 0 (fails), 1 (partial), 2 (strong):

| Dimension | What a strong answer does |
| --- | --- |
| Goal fit | Answers the actual question at useful depth, rather than producing a generic summary |
| Actionability / understanding | Gives ordered steps or the argument's reasoning; includes a worked example and a check when the goal calls for them |
| Fidelity and attribution | Backs important source claims with read passages; labels interpretations and adaptations; does not invent speaker instructions |
| Conditions and scope | Retains prerequisites, exceptions, uncertainty, and actual reading scope; acknowledges missing details |
| Efficiency | Makes the first response useful, uses bounded retrieval, and offers relevant deeper branches without unnecessary transcript dumps |

Suggested gate: **8/10 or better**, with no fabricated material source claim, no unlabelled synthetic
source, and no false claim of a full-video review. Those failures override the numerical score.
A short answer is not automatically efficient if it omits the details needed to act.

## Required challenge cases

- **Overview:** identify both relevance and the important limits; no promised speedup.
- **Learn:** include baseline measurement, eligibility, staged rollout, monitoring, and rollback.
- **Apply:** honor stale-data constraints and tenant isolation; distinguish source instructions from adaptations.
- **Qualify:** reject the authorization-cache use case despite an attractive performance benefit.
- **Unsupported:** acknowledge the source does not recommend an SDK; don't attribute invented code to it.

Add real user tasks over time, including different vocabulary, non-English captions, missing chapters,
contradictory arguments, and deliberately small budgets. Keep a held-out set so tuning a workflow does
not amount to memorizing the evaluation queries. Report source coverage, not just keyword recall.

## Current status

The automated retrieval baseline is executable. [Authored workflow examples](../examples/README.md)
show intended answer shape. **No agent answer-quality benchmark has been run or scored yet.**
