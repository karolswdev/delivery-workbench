"""Build-time payload assembly for the delivery-workbench package.

All metadata lives in pyproject.toml; this file exists for one
reason: the distribution contract (docs/distribution.md) ships the
vendorable payload as ``dw_pmo/_payload/`` mirroring the
``pmo-roadmap/`` source layout, so install.sh and update.sh run
unmodified from a checkout or from the installed package. Standard
package-data cannot pull files from outside the package directory,
so a build_py hook copies the payload into the build tree.
"""

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "pmo-roadmap"

# Mirrors the install.sh copy inventory (cross-checked in
# docs/distribution.md): directories grafted whole, scripts copied
# executable. lib/dw_pmo is intentionally included — the payload is
# what gets vendored into repos, and vendored rails must be complete
# even though the same modules also ship as the import package.
PAYLOAD_DIRS = ["hooks", "bin", "lib", "templates", "workbench", "bootstrap", "agent"]
PAYLOAD_FILES = ["install.sh", "update.sh"]


class BuildPyWithPayload(build_py):
    def run(self):
        super().run()
        dest = Path(self.build_lib) / "dw_pmo" / "_payload"
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        for name in PAYLOAD_DIRS:
            shutil.copytree(
                SRC / name,
                dest / name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        for name in PAYLOAD_FILES:
            shutil.copy2(SRC / name, dest / name)


setup(cmdclass={"build_py": BuildPyWithPayload})
