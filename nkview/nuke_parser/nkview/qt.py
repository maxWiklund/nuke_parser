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
try:
    from PySide6 import QtCore, QtGui, QtWebEngineWidgets, QtWidgets

    def get_pos(self):
        return self.position().toPoint()

    QtGui.QMouseEvent.pos = get_pos

    QtWidgets.QAction = QtGui.QAction


except ImportError:
    from PySide2 import QtCore, QtGui, QtWebEngineWidgets, QtWidgets

    if not hasattr(QtWidgets.QApplication, "exec"):
        QtWidgets.QApplication.exec = QtWidgets.QApplication.exec_

    intersects_func = QtCore.QLineF.intersects

    def intersects_wrapper(self, line):
        point = QtCore.QPointF()
        type_ = intersects_func(self, line, point)
        return type_, point

    QtCore.QLineF.intersects = intersects_wrapper
