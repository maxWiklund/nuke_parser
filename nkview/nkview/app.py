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
import argparse
import ctypes
import functools
import os
import platform
import sys

import nkview
from nkview import utils
from nkview.constants import QT_STYLE
from nkview.graph_view import NukeNodeGraphWidget
from nkview.outliner import OutlinerWidget
from nkview.qt import QtCore, QtGui, QtWebEngineWidgets, QtWidgets
from nuke_parser.parser import _parseGizmos


def _setupCli() -> argparse.Namespace:
    """Setup command line options.

    Returns:
        Parsed args.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", "-o", help="File path to nk file")
    return parser.parse_args()


class DocsWidget(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget):
        super(DocsWidget, self).__init__(parent)
        self.web_view = QtWebEngineWidgets.QWebEngineView()
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_view)
        self.setLayout(layout)

    def loadPage(self, url: str) -> None:
        self.web_view.load(QtCore.QUrl(url))


class NkViewMainWindow(QtWidgets.QMainWindow):
    """Main application window."""

    def __init__(self):
        super(NkViewMainWindow, self).__init__()
        self.setWindowTitle("NkView")
        self.setWindowIcon(QtGui.QIcon(":nuke.png"))
        self.resize(1500, 800)
        self.setStyleSheet(QT_STYLE)

        self.outliner = OutlinerWidget(self)

        self._node_graph_view = NukeNodeGraphWidget(self)

        spliter = QtWidgets.QSplitter()
        spliter.addWidget(self.outliner)
        spliter.addWidget(self._node_graph_view)
        spliter.setStretchFactor(1, 5)

        self.setCentralWidget(spliter)
        self._setupMenu()

        self._node_graph_view.sceneLoaded.connect(
            lambda node: self.outliner.buildTree(node.nk_node)
        )
        self._node_graph_view.scenePath.connect(self._setWindowTitleCallback)
        self._node_graph_view.scenePath.connect(self._updateRecentlyOpenedCallback)
        self.outliner.nodesSelected.connect(self._node_graph_view.selectNodes)
        self.outliner.nodesDeSelected.connect(self._node_graph_view.deselectNodes)
        self.outliner.navigated.connect(self._node_graph_view.navigateToNode)
        self._node_graph_view.selectionChanged.connect(self.outliner.selectNodes)

        self.loadNk = self._node_graph_view.loadNk

    def _setWindowTitleCallback(self, file_path: str) -> None:
        self.setWindowTitle(os.path.abspath(file_path))

    def _setupMenu(self) -> None:
        """Setup menubar."""
        file_menu = QtWidgets.QMenu("&File", self)
        open_action = QtWidgets.QAction(QtGui.QIcon(), "Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._openNkFileCallback)
        file_menu.addAction(open_action)

        self.open_recent = file_menu.addMenu(QtGui.QIcon(), "Open Recent")
        self._buildRecentlyOpenedMenu()

        file_menu.addSeparator()
        close_action = QtWidgets.QAction(QtGui.QIcon(), "Close", self)
        close_action.setShortcut("Ctr+Q")
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        help_menu = QtWidgets.QMenu("&Help", self)
        docs_action = QtWidgets.QAction(QtGui.QIcon(), "Documentation", self)
        docs_action.triggered.connect(self._openDocsCallback)
        help_menu.addAction(docs_action)

        self.menuBar().addMenu(file_menu)
        self.menuBar().addMenu(help_menu)

    def _openNkFileCallback(self) -> None:
        """Brows files to open nuke script."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select .nk file to open...",
            QtCore.QDir.currentPath(),
            "NK (*.nk)",
        )
        if path:
            self.loadNk(path)

    def _updateRecentlyOpenedCallback(self, file_path: str) -> None:
        utils.addRecentlyOpened(os.path.realpath(file_path))
        self._buildRecentlyOpenedMenu()

    def _buildRecentlyOpenedMenu(self) -> None:
        self.open_recent.clear()
        for path in utils.recentlyOpened():
            action = QtWidgets.QAction(QtGui.QIcon(), path, self)
            action.triggered.connect(
                functools.partial(self._node_graph_view.loadNk, path)
            )
            self.open_recent.addAction(action)

    def _openDocsCallback(self) -> None:
        win = DocsWidget(self)
        win.loadPage(
            "https://github.com/maxWiklund/nuke_parser/blob/master/docs/nkview.md"
        )
        win.show()
        win.exec()


def run() -> None:
    """Run app."""
    args = _setupCli()
    if platform.system() == "Windows":
        # Fix app icon on taskbar on Windows.
        app_id = f"nkview.{nkview.__version__}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(":nuke.png"))
    app.setStyle("Fusion")
    win = NkViewMainWindow()

    # Load gizmos.
    _parseGizmos()

    if args.open:
        win.loadNk(args.open)
    win.show()
    sys.exit(app.exec())
