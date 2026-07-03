# Source of truth for the future public tap. Installs the pure-python
# wheel by unzipping it into libexec and writing a thin interpreter
# shim — no pip, no venv, no network at install time. The runtime is
# stdlib-only by design (docs/distribution.md), so there are no
# resources to vendor; skipping Language::Python::Virtualenv is a
# deliberate, recorded waiver, not an omission.
#
# The url below targets the GitHub release artifact for this version;
# tests/brew-formula-smoke.sh proves the same formula against a
# locally built wheel by rewriting url/sha256 to a file:// path.
class DeliveryWorkbench < Formula
  desc "Evidence-first rails for agentic software delivery"
  homepage "https://github.com/karolswdev/delivery-workbench"
  url "https://github.com/karolswdev/delivery-workbench/releases/download/v1.7.0/delivery_workbench-1.7.0-py3-none-any.whl",
      using: :nounzip
  sha256 "d9d1d8f7f999d5c5708d50b6b8aa2e82e2689c92d59008a1d91cc181c896b5ff"
  license "MIT"

  depends_on "python@3.14"

  def install
    wheel = Dir["*.whl"].first
    odie "no wheel staged" if wheel.nil?
    system "unzip", "-q", wheel, "-d", libexec
    python = formula_opt_bin("python@3.14")/"python3.14"
    (bin/"dw").write <<~SHIM
      #!#{python}
      import sys

      sys.path.insert(0, "#{libexec}")

      from dw_pmo.launcher import main

      sys.exit(main())
    SHIM
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/dw --version")
  end
end
