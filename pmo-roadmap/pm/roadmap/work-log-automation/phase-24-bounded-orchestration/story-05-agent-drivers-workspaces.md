# WLA-24-05 - Drive research and worker agents in isolated workspaces

- **Project:** work-log-automation
- **Phase:** 24
- **Status:** done
- **Depends on:** WLA-24-02, WLA-24-04
- **Unblocks:** WLA-24-06, WLA-24-08
- **Owner:** unassigned

## Problem

Delivery Workbench cannot coordinate useful software work through roadmap
verbs alone. It needs a provider-neutral agent seam that supports parallel
research, typed artifacts, synthesis, write-capable workers, and interruption
without storing provider executables/secrets or pretending to enforce a
harness sandbox it does not own.

## Scope

- **In:** agent profile/capability discovery; structured work-packet and
  driver start/poll/interrupt/collect receipt schemas; operator-local logical
  profile→adapter mapping; deterministic fixture driver; at least one real
  supported harness adapter; read-only research and synthesis artifacts;
  isolated Git worktrees/resource locks for writers; context and stream caps;
  output existence/format/schema/section/citation/path/diff-scope validation;
  lost/stale/unsupported/refusal/cancel states; agent/session correlation.
- **Out:** provider argv or credentials in scores; LLM-generated commands;
  shared writable cwd; automatic worktree merge/conflict resolution; runtime
  scheduling policy (WLA-24-06); certification/commit.

## Acceptance criteria

- [x] Drivers expose a provider-neutral capability document and accept only a
  bounded structured work packet; unsupported capability/profile/workspace
  requests refuse before agent start with no claim marked successful.
- [x] Two research nodes can run concurrently read-only, emit separate declared
  artifacts with required citations/schema/sections, and a synthesis packet
  receives only outputs whose deterministic conventions passed.
- [x] Write agents receive distinct contained worktrees and resource locks;
  concurrent writers never share a cwd, undeclared paths/diff scope fail, and
  integration into the operator tree remains a separate reviewed act.
- [x] Start/poll/collect/interrupt is receipt- and idempotency-keyed; lost,
  malformed, oversized, stale, nonzero, timeout, and cancellation cases are
  truthful and recoverable without duplicate launch.
- [x] Fixture driver gives reproducible CI proof; one installed live harness
  run proves the real adapter without making it the deterministic test oracle;
  Python floors/package/privacy/credential checks stay green.

## Test plan

- **Unit:** packet/capability schemas, context caps, profile refusal, worktree
  containment/locks, output validators, driver state mapping, idempotency,
  timeout/cancel/lost states, privacy.
- **Integration:** parallel fixture research→synthesis plus two attempted
  writers proving separate worktrees; live adapter smoke where provisioned.
- **Manual / device:** inspect work packets and artifacts from a real research
  agent; confirm capabilities and output rules shown before start match what
  the adapter received.

## Notes / open questions

The tracked score references logical profiles only. Machine-specific adapter
commands, credentials, and provider defaults live in operator configuration.
Delivery Workbench must report what a driver claims to enforce and refuse an
unsupported request; it must not advertise sandbox guarantees it cannot
observe.
