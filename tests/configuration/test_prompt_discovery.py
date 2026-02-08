from __future__ import annotations

from pathlib import Path

from tnh_scholar.configuration.context import TNHContext


def _build_context(
    *,
    builtin_root: Path,
    workspace_root: Path | None,
    user_root: Path,
) -> TNHContext:
    return TNHContext(
        builtin_root=builtin_root,
        workspace_root=workspace_root,
        user_root=user_root,
        correlation_id="corr",
        session_id="sess",
    )


def test_prompt_search_paths_precedence(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    user_root = tmp_path / "user"
    builtin_root = tmp_path / "builtin"

    (workspace_root / "prompts").mkdir(parents=True)
    (user_root / "prompts").mkdir(parents=True)
    (builtin_root / "prompts").mkdir(parents=True)

    context = _build_context(
        builtin_root=builtin_root,
        workspace_root=workspace_root,
        user_root=user_root,
    )

    assert context.get_prompt_search_paths() == [
        workspace_root / "prompts",
        user_root / "prompts",
        builtin_root / "prompts",
    ]


def test_prompt_search_paths_skip_missing(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    user_root = tmp_path / "user"
    builtin_root = tmp_path / "builtin"

    workspace_root.mkdir(parents=True)
    (user_root / "prompts").mkdir(parents=True)
    (builtin_root / "prompts").mkdir(parents=True)

    context = _build_context(
        builtin_root=builtin_root,
        workspace_root=workspace_root,
        user_root=user_root,
    )

    assert context.get_prompt_search_paths() == [
        user_root / "prompts",
        builtin_root / "prompts",
    ]


def test_primary_prompt_dir_none_when_no_dirs(tmp_path: Path) -> None:
    context = _build_context(
        builtin_root=tmp_path / "builtin",
        workspace_root=tmp_path / "workspace",
        user_root=tmp_path / "user",
    )

    assert context.get_primary_prompt_dir() is None
