import os
import re
from ir import (IR, IRScript, IRBlock, IRCMouth, IRValue,
                IRDropdown, IRVariable, IRList, IROperator, IRHatBlock)
from renderers.base import Renderer


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

    def render_node(self, node: IR, depth: int, context: str = "") -> str:
        """Render an inline IR node (input/reporter) as LaTeX."""
        # context is unused here - it exists to satisfy the base class interface
        # which passes it from _fill_text (AnsiRenderer uses it as parent_color)
        match node:
            case IRValue():
                if node.kind == "color":
                    color_name = self._get_color_name(node.value)
                    return f"\\pencolor{{{color_name}}}"
                if node.kind == "symbol":
                    if "\U0001f3f3" in node.value or "flag" in node.value.lower():
                        return "\\greenflag"
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
                if node.opcode in self._bool_opcodes:
                    suffix = self._get_suffix(node.category)
                    return f"\\bool{suffix}{{{text}}}"
                suffix = self._get_suffix(node.category)
                return f"\\oval{suffix}{{{text}}}"

            case _:
                return self._escape(str(node))

    def _get_suffix(self, category: str) -> str:
        """Map internal color/category name to scratch3 package suffix."""
        return self._category_to_suffix.get(category, "move")

    def _fill_text(self, text: str, inputs: list[IR], context: str = "") -> str:
        """Replace %1, %2, ... placeholders with rendered input nodes.

        We split on placeholder markers first, then escape only the static
        fragments. This avoids escaping the LaTeX commands that render_node()
        produces (e.g. \\ovalnum, \\selectmenu)."""
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
