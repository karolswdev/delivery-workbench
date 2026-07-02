# Security And Privacy

Delivery Workbench is local developer tooling. It installs Git hooks and can
optionally capture staged diffs into a local daily work log.

Work logging is off by default. When enabled, a log entry is only created if
the per-commit contract contains explicit work-log consent:

```markdown
**Work-log consent:** yes
```

Use `PMO_WORK_LOG_EXCLUDE_REGEX` to mechanically omit sensitive or noisy staged
paths from work-log payloads. This is a practical guardrail, not a security
boundary. Do not consent to logging material that should not be retained.

Do not publish generated work logs unless you have reviewed them for secrets,
customer data, credentials, and private implementation details.

## Workbench runtime boundary

`dw-workbench` is a local tool with a deliberately small surface,
enforced by tests on every push: it binds 127.0.0.1 only, serves
exactly one repo root, rejects non-local `Host` headers and CORS
preflights, contains every file read to the roadmap tree (or the
work-log root, for log artifacts), writes only through
fingerprint-verified preview→apply inside `pm/roadmap/**`, and has no
endpoint that stages or commits git changes. Do not tunnel or expose
it: it has no authentication because it is designed never to need
any. Report suspected boundary violations as security issues.
