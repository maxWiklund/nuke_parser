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

import platform
import sys
from typing import List, Optional, Union, Tuple

from nkview.gui_nodes import GroupNode, GuiNode
from nkview.navbar import NavigationBar
from nkview.qt import QtCore, QtGui, QtWidgets
from nkview.utils import qt_cursor
from nuke_parser.parser import parseNk, Node

INT_MAX = sys.maxsize // 2
INT_MIN = ~sys.maxsize // 2
if platform.system() == "Windows":
    # https://github.com/maxWiklund/nuke_parser/issues/1
    INT_MAX = (2**31) - 1  # Maximum value for a signed 32-bit integer
    INT_MIN = -(2**31)  # Minimum value for a signed 32-bit integer


class _PrivateApi:
    """Class to expose private methods of the node graph.
    Use it on your own risk."""

    def __init__(self, node_view: _NkGraphView):
        self._node_view = node_view

    def addGraphicsItemToScene(self, item: QtWidgets.QGraphicsItem) -> None:
        self._node_view.scene().addItem(item)

    def removeGraphicsItemFromScene(self, item):
        self._node_view.scene().removeItem(item)

    def selectedItems(self) -> List[QtWidgets.QGraphicsItem]:
        return self._node_view.scene().selectedItems()

    def guiNodeFromPath(self, path: str) -> Optional[GuiNode]:
        return self._node_view._scene_map.get(path)

    def clearSelection(self) -> None:
        self._node_view.scene().clearSelection()


class _NkGraphView(QtWidgets.QGraphicsView):
    """Private node graph view to to visualize nuke script."""

    sceneChanged = QtCore.Signal(object)
    sceneLoaded = QtCore.Signal(object)
    scenePath = QtCore.Signal(str)

    selectionChanged = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self._scene_map = {}
        self._last_mouse_pos = QtGui.QCursor.pos()

        self.setScene(QtWidgets.QGraphicsScene())
        self.centerOn(0, 0)

        self.setSceneRect(INT_MIN / 2, INT_MIN / 2, INT_MAX, INT_MAX)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)

    def setScene(self, scene: Optional[QtWidgets.QGraphicsScene]) -> None:
        """Set scene for view to display and setup selection signal.

        Args:
            scene: Scene to Display.

        """
        super().setScene(scene)
        if scene:
            scene.selectionChanged.connect(self.selectionChanged.emit)

    def setSelectStateOnNode(self, node_path: str, state: bool) -> None:
        """Set selection stata on node.

        Args:
            node_path: Path to node to set selection state on.
            state: If True select node else deselect node.

        """
        gui_node: GroupNode = self._scene_map.get(node_path)
        if gui_node:
            gui_node.setSelected(state)

    def guiNodeFromPath(self, node_path: str) -> Union[GuiNode, None]:
        """Get gui-node form node path.

        Args:
            node_path: Node path to get gui node from.

        Returns:

        """
        return self._scene_map.get(node_path)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Process drag enter event (drag file on to node graph).

        Args:
            event: Event to process.

        """
        if all(url.path().endswith(".nk") for url in event.mimeData().urls()):
            event.accept()
            return
        event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        """If ``dragEnterEvent`` has accepted the event, accept it and move on.

        Args:
            event: Event to process.

        """
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Load nk file.

        Args:
            event: Event to process.

        """
        for url in event.mimeData().urls():
            self.loadNk(url.toLocalFile())
            return
        event.accept()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Process key press events.

        Args:
            event: Event to process.

        """
        if event.key() == QtCore.Qt.Key_F:
            self.frameSelected()  # Frame selected nodes in graph.
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        """Process mouse double click event.

        Allow users to expand group nodes.


        Args:
            event: Event to process.

        """
        pos = event.pos()
        gui_node: GroupNode = self.itemAt(pos)
        if not gui_node or not isinstance(gui_node, GroupNode):
            super().mouseDoubleClickEvent(event)
            return

        self.stepIntoNode(gui_node)

    def stepIntoNode(self, gui_node: GroupNode) -> None:
        """Show node network inside node.

        Args:
            gui_node: Node to show content of.

        """
        nk_node = gui_node.nk_node
        if nk_node.children() or nk_node.Class() in ("Group", "Root"):
            # Store last viewport position to use when exiting the group.
            viewport_rect = self.mapToScene(self.viewport().geometry()).boundingRect()
            self.scene().groupNode().setViewportRect(viewport_rect)

            self.scene().clearSelection()
            self.setScene(gui_node.getScene())

            rect = gui_node.viewportRect()
            if rect:
                self.fitInView(rect, QtCore.Qt.KeepAspectRatio)
            else:
                self.frameSelected()
            self.sceneChanged.emit(gui_node)

    def frameSelected(self) -> None:
        """Frame selected nodes in graph is nodes are selected else frame scene."""
        selected = self.scene().selectedItems()
        box = QtCore.QRectF()
        for item in selected:
            item: QtWidgets.QGraphicsItem = item
            box = box.united(item.sceneBoundingRect())

        box = box if selected else self.scene().itemsBoundingRect()

        box_in_screen_space: QtCore.QRect = self.mapFromScene(box).boundingRect()

        screen_rect = self.viewport().rect()
        offset = 40
        if (
            box_in_screen_space.width() < screen_rect.width()
            or box_in_screen_space.height() < screen_rect.height()
        ):
            box.adjust(-offset // 2, -offset // 2, offset, offset)

        self.fitInView(box, QtCore.Qt.KeepAspectRatio)

    @qt_cursor
    def loadNk(self, file_path: str) -> None:
        """Load nuke script in graph view.

        Args:
            file_path: File path to nuke script.

        """
        if not file_path.endswith(".nk"):
            self.setScene(QtWidgets.QGraphicsScene())
            self.sceneLoaded.emit(None)
            return

        self._scene_map = {}
        self.root = parseNk(file_path)

        self.gui_root = GroupNode(self.root, self._scene_map)
        self.setScene(self.gui_root.getScene())
        self.frameSelected()
        self.sceneLoaded.emit(self.gui_root)
        self.scenePath.emit(file_path)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Process mouse move event.

        Args:
            event: Event to process.

        """
        if event.buttons() == QtCore.Qt.MouseButton.MiddleButton:
            mouse_delta = self.mapToScene(event.pos()) - self.mapToScene(
                self._last_mouse_pos
            )

            self.pan(mouse_delta)
            self._last_mouse_pos = event.pos()
            event.accept()
            return

        super().mouseMoveEvent(event)
        self._last_mouse_pos = event.pos()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Process mouse click event.

        Args:
            event: Event to process.

        """
        if event.buttons() == QtCore.Qt.MiddleButton:
            event.accept()
            return
        super().mousePressEvent(event)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """Process wheel event. Implement zoom in / out.

        Args:
            event: Event to process.

        """
        event.accept()
        delta = 1.0
        delta += 0.1 if event.angleDelta().y() > 0 else -0.1
        horizontal_scale = self.transform().m11() * delta

        # Max zoom in.
        if horizontal_scale > 4 and delta > 1:
            return
        self.setTransformationAnchor(
            QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )
        self.scale(delta, delta)

    def pan(self, delta: QtCore.QPointF) -> None:
        """Pan view.

        Args:
            delta: Delta to translate view with.

        """

        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.NoAnchor)
        self.translate(delta.x(), delta.y())

    def drawBackground(self, painter: QtGui.QPainter, rect: QtCore.QRect) -> None:
        """Draw graph background.

        Args:
            painter: Class to paint with.
            rect: Rect to paint on

        """
        painter.fillRect(rect, QtGui.QColor(59, 59, 59))


class NukeNodeGraphWidget(QtWidgets.QWidget):
    """Nuke node-graph widget."""

    scenePath = QtCore.Signal(str)
    sceneLoaded = QtCore.Signal(object)
    selectionChanged = QtCore.Signal(object)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super(NukeNodeGraphWidget, self).__init__(parent)
        self.nav_bar = NavigationBar(self)
        self._view = _NkGraphView(self)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.nav_bar.setFont(font)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.nav_bar)
        layout.addWidget(self._view)
        self.setLayout(layout)

        self._private_api = _PrivateApi(self._view)

        self._view.sceneChanged.connect(self.nav_bar.addItem)
        self._view.sceneLoaded.connect(self._sceneLoadedCallback)
        self._view.sceneLoaded.connect(self.sceneLoaded.emit)
        self._view.scenePath.connect(self.scenePath.emit)
        self.nav_bar.change_path.connect(self._changeSceneCallback)
        self._view.selectionChanged.connect(self._selectionChangedCallback)

        self.loadNk = self._view.loadNk
        self.frameSelected = self._view.frameSelected

    def privateApi(self) -> _PrivateApi:
        """API to interact with `QGraphicsScene` and `QGraphicsView`."""
        return self._private_api

    def selectedNodes(self) -> Tuple[Node, ...]:
        """Get selected nodes as nk_parser nodes."""
        return tuple(
            [
                node.nk_node
                for node in self._view.scene().selectedItems()
                if isinstance(node, GuiNode)
            ]
        )

    def _sceneLoadedCallback(self, root_node: GroupNode) -> None:
        """Scene loaded callback to deal with nav_bar.

        Args:
            root_node: New root node of scene.

        """
        self.nav_bar.clear()
        self.nav_bar.addItem(root_node)

    def _changeSceneCallback(self, node: GroupNode) -> None:
        """Callback when nav_bar want's to change the group node to view.

        Args:
            node: Node to view children of.

        """
        # Store the current viewport position if the user wants to set into the group again.
        viewport_rect = self._view.mapToScene(
            self._view.viewport().geometry()
        ).boundingRect()
        self._view.scene().groupNode().setViewportRect(viewport_rect)

        self._view.setScene(node.getScene())
        self._view.scene().clearSelection()

        rect = node.viewportRect()
        if rect:
            self._view.fitInView(rect, QtCore.Qt.KeepAspectRatio)
        else:
            self.frameSelected()

    def _selectionChangedCallback(self) -> None:
        """Callback to emit selection change."""
        self.selectionChanged.emit(
            [gui_node.nk_node.path() for gui_node in self._view.scene().selectedItems()]
        )

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Process show event.

        Args:
            event: Event to process.

        """
        super().showEvent(event)
        self.frameSelected()

    def selectNodes(self, node_paths: List[str]) -> None:
        """Select nodes in node graph.

        Args:
            node_paths: Node path to select in view.

        """
        for path in node_paths:
            self._view.setSelectStateOnNode(path, True)

    def deselectNodes(self, node_paths: List[str]) -> None:
        """Deselect node in node graph.

        Args:
            node_paths: Node path to deselect in view.

        """
        for path in node_paths:
            self._view.setSelectStateOnNode(path, False)

    def navigateToNode(self, path: str) -> None:
        """Step into node from node path.

        Args:
            path: Node path to step into.

        """
        gui_node = self._view.guiNodeFromPath(path)
        if not gui_node:
            return

        if not (
            gui_node.nk_node.isGizmo()
            or gui_node.nk_node.Class() in ("Group", "LiveGroup")
        ):
            return
        nodes = []

        node = gui_node.nk_node

        while node:
            nodes.insert(0, self._view.guiNodeFromPath(node.path()))
            node = node.parent()

        if self.nav_bar.getHead() == gui_node:
            return
        self.nav_bar.clear()
        for node in nodes:
            self._view.stepIntoNode(node)


def __test() -> None:
    template = "../../../test_scenes/nested_group.nk"

    app = QtWidgets.QApplication(sys.argv)
    win = NukeNodeGraphWidget()
    win.resize(1600, 1600)
    win.loadNk(template)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    __test()
