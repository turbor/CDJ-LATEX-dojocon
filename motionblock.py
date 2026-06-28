from block import SimpleBlock
from ir import IR, IRDropdown
from translator import Translator


class MotionBlock(SimpleBlock):
    """Handles motion blocks. Overrides shadow_to_ir() for menu shadow blocks
    like goto_menu, glideto_menu, pointtowards_menu which contain destination
    choices (_random_, _mouse_, or a sprite name)."""

    # Maps menu opcodes to the field key that holds the destination value
    _menu_field_keys = {
        "MOTION_POINTTOWARDS_MENU": "TOWARDS",
        "MOTION_GOTO_MENU": "TO",
        "MOTION_GLIDETO_MENU": "TO",
    }

    # Maps internal scratch values to translation keys
    _special_values = {
        "_random_": "MOTION_GOTO_RANDOM",
        "_mouse_": "MOTION_GOTO_POINTER",
    }

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        # Menu shadow blocks (dropdown with destination choices)
        if self.opcode.endswith("_MENU"):
            field_key = self._menu_field_keys.get(self.opcode)
            if field_key is None:
                raise Exception(f"Unknown motion menu shadow block: {self.opcode}")

            destination = self.fields[field_key]
            if isinstance(destination, list):
                raw_value = destination[0]
                # Translate special internal values (_random_, _mouse_)
                if raw_value in self._special_values:
                    translated = Translator().translateOpcode(self._special_values[raw_value])
                    return IRDropdown(value=translated)
                # Otherwise it's a sprite name - use as-is
                return IRDropdown(value=raw_value)

        # Reporter blocks (x position, y position, direction)
        if self.opcode in ("MOTION_XPOSITION", "MOTION_YPOSITION", "MOTION_DIRECTION"):
            return IRDropdown(value=Translator().translateOpcode(self.opcode))

        # Fallback to base class
        return super().shadow_to_ir(blocksAST)
