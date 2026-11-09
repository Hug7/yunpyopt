from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import version as version_mod  # noqa: E402


def _make_repo(
    root: Path,
    *,
    version: str = "0.3.0",
    package_version: str | None = None,
    sdk_version: str = "0.3.1",
    release_workflow: str | None = None,
    changelog: str | None = None,
    readme: str = "# yunpyopt\n\n安装包版本见 `VERSION`。\n",
) -> Path:
    (root / "VERSION").write_text(f"{version}\n", encoding="utf-8")
    package = version if package_version is None else package_version
    (root / "pyproject.toml").write_text(
        f'[tool.poetry]\nname = "yunpyopt"\nversion = "{package}"\n',
        encoding="utf-8",
    )
    (root / "yun-sdk-version.txt").write_text(f"{sdk_version}\n", encoding="utf-8")
    workflow = (
        release_workflow
        if release_workflow is not None
        else "      - name: Verify version\n        run: python scripts/version.py check\n"
    )
    workflow_path = root / ".github" / "workflows" / "release.yml"
    workflow_path.parent.mkdir(parents=True)
    workflow_path.write_text(workflow, encoding="utf-8")
    changelog_text = changelog if changelog is not None else f"# 变更日志\n\n## [{version}] — Unreleased\n"
    (root / "CHANGELOG.md").write_text(changelog_text, encoding="utf-8")
    (root / "README.md").write_text(readme, encoding="utf-8")
    return root


def test_repository_versions_are_consistent():
    assert version_mod.check(ROOT) == []


def test_check_accepts_consistent_repo(tmp_path: Path):
    assert version_mod.check(_make_repo(tmp_path)) == []


def test_check_reports_pyproject_drift(tmp_path: Path):
    problems = version_mod.check(_make_repo(tmp_path, package_version="0.2.0"))

    assert any("pyproject.toml" in problem for problem in problems), problems


def test_check_reports_sdk_major_minor_drift(tmp_path: Path):
    problems = version_mod.check(_make_repo(tmp_path, sdk_version="0.4.0"))

    assert any("yun-sdk-version.txt" in problem for problem in problems), problems


def test_check_allows_sdk_patch_drift(tmp_path: Path):
    root = _make_repo(tmp_path, version="0.3.0", sdk_version="0.3.9")

    assert version_mod.check(root) == []


def test_check_reports_hardcoded_release_url_in_docs(tmp_path: Path):
    readme = (
        "pip install https://github.com/Hug7/yunpyopt/releases/download/"
        "v0.3.0/yunpyopt-0.3.0-cp311-cp311-win_amd64.whl\n"
    )
    problems = version_mod.check(_make_repo(tmp_path, readme=readme))

    assert any("README.md" in problem and "0.3.0" in problem for problem in problems), problems


def test_check_reports_hardcoded_version_in_release_workflow(tmp_path: Path):
    workflow = "        assert sdk == '0.3.0'\n        run: python scripts/version.py check\n"
    problems = version_mod.check(_make_repo(tmp_path, release_workflow=workflow))

    assert any("release.yml" in problem for problem in problems), problems


def test_check_reports_missing_changelog_section(tmp_path: Path):
    problems = version_mod.check(_make_repo(tmp_path, changelog="# 变更日志\n\n## [0.2.0] — Unreleased\n"))

    assert any("CHANGELOG.md" in problem for problem in problems), problems


def test_check_reports_tag_version_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v0.2.0")
    monkeypatch.setenv("GITHUB_REF_NAME", "v0.2.0")

    problems = version_mod.check(_make_repo(tmp_path))

    assert any("git tag" in problem for problem in problems), problems


def test_set_version_updates_version_and_pyproject(tmp_path: Path):
    root = _make_repo(tmp_path)

    version_mod.set_version("0.4.0", root=root)

    assert (root / "VERSION").read_text(encoding="utf-8").strip() == "0.4.0"
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["tool"]["poetry"]["version"] == "0.4.0"


def test_set_version_rejects_invalid_version(tmp_path: Path):
    with pytest.raises(version_mod.VersionError, match="X.Y.Z"):
        version_mod.set_version("0.4", root=_make_repo(tmp_path))


def test_bump_uses_semantic_version_parts():
    assert version_mod.next_version("1.2.3", "major") == "2.0.0"
    assert version_mod.next_version("1.2.3", "minor") == "1.3.0"
    assert version_mod.next_version("1.2.3", "patch") == "1.2.4"


def test_runtime_version_matches_version_file():
    import yunpyopt

    assert yunpyopt.__version__ == version_mod.read_version(ROOT)
