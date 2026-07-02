from ir import (IR, IRScript, IRBlock, IRCMouth, IRValue,
                IRDropdown, IRVariable, IRList, IROperator, IRHatBlock)
from renderers.ansi import AnsiRenderer


class NerdFontRenderer(AnsiRenderer):
    """Enhanced ANSI renderer using Nerd Font glyphs for rounded/pointed block shapes.
    Requires a terminal with a Nerd Font installed (e.g. FiraCode Nerd Font)."""

    # Powerline / Nerd Font glyphs
    ROUND_L = "\ue0b6"   # left half-circle
    ROUND_R = "\ue0b4"   # right half-circle
    POINT_L = "\ue0b2"   # solid right-pointing triangle (starts the hexagon)
    POINT_R = "\ue0b0"   # solid left-pointing triangle (ends the hexagon)

    def _render_block_line(self, node: IR, color_stack: list[str]) -> str:
        """Render block with rounded ends."""
        indent = self._make_indent(color_stack)
        match node:
            case IRHatBlock():
                color = self._color(node.category)
                text = self._fill_text(node.text, node.inputs, node.category)
                # Rising/falling blob dome - inverted colors (block color as fg on default bg)
                _, bg = self._colorvals[node.category]
                dome_color = f"\033[38;5;{bg}m"
                dome = f"{indent}{dome_color} \u2582\u2584\u2586\u2588\u2588\u2588\u2588\u2586\u2584\u2582 {self.RESET}"
                body = f"{indent}{color} {text} {self.RESET}"
                return f"{dome}\n{body}"
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

    def render_node(self, node: IR, depth: int, parent_color: str = "white") -> str:
        match node:
            case IRValue():
                if node.kind == "color":
                    return self._render_color_swatch(node.value, parent_color)
                if node.kind == "empty":
                    # Empty boolean slot: pointed hexagon with white fill
                    _, parent_bg = self._colorvals[parent_color]
                    white_bg = self._colorvals["white"][1]
                    point_l = f"\033[38;5;{white_bg};48;5;{parent_bg}m"
                    white = "\033[38;5;0;48;5;15m"
                    point_r = f"\033[38;5;{white_bg};48;5;{parent_bg}m"
                    parent = self._color(parent_color)
                    return f"{point_l}{self.POINT_L}{white}  {point_r}{self.POINT_R}{parent}"
                # White rounded pill for values
                white_fg = "\033[38;5;15m"  # white foreground (for round glyph)
                white = "\033[38;5;0;48;5;15m"  # black on white
                parent = self._color(parent_color)
                return f"{parent}{white_fg}{self.ROUND_L}{white} {node.value} {parent}{white_fg}{self.ROUND_R}{parent}"
            case IRDropdown():
                return f"| {node.value} \u25be|"
            case IRVariable():
                # Orange rounded pill for variables
                var_color = self._color("mango")
                var_fg = f"\033[38;5;{self._colorvals['mango'][1]}m"
                parent = self._color(parent_color)
                return f"{parent}{var_fg}{self.ROUND_L}{var_color} {node.name} {parent}{var_fg}{self.ROUND_R}{parent}"
            case IRList():
                # Orange rounded pill for lists
                list_color = self._color("orange")
                list_fg = f"\033[38;5;{self._colorvals['orange'][1]}m"
                parent = self._color(parent_color)
                return f"{parent}{list_fg}{self.ROUND_L}{list_color} {node.name} {parent}{list_fg}{self.ROUND_R}{parent}"
            case IROperator():
                # Pointed hexagonal shape using powerline separators
                _, op_bg = self._colorvals[node.category]
                _, parent_bg = self._colorvals[parent_color]
                point_l = f"\033[38;5;{op_bg};48;5;{parent_bg}m"
                point_r = f"\033[38;5;{op_bg};48;5;{parent_bg}m"
                color = self._color(node.category)
                text = self._fill_text(node.text, node.operands, node.category)
                parent = self._color(parent_color)
                return f"{point_l}{self.POINT_L}{color} {text} {point_r}{self.POINT_R}{parent}"
            case _:
                return str(node)

    def _render_color_swatch(self, hex_color: str, parent_color: str) -> str:
        """Color swatch with rounded edges."""
        r, g, b = self._hex_to_rgb(hex_color)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        fg = 16 if brightness > 128 else 231
        swatch_bg = f"\033[48;2;{r};{g};{b}m"
        swatch_fg = f"\033[38;2;{r};{g};{b}m"
        text_fg = f"\033[38;5;{fg}m"
        parent = self._color(parent_color)
        return f"{parent}{swatch_fg}{self.ROUND_L}{swatch_bg}{text_fg} {hex_color} {parent}{swatch_fg}{self.ROUND_R}{parent}"
