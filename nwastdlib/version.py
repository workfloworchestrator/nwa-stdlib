# Copyright 2019-2025 SURF.
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

from subprocess import check_output  # noqa: S404

import structlog

logger = structlog.getLogger(__name__)


def __getattr__(name: str) -> str | None:
    """Return the GIT_COMMIT_HASH.

    Usage::

        from server.version import GIT_COMMIT_HASH
        print(GIT_COMMIT_HASH)

    Args:
        name: "GIT_COMMIT_HASH"

    Returns: current GIT commit SHA if any.

    """
    if name != "GIT_COMMIT_HASH":
        raise AttributeError(name)
    try:
        return check_output(["/usr/bin/env", "git", "rev-parse", "HEAD"]).decode().strip()  # noqa: S603
    except Exception:
        logger.exception("Could not get git commit hash")
        return None
