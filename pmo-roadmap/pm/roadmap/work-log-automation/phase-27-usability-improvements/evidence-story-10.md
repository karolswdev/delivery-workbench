# Evidence - WLA-27-10

- **Story:** WLA-27-10 - Prove the redesigned application end to end
- **Status:** done
- **Date:** 2026-07-25

## Proof

## One fresh installed consumer completes the whole task

[`usability-packaged-exam.py`](../../../../tests/usability-packaged-exam.py)
is the Phase 27 public exit entry point. It accepts one isolated installed
`dw`, runs the existing Phase 26 autonomous exam exactly once, validates the
observed production facts, and renders the acceptance transcript directly from
the thirteen versioned journeys. `package-smoke.sh` now invokes this composed
entry point instead of running a second autonomous specimen.

The same consumer proves the ordering that matters:

1. A wheel-installed `dw` installs one fresh repository and authors only an
   ordinary roadmap.
2. `program list`, `status`, `step`, `next`, and task-first `setup` run before
   optional policy exists. The program inventory is healthy and empty; the
   current story is available; program/run stores and optional policy
   directories remain absent; no program process starts; and a full file
   snapshot is unchanged.
3. Only then does the consumer author and commit the reviewed workflow,
   organization, rubrics, and program. All three editable policy families
   round-trip without semantic or layout loss. Authoring starts no work and
   creates no permission.
4. The same consumer separately reviews and confirms one real bounded run,
   resolves its blocked human decision, permanently revokes another bounded
   run, preflights the optional program, and finally crosses the existing
   separate program-start boundary.

The no-program assertion is therefore not a second easier fixture substituted
for the delivery journey. The underlying Phase 26 exam still keeps its
independent fresh no-program consumer as a compatibility backstop.

## Canonical acceptance transcript and measured friction

The composed exam has one explicit evidence path for every ID in
`journeys-v1.json`: arrival, deliberate capability choice, plan setup, team and
review setup, preflight, live progress, failed review and repair, blocked
decision, remaining permission and cost, stop, crash recovery, completion, and
technical inspection. There is no second friendlier journey model.

The generated transcript records:

- 13/13 passing journey checkpoints;
- four explicit authority confirmations;
- 13 safe refusal/recovery paths;
- zero unresolved transcript dead ends; and
- zero reserved engineering terms in everyday transcript regions.

The earlier baseline remains an honest different measure: 88 visible screen
steps, 38 decisions, 81 engineering-term occurrences, 13 recorded dead ends,
and 26 context switches. The exit exam does not subtract its thirteen
whole-task checkpoints from those screen observations as though the two counts
were interchangeable.

## Deliberate authority, review, recovery, and exact inspection

The bounded decision reaches `awaiting-approval`, exposes only **approve** and
**reject**, names the responsible resolver and next step, previews without a
write, and applies one hash-bound response. Its exact ledger head changes only
at apply. The permanent-stop journey likewise previews without a write,
increments the control generation once, reaches `revoked`, and retains an exact
receipt.

Program preflight names three scoped stories across two phases, the
implementer and independent verifier, provider/model bindings, decision
council, permitted effects, finite limits, stop conditions, permanent
exclusions, cost accounting, and failure branches. Its five effect flags are
false until a separately confirmed start.

The completed delivery demonstrates:

- independent `needs-repair` followed by one repair and `pass`;
- a governed council outcome with dissent and its obligation preserved;
- all seven ordinary operator answers, current progress, team/review,
  remaining permission, counted limits, and observed usage;
- nine planted conductor crashes and eighteen delivery effect/receipt crashes;
- unique claims, dispatches, and receipt hashes with no duplicate delivery
  action; and
- complete scope at 3/3 stories with a readable next step.

**Technical details** retains the exact run ID, generation, grant/plan/ledger
hashes, receipt hashes, resolved principal fingerprints, and ordered event
counts. Exact views agree across CLI, MCP, HTTP, and Workbench. Exact events
agree across CLI, MCP, HTTP, and SSE: 203 verified ledger events equal 203
streamed events.

## Planted failures

Five deliberate corruptions prove the wrapper cannot pass on a friendly
transcript alone:

- created program state during first arrival;
- lost reject/repair evidence;
- missing crash recovery;
- false completion; and
- a hidden or relabelled technical boundary.

Each mutation is applied to an otherwise passing production report and must
trigger its named validation refusal. The focused core test also starts from a
minimal valid report, proves it passes, and proves all five corruptions fail.

## Responsive, keyboard, and manual replay

The current browser run retained all 88 exact 1440×900 and 390×844 PNGs under
`.tmp/wla27-story10-ui/`. The real Firefox 152 exam again passed thirteen
journeys, 26 wide/narrow DOM audits, and 92 keyboard/focus/semantic assertions.

Wide and narrow contact sheets replayed one representative state for each
canonical journey: ordinary arrival, capability choice, plan, team/review,
preflight, active progress, repair, human decision, remaining limits,
permanent-stop receipt, stale-live recovery, completion, and technical
inspection. Direct inspection found the task heading, status, consequence or
next action readable at both widths; grids collapsed without page-level
horizontal clipping; exact long values stayed inside their owning technical
region; and the explicit Technical-details view retained identities, hashes,
events, and provenance. The action-focused captures also retained the visible
skip control and non-color focus/status treatment.

This is deterministic browser and recorded assistive-use review, not a formal
third-party accessibility certification or an external usability study.

## Regression and distribution proof

- The full Python 3.14 core suite passes 499/499 tests in 830.417 seconds.
  Three new WLA-27-10 tests pin the canonical transcript, production-report
  validator, planted red cases, and package/CI wiring.
- Python 3.9.6 builds both the v1.14.0 sdist and wheel, installs the wheel in an
  isolated environment, and passes guided ordinary delivery, deliberate step,
  bounded orchestration, outward signals, and the composed usability/program
  exam. The final package result is 13 journeys, five red cases, 9/18 crash
  recoveries, and 203/203 ledger/SSE events.
- Workbench passes 88 retained viewport renders plus all thirteen keyboard,
  semantic, focus, and wide/narrow journey exams.
- Product-language, usability-journey, accessibility, docs/link, snippet,
  canonical-roadmap, rider, vendored-source, Firefox JavaScript execution,
  Python, shell, whitespace, and history checks pass.
- Roadmap CLI, Workbench explorer, MCP, deliberate-step, orchestration,
  contributor, plugin, work-log, guided-status, range, and exact adapter-parity
  entry points pass.
- The real v1.5.0-to-current consumer upgrade path passes, and full history
  verification reports 172 verified commits with 17 pre-epoch commits skipped.
- Telegram passes 153 interface tests and 10 architecture-fitness tests; nine
  optional image-renderer cases honestly skip because Pillow is not installed
  in this local environment.
- The local Homebrew smoke honestly abstains because Delivery Workbench is
  already installed. It was not uninstalled or replaced for this story; the
  clean-machine macOS CI lane remains the owner of that environment proof.

## Acceptance mapping and closeout boundary

- Healthy first arrival and ordinary work are proved before optional
  configuration on the same installed consumer.
- Deliberate authoring, readable team/review/decision ownership, exact effects
  and limits, pure preflight, and separate start are proved from canonical
  models.
- Live progress, reject/repair/pass, blocked decision, remaining
  permission/cost, permanent stop, and completion are proved by real bounded
  and program state.
- Crash replay and the explicit Technical-details transition preserve exact
  events, hashes, identities, generations, receipts, and adapter parity.
- The public core, UI, docs, parity, package, upgrade, history, and
  distribution entry points remain green, with the two local environment
  limitations above recorded rather than promoted to passes.

No version was changed; no commit, merge, tag, release, publication, formula
update, deployment, hosted authority, or landing decision was performed or
inferred.

## Deferred honestly

- External user study or broad usability claims.
- Authenticated live-provider quality.
- Localization and formal third-party accessibility certification.
- Release, publication, deployment, and landing decisions.

### Captured run — 2026-07-26T05:37:00Z

- **Command:** `bash -lc set -e
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
python3 pmo-roadmap/tests/workbench-accessibility-contract.py
python3 -m unittest -v pmo-roadmap/tests/dw-core-tests.py -k UsabilityPackagedExamContractTest
python3 -m py_compile pmo-roadmap/tests/autonomous-program-packaged-exam.py pmo-roadmap/tests/usability-packaged-exam.py
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
node --check pmo-roadmap/workbench/app.js
bash -n pmo-roadmap/tests/package-smoke.sh pmo-roadmap/tests/workbench-ui-smoke.sh
cmp pmo-roadmap/workbench/app.js .githooks/workbench/app.js
cmp pmo-roadmap/workbench/index.html .githooks/workbench/index.html
cmp pmo-roadmap/workbench/style.css .githooks/workbench/style.css
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
git diff --check`
- **Cwd:** .
- **Exit code:** 134
- **Index-tree:** 2dbc94019263e8423d99c3d2d9b005397b673e76

```text
product-language-contract: ok (10 concepts, 18 surfaces, 15 migrated, 18 reserved terms, 13 fixtures, 7 snapshots, 8 source regions)
usability-journey-contract: ok (13 journeys, 23 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
workbench-accessibility-contract.py: ok (13 journeys, 2 viewports, keyboard/focus/semantics/manual evidence)
test_canonical_transcript_covers_every_journey_without_reserved_terms (pmo-roadmap.tests.dw-core-tests.UsabilityPackagedExamContractTest) ... ok
test_observation_validator_rejects_each_planted_regression (pmo-roadmap.tests.dw-core-tests.UsabilityPackagedExamContractTest) ... ok
test_public_package_and_ci_entry_points_run_the_composed_exam (pmo-roadmap.tests.dw-core-tests.UsabilityPackagedExamContractTest) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.007s

OK
docs-lint: ok (477 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
dyld[55127]: Library not loaded: /opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib
  Referenced from: <BD9D65B7-B478-3E6C-8530-96FD5D1D2AF9> /opt/homebrew/Cellar/node/25.9.0/bin/node
  Reason: tried: '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file)
bash: line 8: 55127 Abort trap: 6           node --check pmo-roadmap/workbench/app.js
```

The nonzero capture is retained intentionally. It reached and passed every
contract/focused/docs/canon check before the local Homebrew Node executable
aborted during dynamic linking. `node` 25.9.0 requests
`libllhttp.9.3.dylib`, while the installed `llhttp` 9.4.1 provides
`libllhttp.9.4.1.dylib`. This is a local package-manager linkage mismatch, not
a JavaScript parse or application failure. The same `app.js` was parsed and
executed by Firefox 152 across the two green 88-render browser runs above.
The following capture omits only that broken external executable and retains
all repository-owned checks.

### Captured run — 2026-07-26T05:37:58Z

- **Command:** `bash -lc set -e
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
python3 pmo-roadmap/tests/workbench-accessibility-contract.py
python3 -m unittest -v pmo-roadmap/tests/dw-core-tests.py -k UsabilityPackagedExamContractTest
python3 -m py_compile pmo-roadmap/tests/autonomous-program-packaged-exam.py pmo-roadmap/tests/usability-packaged-exam.py
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
bash -n pmo-roadmap/tests/package-smoke.sh pmo-roadmap/tests/workbench-ui-smoke.sh
cmp pmo-roadmap/workbench/app.js .githooks/workbench/app.js
cmp pmo-roadmap/workbench/index.html .githooks/workbench/index.html
cmp pmo-roadmap/workbench/style.css .githooks/workbench/style.css
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2dbc94019263e8423d99c3d2d9b005397b673e76

```text
product-language-contract: ok (10 concepts, 18 surfaces, 15 migrated, 18 reserved terms, 13 fixtures, 7 snapshots, 8 source regions)
usability-journey-contract: ok (13 journeys, 23 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
workbench-accessibility-contract.py: ok (13 journeys, 2 viewports, keyboard/focus/semantics/manual evidence)
test_canonical_transcript_covers_every_journey_without_reserved_terms (pmo-roadmap.tests.dw-core-tests.UsabilityPackagedExamContractTest) ... ok
test_observation_validator_rejects_each_planted_regression (pmo-roadmap.tests.dw-core-tests.UsabilityPackagedExamContractTest) ... ok
test_public_package_and_ci_entry_points_run_the_composed_exam (pmo-roadmap.tests.dw-core-tests.UsabilityPackagedExamContractTest) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.005s

OK
docs-lint: ok (477 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
dw check: ok
```
