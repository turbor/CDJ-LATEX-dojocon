from ir import (IR, IRScript, IRBlock, IRCMouth, IRValue,
                IRDropdown, IRVariable, IRList, IROperator, IRHatBlock)
from renderers.base import Renderer


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

    def render_node(self, node: IR, depth: int, context: str = "") -> str:
        # context is unused here - it exists to satisfy the base class interface
        # which passes it from _fill_text (AnsiRenderer uses it as parent_color)
        match node:
            case IRValue():
                if node.kind == "color":
                    return f"[{node.value}]"
                if node.kind == "empty":
                    return "<>"
                return f"( {node.value} )"
            case IRDropdown():
                val = self._translate_dropdown(node)
                return f"| {val} v|"
            case IRVariable():
                return "{ " + self.translate_var_name(node.name) + " }"
            case IRList():
                return f"[ {self.translate_var_name(node.name)} ]"
            case IROperator():
                text = self._fill_text(node.text, node.operands)
                return f"<{text}>"
            case _:
                return str(node)

    def print_boxed(self, title: str):
        print("+-" + "-" * len(title) + "-+")
        print(f"| {title} |")
        print("+-" + "-" * len(title) + "-+")

    def print_underlined(self, title: str):
        print(f"\n\n {title} ")
        print("=" * max(20, 2 + len(title)))
