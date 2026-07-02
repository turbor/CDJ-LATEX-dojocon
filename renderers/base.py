import re
from abc import ABC, abstractmethod
from ir import (IR, IRScript, IRBlock, IRCMouth, IRValue,
                IRDropdown, IRVariable, IRList, IROperator, IRHatBlock)


class Renderer(ABC):
    """Base class for rendering IR nodes to a specific output format."""

    @abstractmethod
    def render_script(self, script: IRScript, depth: int):
        """Render a complete script (chain of blocks)."""
        ...

    @abstractmethod
    def render_node(self, node: IR, depth: int, context: str = "") -> str:
        """Render a single IR node and return its string representation.
        context is passed through from _fill_text (used as parent_color by AnsiRenderer)."""
        ...

    @abstractmethod
    def print_boxed(self, title: str):
        """Print a boxed section header."""
        ...

    @abstractmethod
    def print_underlined(self, title: str):
        """Print an underlined section header."""
        ...

    def _fill_text(self, text: str, inputs: list, context: str = "") -> str:
        """Replace %1, %2, ... placeholders with rendered inputs.
        context is passed as the third argument to render_node
        (used as parent_color by AnsiRenderer, ignored by others)."""
        def replacer(m):
            idx = int(m.group(1)) - 1
            if idx < len(inputs):
                return self.render_node(inputs[idx], 0, context)
            return m.group(0)
        return re.sub(r'%(\d+)', replacer, text)
