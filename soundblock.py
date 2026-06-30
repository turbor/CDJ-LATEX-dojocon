from block import SimpleBlock
from ir import IR, IRDropdown
from translator import Translator


class SoundBlock(SimpleBlock):
    """Handles sound blocks. Overrides _decode_fields_ir() to translate
    the EFFECT field (PITCH, PAN) via SOUND_EFFECTS_* l10n keys."""

    def _decode_fields_ir(self, blocksAST: dict) -> list[IR]:
        """Translate sound effect dropdown values."""
        result = []
        for name, val in self.fields.items():
            if name == "EFFECT":
                # e.g. "PITCH" -> SOUND_EFFECTS_PITCH
                key = f"SOUND_EFFECTS_{val[0].upper()}"
                result.append(IRDropdown(value=Translator().translateOpcode(key)))
            else:
                result.append(IRDropdown(value=val[0]))
        return result
