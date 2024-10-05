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

from typing import Generic, List, TypeVar

T = TypeVar("T")


class Stack(Generic[T]):
    def __init__(self):
        self._items: List[T] = []

    def pop(self) -> T:
        return self._items.pop() if self._items else None

    def push(self, item: T) -> None:
        self._items.append(item)

    def peek(self) -> T:
        return self._items[-1]

    def empty(self) -> bool:
        return not self._items
