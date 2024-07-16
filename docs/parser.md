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

# Get knob values
print(root.knob("first_frame"))
# out: 1001


```

