# Copyright 2019-2023 SURF.
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
from pydantic import VERSION

if VERSION > "2.0":
    from pydantic_settings import BaseSettings
else:
    from pydantic import BaseSettings  # type: ignore[no-redef]


class NwaSettings(BaseSettings):
    """Common settings for applications depending on nwa-stdlib."""

    DEBUG_VSCODE: bool = False
    DEBUG_PYCHARM: bool = False


nwa_settings = NwaSettings()
