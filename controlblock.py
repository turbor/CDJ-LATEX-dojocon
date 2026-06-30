from block import SimpleBlock
from ir import IR, IRBlock, IRDropdown
from translator import Translator


class ControlBlock(SimpleBlock):
    """Handles control blocks that have fields needing translation:
    - STOP_OPTION: 'all', 'this script', 'other scripts in sprite'
    - CLONE_OPTION: '_myself_' or a sprite name"""

    # Maps raw stop option values to l10n keys
    _stop_keys = {
        "all": "CONTROL_STOP_ALL",
        "this script": "CONTROL_STOP_THIS",
        "other scripts in sprite": "CONTROL_STOP_OTHER",
    }

    # Maps raw clone option values to l10n keys
    _clone_keys = {
        "_myself_": "CONTROL_CREATECLONEOF_MYSELF",
    }

    def _decode_fields_ir(self, blocksAST: dict) -> list[IR]:
        """Translate control block field values."""
        result = []
        for name, val in self.fields.items():
            if name == "STOP_OPTION":
                key = self._stop_keys.get(val[0])
                if key:
                    result.append(IRDropdown(value=Translator().translateOpcode(key)))
                else:
                    result.append(IRDropdown(value=val[0]))
            elif name == "CLONE_OPTION":
                key = self._clone_keys.get(val[0])
                if key:
                    result.append(IRDropdown(value=Translator().translateOpcode(key)))
                else:
                    # Sprite name - pass through
                    result.append(IRDropdown(value=val[0]))
            else:
                result.append(IRDropdown(value=val[0]))
        return result

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        """Handle CONTROL_CREATE_CLONE_OF_MENU shadow block."""
        if self.opcode == "CONTROL_CREATE_CLONE_OF_MENU":
            val = self.fields.get("CLONE_OPTION", [None])[0]
            if val:
                key = self._clone_keys.get(val)
                if key:
                    return IRDropdown(value=Translator().translateOpcode(key))
                return IRDropdown(value=val)
            return IRDropdown(value="?")
        return super().shadow_to_ir(blocksAST)

    def to_ir(self, blocksAST: dict) -> IR:
        """Override to append %1 placeholder when the translation text has no
        placeholders but there are field values to display (e.g. 'stop' + option)."""
        text = self._get_translated_text()
        inputs_ir = self._decode_inputs_ir(blocksAST)
        fields_ir = self._decode_fields_ir(blocksAST)
        all_params = [*fields_ir, *inputs_ir]

        # If text has no %N placeholders but we have params, append %1 %2 ...
        if all_params and '%' not in text:
            for i in range(len(all_params)):
                text += f" %{i + 1}"

        return IRBlock(opcode=self.opcode, category=self.color,
                       text=text, inputs=all_params, fields=[])
