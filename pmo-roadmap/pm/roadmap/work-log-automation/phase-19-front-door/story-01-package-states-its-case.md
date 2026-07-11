# WLA-19-01 - The package states its case — metadata and community polish

- **Project:** work-log-automation
- **Phase:** 19
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-19-03
- **Owner:** unassigned

## Problem

The 2026-07-11 readiness audit found the package publishes with an
incomplete case: PyPI renders only Homepage and Documentation links
(no Repository, Changelog, or Issues), the classifiers never state
the MIT license even though LICENSE, the `license` field, and the
README all do, the author entry has no contact, and LICENSE says
"Karol" where every other surface says "Karol Sane". A serious
published package states these things once, consistently, and lets
the index render them.

## Scope

- **In:** `pyproject.toml` — add `Repository`, `Changelog`, and
  `Issues` to `[project.urls]`; add
  `License :: OSI Approved :: MIT License` to classifiers; add the
  author email. `LICENSE` — holder becomes "Karol Sane". README —
  badges (validation workflow status, PyPI version, license) near
  the title.
- **Out:** any packaging-layout change (MANIFEST.in, package-dir);
  per-minor Python classifiers; renaming the project or touching
  the description/keywords; CODE_OF_CONDUCT/SECURITY/templates
  (audited healthy).

## Acceptance criteria

- [ ] `python3 -m build` (or the package smoke) succeeds and the
  built metadata shows the three new urls, the MIT classifier, and
  the author email.
- [ ] LICENSE holder reads "Karol Sane"; no surface still carries
  the bare-name inconsistency.
- [ ] README renders three badges pointing at the validation
  workflow, the PyPI project page, and the license.
- [ ] Full core suite green (no parity regression from the edits).

## Test plan

- **Unit:** core suite (version/manifest parity family unaffected).
- **Integration:** `tests/package-smoke.sh` — build + install from
  the local artifact with the new metadata.
- **Manual / device:** inspect built wheel METADATA for the urls
  and classifier; render README locally for the badges.

## Notes / open questions

Author email: karolsane@gmail.com — already public in
CODE_OF_CONDUCT.md, so no new exposure.
