import re
from abc import ABC, abstractmethod
from ir import (IR, IRScript, IRBlock, IRCMouth, IRValue,
                IRDropdown, IRVariable, IRList, IROperator, IRHatBlock)


class Renderer(ABC):
    """Base class for rendering IR nodes to a specific output format."""

    def __init__(self):
        self._var_translations = {}  # loaded from -t JSON file
        self._language = "en"        # target language for variable translation
        self._current_sprite = ""    # set before rendering each sprite

    def load_var_translations(self, json_path: str, language: str):
        """Load variable name translations from a JSON file.
        Format: {"varname": {"fr": "nom"}, "Sprite.varname": {"fr": "override"}}
        Sprite-specific entries (dot-notation) take priority over generic ones."""
        import json
        with open(json_path, encoding='utf-8') as f:
            self._var_translations = json.load(f)
        self._language = language

    def set_current_sprite(self, sprite_name: str):
        """Set the current sprite context for sprite-specific variable lookups."""
        self._current_sprite = sprite_name

    def translate_var_name(self, name: str) -> str:
        """Translate a variable/list name using the loaded translation file.
        Uses the current sprite context for lookup."""
        return self._translate_var_for_sprite(name, self._current_sprite)

    def _translate_var_for_sprite(self, name: str, sprite: str) -> str:
        """Translate a variable/list name in the context of a specific sprite.
        Lookup order: 'SpriteName.varname' first, then 'varname'.
        Returns the original name if no translation is found."""
        if not self._var_translations:
            return name
        # Try sprite-specific override first
        entry = self._var_translations.get(f"{sprite}.{name}")
        if entry and self._language in entry:
            return entry[self._language]
        # Fall back to generic entry
        entry = self._var_translations.get(name)
        if entry and self._language in entry:
            return entry[self._language]
        return name

    def _translate_dropdown(self, node) -> str:
        """Translate an IRDropdown value if it's a variable reference.
        Uses ref_sprite as context when available (for 'property of sprite' blocks),
        otherwise uses the current sprite being rendered."""
        if not node.is_variable_ref:
            return node.value
        sprite = node.ref_sprite or self._current_sprite
        return self._translate_var_for_sprite(node.value, sprite)

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

    def render_local_variables(self, variables: list[tuple[str, str]], lists: list[tuple[str, list]]):
        """Render a sprite's local variables and lists.
        Default implementation prints plain text. Subclasses override for styling."""
        if not variables and not lists:
            return
        print("  Local variables:")
        for name, value in variables:
            print(f"    {self.translate_var_name(name)} = {value}")
        for name, contents in lists:
            print(f"    {self.translate_var_name(name)} (list) = {contents}")
        print()
