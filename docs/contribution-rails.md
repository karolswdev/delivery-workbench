# Delivery Workbench — Contribution Contract

What the gate's guarantees mean when work arrives by pull request
instead of a direct push. This is the design contract for
WLA-11-02 (the fixture proof) and WLA-11-03 (enforcement and
contributor docs); the classifications and failure narratives below
are what those stories are tested against. It builds directly on
[remote-verification.md](./remote-verification.md), which defines
what is re-derivable from pushed history at all.

## The fork boundary

Every guarantee before this phase assumed the committer is the
pusher. A pull request splits those roles: the contributor gates
their commits in their clone, and the maintainer merges work they
did not gate. Two facts shape everything below.

What travels with the commits: trees (including roadmap, story,
and evidence files with their captured runs), commit messages with
their trailers, and parentage. `dw verify` over the PR range checks
all of it, and it runs as a required status check on this
repository.

What stays behind in the contributor's clone: the certified
contract text, the contract archive under
`.git/pmo-contract-archive/`, and any `BUNDLE-OK.md`. Upstream
never receives these. The `PMO-Contract-Digest:` trailer is the
anchor: the contributor can always produce the archived contract
whose hash matches, but upstream holds only the attestation.

## Guarantee classification across a PR

| Guarantee | Across a PR | How |
|---|---|---|
| One story flips done per commit (`atomicity`) | verified mechanically | `dw verify` on the PR range, a required check |
| Flipped story ships its evidence (`evidence-missing`) | verified mechanically | same |
| Evidence never orphaned (`orphan-evidence`, `evidence-deletion-orphans-story`) | verified mechanically | same |
| Flips declared in trailers (`contract-story-mismatch`, `trailer-missing`, `trailer-format`) | verified mechanically | same |
| Contract facts were true at commit time (branch, HEAD, index tree, sample) | attestation | digest trailer anchors an archive only the contributor holds |
| Rules were honestly certified | attestation | as everywhere: certification is a human or agent act, never mechanical |
| Tests passed | readable, not enforced | captured runs with exit codes are in the evidence files; reviewers read them |
| Work outside the roadmap tree | out of scope | the verifier only examines commits touching `pm/roadmap/` paths, by design |

The honest summary for maintainers: the green `verify-history`
check proves the range's structural integrity. It does not prove
the tests passed (read the captured runs) and it does not prove the
certification was honest (nothing can; that is what review is
for).

## Merge methods

**Rebase is the only allowed merge method.** The reasoning, per
method:

Rebase rewrites SHAs but preserves each commit's tree, message,
and trailers. Every stamped fact that mentions a SHA (HEAD, index
tree) is attested-only per the remote verification contract, so
rewriting SHAs breaks nothing the verifier checks. After a rebase
merge, `dw verify --all` on main stays green. Approved.

Squash is banned because it corrupts the audit trail two ways.
First, GitHub composes the squash commit's message by concatenating
the titles and bodies of every commit in the PR; git only parses
trailers in the message's final block, so `PMO-Story:` and
`PMO-Contract-Digest:` lines from earlier commits land mid-body
and stop being trailers (`trailer-missing` on the squashed
commit). Second, a PR containing two story flips squashes into one
commit flipping both (`atomicity`). Either way the violation lands
on main itself, and `verify-history` then fails every subsequent
push. WLA-11-02 demonstrates both failure modes with those exact
rule ids before the button is removed.

Merge commits are already blocked by the required-linear-history
branch protection, and the verifier deliberately does not examine
merge-commit content (an "evil merge" could smuggle changes), so
allowing them would open an unverified channel. Banned.

## One story per PR

The gate's oldest rule is one story flips done per commit. The PR
is the review unit, so the convention extends naturally: one story
per pull request. A PR may contain several commits (setup, the
flip, docs), but exactly one of them flips a story to done, and
that commit carries the evidence. Deliberate bundling stays
possible exactly as it is locally: `BUNDLE-OK.md` at commit time
stamps a `PMO-Bundle:` trailer, which the verifier accepts —
visible in the PR range like everything else.

## What contributors need

Rails travel with the repo: a clone of an adopted repository
carries the hooks and CLI under `.githooks/`, and one command
activates them (`git config core.hooksPath .githooks`; `dw doctor`
confirms the wiring). Contributors install nothing except
optionally the global toolchain (`pipx install delivery-workbench`
or the Homebrew tap) for the bootstrap verbs. Contributors without
working rails cannot produce the trailers, and their roadmap
commits fail the required check. Work that never touches the
roadmap tree carries no gate obligations at all.

## Proof obligations (WLA-11-02)

- Green: contributor clone → branch → one story worked through the
  gate → `dw verify <base>..<head>` green → rebase onto main →
  `dw verify --all` green on main.
- Red 1: two-flip branch squashed with GitHub-style message
  concatenation → verify names `atomicity` or `trailer-missing`.
- Red 2: single-flip branch with a fixup commit, squashed → verify
  names the trailer damage.

## Enforcement (WLA-11-03)

Repository settings allow rebase merges only; the PR template asks
for the story ID and evidence link and states the merge policy in
one line; CONTRIBUTING walks the loop end to end.
