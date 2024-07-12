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

import collections
import copy
import functools
import json
import os
import re
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

from nuke_parser.stack import Stack

GizmoNameStr = str

_NODE_OPEN_RE = re.compile(r"(?P<type>[\w\.]+)\s\{$")
_NODE_CLOSE_RE = re.compile(r"\}$")
_NESTED_KNOB_CLOSE_RE = re.compile(r"^\s+\}\n")
_BRANCH_STACK_RE = re.compile(r"set (?P<key>\w+) \[stack \d\]")  # set
_PUSH_RE = re.compile(r"push \$(?P<key>\w+)")
_VERSION_RE = re.compile(r"version[ ]+(?P<version>[\d\.]+([ ]v\d)?)")
_CLONE_RE = re.compile(r"clone \$(?P<key>\w+)\s\{")
_NODE_KNOB_RE = re.compile(r"^\s*(?P<key>[\w_]+)[ ]+(?P<value>(:?\"|\w|\{|-|/).*)")


class Node:
    """Class representing nuke nodes."""

    def __init__(self, class_: str, knobs: dict):
        """Initialize class and do nothing.

        Args:
            class_: Nuke node type.
            knobs: Nuke node knobs.

        """
        self._knobs = {
            "inputs": 1,
        }
        self._knobs.update(knobs)
        self._class = class_
        self._inputs: List[Node] = [None] * eval(str(self._knobs.get("inputs")))
        self._outputs: List[Node] = []
        self._children: List[Node] = []
        self._parent: Optional[Node] = None

        self._is_gizmo = False
        self._clone_suffix = self._knobs.get("__clone__", "")
        self._knobs.pop("__clone__", None)  # Remove clone suffix.

    def __repr__(self) -> str:
        """Get node repr.

        Returns:
            Node repr.

        """
        return f"{type(self).__name__}(name='{self.name()}', Class='{self._class}')"

    def Class(self) -> str:
        """Get class type of node.

        Returns:
            Node class type.

        """
        return self._class

    def parent(self) -> Optional[Node]:
        """Get parent node.

        Returns:
            Parent node.

        """
        return self._parent

    def name(self) -> str:
        """Get node name.

        Returns:
            Node name.

        """
        return self._knobs.get("name", "") if self.Class() != "Root" else "Root"

    def fullName(self) -> str:
        node = self
        path = []
        while node and node.Class() != "Root":
            path.insert(0, node.name())
            node = node.parent()
        return ".".join(path)

    def _addChild(self, child: Node) -> None:
        """Add child to node. This should only be called from the parser.

        Args:
            child: Child node to add.

        """
        self._children.append(child)
        child._parent = self

    def children(self) -> Tuple[Node]:
        """Get children.

        Returns:
            Children of node.

        """
        return tuple(self._children)

    def inputs(self) -> Tuple[Node]:
        """Get inputs.

        Returns:
            Inputs of node.

        """
        return tuple(filter(None, self._inputs))

    def outputs(self) -> Tuple[Node]:
        """Get outputs.

        Returns:
            Outputs of node.

        """
        return tuple(self._outputs)

    def isGizmo(self) -> bool:
        return self._class == "gizmo" or self._is_gizmo

    def setInput(self, i: int, node: Node) -> None:
        """Add input to node. This should only be called from the parser.

        Args:
            i: Input index.
            node: Input node to add.

        """
        old_input = self._inputs[i]
        if old_input and self in old_input._outputs:
            index = old_input._outputs.index(self)
            old_input._outputs[index] = None

        self._inputs[i] = node
        if node:
            node._outputs.append(self)

    def knobs(self) -> Dict[str, Any]:
        """All knob names.

        Returns:
            All knobs as dict.

        """
        return copy.deepcopy(self._knobs)

    def knob(self, name: str, default=None) -> Any:
        """Get knob value from knob name.

        Args:
            name: Knob name.
            default: Default value if not found.

        Returns:
            Value from knob.

        """

        return self._knobs.get(name, default)

    def ypos(self) -> Union[int, None]:
        """Y position of node in node graph."""
        return self._knobs.get("ypos")

    def xpos(self) -> Union[int, None]:
        """X position of node in node graph."""
        return self._knobs.get("xpos")

    def setXpos(self, value: int) -> None:
        """Set the x position of node in node graph.
        Args:
            value: The x position of node in node graph.

        """
        self._knobs["xpos"] = value

    def setYpos(self, value: int) -> None:
        """Set the y position of node in node graph.

        Args:
            value: The y position of node in node graph.

        """
        self._knobs["ypos"] = value

    def hasKnob(self, name: str) -> bool:
        """Check if node hase knob.

        Args:
            name: Knob name to check.

        Returns:
            True if knob exists.

        """
        return name in self._knobs

    def _allNodes(self) -> Generator[Node, None, None]:
        """Recursively get all child nodes.

        Yields:
            Node: Child nodes.

        """

        def travers(node: Node) -> Generator[Node, None, None]:
            yield node
            for _child in node.children():
                yield from travers(_child)

        for child in self.children():
            yield from travers(child)

    def allNodes(self) -> Tuple[Node]:
        """Get all child nodes.

        Returns:
            All child nodes.

        """
        return tuple(self._allNodes())

    def path(self) -> str:
        """Get node path from node.

        Returns:
            Node path.

        """
        node = self
        path = ""
        while node:
            # The name of Root is the file path. We don't want that.
            name = node.name() if node.Class() != "Root" else "Root"
            path = "/" + name + path
            node = node.parent()
        return path + self._clone_suffix


def decodeKnob(value: str) -> Any:
    """Decode string to value.

    Args:
        value: Encoded knob value.

    Returns:
        Decoded knob value.

    """
    value = value.replace("\\n", "\n").replace("\\", "")
    try:
        result = json.loads(value)  # Nuke does not have dict attributes.
        return result if not isinstance(result, dict) else value
    except json.JSONDecodeError:
        return value


def _parseNk(file_path: str, gizmos: Optional[dict] = None) -> Node:
    """Parse nuke script and return root node.

    Args:
        file_path: File path to nuke script.
        gizmos: Dict of parser gizmos {gizmo name: Gizmo class}.

    Returns:
        Root node of nuke scene description.

    """
    gizmos = gizmos or {}

    with open(file_path) as file:
        lines = iter(file.readlines())

    main_stack = Stack[Node]()
    node_map: Dict[str, Node] = {}
    knobs = {}
    class_ = ""
    parents_stack = Stack[Node]()
    clone_map = collections.defaultdict(int)

    if file_path.endswith(".gizmo"):
        root = Node("Root", {})
        parents_stack.push(root)
        main_stack.push(root)

    for line in lines:
        if "push 0" in line:
            main_stack.push(None)
            continue
        elif _BRANCH_STACK_RE.search(line):  # set stack-key
            key = _BRANCH_STACK_RE.search(line).group("key")
            if key in "cut_paste_input":
                parents_stack.push(Node("Root", {}))
                continue

            node_map[key] = main_stack.peek()
            continue

        elif _PUSH_RE.search(line):
            key = _PUSH_RE.search(line).group("key")
            main_stack.push(node_map.get(key))
            continue
        elif "end_group" in line:
            node = main_stack.pop()
            while node and (
                node.Class() not in ("Group", "Gizmo") and not main_stack.empty()
            ):
                node = main_stack.pop()
            main_stack.push(node)
            parents_stack.pop()
            continue

        elif _CLONE_RE.search(line) and not class_:
            key = _CLONE_RE.search(line).group("key")
            node_to_clone = node_map[key]
            class_ = node_to_clone.Class()
            knobs = copy.deepcopy(node_to_clone._knobs)

            clone_map[key] += 1
            knobs["__clone__"] = f"_{clone_map[key]}"

        elif _NODE_OPEN_RE.search(line) and not class_:
            class_ = _NODE_OPEN_RE.search(line).group("type")
            if gizmos.get(class_):
                knobs.update(gizmos[class_].knobs())
            if class_ == "Gizmo":
                knobs["name"] = os.path.splitext(os.path.basename(file_path))[0]

        elif "addUserKnob" in line:
            continue
        elif _NODE_KNOB_RE.search(line):
            match = _NODE_KNOB_RE.search(line)
            value = match.group("value")
            if not value.startswith(("{", '"')):
                knobs[match.group("key")] = decodeKnob(value)
                continue

            string = value
            if value.startswith('"'):
                count = value.count('"') - value.count('\\"')
                while count % 2 != 0:
                    line = next(lines)
                    count += line.count('"') - line.count('\\"')
                    string += line
                # Remove first and last quote to help the if the string holds serialized json.
                string = f"{string[1:-1]}" if len(string) > 1 else string
            elif value.startswith("{"):
                count = value.count("{") - value.count("}")
                while count:
                    line = next(lines)
                    count += line.count("{") - line.count("}")
                    string += line
            knobs[match.group("key")] = decodeKnob(string)
            continue

        elif _NODE_CLOSE_RE.search(line) and class_:
            nk_node = Node(class_, knobs)
            class_ = ""
            knobs = {}
            for index in range(eval(str(nk_node.knob("inputs")))):
                node = main_stack.pop()
                if not node:
                    continue

                # Add connections.
                nk_node.setInput(index, node)

            if gizmos.get(nk_node.Class()):
                nk_node._children.extend(
                    copy.deepcopy(gizmos[nk_node.Class()].children())
                )
                nk_node._is_gizmo = True

            main_stack.push(nk_node)
            if nk_node.Class() == "Root":
                parents_stack.push(nk_node)
                continue

            parents_stack.peek()._addChild(nk_node)
            # Deal with groups
            if nk_node.Class() in ("Group", "Gizmo"):
                parents_stack.push(nk_node)

    return parents_stack.pop() if parents_stack else Node("Root", {})


def _gizmoPaths() -> List[str]:
    """Get all .gizmo file paths from ``NUKE_PATH`` env."""
    gizmo_paths = []
    for nuke_path in os.getenv("NUKE_PATH", "").split(os.path.pathsep):
        for root, _, files in os.walk(nuke_path):
            for file in files:
                if not file.endswith(".gizmo"):
                    continue

                gizmo_paths.append(os.path.join(root, file))

    return gizmo_paths


@functools.lru_cache()
def _parseGizmos() -> Dict[GizmoNameStr, Node]:
    """Parse all gizmo nodes and return map."""
    gizmos = {}
    for gizmo_path in _gizmoPaths():
        root = _parseNk(gizmo_path)
        if not root:
            continue
        for gizmo in root.children():
            gizmos[gizmo.name()] = gizmo
            gizmos[f"{gizmo.name()}.gizmo"] = gizmo
    return gizmos


def parseNk(file_path: str) -> Node:
    """Parse nuke script and return root node.

    Args:
        file_path: File path to nuke script.

    Returns:
        Root node of nuke scene description.

    """
    return _parseNk(file_path, _parseGizmos())
