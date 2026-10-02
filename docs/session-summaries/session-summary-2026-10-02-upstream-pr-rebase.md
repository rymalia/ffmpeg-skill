---
session_id: 18b5e10e-6085-48d6-b1cc-7495651d4170
date: 2026-10-02
time: "2:38 AM PDT – 5:06 AM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
related_pr: "301, 302, 303, 304, 305, 306"
---

# Session summary: rebasing the six upstream PRs onto 2.4.0 and opening them

## Overview

Upstream (`kajisho5/ffmpeg-skill`) released 2.4.0 with two new PRs, #299 and #300, after the PR split from 2026-09-30. This session rebased all six PR branches onto it and fixed A's commit message. It also scrubbed the working-note references, private labels and premature "2.4" version claims that two independent reviewers found. The user then opened the PRs as #301–#306, with D (#306) as a draft.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **A's "WHOSHOWS UP?" wording was clarified, not "fixed" with a newline** | The text was correct, but it left out that the wrapper broke the title as `"WHO\nSHOWS UP?"`. Without that step, the missing space read like a typo. Fixed in the plan doc, A's commit message and A's CHANGELOG bullet. |
| **Rebase every branch onto `upstream/main` (`9392328`) before pushing** | All six branches conflicted with the new upstream in `CHANGELOG.md`, and B also conflicted in `join.py`. Unrebased, GitHub would have shown all six PRs as conflicting. |
| **CHANGELOG resolution: each commit's own Unreleased bullets plus upstream's released sections** | Upstream's release automation had moved the old Unreleased bullet into 2.4.0, so that bullet is dropped. A script did this for every conflicting commit. Afterwards, every branch's bullets were checked against its backup. |
| **B × #300 in `join.py`: B's `lens = [clip_length(...)]`, then #300's `place_silent(lens, d)`** | B's single length per clip is what the concat filter now uses to place clips, so #300's `at`/`end` became accurate for plain cuts too. Codex confirmed this by static reading. B's commit message and PR description say so. |
| **"2.4" labels became "Unreleased — …" headings, and the version tags were dropped** | 2.4.0 shipped without these features. Upstream marks pending work with `## Unreleased — …` and "added after <release>" tables. The rows in contract.md were left where they were, because the 1.17 table already holds later keys (`timeline`, `cache`). |
| **filter-branch `--tree-filter` for the multi-commit scrubs** | Each commit's tree is rewritten independently, so there are no rebase conflicts. A deterministic script rewrites C1's commits to the same hashes inside D, so D stays stacked on C1 (checked with `merge-base` after every pass). |
| **Dropped Codex's "B's committer date changed" finding** | A rebase resets committer dates on every commit anyway. Author dates are kept. |
| **Kept the "iPhone 17 Pro" provenance in C1's design notes** | It tells the maintainer what footage the VideoToolbox curve was fitted on. Only the personal `IMG_0761.MOV` example path was made generic. |
| **AI-review mentions stay in commit messages and out of PR descriptions (user's choice)** | The plan-doc descriptions had none. The doc now says to paste them over GitHub's pre-filled body, because a one-commit PR (A) pre-fills from its message. The user checked #301–#306: no agent mentions. |
| **D is a draft against `main` with a "builds on #304" note (user's choice)** | A fork's PR can only target a branch in the upstream repo, so "stacked on C1's branch" was impossible without pushing to upstream. D shows 15 commits until #304 merges and D is rebased. |

## Changes Made

| Change | Detail |
|--------|--------|
| **Six `pr/*` branches rebased onto `upstream/main` `9392328`** | Final tips: A `1d0146f`, B `256c374`, E `d9479ac`, C1 `8ee517a`, C2 `2790818`, D `bbbc465` (9 commits on C1). All six were pushed by the user and track `origin`. |
| **A's commit message and CHANGELOG bullet** | They now say the title was wrapped as `"WHO\nSHOWS UP?"` before the newline was stripped. |
| **Working-note references removed** | A/B: `ISSUES.md T1/J1` and "the J1 rule". D: `tests/prototypes/join_copy_p3.py`, "(item N)" headers, and the docstring labels `R7`, `Item 3.1`, `1-a.`…`1-i.`, `1-f2.`, `2-c`/`2-d`, `R4's`, `Item 1's`, "The user's iPhone", "today's cut"/"Today's join". In D 464a22f's message, "(R5)… the as-built note records it" was removed. "The copy path." fragments became "On the copy path, …". |
| **Unreleased "2.4" claims removed (C1, C2, D)** | `docs/design-decisions.md` headings, `docs/contract.md`, `references/scripts.md`, the README sentence "Since 2.4 the one GPU path…", code section comments in `decision.py`/`asr.py`, the `silence.py` comment "pre-2.4", test module docstrings, and `bench_vt.py`. |
| **B's `clip_length` docstring** | "in a crossfaded join" → "in a join", since the plain cut now uses it too. |
| **C1 bench example** | `~/Footage/IMG_0761.MOV` → `~/Footage/clip.mov`. |
| **Plan doc `docs/plans/2026-09-30-upstream-pr-series.md`** | New base. The full conflict map, including B × C1/C2/D in `design-decisions.md`; `mcp_tools.json` merges cleanly in every pair. B's effect on #300. Test results on the rebased tips. Paste-over-prefill note. D's draft note. PR numbers. Commits `8b43fb1`, `dc2e344`, `a0116e4`, `0687462`, `dd15bb0`, `06ff869`. |
| **Backup branches** | `backup/2026-10-02/*` (pre-rebase) was created, and so were two intermediate sets (`…02b`, `…02c`). All of them were deleted, the last six at the user's request after the PRs were open. |

## Testing / Research Performed

**Upstream assessment.** `git fetch` brought in #299 (`0682a83`: doctor's drawtext probe uses the tools' `fontfile=`; raw docstrings) and #300 (`f0727a1`: `join.py` silent `at`/`end`, `--allow-silent`), released as v2.3.2 and v2.4.0. A trial merge of each branch onto the new upstream found CHANGELOG conflicts in all six and a `join.py` conflict in B.

**Reviews:**
- **Opus scan agent** (read-only): found the "2.4" labels, D's test labels, the B × C1/C2/D `design-decisions.md` conflicts, and the AI-review mentions in messages. It confirmed that every commit parses and that the MCP snapshot matches on every branch and every pair that merges cleanly.
- **Codex `gpt-5.6-terra` xhigh, pass 1** (rebase mechanics): FIX, Minors only. It confirmed the range-diffs, found no lost CHANGELOG bullets, and confirmed that B's resolution and its commit-message claim are correct. It missed the "2.4" labels.
- **Codex pass 2** (on the fixes): FIX. It found the "The copy path." fragments and the `IMG_0761.MOV` path (both fixed). The committer-date finding was dropped, and the review-mention finding went to the user.

**Verification by hand:**
- A range-diff-style comparison of each branch against its backup showed only the intended edits.
- A fixed-string scan for "2.4" in every line the PRs add caught the README sentence that the first scan missed. That scan used `git grep -E` with `\b`, which silently matched nothing.
- All 105 changed `.py` files parsed under `python3 -W error` in every commit; the 78 on C1/D were rechecked after the last pass.
- `git merge-base` confirmed that D sits on C1's tip after every rewrite.
- `gh pr view` confirmed that each PR head matches its local tip and that no PR body mentions an agent.

**Test runs.** Each run used a fresh `OUT`, in per-branch worktrees.

| PR | Results |
|---|---|
| A | `test_picture` 211 OK (3 skipped) |
| B | `test_editing` 133 OK (before and after the docstring amend) |
| E | `test_editing` 138 OK; contract 152 OK (1 skipped) |
| C1 | full suite 602 OK (3 skipped); `test_accel` 25 OK; contract 152 OK (1 skipped); `test_delivery` 21 OK; `test_orchestration` 80 OK |
| C2 | full suite 598 OK (3 skipped); `test_asr` 20 OK; contract 152 OK (1 skipped); `test_delivery` 21 OK; `test_orchestration` 80 OK |
| D | `test_cut_copy` 93 OK; `test_editing` 132 OK; `test_orchestration` 80 OK; `test_delivery` 21 OK; `test_accel` 25 OK; contract 152 OK (1 skipped) |

- The C1 and C2 full suites ran on the first-round tips.
- The modules that read docs (contract, delivery and orchestration) were rerun after the "2.4" edits.
- The last pass changed only a docstring and a usage example, so no tests were rerun after it.
- An earlier trial merge of all six PRs together gave 709 OK. That run skipped one module, because my union resolution of `test_all.py` doubled the `MODULES` line. `test_asr`, `test_accel` and `test_cut_copy` were then run on their own: all OK.

## Summary Statistics

- **PRs opened by the user:** 6 (#301–#306; #306 is a draft).
- **Branches rebased:** 6, with 1/1/1/6/5/9 commits.
- **Commits on `m-series-hw-parakeet`:** 6 plan-doc updates, pushed by the user, plus this summary.
- **Review passes:** 3: two Codex, one Opus scan.
- **References removed:** 6 file references, about 20 docstring labels, 1 commit-message reference, and the "2.4" claims in 10 files.
- **Test runs:** 28 module runs in the per-branch lanes, all OK.

## Discoveries / Handoff Notes

- **A fork can't stack a PR on another fork branch.** The base must be a branch in the upstream repo. A stacked PR goes against `main` with a note naming the PR it builds on.
- **GitHub pre-fills a one-commit PR's body from its commit message.** Paste the prepared description over it.
- **Upstream releases are automated** (`chore(release): bump version … [skip ci]`). The version a feature lands in isn't known until it merges, so docs should say "Unreleased", not a guessed version.
- **The CHANGELOG resolver drops any bullet already present on the upstream side.** That is wrong when replaying a series whose earlier commits are on HEAD. It was safe this time only because each series conflicted only on its first commit, which was verified afterwards. Rethink it before reusing.
- **zsh traps hit several times:** `echo ===…` (`=` expansion), `$r:t` in `"$r:tests/…"` (a history modifier), and backticks inside double quotes. Use `bash -c` or a quoted heredoc.
- **`git grep -E` doesn't support `\b`.** Its searches silently return nothing; use plain `grep` on `git diff` output instead.
- **Upstream's own commits carry `Claude-Session` / `Co-authored-by: Claude` trailers.** The maintainer uses Claude too.

## Current State

- **`m-series-hw-parakeet`** is at `06ff869`, level with `origin`. Untracked: `CLAUDE.local.md` (pre-existing).
- **PRs:**

  | PR | Branch | Number |
  |---|---|---|
  | A | `pr/graphics-wrapped-title` | #301 |
  | B | `pr/join-no-hole` | #302 |
  | E | `pr/loop-boomerang` | #303 |
  | C1 | `pr/hw-videotoolbox` | #304 |
  | C2 | `pr/asr-parakeet` | #305 |
  | D | `pr/cut-exact-joins` | #306 (draft) |

  All of them are against `kajisho5/ffmpeg-skill` `main`, and every branch tracks `origin`.
- **Worktrees and backups:** no scratch worktrees and no backup branches remain.
- **Local `main`** is behind `upstream/main` (`df5d273` vs `9392328`). `git fetch upstream main:main` fast-forwards it.

## Unfinished Work

- **After each upstream merge:**
  1. Rebase the open PRs onto the new `upstream/main`, resolving the conflicts the plan doc lists.
  2. Rerun each PR's test modules.
  3. Push with `--force-with-lease`.
- **When #304 merges:**
  1. Rebase D (#306) onto `upstream/main` so it shows only its 9 commits.
  2. Push it.
  3. Mark it ready.
- **Optional:** reword the "For review" line in A's description (#301) on GitHub. It says "a newline in the user's text", which reads ambiguously; a clearer version is "draws a newline in its text as a line break, where before it dropped the newline". The edit was proposed, but the user didn't choose it before opening the PR.
- **Optional, carried over:** re-run `tests/bench_vt.py` on the M4 Max, and time hardware decode more broadly before deciding on `--hw` decode.
