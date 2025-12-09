from dataclasses import dataclass
from enum import Enum
from typing import List


class NodeStatus(Enum):
    INFO = 1
    WARNING = 2
    ERROR = 3


@dataclass
class Node:
    text: str
    node_status: NodeStatus
    children: List["Node"]
