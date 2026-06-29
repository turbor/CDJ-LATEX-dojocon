from block import SimpleBlock
from ir import IR, IRDropdown, IROperator
from translator import Translator


class LooksBlock(SimpleBlock):
    """Handles looks blocks. Overrides shadow_to_ir() for costume/backdrop
    menu shadows and _decode_fields_ir() for effect/layer/numbername dropdowns
    that need translation via constructed l10n keys."""

    # Maps menu opcodes to the field key holding the selection
    _menu_field_keys = {
        "LOOKS_BACKDROPS": "BACKDROP",
        "LOOKS_COSTUME": "COSTUME",
    }

    # Special backdrop values that need translation
    _backdrop_special = {
        "next backdrop": "LOOKS_NEXTBACKDROP_BLOCK",
        "previous backdrop": "LOOKS_PREVIOUSBACKDROP",
        "random backdrop": "LOOKS_RANDOMBACKDROP",
    }

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        """Decode costume/backdrop menu shadows and numbername reporters."""
        if self.opcode in self._menu_field_keys:
            field_key = self._menu_field_keys[self.opcode]
            destination = self.fields[field_key]
            if isinstance(destination, list):
                raw = destination[0]
                # Translate special backdrop values
                if self.opcode == "LOOKS_BACKDROPS" and raw in self._backdrop_special:
                    return IRDropdown(value=Translator().translateOpcode(self._backdrop_special[raw]))
                return IRDropdown(value=raw)
            return IRDropdown(value=str(destination))

        # "costume number/name" and "backdrop number/name" reporters
        if self.opcode in ("LOOKS_COSTUMENUMBERNAME", "LOOKS_BACKDROPNUMBERNAME"):
            text = Translator().translateOpcode(self.opcode)
            operands = []
            nn = self.fields.get("NUMBER_NAME", [None])[0]
            if nn:
                key = f"LOOKS_NUMBERNAME_{nn.upper()}"
                operands.append(IRDropdown(value=Translator().translateOpcode(key)))
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=operands)

        return super().shadow_to_ir(blocksAST)

    def _decode_fields_ir(self, blocksAST: dict) -> list[IR]:
        """Override field decoding to translate effect/layer dropdown values.
        Constructs translation keys like LOOKS_EFFECT_COLOR, LOOKS_GOTOFRONTBACK_FRONT, etc."""
        result = []
        for name, val in self.fields.items():
            match name:
                case "FRONT_BACK":
                    # e.g. "front" -> LOOKS_GOTOFRONTBACK_FRONT
                    key = f"LOOKS_GOTOFRONTBACK_{val[0].upper()}"
                    result.append(IRDropdown(value=Translator().translateOpcode(key)))
                case "FORWARD_BACKWARD":
                    # e.g. "forward" -> LOOKS_GOFORWARDBACKWARDLAYERS_FORWARD
                    key = f"LOOKS_GOFORWARDBACKWARDLAYERS_{val[0].upper()}"
                    result.append(IRDropdown(value=Translator().translateOpcode(key)))
                case "EFFECT":
                    # e.g. "color" -> LOOKS_EFFECT_COLOR
                    key = f"LOOKS_EFFECT_{val[0].upper()}"
                    result.append(IRDropdown(value=Translator().translateOpcode(key)))
                case "NUMBER_NAME":
                    # e.g. "number" -> LOOKS_NUMBERNAME_NUMBER
                    key = f"LOOKS_NUMBERNAME_{val[0].upper()}"
                    result.append(IRDropdown(value=Translator().translateOpcode(key)))
                case _:
                    result.append(IRDropdown(value=val[0]))
        return result
