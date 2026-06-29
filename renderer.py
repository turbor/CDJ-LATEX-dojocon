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
    def render_node(self, node: IR, depth: int) -> str:
        """Render a single IR node and return its string representation."""
        ...

    @abstractmethod
    def print_boxed(self, title: str):
        """Print a boxed section header."""
        ...

    @abstractmethod
    def print_underlined(self, title: str):
        """Print an underlined section header."""
        ...


class PlainRenderer(Renderer):
    """Renders blocks as plain ASCII text."""

    def render_script(self, script: IRScript, depth: int):
        for node in script.blocks:
            print(self.render_block_line(node, depth))

    def render_block_line(self, node: IR, depth: int) -> str:
        indent = "  | " * depth
        match node:
            case IRHatBlock():
                text = self._fill_text(node.text, node.inputs)
                return f"{indent} {text} "
            case IRCMouth():
                lines = []
                text = self._fill_text(node.text, node.inputs)
                lines.append(f"{indent} {text} ")
                self._render_cmouth_body(node, depth, lines)
                return "\n".join(lines)
            case IRBlock():
                text = self._fill_text(node.text, node.inputs)
                return f"{indent} {text} "
            case _:
                return f"{indent} {self.render_node(node, depth)} "

    def _render_cmouth_body(self, node: IRCMouth, depth: int, lines: list):
        indent = "  | " * depth
        for child in node.body.blocks:
            lines.append(self.render_block_line(child, depth + 1))
        if node.else_body is not None:
            lines.append(f"{indent} else ")
            for child in node.else_body.blocks:
                lines.append(self.render_block_line(child, depth + 1))
        lines.append(f"{indent}________")

    def render_node(self, node: IR, depth: int) -> str:
        match node:
            case IRValue():
                if node.kind == "color":
                    return f"[{node.value}]"
                return f"( {node.value} )"
            case IRDropdown():
                return f"| {node.value} v|"
            case IRVariable():
                return "{ " + node.name + " }"
            case IRList():
                return f"[ {node.name} ]"
            case IROperator():
                text = self._fill_text(node.text, node.operands)
                return f"<{text}>"
            case _:
                return str(node)

    def _fill_text(self, text: str, inputs: list[IR]) -> str:
        """Replace %1, %2, ... placeholders with rendered inputs."""
        import re
        def replacer(m):
            idx = int(m.group(1)) - 1
            if idx < len(inputs):
                return self.render_node(inputs[idx], 0)
            return m.group(0)
        return re.sub(r'%(\d+)', replacer, text)

    def print_boxed(self, title: str):
        print("+-" + "-" * len(title) + "-+")
        print(f"| {title} |")
        print("+-" + "-" * len(title) + "-+")

    def print_underlined(self, title: str):
        print(f"\n\n {title} ")
        print("=" * max(20, 2 + len(title)))


class AnsiRenderer(Renderer):
    """Renders blocks with ANSI color codes for terminal display."""

    # Color lookup table (same values as colorize.py)
    _colorvals = {
        "blueberry": [15, 75],
        "lightviolet": [15, 141],
        "magenta": [15, 176],
        "amber": [15, 220],
        "brightyellow": [15, 214],
        "moderateblue": [15, 110],
        "coolgreen": [15, 114],
        "mango": [0, 215],
        "orange": [0, 202],
        "hotpink": [0, 211],
        "limegreen": [0, 43],
        "white": [0, 15],
    }

    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLUEBG = '\033[97;44m'

    def __init__(self):
        # Calculate contrasting text colors
        for key, (fg, bg) in self._colorvals.items():
            cl = int(bg) - 16
            r, g, b = cl // 36, (cl // 6) % 6, cl % 6
            fg = 16 if (r * r + g * g + b * b) > 36 else 231
            self._colorvals[key] = [fg, bg]

    def _color(self, name: str) -> str:
        fg, bg = self._colorvals[name]
        return f"\033[38;5;{fg};48;5;{bg}m"

    def _color_bg(self, name: str) -> str:
        _, bg = self._colorvals[name]
        return f"\033[48;5;{bg}m"

    def render_script(self, script: IRScript, depth: int):
        for node in script.blocks:
            print(self._render_block_line(node, []))

    def render_block_line(self, node: IR, depth: int) -> str:
        # Public interface (called from sb3docbuilder) - no parent colors
        return self._render_block_line(node, [])

    def _render_block_line(self, node: IR, color_stack: list[str]) -> str:
        """Render a block line with colored sidebar from enclosing C-mouths."""
        indent = self._make_indent(color_stack)
        match node:
            case IRHatBlock():
                color = self._color(node.category)
                text = self._fill_text(node.text, node.inputs, node.category)
                return f"{indent}{color} {text} {self.RESET}"
            case IRCMouth():
                lines = []
                color = self._color(node.category)
                text = self._fill_text(node.text, node.inputs, node.category)
                lines.append(f"{indent}{color} {text} {self.RESET}")
                self._render_cmouth_body(node, color_stack, lines)
                return "\n".join(lines)
            case IRBlock():
                color = self._color(node.category)
                text = self._fill_text(node.text, node.inputs, node.category)
                return f"{indent}{color} {text} {self.RESET}"
            case _:
                return f"{indent}{self.render_node(node, 0, 'white')}"

    def _make_indent(self, color_stack: list[str]) -> str:
        """Build indent with a colored bar character for each enclosing C-mouth."""
        if not color_stack:
            return ""
        parts = []
        for clr in color_stack:
            # Colored bar as first char, then spaces for the rest of the indent
            parts.append(f"{self._color(clr)}\u2503{self.RESET}   ")
        return "".join(parts)

    def _render_cmouth_body(self, node: IRCMouth, color_stack: list[str], lines: list):
        color = self._color(node.category)
        indent = self._make_indent(color_stack)
        # Children are indented with this C-mouth's color added to the stack
        child_stack = [*color_stack, node.category]
        for child in node.body.blocks:
            lines.append(self._render_block_line(child, child_stack))
        if node.else_body is not None:
            lines.append(f"{indent}{color} else {self.RESET}")
            for child in node.else_body.blocks:
                lines.append(self._render_block_line(child, child_stack))
        lines.append(f"{indent}{color}{'_' * 8}{self.RESET}")

    def render_node(self, node: IR, depth: int, parent_color: str = "white") -> str:
        match node:
            case IRValue():
                if node.kind == "color":
                    return self._render_color_swatch(node.value, parent_color)
                white = "\033[38;5;0;48;5;15m"
                return f"{white} {node.value} {self._color(parent_color)}"
            case IRDropdown():
                return f"| {node.value} v|"
            case IRVariable():
                return "{ " + node.name + " }"
            case IRList():
                return f"[ {node.name} ]"
            case IROperator():
                color = self._color(node.category)
                text = self._fill_text(node.text, node.operands, node.category)
                # Restore parent color after operator, not RESET,
                # so surrounding block text keeps its background
                return f"{color}<{text}>{self._color(parent_color)}"
            case _:
                return str(node)

    def _render_color_swatch(self, hex_color: str, parent_color: str) -> str:
        """Render a color value as a swatch: the hex code shown on a background
        of that color, with contrasting black or white text."""
        r, g, b = self._hex_to_rgb(hex_color)
        # Choose black or white text based on perceived brightness
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        fg = 16 if brightness > 128 else 231  # 16=black, 231=white
        bg_code = f"\033[38;5;{fg};48;2;{r};{g};{b}m"
        return f"{bg_code} {hex_color} {self._color(parent_color)}"

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Parse #RRGGBB to (r, g, b) integers."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return 0, 0, 0

    def _fill_text(self, text: str, inputs: list[IR], category: str) -> str:
        """Replace %1, %2, ... placeholders with rendered inputs."""
        import re
        def replacer(m):
            idx = int(m.group(1)) - 1
            if idx < len(inputs):
                return self.render_node(inputs[idx], 0, category)
            return m.group(0)
        return re.sub(r'%(\d+)', replacer, text)

    def print_boxed(self, title: str):
        print()
        print(self.BLUEBG + " " * (4 + len(title)) + self.RESET)
        print(self.BLUEBG + self.UNDERLINE + f"  {title}  " + self.RESET)

    def print_underlined(self, title: str):
        print(f"\n\n  " + self.BOLD + self.UNDERLINE + f" {title} ")
        print(self.RESET)


class LatexRenderer(Renderer):
    """Renders blocks as LaTeX commands (using scratch3 LaTeX package)."""

    def render_script(self, script: IRScript, depth: int):
        for node in script.blocks:
            print(self.render_block_line(node, depth))

    def render_block_line(self, node: IR, depth: int) -> str:
        indent = "  " * depth
        match node:
            case IRHatBlock():
                text = self._fill_text(node.text, node.inputs)
                return f"{indent}\\begin{{scratch}}\n{indent}  \\blockevent{{{text}}}\n{indent}\\end{{scratch}}"
            case IRCMouth():
                lines = []
                text = self._fill_text(node.text, node.inputs)
                lines.append(f"{indent}\\blockcontrol{{{text}}}")
                for child in node.body.blocks:
                    lines.append(self.render_block_line(child, depth + 1))
                if node.else_body is not None:
                    lines.append(f"{indent}\\blockcontrol{{else}}")
                    for child in node.else_body.blocks:
                        lines.append(self.render_block_line(child, depth + 1))
                return "\n".join(lines)
            case IRBlock():
                text = self._fill_text(node.text, node.inputs)
                cat = node.category
                return f"{indent}\\block{cat}{{{text}}}"
            case _:
                return f"{indent}% unknown node: {node}"

    def render_node(self, node: IR, depth: int) -> str:
        match node:
            case IRValue():
                return f"\\ovalnum{{{node.value}}}"
            case IRDropdown():
                return f"\\selectmenu{{{node.value}}}"
            case IRVariable():
                return f"\\ovalmenu{{{node.name}}}"
            case IRList():
                return f"\\ovalmenu{{{node.name}}}"
            case IROperator():
                text = self._fill_text(node.text, node.operands)
                return f"\\booloperator{{{text}}}"
            case _:
                return str(node)

    def _fill_text(self, text: str, inputs: list[IR]) -> str:
        import re
        def replacer(m):
            idx = int(m.group(1)) - 1
            if idx < len(inputs):
                return self.render_node(inputs[idx], 0)
            return m.group(0)
        return re.sub(r'%(\d+)', replacer, text)

    def print_boxed(self, title: str):
        print(f"% === {title} ===")

    def print_underlined(self, title: str):
        print(f"\n% --- {title} ---")
