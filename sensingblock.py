from block import SimpleBlock, Block, replace_placeholders
from ir import IR, IROperator, IRDropdown, IRValue
from translator import Translator


class SensingBlock(SimpleBlock):
    """Handles sensing blocks. These can appear as reporters in other blocks' inputs.
    Special handling for:
    - SENSING_TOUCHINGOBJECT: resolves the touching object menu
    - SENSING_CURRENT: resolves the current time field (year, month, etc.)
    - Other sensing reporters used as shadows."""

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        """Decode sensing block when used as an inline reporter."""

        if self.opcode == "SENSING_TOUCHINGOBJECT":
            # "touching %1?" with the object menu as parameter
            text = Translator().translateOpcode(self.opcode)
            # Resolve the TOUCHINGOBJECTMENU input
            item = self.inputs.get("TOUCHINGOBJECTMENU")
            if item is not None:
                resolved = self._decode_input_value_ir(item[1], blocksAST)
                text = replace_placeholders(text, [self._ir_to_placeholder(resolved)])
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=[])

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
        # Just return the translated opcode name
        return IRDropdown(value=Translator().translateOpcode(self.opcode))
