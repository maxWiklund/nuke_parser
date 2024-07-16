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
import re
from typing import Any, List, Optional, Union

from nuke_parser.nkview.qt import QtCore, QtGui, QtWidgets
from nuke_parser.parser import Node

NodePathRole = QtCore.Qt.UserRole + 1
NodeClassRole = QtCore.Qt.UserRole + 2
NodeFullNameRole = QtCore.Qt.UserRole + 3


class NodeItem(QtGui.QStandardItem):
    """Class representing outliner tree item of nuke node."""

    def __init__(self, node: Node):
        super(NodeItem, self).__init__()
        self.node = node
        self._icon = (
            QtGui.QIcon(":nuke_types/Group.png")
            if node.children()
            else QtGui.QIcon(f":nuke_types/{self.node.Class()}.png")
        )

    def data(self, role: int = ...) -> Any:
        """Returns the data stored under the given role.

        Args:
            role: Role enum (number).

        Returns:
            Data from model index.

        """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.node.nodeName()
        elif role == NodePathRole:
            return self.node.path()
        elif role == NodeClassRole:
            return self.node.Class()
        elif role == QtCore.Qt.ItemDataRole.DecorationRole:
            return self._icon
        return super(NodeItem, self).data(role)


class OutlinerModel(QtGui.QStandardItemModel):
    def __init__(self):
        super(OutlinerModel, self).__init__()
        self._zoom_factor = 1.0

    def zoomFactor(self) -> float:
        """Get zoom factor. Value to use when multiplying scale of row and font."""
        return self._zoom_factor

    def setZoomFactor(self, value: float):
        """Set zoom factor for the item. Value to scale the  row and font by."""
        self._zoom_factor = value

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> Any:
        """Request data from model.

        Args:
            index: Model index to query.
            role: Role enum (number).

        Returns:
            Data from model index.

        """
        if role == QtCore.Qt.ItemDataRole.FontRole:
            font = QtGui.QFont()
            font.setPointSizeF(12 * self.zoomFactor())
            return font
        elif role == QtCore.Qt.ItemDataRole.SizeHintRole:
            return QtCore.QSize(0, 25) * self.zoomFactor()
        return super().data(index, role)

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """Returns the item flags for the given index.

        Args:
            index: Model index to query.

        Returns:
            Flags for given index.

        """
        flags = QtCore.Qt.ItemFlag.ItemIsEnabled
        if index.data(NodeClassRole) != "Root":
            flags |= QtCore.Qt.ItemFlag.ItemIsSelectable

        return flags


class OutlinerFilterModel(QtCore.QSortFilterProxyModel):
    def __init__(self, source_model: OutlinerModel):
        super(OutlinerFilterModel, self).__init__()
        self.filter: Union[None, re.Pattern] = None
        self.setSourceModel(source_model)

    def setFilter(self, pattern: Union[re.Pattern, None]):
        """Set filter regex to use when filtering rows.

        Args:
            pattern: Regex to use when filtering.

        """
        self.filter = pattern
        self.invalidateFilter()

    def filterAcceptsRow(
        self, source_row: int, source_parent: QtCore.QModelIndex
    ) -> bool:
        """Filter row.

        Args:
            source_row: The row index.
            source_parent: The item's parent index.

        Returns:
            The result of the filters.

        """
        if not source_parent.isValid():
            return True  # Deal with root index.

        index = self.sourceModel().index(source_row, 0, source_parent)
        for row in range(self.sourceModel().rowCount(index)):
            if self.filterAcceptsRow(row, index):
                return True

        if self.sourceModel().rowCount(index):
            return False

        if self.filter and not self.filter.search(index.data(NodePathRole)):
            return False
        return True


class TreeView(QtWidgets.QTreeView):
    def __init__(self, parent: Optional[QtWidgets.QWidget]):
        super(TreeView, self).__init__(parent)

        self._scene_map = {}

        self.source_model = OutlinerModel()
        self.filter_model = OutlinerFilterModel(self.source_model)
        self.setModel(self.filter_model)
        self.setIconSize(QtCore.QSize(24, 24))
        self.setExpandsOnDoubleClick(False)
        self.setUniformRowHeights(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """Process wheel event.

        Args:
            event: Event to process.

        """
        if event.modifiers() == QtCore.Qt.ControlModifier:
            event.accept()

            delta = 0.09 if event.angleDelta().y() > 0 else -0.09
            self.source_model.setZoomFactor(self.source_model.zoomFactor() + delta)
            self.setIconSize(QtCore.QSize(24, 24) * self.source_model.zoomFactor())
            self.repaint()
            self.setIndentation(20 * self.source_model.zoomFactor())
            return
        super(TreeView, self).wheelEvent(event)

    def buildTree(self, root: Node):
        """Populate tree."""
        self.source_model.clear()
        self._scene_map = {}

        def build(node, parent) -> None:
            item = NodeItem(node)
            self._scene_map[node.path()] = item
            parent.appendRow(item)
            for child in node.children():
                build(child, item)

        build(root, self.source_model.invisibleRootItem())
        self.expandAll()

    def itemFromPath(self, path: str) -> Union[NodeItem, None]:
        """Get outliner tree item from node path.

        Args:
            path: Node path to get outliner item from.

        Returns:
            Outliner item.

        """
        return self._scene_map.get(path)


class OutlinerWidget(QtWidgets.QWidget):
    """Outliner widget."""

    nodesSelected = QtCore.Signal(object)
    nodesDeSelected = QtCore.Signal(object)
    navigated = QtCore.Signal(object)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super(OutlinerWidget, self).__init__(parent)
        self._selection_blocked = False

        #####################
        # Create Widgets:
        self._search_lineedit = QtWidgets.QLineEdit()
        self._view = TreeView(self)

        #####################
        # Widget settings:
        font = QtGui.QFont()
        font.setPointSize(16)
        self._search_lineedit.setFont(font)
        self._search_lineedit.setPlaceholderText("Search for...")

        self._view.header().setVisible(False)
        self._view.setAlternatingRowColors(True)
        self._view.setFocusPolicy(QtCore.Qt.NoFocus)

        #####################
        # Setup Layout:
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._search_lineedit)
        layout.addWidget(self._view)
        self.setLayout(layout)

        #####################
        # Setup signals:

        self._search_lineedit.textChanged.connect(self._updateFilterCallback)
        self._view.selectionModel().selectionChanged.connect(self._selectionCallback)
        self._view.doubleClicked.connect(self._navigateCallback)

        self.buildTree = self._view.buildTree

    def _navigateCallback(self, index: QtCore.QModelIndex) -> None:
        """Callback to emit node step into.

        Args:
            index: Model index that has been double-clicked.
        """
        self.navigated.emit(index.data(NodePathRole))

    def _selectionCallback(
        self,
        selected: QtCore.QItemSelection,
        deselected: QtCore.QItemSelection,
    ) -> None:
        """Selection change callback. Deal with selection changes."""
        if self._selection_blocked:
            return

        self._selection_blocked = True
        self.nodesSelected.emit(
            [index.data(NodePathRole) for index in selected.indexes()]
        )
        self.nodesDeSelected.emit(
            [index.data(NodePathRole) for index in deselected.indexes()]
        )
        self._selection_blocked = False

    def _updateFilterCallback(self) -> None:
        """Text search callback."""
        text = self._search_lineedit.text()

        # Search with new text and expand tree.
        self._view.filter_model.setFilter(
            re.compile(text, flags=re.IGNORECASE) if text else None
        )
        self._view.expandAll()

    def selectNodes(self, nodePaths: List[str]) -> None:
        """Select node pahts in tree-view.

        Args:
            nodePaths: Node paths to select.

        """
        self._selection_blocked = True

        nodes = filter(None, [self._view.itemFromPath(path) for path in nodePaths])
        indices = [
            self._view.filter_model.mapFromSource(node.index()) for node in nodes
        ]

        self._view.selectionModel().clear()
        for index in indices:
            self._view.selectionModel().select(index, QtCore.QItemSelectionModel.Select)
        self._selection_blocked = False
