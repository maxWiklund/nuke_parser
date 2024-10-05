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
from nkview.icons import qresource
from nkview.qt import QtGui

qresource.qInitResources()

# fmt: off
BASE_SHAPE = (
    (-0.1, 0.0),
    (1.1, 0.0),
    (1.1, 0.25),
    (-0.1, 0.25)
)


GEO_SHAPE = [
    [0, 0.26],
    [0.0121, 0.2884],
    [0.0406, 0.3],
    [0.96, 0.3],
    [0.9869, 0.2893],
    [1, 0.26],
    [1, 0.04],
    [0.9879, 0.0116],
    [0.9594, 0],
    [0.04, 0],
    [0.0131, 0.0107],
    [0, 0.04],
]




READ_SHAPE = (
    (0.0, 0.0),
    (1.0, 0.0),
    (1.0, 1.0),
    (0.0, 1.0),
)


VIEWER_SHAPE = (
    (0.0, 0.1),  # left center
    (0.05, 0.0),
    (0.95, 0.0),
    (1.0, 0.1),  # right center.
    (0.95, 0.2),
    (0.05, 0.2),
)


GIZMO_SHAPE = (
    (0.0, 0.0),
    (0.9, 0.0),
    (1.0, 0.15),  # right center.
    (0.9, 0.3),
    (0.0, 0.3),
)

GROUP_SHAPE = (
    (0.0, 0.15),  # left center
    (0.1, 0.0),
    (0.9, 0.0),
    (1.0, 0.15),  # right center.
    (0.9, 0.3),
    (0.1, 0.3),
)

OUTPUT_SHAPE = (
    (0.1, 0.0),
    (0.9, 0.0),
    (1.0, 0.2),
    (0.0, 0.2)
)


INPUT_SHAPE = (
    (0.0, 0.0),
    (1.0, 0.0),
    (0.9, 0.2),
    (0.1, 0.2)
)


SCENE_3D_SHAPE = (
    (0.21, 0.155),
    (0.2135, 0.1996),
    (0.2239, 0.2431),
    (0.241, 0.2844),
    (0.2644, 0.3225),
    (0.2935, 0.3565),
    (0.3275, 0.3856),
    (0.3656, 0.409),
    (0.4069, 0.4261),
    (0.4504, 0.4365),
    (0.495, 0.44),
    (0.5396, 0.4365),
    (0.5831, 0.4261),
    (0.6244, 0.409),
    (0.6625, 0.3856),
    (0.6965, 0.3565),
    (0.7256, 0.3225),
    (0.749, 0.2844),
    (0.7661, 0.2431),
    (0.7765, 0.1996),
    (0.78, 0.155),
    (0.7765, 0.1104),
    (0.7661, 0.0669),
    (0.749, 0.0256),
    (0.7256, -0.0125),
    (0.6965, -0.0465),
    (0.6625, -0.0756),
    (0.6244, -0.099),
    (0.5831, -0.1161),
    (0.5396, -0.1265),
    (0.495, -0.13),
    (0.4504, -0.1265),
    (0.4069, -0.1161),
    (0.3656, -0.099),
    (0.3275, -0.0756),
    (0.2935, -0.0465),
    (0.2644, -0.0125),
    (0.241, 0.0256),
    (0.2239, 0.0669),
    (0.2135, 0.1104),
)

DOT_SHAPE = (
    (0.1, 0.0),
    (0.1309, 0.0049),
    (0.1588, 0.0191),
    (0.1809, 0.0412),
    (0.1951, 0.0691),
    (0.2, 0.1),
    (0.1951, 0.1309),
    (0.1809, 0.1588),
    (0.1588, 0.1809),
    (0.1309, 0.1951),
    (0.1, 0.2),
    (0.0691, 0.1951),
    (0.0412, 0.1809),
    (0.0191, 0.1588),
    (0.0049, 0.1309),
    (0.0, 0.1),
    (0.0049, 0.0691),
    (0.0191, 0.0412),
    (0.0412, 0.0191),
    (0.0691, 0.0049),
)

# fmt: on


DISABLED_WIDGET_COLOR = QtGui.QColor(48, 48, 48)
BORDER_COLOR = QtGui.QColor(13, 13, 13)
DARK_BACKGROUND_COLOR = QtGui.QColor(28, 28, 28)
FOREGROUND_COLOR = QtGui.QColor(77, 77, 77)
WIDGET_COLOR_INPUT = QtGui.QColor(128, 128, 128)
SELECTED_COLOR = QtGui.QColor(250, 154, 0)
CLICKED_COLOR = QtGui.QColor(
    SELECTED_COLOR.red(), SELECTED_COLOR.green(), SELECTED_COLOR.blue(), 180
)

QT_STYLE = f"""
QWidget
{{
    color: white;
    background: {DISABLED_WIDGET_COLOR.name()};
    border-color: {BORDER_COLOR.name()};
}}


QWidget::disabled
{{
    color: grey;
    background: {FOREGROUND_COLOR.name()};
    border-color: {DISABLED_WIDGET_COLOR.name()};
}}


QLabel
{{
    background: transparent;
    border-radius: 2px;
}}


QLabel::disabled, QCheckBox:disabled
{{
    background: transparent;
}}


QCheckBox
{{
    background: {FOREGROUND_COLOR.name()};
}}


QCheckBox::indicator:disabled
{{
    border-radius: 3px;
    border: 1px solid {DISABLED_WIDGET_COLOR.name()};
    background: {FOREGROUND_COLOR.name()};
}}



QLineEdit{{
    border-radius: 2px;
    border-style: solid;
    border-width: 1px;
    background: {DARK_BACKGROUND_COLOR.name()};
}}

QPushButton
{{
    border-radius: 2px;
    border-style: solid;
    border-width: 1px;
    background: {WIDGET_COLOR_INPUT.name()};
}}


QPushButton
{{
    padding: 1 5px;
}}


QPushButton::hover
{{
    background: {SELECTED_COLOR.name()};
}}


QPushButton::pressed
{{
    background: {CLICKED_COLOR.name()};
}}


QGroupBox
{{
    border: 1px solid rgb(28, 28, 28);
    border-radius: 7px;
    margin-top: 9px;
    padding-top: 8px;
    padding-right: 4px;
    padding-bottom: 0px;
    padding-left: 4px;
    background: rgb(60, 60, 60);
}}


QGroupBox::title
{{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    background: transparent;
    padding-left: 4px;
    padding-right: 4px;
    position: absolute;
    left: 7px;
}}


QTreeView, QListView
{{
    background: rgb(50, 50, 50);
    border-width: 1px;
    border-style: solid;
    border-radius: 3px;
    alternate-background-color: {FOREGROUND_COLOR.name()};
}}



QTableView::item:selected, QTreeView::item:selected
{{
    background: {SELECTED_COLOR.name()};
}}


QHeaderView::down-arrow
{{
    width: 0;
    height: 0;
    border-left: 4px solid rgba(132, 132, 132, 0);
    border-right: 4px solid rgba(132, 132, 132, 0);
    border-top: 7px solid rgb(132, 132, 132);
    margin-right: 7px;
}}


QHeaderView::section
{{
    border: 1px solid rgb(25, 25, 25);
    border-right: 0;
    padding: 5px;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 rgb(58, 58, 58), stop: 1.0 rgb(39, 39, 39) );
}}


QHeaderView::up-arrow
{{
    width: 0;
    height: 0;
    border-left: 4px solid rgba(86, 86, 86, 0);
    border-right: 4px solid rgba(86, 86, 86, 0);
    border-bottom: 7px solid rgb(132, 132, 132);
    margin-right: 7px;
}}
"""


NUKE_NODE_COLORS = {
    "Merge2": "#3a4aa4",
    "TimeEcho": "#9a8e48",
    "Inpaint2": "#b06c3b",
    "Copy": "#a33966",
    "Grade": "#637696",
    "ColorCorrect": "#637696",
    "Shuffle2": "#812d50",
    "CopyCat": "#812d50",
    "Remove": "#812d50",
    "TimeClip": "#8d8343",
    "Clamp": "#7085aa",
    "Write": "#848401",
    "Scene": "#014500",
    "Axis3": "#014500",
    "Axis4": "#014500",
    "ScanlineRender": "#014500",
    "Camera3": "#014500",
    "DepthToPoints": "#014500",
    "Crop": "#906896",
    "Invert": "#798eb3",
    "Reformat": "#926c97",
    "CameraTrackerPointCloud": "#a90000",
    "Blur": "#a9683a",
    "FilterErode": "#b06c3b",
    "LensDistortion2": "#735378",
    "Roto": "#498244",
    "RotoPaint": "#498244",
    "Defocus": "#88542e",
    "CornerPin2D": "#735378",
    "Transform": "#745479",
}
