# From a video to something useful

ytmd supplies source evidence. Your existing agent explains it at the depth your task needs.
These workflows work in Pi, Codex, or Claude Code with the installed skill. Replace `URL` and
`VIDEO_ID` with your requested video; `read` and `context` operate on saved captions only.

## 1. Understand before investing an hour

**Ask your agent**

> Help me decide whether this video is relevant to reducing database load in my app: URL.
> Explain the central idea, when it applies, and what it doesn't solve. Keep the first answer
> concise, but include the important qualifications and timestamps. Tell me what you actually read.

**Retrieval route**

```bash
ytmd add "URL" --json
ytmd info VIDEO_ID --json
ytmd read VIDEO_ID --chapter 1 --max-chars 4000 --json
```

The agent uses the outline to choose further chapters or queries; chapter 1 alone is not a review
of the whole talk. If there are no chapters, it uses bounded sequential reads or time windows.

**Authored reference response using the synthetic cache fixture—not a real video summary**

> Relevant if your endpoint repeats database reads and tolerates some stale data. The technique
> does not repair an inefficient underlying query ([fixture 0:00](../evals/cases.json)).
> Baseline measurement and stale-data eligibility are prerequisites, and authorization decisions
> are explicitly excluded ([fixture 1:00](../evals/cases.json)). There is no promised speedup;
> the workload must be benchmarked ([fixture 6:00](../evals/cases.json)).
>
> A useful next step is to examine eligibility before the rollout procedure. This is a selective
> overview of the cited fixture passages, not a full review.

## 2. Learn a technique well enough to perform it

**Ask your agent**

> Teach me the technique in this video: URL. Include prerequisites, the sequence of steps,
> a worked example, failure modes, and how I'd know it worked. Read beyond search hits when
> needed. Clearly label any implementation detail you add that the speaker didn't provide.

**Retrieval route**

```bash
ytmd add "URL" --json
ytmd info VIDEO_ID --json
ytmd read VIDEO_ID --chapter 2 --max-chars 8000 --json
```

Follow the returned `next_command` until the selected scope is exhausted. Read prerequisites and
exceptions in other chapters as needed. To review the whole saved transcript, omit `--chapter`
and follow every page. A completed scope does not prove captions are complete or correct.

**Authored reference response using the synthetic fixture**

1. Measure baseline latency/errors; confirm the endpoint permits data up to thirty seconds old.
   Do not use this recipe for authorization ([fixture 1:00](../evals/cases.json)).
2. Shadow reads, compare cached/uncached responses, then enable five percent of traffic behind a
   reversible flag ([fixture 2:00](../evals/cases.json)).
3. For the inventory-preview example, thirty seconds is illustrative, not a universal TTL
   ([fixture 3:00](../evals/cases.json)).
4. If errors rise by more than one percentage point above baseline, disable the flag, restore
   uncached reads, and continue monitoring ([fixture 4:00](../evals/cases.json)).
5. **Suggested validation, not a speaker quote:** define the measurement interval and comparison
   workload before running this experiment. The source does not specify them or a vendor SDK.

The numerical choices above belong to this synthetic lesson; they are not universal operational advice.

## 3. Apply ideas to your constraints

**Ask your agent**

> Help me use this video to improve our multi-tenant inventory preview endpoint: URL.
> Inspect the relevant code, explain which ideas fit our constraints, and propose concrete
> changes with tests and rollback conditions. Separate source guidance from your adaptations.
> Don't edit code until I approve the plan.

**Retrieval route (keywords supplied by the agent)**

```bash
ytmd add "URL" --json
ytmd context VIDEO_ID --query "inventory" --query "tenant" --query "rollback" --max-chars 8000 --json
```

The result includes source metadata, an outline, evidence quotes, query-hit navigation hints,
excerpt budgets, and omissions. It is not a generated answer. Search is lexical: the agent may
need different terms or chapter reads to find missing context.

**Authored reference response using the synthetic fixture**

> **Source guidance:** stale-data tolerance must be established before adopting the TTL example;
> tenant IDs belong in cache keys, and two tenants requesting the same resource ID should be
> tested ([fixture 3:00 and 5:00](../evals/cases.json)). Rollback guidance appears at
> [fixture 4:00](../evals/cases.json).
>
> **Adaptation to investigate:** inspect where this endpoint constructs keys and whether the
> tests exercise identical resource IDs under different tenants. Add an isolation test if missing.
> I have not inspected your repository yet, so this is a proposed investigation—not a claim that
> your code has a defect or that a change has been implemented.

## What is actually measured?

The reference responses above are authored examples, not scored model outputs. Run
`python3 evals/run.py` for offline retrieval checks. Use the [evaluation rubric](../evals/README.md)
to assess real agent answers, including unsupported questions and critical exceptions.

Character budgets apply to quoted text, not total JSON or model tokens. Partial quotes keep their
source passage's timestamps. Citation links let the user inspect the source; they do not make an
interpretation correct by themselves.
