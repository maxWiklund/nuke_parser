# Copyright (C) 2024  Max Wiklund
#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import copy
import json
import logging
import os
from typing import Any, Callable, List

from nuke_parser.nkview.qt import QtCore, QtWidgets

LOG = logging.getLogger(__name__)

_MAX_COUNT = 20


_CONFIG_ROOT = os.path.join(os.path.expanduser("~"), ".config")

_NKVIEW_SETTINGS = os.path.join(_CONFIG_ROOT, "nkview.json")


def addRecentlyOpened(file_path: str) -> None:
    """Add file to recently opened files.

    Args:
        file_path: File path to add.

    """
    file_paths = []
    config_data = {}
    if os.path.exists(_NKVIEW_SETTINGS):
        with open(_NKVIEW_SETTINGS) as f:
            config_data = json.load(f)
        file_paths = config_data.get("recently_opened", [])

    if file_path in file_paths:
        file_paths.remove(file_path)

    file_paths.insert(0, file_path)

    config_data["recently_opened"] = file_paths[:_MAX_COUNT]
    try:
        os.makedirs(_CONFIG_ROOT, exist_ok=True)
        with open(_NKVIEW_SETTINGS, "w") as f:
            json.dump(config_data, f, indent=4)
    except PermissionError:
        LOG.error("No Permission to save file")


def recentlyOpened() -> List[str]:
    """Get list of recently opened file."""
    if not os.path.exists(_NKVIEW_SETTINGS):
        return []
    with open(_NKVIEW_SETTINGS, "r") as f:
        return copy.deepcopy(json.load(f).get("recently_opened", []))


class WaitCursorContext(object):
    """Qt working cursor context."""

    def __enter__(self) -> WaitCursorContext:
        """Start Working cursor."""
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore cursor."""
        QtWidgets.QApplication.restoreOverrideCursor()


def qt_cursor(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """Decorator to add Qt cursor wheel on function call.

    Args:
        func: Function to decorate.

    Returns:
        Wrapper function.

    """
    # pylint: disable=missing-return-doc
    def wrapper(*args, **kwargs) -> Any:
        with WaitCursorContext():
            return func(*args, **kwargs)

    return wrapper
