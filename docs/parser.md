nk_parser
=======
Python module to parse nuke scripts.

## Usage

```python
from nuke_parser.parser import parseNk

root = parseNk("../test_scenes/nested_group.nk")

# iterate over all nodes.
for node in root.allNodes():
    ...
# Important note.
# `node.name()` Will not return the file path but rather the name of the node (Root).
root.name()
# out: "Root"

root.knob("name")
# out: "/path/to/nested_group.nk"

```

