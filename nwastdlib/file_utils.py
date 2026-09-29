# Copyright 2019-2026 SURF, GÉANT.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for safely handling caller-supplied file names."""

import os
import re
from pathlib import Path
from typing import Annotated

import anyio
from pydantic import BeforeValidator, Field

#: Characters a caller-supplied file name may consist of. Such a name is meant to be used as a filesystem path,
#: so this allowlist keeps shell metacharacters, whitespace and control characters out of it, while ordinary
#: names (including ones in a subdirectory) are within it.
SAFE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")


class PathOutsideRootError(ValueError):
    """Raised when a caller-supplied name resolves to a path outside of its root directory."""

    def __init__(self, name: str | os.PathLike[str]) -> None:
        # Deliberately echoes only what the caller sent: naming the resolved path here would disclose the
        # server's filesystem layout to whoever probes an endpoint that surfaces this message.
        super().__init__(f"Path '{name}' is outside the configured root directory.")
        self.name = name


def _check_contained(root: Path, path: Path, name: str | os.PathLike[str]) -> Path:
    if not path.is_relative_to(root):
        raise PathOutsideRootError(name)
    return path


def resolve_within_root(root_dir: str | os.PathLike[str], name: str | os.PathLike[str]) -> Path:
    """Resolve a caller-supplied `name` inside `root_dir`, rejecting anything that escapes it.

    `Path(root_dir) / name` offers no containment on its own: `pathlib` discards `root_dir` entirely when `name`
    is absolute, and `..` segments walk out of it. Both sides are resolved before being compared, so that a
    symlinked root directory (a symlinked `/opt` or data mount is common in a container) does not reject
    names that are in fact contained.

    Resolving follows symlinks, so a symlink inside `root_dir` pointing outside of it is rejected as well.

    Which characters a name may consist of is a separate, declarative constraint; see `SafeName`.

    Args:
        root_dir: The configured directory that `name` has to stay inside of.
        name: The caller-supplied name to resolve against `root_dir`.

    Returns:
        The resolved path, guaranteed to lie inside `root_dir`.

    Raises:
        PathOutsideRootError: If the resolved path lies outside `root_dir`.

    """
    root = Path(root_dir).resolve()
    return _check_contained(root, (root / name).resolve(), name)


async def resolve_within_root_async(root_dir: str | os.PathLike[str], name: str | os.PathLike[str]) -> Path:
    """Async variant of `resolve_within_root` that does not block the event loop while resolving.

    Args:
        root_dir: The configured directory that `name` has to stay inside of.
        name: The caller-supplied name to resolve against `root_dir`.

    Returns:
        The resolved path, guaranteed to lie inside `root_dir`.

    Raises:
        PathOutsideRootError: If the resolved path lies outside `root_dir`.

    """
    root = Path(await anyio.Path(root_dir).resolve())
    return _check_contained(root, Path(await anyio.Path(root / name).resolve()), name)


def _reject_unsafe_name(value: str | os.PathLike[str]) -> str | os.PathLike[str]:
    """Reject a name holding characters outside `SAFE_NAME_PATTERN`.

    Raises:
        ValueError: If the name holds any other character. Pydantic turns this into a validation error (a 422
            in FastAPI), because this is a constraint on the shape of the input and not a judgement that needs
            the filesystem.

    """
    if not SAFE_NAME_PATTERN.fullmatch(str(value)):
        raise ValueError(f"Name '{value}' contains characters that are not allowed.")
    return value


#: A file name supplied by the caller, constrained to `SAFE_NAME_PATTERN`. The constraint is declared on the
#: field so that it lands in the OpenAPI schema, while the annotated type stays `Path`. Containment within
#: a root directory is a separate check: it needs the filesystem, so it cannot be a pattern. Use
#: `resolve_within_root` for that.
SafeName = Annotated[
    Path, BeforeValidator(_reject_unsafe_name), Field(json_schema_extra={"pattern": SAFE_NAME_PATTERN.pattern})
]
