from block import SimpleBlock, Block, replace_placeholders
from ir import IR, IROperator, IRDropdown, IRValue
from translator import Translator


class SensingBlock(SimpleBlock):
    """Handles sensing blocks. These can appear as reporters in other blocks' inputs.
    Special handling for:
    - SENSING_TOUCHINGOBJECTMENU: shadow menu for touching object selection
    - SENSING_KEYOPTIONS: shadow menu for key selection
    - SENSING_TOUCHINGOBJECT: resolves the touching object menu (_mouse_, _edge_, sprite)
    - SENSING_TOUCHINGCOLOR: resolves color input
    - SENSING_COLORISTOUCHINGCOLOR: resolves two color inputs
    - SENSING_KEYPRESSED: resolves key option menu with special key translation
    - SENSING_CURRENT: resolves the current time field (year, month, etc.)"""

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

        # Menu shadow blocks that belong to sensing category
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

        # Reporter blocks used as shadows in other blocks' inputs
        if self.opcode == "SENSING_TOUCHINGOBJECT":
            # "touching %1?" with the object menu as parameter
            text = Translator().translateOpcode(self.opcode)
            item = self.inputs.get("TOUCHINGOBJECTMENU")
            if item is not None:
                resolved = self._decode_input_value_ir(item[1], blocksAST)
                # Translate special values (_mouse_, _edge_)
                if isinstance(resolved, IRDropdown):
                    resolved = self._translate_touching_value(resolved)
                text = replace_placeholders(text, [self._ir_to_placeholder(resolved)])
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=[])

        if self.opcode == "SENSING_TOUCHINGCOLOR":
            # "touching color %1?"
            text = Translator().translateOpcode(self.opcode)
            inputs_ir = self._decode_inputs_ir(blocksAST)
            if inputs_ir:
                text = replace_placeholders(text, [self._ir_to_placeholder(p) for p in inputs_ir])
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=inputs_ir)

        if self.opcode == "SENSING_COLORISTOUCHINGCOLOR":
            # "color %1 is touching %2?"
            text = Translator().translateOpcode(self.opcode)
            inputs_ir = self._decode_inputs_ir(blocksAST)
            if inputs_ir:
                text = replace_placeholders(text, [self._ir_to_placeholder(p) for p in inputs_ir])
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=inputs_ir)

        if self.opcode == "SENSING_KEYPRESSED":
            # "key %1 pressed?" with a key option menu
            text = Translator().translateOpcode(self.opcode)
            inputs_ir = self._decode_inputs_ir(blocksAST)
            if inputs_ir:
                text = replace_placeholders(text, [self._ir_to_placeholder(p) for p in inputs_ir])
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=inputs_ir)

        if self.opcode == "SENSING_CURRENT":
            # "current %1" with the time unit from CURRENTMENU field
            text = Translator().translateOpcode(self.opcode)
            menu_value = self.fields.get("CURRENTMENU", [None])[0]
            if menu_value:
                # Translate via constructed key: SENSING_CURRENT_YEAR, etc.
                key = f"SENSING_CURRENT_{menu_value}"
                translated = Translator().translateOpcode(key)
                text = replace_placeholders(text, [translated])
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=[])

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
