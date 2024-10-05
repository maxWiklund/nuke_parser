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
from dataclasses import dataclass
from typing import List, Optional

from nkview.constants import SELECTED_COLOR
from nkview.gui_nodes import GroupNode
from nkview.qt import QtCore, QtGui, QtWidgets


@dataclass()
class PrivateShape:
    """Class holding polygon data for nav item."""

    poly: QtGui.QPolygonF
    path: QtGui.QPainterPath
    node: GroupNode


class NavigationBar(QtWidgets.QWidget):
    """Navigation bar widget."""

    change_path = QtCore.Signal(object)
    _ARROW_DELTA = 5

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """Initialize class and do nothing.

        Args:
            parent: Parent widget.

        """
        super(NavigationBar, self).__init__(parent)
        self.setMouseTracking(True)
        self._items: List[GroupNode] = []

    def minimumSizeHint(self) -> QtCore.QSize:
        """Widget size hint."""
        height = QtGui.QFontMetrics(self.font()).height() + 10
        width = (
            sum(shape.poly.boundingRect().width() for shape in self._getShapes()) or 1
        )
        return QtCore.QSize(width, height)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Process mouse move event.

        Args:
            event: Event to process.

        """
        super(NavigationBar, self).mouseMoveEvent(event)
        self.update()

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        """Process mouse leave event.

        Args:
            event: Event to process.

        """
        super(NavigationBar, self).leaveEvent(event)
        self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Process mouse press event.

        Args:
            event: Event to process.

        """
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            super(NavigationBar, self).mousePressEvent(event)
            return

        for shape in self._getShapes():
            if self._cursorAbove(shape):
                self._setTailItem(shape.node)
                event.accept()
                break

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Process paint event.

        Args:
            event: Event to process.

        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        for shape in self._getShapes():
            color = (
                QtGui.QColor(SELECTED_COLOR)
                if self._cursorAbove(shape)
                else QtCore.Qt.gray
            )
            painter.setPen(QtCore.Qt.black)
            painter.fillPath(shape.path, QtGui.QBrush(color))
            painter.drawPolygon(shape.poly)

            painter.setPen(QtCore.Qt.white)
            painter.drawText(
                shape.poly.boundingRect(),
                QtCore.Qt.AlignCenter,
                str(shape.node.name()),
            )
        event.accept()

    def _setTailItem(self, node: GroupNode) -> None:
        """Set new tail of list and repaint widget

        Args:
            item: New tail item.

        """
        index = self._items.index(node) + 1
        while index < len(self._items):
            self._items.pop(index)
        self.update()
        self.change_path.emit(node)

    def clear(self) -> None:
        """Clear all items."""
        self._items = []
        self.update()

    def _cursorAbove(self, shape: PrivateShape) -> bool:
        """Check if the cursor is above the shape obj.

        Args:
            shape: Shape object to check.

        Returns:
            True if cursor is above shape.

        """
        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        return shape.poly.containsPoint(pos, QtCore.Qt.WindingFill)

    def _createShape(
        self,
        left: int,
        width: int,
        height: int,
        item: GroupNode,
        not_first: bool = False,
    ) -> PrivateShape:
        """Create shape item to be painted.

        Args:
            left: Left start position.
            width: Width of item.
            height: Height of item.
            item: Private item to represent.
            not_first: If True draw straight line at start of polygon else draw arrow.

        Returns:
            Shape item to be used for drawing and intersection check.

        """

        # fmt: off
        positions = [
            QtCore.QPointF(left, 0),  # Left top
            QtCore.QPointF(left + width, 0),  # Right top
            QtCore.QPointF(left + width + self._ARROW_DELTA, height / 2),  # Right middel
            QtCore.QPointF(left + width, height),  # Right bottom
            QtCore.QPointF(left, height),  # Left bottom
        ]
        # fmt: on
        if not_first:
            positions.append(QtCore.QPointF(left + self._ARROW_DELTA, height / 2))

        polygon = QtGui.QPolygonF()
        for point in positions:
            polygon.append(point)

        path = QtGui.QPainterPath()
        path.addPolygon(polygon)
        path.closeSubpath()
        return PrivateShape(polygon, path, item)

    def getHead(self) -> GroupNode:
        """Get the latest node in navigation bar.

        Returns:
            The last item in the widget.

        """
        return self._items[-1] if self._items else None

    def addItem(self, node: GroupNode) -> None:
        """Add tree node to navigation widget.

        Args:
            node: Node to att to widget.

        """
        if self.getHead() == node:
            return
        self._items.append(node)
        self.updateGeometry()
        self.update()

    def _getShapes(self) -> List[PrivateShape]:
        """Get shape objects to draw.

        Returns:
            Shape nodes to draw and check for hover and mouse click.

        """
        fm = QtGui.QFontMetrics(self.font())
        left = self.rect().left()
        shapes = []
        for i, node in enumerate(self._items):
            width = fm.horizontalAdvance(node.name()) + 30  # 30 is the offset
            shapes.append(
                self._createShape(left, width, self.rect().height(), node, bool(i))
            )
            left += width + 2
        return shapes
