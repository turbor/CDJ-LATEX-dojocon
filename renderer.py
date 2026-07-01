import os
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
                if node.kind == "empty":
                    return "<>"
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
                if node.kind == "empty":
                    return "<>"
                white = "\033[38;5;0;48;5;15m"
                return f"{white} {node.value} {self._color(parent_color)}"
            case IRDropdown():
                return f"| {node.value} \u25be|"
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
    """Renders blocks as compilable LaTeX using the scratch3 package (v0.19).

    Usage modes:
    - Full document: render_preamble() + render_script()s + render_postamble()
    - Fragment only: render_script() alone (for inclusion in existing documents)
    """

    # Maps internal category names to scratch3 package suffixes
    _category_to_suffix = {
        "blueberry": "move",         # motion
        "lightviolet": "look",       # looks
        "magenta": "sound",          # sound
        "amber": "event",            # event
        "brightyellow": "control",   # control
        "moderateblue": "sensing",   # sensing
        "coolgreen": "operator",     # operators
        "mango": "variable",         # variable
        "orange": "list",            # list
        "limegreen": "pen",          # pen & extensions
        "hotpink": "moreblocks",     # my blocks
        "white": "move",             # fallback
    }

    # Boolean operator categories (rendered as diamond/hexagon)
    _bool_categories = {"coolgreen", "moderateblue"}

    # Opcodes that represent boolean reporters (diamond shape)
    _bool_opcodes = {
        "OPERATOR_LT", "OPERATOR_GT", "OPERATOR_EQUALS",
        "OPERATOR_AND", "OPERATOR_OR", "OPERATOR_NOT",
        "OPERATOR_CONTAINS",
        "SENSING_TOUCHINGOBJECT", "SENSING_TOUCHINGCOLOR",
        "SENSING_COLORISTOUCHINGCOLOR", "SENSING_KEYPRESSED",
        "SENSING_MOUSEDOWN",
        "DATA_LISTCONTAINSITEM",
    }

    # Hat opcodes that use \blockinitclone instead of \blockinit
    _clone_hat_opcodes = {"CONTROL_START_AS_CLONE"}

    # Opcodes that represent stop blocks (no bottom notch)
    _stop_opcodes = {"CONTROL_STOP", "CONTROL_DELETE_THIS_CLONE"}

    # Opcodes for forever loops (\blockinfloop)
    _infloop_opcodes = {"CONTROL_FOREVER"}

    # Opcodes for finite loops (\blockrepeat)
    _repeat_opcodes = {"CONTROL_REPEAT", "CONTROL_REPEAT_UNTIL"}

    # Characters that need escaping in LaTeX.
    # The translation strings from scratch-l10n contain raw text that may include
    # characters with special meaning in LaTeX. For example:
    # - "set size to %1 %" has a literal % that becomes a LaTeX comment
    # - "< %1" / "> %1" operators produce bare < > which are missing in T1 encoding
    # - Variable names created by users can contain #, $, &, _, etc.
    _latex_special = str.maketrans({
        '#': r'\#',
        '$': r'\$',
        '%': r'\%',
        '&': r'\&',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    })

    def _escape(self, text: str) -> str:
        """Escape LaTeX special characters in user-provided text.
        Does NOT escape backslash since we embed LaTeX commands in the output."""
        # The pen block prefixes its text with a pencil unicode (U+270E) at the IR level.
        # pdflatex cannot render this glyph (it's outside T1/OT1 encoding), so replace
        # with a simple ASCII marker.
        text = text.replace("\u270e", "/")
        # Extension icons that pdflatex cannot render (outside T1 encoding)
        text = text.replace("\u266b", "/")       # music note
        text = text.replace("\U0001f3a5", "/")   # video camera
        text = text.replace("\U0001f642", "/")   # face sensing
        text = text.replace("\U0001f4ac", "/")   # speech bubble (text2speech)
        text = text.replace("\U0001f310", "/")   # globe (translate)
        text = text.replace("\u2328", "/")       # keyboard (makey makey)
        text = text.replace("\u25a3", "/")       # square (microbit)
        text = text.replace("\u2699", "/")       # gear (gdx force)
        text = text.replace("\U0001f916", "/")   # robot (ev3)
        text = text.replace("\U0001f9e9", "/")   # puzzle piece (boost/wedo)
        return text.translate(self._latex_special)

    def __init__(self):
        self._colors = {}  # hex -> color name mapping
        self._else_word = "else"  # default, overridden by set_else_word()

    def set_else_word(self, word: str):
        """Set the translated 'else' word for the scratch3 package.
        The scratch3 LaTeX package defaults to "sinon" (French) because the
        package author is francophone. This must be overridden for other languages."""
        self._else_word = word

    def _get_color_name(self, hex_val: str) -> str:
        """Register a hex color and return its LaTeX color name."""
        hex_val = hex_val.lstrip('#').lower()
        if hex_val not in self._colors:
            self._colors[hex_val] = f"scrcolor{chr(65 + len(self._colors) % 26)}{len(self._colors)}"
        return self._colors[hex_val]

    def render_preamble(self) -> str:
        """Return a complete LaTeX document preamble that loads scratch3."""
        return (
            r"\documentclass[a4paper,10pt]{article}" "\n"
            r"\usepackage[utf8]{inputenc}" "\n"
            r"\usepackage[T1]{fontenc}" "\n"
            r"\usepackage[margin=2cm]{geometry}" "\n"
            r"\usepackage{graphicx}" "\n"
            r"\usepackage{scratch3}" "\n"
            f"\\setscratch{{else word={self._else_word}}}" "\n"
            r"\begin{document}" "\n"
        )

    def render_postamble(self) -> str:
        """Return the LaTeX document closing."""
        return r"\end{document}" "\n"

    def render_sprite_image(self, image_path: str):
        """Emit a tikz overlay that places the sprite costume in the top-right corner.
        Uses 'remember picture, overlay' so it floats over the page content
        without affecting text flow.
        The caller is responsible for providing a path that is correct relative
        to the .tex file location (relative when using -o, absolute otherwise)."""
        print(r"\begin{tikzpicture}[remember picture, overlay]")
        print(f"  \\node[anchor=north east, inner sep=5mm] at (current page.north east)")
        print(f"    {{\\includegraphics[height=2cm]{{{image_path}}}}};")
        print(r"\end{tikzpicture}")
        print()

    def render_script(self, script: IRScript, depth: int):
        """Render a complete script as a scratch environment.

        The scratch3 package's \\pencolor{} macro passes its argument directly to
        tikz as a fill color name. It does NOT accept raw hex values like #RRGGBB
        (the # would be interpreted as a LaTeX parameter token). So we define each
        unique color with \\definecolor{name}{HTML}{RRGGBB} and pass the name to
        \\pencolor instead."""
        lines = []
        indent = "  " * depth
        # First pass: render blocks (this populates self._colors for new hex values)
        block_lines = []
        for node in script.blocks:
            block_lines.append(self._render_block(node, depth + 1))
        # Emit color definitions for any newly encountered colors
        for hex_val, name in self._colors.items():
            # definecolor only needs to appear once; LaTeX ignores redefinitions
            lines.append(f"{indent}\\definecolor{{{name}}}{{HTML}}{{{hex_val.upper()}}}")
        if self._colors:
            lines.append("")
        lines.append(f"{indent}\\begin{{scratch}}")
        lines.extend(block_lines)
        lines.append(f"{indent}\\end{{scratch}}")
        print("\n".join(lines))

    def _render_block(self, node: IR, depth: int) -> str:
        """Render a single IR node as LaTeX scratch3 command(s)."""
        indent = "  " * depth
        match node:
            case IRHatBlock():
                text = self._fill_text(node.text, node.inputs)
                if node.opcode in self._clone_hat_opcodes:
                    return f"{indent}\\blockinitclone{{{text}}}"
                return f"{indent}\\blockinit{{{text}}}"

            case IRCMouth():
                return self._render_cmouth(node, depth)

            case IRBlock():
                # Stop blocks
                if node.opcode in self._stop_opcodes:
                    text = self._fill_text(node.text, node.inputs)
                    return f"{indent}\\blockstop{{{text}}}"
                # Regular blocks
                suffix = self._get_suffix(node.category)
                text = self._fill_text(node.text, node.inputs)
                return f"{indent}\\block{suffix}{{{text}}}"

            case _:
                return f"{indent}% unknown node: {node}"

    def _render_cmouth(self, node: IRCMouth, depth: int) -> str:
        """Render C-mouth blocks (loops, if, if-else)."""
        indent = "  " * depth
        text = self._fill_text(node.text, node.inputs)

        # Infinite loop (forever)
        if node.opcode in self._infloop_opcodes:
            lines = [f"{indent}\\blockinfloop{{{text}}}"]
            lines.append(f"{indent}{{")
            for child in node.body.blocks:
                lines.append(self._render_block(child, depth + 1))
            lines.append(f"{indent}}}")
            return "\n".join(lines)

        # Finite loop (repeat N, repeat until)
        if node.opcode in self._repeat_opcodes:
            lines = [f"{indent}\\blockrepeat{{{text}}}"]
            lines.append(f"{indent}{{")
            for child in node.body.blocks:
                lines.append(self._render_block(child, depth + 1))
            lines.append(f"{indent}}}")
            return "\n".join(lines)

        # If-else
        if node.else_body is not None and len(node.else_body.blocks) > 0:
            lines = [f"{indent}\\blockifelse{{{text}}}"]
            lines.append(f"{indent}{{")
            for child in node.body.blocks:
                lines.append(self._render_block(child, depth + 1))
            lines.append(f"{indent}}}")
            lines.append(f"{indent}{{")
            for child in node.else_body.blocks:
                lines.append(self._render_block(child, depth + 1))
            lines.append(f"{indent}}}")
            return "\n".join(lines)

        # If-then (no else)
        lines = [f"{indent}\\blockif{{{text}}}"]
        lines.append(f"{indent}{{")
        for child in node.body.blocks:
            lines.append(self._render_block(child, depth + 1))
        lines.append(f"{indent}}}")
        return "\n".join(lines)

    def render_node(self, node: IR, depth: int) -> str:
        """Render an inline IR node (input/reporter) as LaTeX."""
        match node:
            case IRValue():
                if node.kind == "color":
                    # Use a named color defined via \definecolor in the preamble
                    color_name = self._get_color_name(node.value)
                    return f"\\pencolor{{{color_name}}}"
                if node.kind == "symbol":
                    # Green flag emoji -> \greenflag
                    if "\U0001f3f3" in node.value or "flag" in node.value.lower():
                        return "\\greenflag"
                    # Turn arrows
                    if node.value == "\u27F2":
                        return "\\turnleft{}"
                    if node.value == "\u27F3":
                        return "\\turnright{}"
                    return self._escape(node.value)
                if node.kind == "empty":
                    return "\\boolempty"
                return f"\\ovalnum{{{self._escape(node.value)}}}"

            case IRDropdown():
                return f"\\selectmenu{{{self._escape(node.value)}}}"

            case IRVariable():
                return f"\\ovalvariable{{{self._escape(node.name)}}}"

            case IRList():
                return f"\\ovallist{{{self._escape(node.name)}}}"

            case IROperator():
                text = self._fill_text(node.text, node.operands)
                # Boolean reporters get diamond shape
                if node.opcode in self._bool_opcodes:
                    suffix = self._get_suffix(node.category)
                    return f"\\bool{suffix}{{{text}}}"
                # Numeric/string reporters get oval shape
                suffix = self._get_suffix(node.category)
                return f"\\oval{suffix}{{{text}}}"

            case _:
                return self._escape(str(node))

    def _get_suffix(self, category: str) -> str:
        """Map internal color/category name to scratch3 package suffix."""
        return self._category_to_suffix.get(category, "move")

    def _fill_text(self, text: str, inputs: list[IR]) -> str:
        """Replace %1, %2, ... placeholders with rendered input nodes.

        We split on placeholder markers first, then escape only the static
        fragments. This avoids escaping the LaTeX commands that render_node()
        produces (e.g. \\ovalnum, \\selectmenu)."""
        import re
        # Split text on %N markers, escape the static parts, then rejoin
        parts = re.split(r'(%\d+)', text)
        result = []
        for part in parts:
            m = re.fullmatch(r'%(\d+)', part)
            if m:
                idx = int(m.group(1)) - 1
                if idx < len(inputs):
                    result.append(self.render_node(inputs[idx], 0))
                else:
                    result.append(part)
            else:
                result.append(self._escape(part))
        return "".join(result)

    def print_boxed(self, title: str):
        print(f"\n\\section{{{self._escape(title)}}}")

    def print_underlined(self, title: str):
        print(f"\n\\subsection{{{self._escape(title)}}}")


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
                # POINT_L: fg=operator bg=parent (triangle of operator color appears in parent)
                # Inside: normal operator colors
                # POINT_R: fg=operator bg=parent (triangle ends back into parent)
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
