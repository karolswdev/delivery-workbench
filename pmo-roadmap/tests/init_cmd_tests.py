#!/usr/bin/python3
"""WLA-30-02 empty-directory bootstrap tests."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS_DIR = Path(__file__).resolve().parent
PMO_ROOT = TESTS_DIR.parent
LIB_ROOT = PMO_ROOT / "lib"
sys.path.insert(0, str(LIB_ROOT))

from dw_pmo import launcher


SYSTEM_PYTHON = "/usr/bin/python3"


def run(*argv: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=str(cwd) if cwd else None,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def tree_snapshot(root: Path) -> dict[str, tuple[str, int, int, str]]:
    snapshot: dict[str, tuple[str, int, int, str]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if path.is_symlink():
            snapshot[relative] = ("link", mode, info.st_mtime_ns, os.readlink(path))
        elif path.is_dir():
            snapshot[relative] = ("dir", mode, info.st_mtime_ns, "")
        else:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot[relative] = ("file", mode, info.st_mtime_ns, digest)
    return snapshot


class InitCommandTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox = Path(tempfile.mkdtemp(prefix="dw-init-test.")).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.sandbox, ignore_errors=True)

    def invoke(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = launcher.main(["init", *args])
        return code, stdout.getvalue(), stderr.getvalue()

    def init_target(self, name: str = "target") -> tuple[Path, str]:
        target = self.sandbox / name
        target.mkdir()
        code, stdout, stderr = self.invoke(str(target))
        self.assertEqual(code, 0, stderr)
        return target, stdout

    def test_empty_directory_becomes_healthy_vendored_repository(self) -> None:
        target, stdout = self.init_target()
        self.assertTrue((target / ".git").is_dir())
        self.assertTrue((target / ".githooks/dw").is_file())
        self.assertIn("start the intake conversation", stdout)
        self.assertIn("Run /dw-scope", stdout)
        self.assertIn("No project or agent was started automatically", stdout)

        doctor = run(SYSTEM_PYTHON, str(target / ".githooks/dw"), "doctor", cwd=target)
        self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
        self.assertIn("dw doctor: healthy", doctor.stdout)

    def test_existing_empty_git_repository_is_supported(self) -> None:
        target = self.sandbox / "existing"
        target.mkdir()
        initialized = run("git", "init", "-q", str(target))
        self.assertEqual(initialized.returncode, 0, initialized.stderr)

        code, stdout, stderr = self.invoke(str(target))
        self.assertEqual(code, 0, stderr)
        self.assertIn("Git repository already present", stdout)
        self.assertTrue((target / ".githooks/dw").is_file())

    def test_nested_target_requires_explicit_independent_root_flag(self) -> None:
        parent = self.sandbox / "parent"
        child = parent / "child"
        child.mkdir(parents=True)
        initialized = run("git", "init", "-q", str(parent))
        self.assertEqual(initialized.returncode, 0, initialized.stderr)

        code, _stdout, stderr = self.invoke(str(child))
        self.assertEqual(code, 2)
        self.assertIn("nested inside another repository", stderr)
        self.assertIn("--inside-existing-repo", stderr)
        self.assertFalse((child / ".git").exists())

        code, stdout, stderr = self.invoke(str(child), "--inside-existing-repo")
        self.assertEqual(code, 0, stderr)
        self.assertTrue((child / ".git").is_dir())
        top = run("git", "-C", str(child), "rev-parse", "--show-toplevel")
        self.assertEqual(Path(top.stdout.strip()).resolve(), child.resolve())
        self.assertIn("initialized Git repository", stdout)

    def test_rerun_reports_components_and_changes_nothing(self) -> None:
        target, _stdout = self.init_target()
        before = tree_snapshot(target)

        code, stdout, stderr = self.invoke(str(target))
        self.assertEqual(code, 0, stderr)
        self.assertEqual(tree_snapshot(target), before)
        for component in launcher._init_components(target):
            self.assertIn(f"already present: {component}", stdout)

    def test_init_creates_no_project_authority_or_runtime_state(self) -> None:
        target = self.sandbox / "no-state"
        target.mkdir()
        initialized = run("git", "init", "-q", str(target))
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        git_files_before = {
            path.relative_to(target / ".git").as_posix()
            for path in (target / ".git").rglob("*")
            if path.is_file()
        }

        code, _stdout, stderr = self.invoke(str(target))
        self.assertEqual(code, 0, stderr)
        git_files_after = {
            path.relative_to(target / ".git").as_posix()
            for path in (target / ".git").rglob("*")
            if path.is_file()
        }
        self.assertEqual(git_files_after, git_files_before)

        roadmap = target / "pm/roadmap"
        self.assertEqual(
            sorted(path.name for path in roadmap.iterdir()),
            ["PMO-CONTRACT.md", "roadmap-builder.md"],
        )
        forbidden = [
            target / ".pmo",
            target / ".tmp",
            target / "pm/programs",
            target / "pm/program",
            target / "pm/driver-roster.json",
            target / ".git/pmo-contract-archive",
            target / ".git/pmo-rail-events.jsonl",
        ]
        self.assertFalse([str(path) for path in forbidden if path.exists()])
        self.assertEqual(run("git", "-C", str(target), "remote").stdout, "")
        self.assertNotEqual(
            run("git", "-C", str(target), "rev-parse", "--verify", "HEAD").returncode,
            0,
        )
        refs = target / ".git/refs"
        self.assertFalse([path for path in refs.rglob("*") if path.is_file()])

    def test_vendored_hooks_are_byte_identical_to_plain_install(self) -> None:
        initialized, _stdout = self.init_target("initialized")
        plain = self.sandbox / "plain"
        plain.mkdir()
        self.assertEqual(run("git", "init", "-q", str(plain)).returncode, 0)
        install = run("bash", str(PMO_ROOT / "install.sh"), str(plain), "--skip-bootstrap")
        self.assertEqual(install.returncode, 0, install.stdout + install.stderr)

        diff = run("diff", "-r", str(initialized / ".githooks"), str(plain / ".githooks"))
        self.assertEqual(diff.returncode, 0, diff.stdout + diff.stderr)

    def test_status_reports_setup_required_and_launcher_defers_after_init(self) -> None:
        target, _stdout = self.init_target()
        status_result = run(
            SYSTEM_PYTHON,
            str(target / ".githooks/dw"),
            "status",
            "--json",
            cwd=target,
        )
        self.assertEqual(status_result.returncode, 0, status_result.stderr)
        status_body = json.loads(status_result.stdout)
        self.assertEqual(status_body["verdict"], "ready")
        self.assertTrue(status_body["rails"]["healthy"])
        self.assertTrue(status_body["roadmap"]["healthy"])
        self.assertEqual(status_body["roadmap"]["projects"], [])
        self.assertEqual(status_body["roadmap"]["issues"], [])
        self.assertEqual(status_body["next_action"]["id"], "setup-project")
        self.assertEqual(status_body["next_action"]["command"], ["dw", "new-project", "--help"])
        self.assertIn("project setup required", status_body["next_action"]["reason"])

        old_cwd = Path.cwd()
        try:
            os.chdir(target)
            with mock.patch.object(launcher, "_run", return_value=0) as delegated:
                self.assertEqual(launcher.main(["doctor"]), 0)
        finally:
            os.chdir(old_cwd)
        delegated_argv = delegated.call_args.args[0]
        self.assertEqual(Path(delegated_argv[1]).resolve(), (target / ".githooks/dw").resolve())
        self.assertEqual(delegated_argv[2:], ["doctor"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
