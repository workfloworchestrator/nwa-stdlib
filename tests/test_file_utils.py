from pathlib import Path

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from nwastdlib.file_utils import (
    SAFE_NAME_PATTERN,
    PathOutsideRootError,
    SafeName,
    resolve_within_root,
)


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("/bin/sh", id="absolute-path"),
        pytest.param("/etc/passwd", id="absolute-path-to-unrelated-file"),
        pytest.param("..", id="parent-directory"),
        pytest.param("../../../../bin/sh", id="parent-traversal"),
        pytest.param("nested/../../../bin/sh", id="traversal-through-subdirectory"),
        pytest.param("/nonexistent-a1b2c3/nope", id="absolute-path-that-does-not-exist"),
    ],
)
def test_name_resolving_outside_root_is_rejected(name: str, tmp_path: Path) -> None:
    with pytest.raises(PathOutsideRootError) as exc:
        resolve_within_root(tmp_path, Path(name))

    assert exc.value.name == Path(name)
    # Only the caller-supplied name is echoed, never the resolved server-side path
    assert str(tmp_path.resolve()) not in str(exc.value)


def test_path_outside_root_error_is_a_value_error() -> None:
    assert issubclass(PathOutsideRootError, ValueError)


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("deploy.yaml", id="plain"),
        pytest.param("deploy_node-v2.yaml", id="underscore-and-hyphen"),
        pytest.param("nested/deploy.yaml", id="subdirectory"),
        pytest.param("nested/../deploy.yaml", id="traversal-staying-inside-root"),
        pytest.param("does-not-exist.md", id="non-existing-file"),
    ],
)
def test_ordinary_names_are_accepted(name: str, tmp_path: Path) -> None:
    assert resolve_within_root(tmp_path, Path(name)) == (tmp_path.resolve() / name).resolve()


def test_root_itself_is_accepted(tmp_path: Path) -> None:
    assert resolve_within_root(tmp_path, Path(".")) == tmp_path.resolve()


@pytest.mark.parametrize("name", ["deploy.yaml", Path("deploy.yaml")])
def test_accepts_str_and_path(name: str | Path, tmp_path: Path) -> None:
    assert resolve_within_root(str(tmp_path), name) == tmp_path.resolve() / "deploy.yaml"


def test_symlink_pointing_out_of_root_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.sh"
    outside.touch()
    (root / "innocent.sh").symlink_to(outside)

    with pytest.raises(PathOutsideRootError):
        resolve_within_root(root, Path("innocent.sh"))


def test_symlinked_root_still_accepts_contained_name(tmp_path: Path) -> None:
    """A root directory that is itself a symlink must not reject names that genuinely sit inside it.

    Containment is decided between two resolved paths. Comparing a resolved candidate against an unresolved
    root would reject every legitimate request as soon as the root, or any of its parents, is a symlink --
    routine in a container, and the case for temporary directories on macOS.
    """
    real_root = tmp_path / "real"
    real_root.mkdir()
    (real_root / "hello.sh").touch()
    linked_root = tmp_path / "linked"
    linked_root.symlink_to(real_root, target_is_directory=True)

    assert resolve_within_root(linked_root, Path("hello.sh")) == real_root.resolve() / "hello.sh"


safe_name_adapter = TypeAdapter(SafeName)


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("deploy.yaml", id="plain"),
        pytest.param("Deploy_Node-v2.yaml", id="mixed-case-underscore-and-hyphen"),
        pytest.param("nested/deploy.yaml", id="subdirectory"),
    ],
)
def test_safe_name_accepts_ordinary_names(name: str) -> None:
    assert safe_name_adapter.validate_python(name) == Path(name)


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("", id="empty"),
        pytest.param("innocent;id", id="semicolon"),
        pytest.param("innocent id", id="space"),
        pytest.param("innocent|id", id="pipe"),
        pytest.param("$(id)", id="command-substitution"),
        pytest.param("`id`", id="backticks"),
        pytest.param("innocent\nid", id="newline"),
        pytest.param("innocent\n", id="trailing-newline"),
        pytest.param("innocent\x00id", id="null-byte"),
        pytest.param("innocent&id", id="ampersand"),
        pytest.param("..\\..\\windows", id="backslash"),
        pytest.param("%2e%2e%2fetc", id="url-encoded"),
        pytest.param("café", id="non-ascii"),
        pytest.param("~root", id="tilde"),
    ],
)
def test_safe_name_rejects_disallowed_characters(name: str) -> None:
    with pytest.raises(ValidationError, match="not allowed"):
        safe_name_adapter.validate_python(name)


def test_safe_name_pattern_is_published_in_json_schema() -> None:
    class Model(BaseModel):
        name: SafeName

    assert Model.model_json_schema()["properties"]["name"]["pattern"] == SAFE_NAME_PATTERN.pattern
