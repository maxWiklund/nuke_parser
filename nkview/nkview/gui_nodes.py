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

from dataclasses import dataclass
import math
from typing import Dict, List, Optional, Tuple, Type, Union

import networkx as nx

from nkview import constants
from nkview.qt import QtCore, QtGui, QtWidgets, PYSIDE6
from nuke_parser.parser import Node
from nuke_parser.stack import Stack

SCALE = 80

EDGE_LENGTH_MIN = 0.1
ARROW_SIZE_CONNECTED = 7
ARROW_HEAD_ANGLE = (3 * math.pi) / 15


def polygonToLines(polygon: QtGui.QPolygonF) -> List[QtCore.QLineF]:
    lines = []
    for i in range(polygon.size()):
        lines.append(
            QtCore.QLineF(
                polygon[i],
                polygon[(i + 1) % polygon.size()],  # wrap around to the first point
            )
        )
    return lines


def defaultNodeColor(class_: str) -> QtGui.QColor:
    """Get default node color from node class.

    Args:
        class_: Node class to get color for.

    Returns:
        Default node color.

    """
    name = constants.NUKE_NODE_COLORS.get(class_, "#a3a3a3")
    return QtGui.QColor(name)


@dataclass()
class Shape:
    """Class holding node shape."""

    polygon: QtGui.QPolygonF  # Polygon to draw the node shape.
    outline: QtGui.QPainterPath  # Outline of node shape.
    selected: QtGui.QPolygonF  # Polygon to draw selected node.


def _createShape(points: Tuple[Tuple[float, float], ...], scale: float = 1.0) -> Shape:
    """Create shape object from node points

    Args:
        points: 2D node vertices of shape.
        scale: Vertical scale of node shape.

    """
    outline = QtGui.QPolygonF()
    selected = QtGui.QPolygonF()

    for p in [QtCore.QPointF(p[0] * SCALE, p[1] * (SCALE * scale)) for p in points]:
        outline.append(p)
        selected.append(p)

    outline_path = QtGui.QPainterPath()
    outline_path.addPolygon(outline)
    outline_path.closeSubpath()
    center = outline.boundingRect().center()

    tf = QtGui.QTransform()
    tf.scale(0.9, 0.9)
    selected = tf.map(selected)

    offset = center - selected.boundingRect().center()
    selected.translate(offset.x(), offset.y())

    return Shape(outline, outline_path, selected)


def shapeFromClass(node: Node, scale: float = 1.0) -> Shape:
    """Get shape class from node.

    Args:
        node: Node to get shape for.
        scale: Vertical scale of node shape.

    Returns:
        Shape of node.

    """

    if node.isGizmo():
        return _createShape(constants.GIZMO_SHAPE, scale)

    class_name = node.Class()
    if class_name in ("Scene", "GeoScene", "Camera3"):
        return _createShape(constants.SCENE_3D_SHAPE)
    elif class_name in ("CameraTrackerPointCloud", "ModelBuilder"):
        return _createShape(constants.GEO_SHAPE, scale)
    elif class_name in ("Viewer", "Switch"):
        return _createShape(constants.VIEWER_SHAPE, scale)
    elif class_name == "Read":
        return _createShape(constants.READ_SHAPE)
    elif class_name == "Group":
        return _createShape(constants.GROUP_SHAPE, scale)
    elif class_name == "Output":
        return _createShape(constants.OUTPUT_SHAPE, scale)
    elif class_name == "Input":
        return _createShape(constants.INPUT_SHAPE, scale)
    elif class_name == "Dot":
        return _createShape(constants.DOT_SHAPE)
    return _createShape(constants.BASE_SHAPE, scale)


def nukeColorToRgb(num: str) -> QtGui.QColor:
    """Convert nuke 32 bit hex to 8 bit rgb."""
    hex_value = int(num, 16)
    red = (hex_value >> 24) & 0xFF
    green = (hex_value >> 16) & 0xFF
    blue = (hex_value >> 8) & 0xFF
    return QtGui.QColor(red, green, blue)


class ConnectionLine(QtWidgets.QGraphicsLineItem):
    """Class representing connection line."""

    def __init__(
        self,
        input_name: str,
        source: DagNode,
        target: DagNode,
        dash_line=False,
    ):
        self.source = source
        self.target = target
        super().__init__()
        self.input_name = input_name
        self._dash_line = dash_line
        self.setZValue(0.8)

        line = QtCore.QLineF(target.center(), source.center())

        polygon = self.mapFromItem(self.target, self.target._shape_cls.polygon)
        edges = polygonToLines(polygon)
        for edge in edges:
            _type, point = edge.intersects(line)
            if _type == QtCore.QLineF.BoundedIntersection:
                line = QtCore.QLineF(point, self.source.center())
                break

        self.setLine(line)

        a = math.acos(line.dx() / max(EDGE_LENGTH_MIN, line.length()))
        if line.dy() < 0:
            a = 2 * math.pi - a

        arrow_size = ARROW_SIZE_CONNECTED * 2
        arrow_p1 = line.p1() + QtCore.QPointF(
            math.cos(a + ARROW_HEAD_ANGLE / 2) * arrow_size,
            math.sin(a + ARROW_HEAD_ANGLE / 2) * arrow_size,
        )

        arrow_p2 = line.p1() + QtCore.QPointF(
            math.cos(a - ARROW_HEAD_ANGLE / 2) * arrow_size,
            math.sin(a - ARROW_HEAD_ANGLE / 2) * arrow_size,
        )

        self.text_pos = line.p1() + QtCore.QPointF(
            math.cos(a) * arrow_size,
            math.sin(a) * arrow_size,
        )

        self.arrow_head = QtGui.QPolygonF()
        for p in [line.p1(), arrow_p1, arrow_p2]:
            self.arrow_head.append(p)

        line_with_offset = QtCore.QLineF(line.p2(), line.p1())
        line_with_offset.setLength(line_with_offset.length() - ARROW_SIZE_CONNECTED)

        self.setLine(QtCore.QLineF(line_with_offset.p2(), line_with_offset.p1()))

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: QtWidgets.QWidget = ...,
    ) -> None:
        """Paint connection line.

        Args:
            painter: Painter to use.
            option: Painting options.
            widget: Widget to paint.

        """
        painter.save()

        line_color = QtGui.QColor(0, 0, 0)

        pen = QtGui.QPen(line_color)
        pen.setWidth(3)
        if self._dash_line:
            pen.setStyle(QtCore.Qt.DashLine)
            pen.setDashPattern([2, 3])

        painter.setPen(pen)
        painter.drawLine(self.line())

        head_path = QtGui.QPainterPath()
        head_path.addPolygon(self.arrow_head)
        head_path.closeSubpath()
        painter.fillPath(head_path, QtGui.QBrush(line_color))

        if self.target.nk_node.Class() != "Dot":
            # Draw input name text.
            fm = QtGui.QFontMetricsF(painter.font())
            input_text_rect = QtCore.QRectF(
                0, 0, fm.horizontalAdvance(self.input_name), fm.height()
            )
            painter.setPen(QtGui.QColor(224, 187, 2))
            painter.setPen(QtCore.Qt.white)
            input_text_rect.moveCenter(self.text_pos)
            painter.drawText(
                input_text_rect,
                QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter,
                self.input_name,
            )

        painter.restore()


class StickyNoteNode(QtWidgets.QGraphicsRectItem):
    """Class representing sticky note."""

    def __init__(self, nk_node: Node):
        super().__init__()
        self.nk_node = nk_node
        self.setPos(QtCore.QPoint(self.nk_node.xpos(), self.nk_node.ypos()))

        font = QtGui.QFont()
        font.setPointSize(nk_node.knob("note_font_size", 14))
        fm = QtGui.QFontMetrics(font)
        text = nk_node.knob("label")
        width = max([100] + [fm.horizontalAdvance(line) for line in text.split("\n")])

        height = fm.height() * len(text.split("\n"))

        self.setRect(QtCore.QRect(0, 0, width + 10, height))
        self.setBrush(QtGui.QColor(204, 205, 118))
        self.setZValue(0.7)

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: Optional[QtWidgets.QWidget] = ...,
    ) -> None:
        """Paint nuke node.

        Args:
            painter: Painter to use.
            option: Painting options.
            widget: Widget to paint.

        """
        super().paint(painter, option, widget)
        painter.save()

        font = QtGui.QFont()
        font.setPointSize(self.nk_node.knob("note_font_size", 14))
        painter.setFont(font)
        draw_rect = self.rect()
        draw_rect.setLeft(draw_rect.left())
        draw_rect.setTop(draw_rect.top())
        draw_rect.setRight(draw_rect.right())

        painter.drawText(
            draw_rect,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter,
            self.nk_node.knob("label"),
        )
        painter.restore()


class BackdropNode(QtWidgets.QGraphicsRectItem):
    """Class represent backdrop node."""

    def __init__(self, nk_node: Node):
        super().__init__()
        self.nk_node = nk_node
        self.setPos(QtCore.QPoint(self.nk_node.xpos(), self.nk_node.ypos()))

        self.setRect(
            QtCore.QRect(
                0,
                0,
                self.nk_node.knob("bdwidth", 0),
                self.nk_node.knob("bdheight", 0),
            )
        )
        z_value = (self.nk_node.knob("z_order") or 0) / 1000
        self.setZValue(z_value)

        color_text = self.nk_node.knob("tile_color")

        self.setBrush(
            nukeColorToRgb(color_text) if color_text else QtGui.QColor(130, 130, 130)
        )

    def center(self) -> QtCore.QPoint:
        """Get center of node."""
        return self.pos() + self.rect().center()

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: Optional[QtWidgets.QWidget] = ...,
    ) -> None:
        """Paint nuke node.

        Args:
            painter: Painter to use.
            option: Painting options.
            widget: Widget to paint.

        """
        super().paint(painter, option, widget)

        # Draw node name
        offset = 20
        name_rect = QtCore.QRectF(self.rect())
        name_rect.setTop(name_rect.top() + 3)
        name_rect.setLeft(name_rect.left() + offset)
        name_rect.setRight(name_rect.right() - offset)
        name_rect.setBottom(name_rect.top() + offset)

        color = self.brush().color()
        painter.fillRect(name_rect, color.lighter(118))
        painter.drawText(
            name_rect,
            QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter,
            self.nk_node.nodeName(),
        )

        # Draw corners

        top_left = self.rect().topLeft() + QtCore.QPointF(1, 1)
        top_right = self.rect().topRight() + QtCore.QPointF(-1, 1)
        bottom_right = self.rect().bottomRight() + QtCore.QPointF(-1, -1)
        bottom_left = self.rect().bottomLeft() + QtCore.QPointF(1, -1)
        poyls = (
            [
                top_left,
                top_left + QtCore.QPointF(offset, 0),
                top_left + QtCore.QPointF(0, offset),
            ],  # Top left
            [
                top_right,
                top_right + QtCore.QPointF(0, offset),
                top_right + QtCore.QPointF(-offset, 0),
            ],  # Top right
            [
                bottom_right,
                bottom_right + QtCore.QPointF(-offset, 0),
                bottom_right + QtCore.QPointF(0, -offset),
            ],  # Bottom right
            [
                bottom_left,
                bottom_left + QtCore.QPointF(0, -offset),
                bottom_left + QtCore.QPointF(offset, 0),
            ],
        )
        painter.save()
        painter.setBrush(self.brush().color().lighter(130))
        painter.setPen(QtCore.Qt.NoPen)
        for points in poyls:
            painter.drawPolygon(points)
        painter.restore()

        font = QtGui.QFont()
        font.setPointSize(self.nk_node.knob("note_font_size", 14) * 0.5)
        painter.save()
        painter.setFont(font)

        offset = 10
        draw_rect = self.rect()
        draw_rect.setLeft(draw_rect.left() + offset)
        draw_rect.setTop(name_rect.bottom())
        draw_rect.setRight(draw_rect.right() - offset)

        text_color = (
            QtCore.Qt.white
            if self.brush().color().lightness() < 80
            else QtCore.Qt.black
        )
        painter.setPen(text_color)
        painter.drawText(
            draw_rect,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop | QtCore.Qt.TextWordWrap,
            self.nk_node.knob("label"),
        )
        painter.restore()


class DagNode(QtWidgets.QGraphicsItem):
    """Class represent nuke nodes."""

    def __init__(self, nk_node: Node):
        super(DagNode, self).__init__()
        self._shape_cls = shapeFromClass(nk_node)

        self.nk_node = nk_node
        if nk_node.Class() != "Root":
            self.setZValue(1)
            self.setPos(QtCore.QPoint(self.nk_node.xpos(), self.nk_node.ypos()))

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        hex_color = self.nk_node.knob("tile_color")
        self.node_color = (
            nukeColorToRgb(hex_color)
            if hex_color
            else defaultNodeColor(self.nk_node.Class())
        )

    def nodeText(self) -> str:
        return self.nk_node.name()

    def nodeShapePointsInWorldSpace(self) -> List[QtCore.QPointF]:
        return [self.pos() + point for point in self._shape_cls.polygon]

    def boundingRect(self) -> QtCore.QRectF:
        """Get bounding rect of node."""
        font = QtGui.QFont()
        fm = QtGui.QFontMetrics(font)
        width = fm.horizontalAdvance(self.nodeText())
        rect = self._shape_cls.polygon.boundingRect()
        if width > rect.width():
            delta = width - rect.width()
            rect.setLeft(rect.left() - delta // 2)
            rect.setRight(rect.right() + delta // 2)
        return rect

    def shape(self) -> QtGui.QPainterPath:
        """Get outline of node."""
        return self._shape_cls.outline

    def center(self) -> QtCore.QPoint:
        """Get center of node."""
        return self.pos() + self._shape_cls.polygon.boundingRect().center()

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: Optional[QtWidgets.QWidget] = ...,
    ) -> None:
        """Paint nuke node.

        Args:
            painter: Painter to use.
            option: Painting options.
            widget: Widget to paint.

        """
        painter.save()
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))

        m_gradient = QtGui.QLinearGradient(
            0, 0, 0, self._shape_cls.polygon.boundingRect().height()
        )
        m_gradient.setColorAt(0.0, self.node_color.lighter(150))
        m_gradient.setColorAt(0.5, self.node_color)
        m_gradient.setColorAt(1.0, self.node_color.lighter(70))

        painter.setBrush(m_gradient)
        painter.drawPolygon(self._shape_cls.polygon)

        if self.isSelected():
            painter.save()
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(constants.SELECTED_COLOR)
            painter.drawPolygon(self._shape_cls.selected)
            painter.restore()

        if self.nk_node.disable():
            painter.save()
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 3))
            rect = self._shape_cls.polygon.boundingRect()

            lines = [
                QtCore.QLineF(rect.topLeft(), rect.bottomRight()),
                QtCore.QLineF(rect.topRight(), rect.bottomLeft()),
            ]
            painter.drawLines(lines)
            painter.restore()

        # Draw clone icon
        if self.nk_node.isClone():
            top_left = self._shape_cls.polygon.boundingRect().topLeft()
            text_rect = QtCore.QRectF(top_left, top_left + QtCore.QPointF(10, 10))
            painter.save()
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
            font = QtGui.QFont()
            font.setPixelSize(9)
            painter.setFont(font)
            painter.setBrush(QtGui.QColor(208, 112, 80))
            painter.drawEllipse(text_rect)
            painter.setPen(QtCore.Qt.white)
            painter.drawText(
                text_rect, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter, "c"
            )
            painter.restore()

        text_rect = QtCore.QRectF(self.boundingRect())
        text_rect.setTop(text_rect.top() + 2)
        if self.nk_node.Class() != "Dot":
            vlayout = (
                QtCore.Qt.AlignBottom
                if self.nk_node.Class() == "Read"
                else QtCore.Qt.AlignVCenter
            )

            text_color = (
                QtCore.Qt.white
                if self.node_color.lightness() < 100
                else QtCore.Qt.black
            )
            painter.setPen(text_color)
            font = QtGui.QFont()
            font.setPointSize(self.nk_node.knob("note_font_size", 10) * 0.5)

            painter.drawText(
                text_rect,
                self.nodeText(),
                QtCore.Qt.AlignHCenter | vlayout,
            )
        painter.restore()


class GroupNode(DagNode):
    """Class represent group node.

    A group node stores a ``QGraphicsScene`` with its children.
    Any node with children will be created as a ``GroupNode``

    """

    def __init__(self, nk_node: Node, scene_map: Dict[str, DagNode]):
        super(GroupNode, self).__init__(nk_node)
        scene_map[nk_node.path()] = self
        self._scene = NkScene(nk_node, scene_map, self)
        self._viewport_rect = None

    def viewportRect(self) -> Union[QtCore.QRectF, None]:
        """Returns the viewport rect from the node (The scene area that was last viewed to restore
        the view where the user left it).

        """
        return self._viewport_rect

    def setViewportRect(self, rect: QtCore.QRect) -> None:
        """Set the viewport rect on the node (the visible rectangle of the graphics-view).

        Args:
            rect: Rect to store.

        """
        self._viewport_rect = rect

    def getScene(self) -> QtWidgets.QGraphicsScene:
        """Get scene from node."""
        return self._scene

    def name(self) -> str:
        """Get node name."""
        return self.nk_node.nodeName()


GuiNode = Union[DagNode, BackdropNode, StickyNoteNode]


def getNodeClass(node: Node) -> Type[GuiNode]:
    """Get gui node class from node.

    Args:
        node: Node to get gui class from.

    Returns:
        Gui node (node graph) from node.

    """
    if node.children() or node.Class() == "Group":
        return GroupNode
    return {
        "Group": GroupNode,
        "StickyNote": StickyNoteNode,
        "BackdropNode": BackdropNode,
    }.get(node.Class(), DagNode)


def niceInputName(index: int, Class: str) -> str:
    """Get nice input name from input index and class name.

    Args:
        index: Input index to get nice name from.
        Class: Class name of node to get input name from.

    Returns:
        Nice input name.

    """
    if Class.startswith("Merge"):
        return (["A", "B", "Mask"] + [f"A+{i}" for i in range(1, index + 1)])[index]

    return str(index + 1)  # Users want the index to start from 1.


class NkScene(QtWidgets.QGraphicsScene):
    """Scene that performs automatic layout on any node with missing position values."""

    def __init__(self, root: Node, scene_map: Dict[str, DagNode], parent: GroupNode):
        super().__init__()
        self._group_node = parent
        node_map = {}
        self._autoLayout(list(root.children()))

        for node in root.children():
            class_ = getNodeClass(node)
            args = (
                (node, scene_map)
                if node.children() or node.Class() == "Group"
                else (node,)
            )
            dag_node = class_(*args)

            node_map[node.path()] = dag_node
            scene_map[node.path()] = dag_node
            self.addItem(dag_node)

        for gui_node in node_map.values():
            for i, node in enumerate(gui_node.nk_node.inputs()):
                out_node = node_map[node.path()]
                line = ConnectionLine(
                    niceInputName(i, gui_node.nk_node.Class()),
                    out_node,
                    gui_node,
                    gui_node.nk_node.Class() == "Viewer",
                )
                self.addItem(line)

            # Add clone line.
            clone_source_nk = gui_node.nk_node._source_node
            if clone_source_nk and node_map[clone_source_nk.path()]:
                source = node_map[clone_source_nk.path()]

                line = QtWidgets.QGraphicsLineItem(
                    QtCore.QLineF(gui_node.center(), source.center())
                )
                pen = QtGui.QPen(QtGui.QColor(211, 110, 75), 2)
                line.setPen(pen)
                self.addItem(line)

    def groupNode(self) -> GroupNode:
        """Get the group node (the parent node of all nodes in the graphics scene).

        Returns:
            Parent node (GUI node) of all nodes in graphics scene.

        """
        return self._group_node

    @staticmethod
    def _assingLevels(G: nx.DiGraph) -> Dict[int, List[Node]]:
        """Assign levels to nodes in the graph based on their positions
        and group them.

        Args:
            G: Graph to process.

        Returns:
            Dict where key is level and values are nodes on that level.

        """
        levels = {}
        # Assign levels to each node
        for node in nx.topological_sort(G):
            if node in levels:
                continue
            level = 0
            stack = Stack[Node]()
            stack.push(node)
            while not stack.empty():
                current = stack.pop()
                levels.setdefault(current, level)

                for successor in G.successors(current):
                    if successor not in levels:
                        stack.push(successor)
                        levels[successor] = levels[current] + 1

        # Group nodes by levels.
        level_nodes = {}
        for node, level in levels.items():
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node)
        return level_nodes

    def _autoLayout(self, nodes: List[Node]) -> None:
        """Auto layout any node with missing position.

        Args:
            nodes: All nodes in scene.

        """
        # Build DAG.
        G = nx.DiGraph()
        for node in nodes:
            G.add_node(node)
            for output in node._outputs:
                G.add_edge(node, output)

        top_nodes = self._findUpstreamNodesToLayoutFrom(G)
        start_x = (
            sum([n.xpos() for n in top_nodes]) // len(top_nodes) if top_nodes else 0
        )
        start_y = (
            sum([n.ypos() for n in top_nodes]) // len(top_nodes) if top_nodes else 0
        )

        level_nodes = self._assingLevels(G)

        # Align nodes in straight horizontal lines based on levels
        for level, nodes_in_level in level_nodes.items():
            # Sort nodes by their x positions if they exist
            sorted_nodes = sorted(
                nodes_in_level,
                key=lambda n: (n.xpos() if n.xpos() is not None else float("inf")),
            )
            nodes_geo = [
                shapeFromClass(node).polygon.boundingRect() for node in sorted_nodes
            ]
            height = max(nodes_geo, key=lambda rect: rect.height()).height()

            h_space = 5
            v_space = 5
            x = start_x + h_space
            for i, node in enumerate(sorted_nodes):
                if node.xpos() is None or node.ypos() is None:
                    node.setXpos(x)
                    node.setYpos(start_y)
                x += nodes_geo[i].width() + h_space
            start_y += height + v_space

    @staticmethod
    def _findUpstreamNodesToLayoutFrom(G: nx.DiGraph) -> List[Node]:
        """Find nodes with output to nodes with no position.

        Args:
            G: GAG to process.

        Returns:
            Nodes to start layout from.

        """
        # Find nodes without positions
        nodes_without_position = [
            node for node in G if node.xpos() is None or node.ypos() is None
        ]

        top_nodes = []

        for node in nodes_without_position:
            # Traverse up to find the top-most node
            top_node = None
            visited = set()
            stack = Stack[Node]()
            stack.push(node)

            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)

                if not any(current.inputs()):  # Node with no inputs is a top node
                    top_node = current
                    break
                else:
                    for n in filter(None, current.inputs()):
                        stack.push(n)

            if top_node and top_node.xpos() is not None and top_node.ypos() is not None:
                top_nodes.append(top_node)

        return top_nodes
