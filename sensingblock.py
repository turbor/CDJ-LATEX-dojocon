from block import SimpleBlock, Block
from ir import IR, IROperator, IRDropdown, IRValue
from translator import Translator


class SensingBlock(SimpleBlock):
    """Handles sensing blocks. These can appear as reporters in other blocks' inputs.
    All shadow_to_ir() methods return IROperator with unresolved template text
    and operand IR nodes - the renderer resolves placeholders with proper formatting.
    This allows nested blocks (e.g. a sensing diamond inside an operator oval) to
    be rendered recursively with correct decorations at each level."""

    # Internal values in the touching object menu that need translation
    _touching_special = {
        "_mouse_": "SENSING_TOUCHINGOBJECT_POINTER",
        "_edge_": "SENSING_TOUCHINGOBJECT_EDGE",
    }

    # Internal key names that need translation.
    # Scratch reuses EVENT_WHENKEYPRESSED_* l10n keys for the key options dropdown.
    _key_special = {
        "space": "EVENT_WHENKEYPRESSED_SPACE",
        "left arrow": "EVENT_WHENKEYPRESSED_LEFT",
        "right arrow": "EVENT_WHENKEYPRESSED_RIGHT",
        "down arrow": "EVENT_WHENKEYPRESSED_DOWN",
        "up arrow": "EVENT_WHENKEYPRESSED_UP",
        "any": "EVENT_WHENKEYPRESSED_ANY",
    }

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        """Decode sensing block when used as an inline reporter or menu shadow."""

        # Menu shadow blocks
        if self.opcode == "SENSING_TOUCHINGOBJECTMENU":
            val = self.fields.get("TOUCHINGOBJECTMENU", [None])[0]
            if val:
                return self._translate_touching_value(IRDropdown(value=val))
            return IRDropdown(value="?")

        if self.opcode == "SENSING_KEYOPTIONS":
            val = self.fields.get("KEY_OPTION", [None])[0]
            if val:
                return self._translate_key_value(IRDropdown(value=val))
            return IRDropdown(value="?")

        # Reporter blocks - return IROperator with template + operands
        if self.opcode == "SENSING_TOUCHINGOBJECT":
            text = Translator().translateOpcode(self.opcode)
            item = self.inputs.get("TOUCHINGOBJECTMENU")
            operands = []
            if item is not None:
                resolved = self._decode_input_value_ir(item[1], blocksAST)
                if isinstance(resolved, IRDropdown):
                    resolved = self._translate_touching_value(resolved)
                operands.append(resolved)
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=operands)

        if self.opcode == "SENSING_TOUCHINGCOLOR":
            text = Translator().translateOpcode(self.opcode)
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=self._decode_inputs_ir(blocksAST))

        if self.opcode == "SENSING_COLORISTOUCHINGCOLOR":
            text = Translator().translateOpcode(self.opcode)
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=self._decode_inputs_ir(blocksAST))

        if self.opcode == "SENSING_KEYPRESSED":
            text = Translator().translateOpcode(self.opcode)
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=self._decode_inputs_ir(blocksAST))

        if self.opcode == "SENSING_CURRENT":
            text = Translator().translateOpcode(self.opcode)
            menu_value = self.fields.get("CURRENTMENU", [None])[0]
            operands = []
            if menu_value:
                key = f"SENSING_CURRENT_{menu_value}"
                operands.append(IRDropdown(value=Translator().translateOpcode(key)))
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=operands)

        # Generic sensing reporters (answer, mouse x, timer, etc.)
        return IRDropdown(value=Translator().translateOpcode(self.opcode))

    def _translate_touching_value(self, dropdown: IRDropdown) -> IRDropdown:
        """Translate internal touching menu values to human-readable text."""
        key = self._touching_special.get(dropdown.value)
        if key:
            return IRDropdown(value=Translator().translateOpcode(key))
        return dropdown

    def _translate_key_value(self, dropdown: IRDropdown) -> IRDropdown:
        """Translate special key names (space, arrows, any) to localized text.
        Regular keys (a-z, 0-9) pass through unchanged."""
        key = self._key_special.get(dropdown.value)
        if key:
            return IRDropdown(value=Translator().translateOpcode(key))
        return dropdown
