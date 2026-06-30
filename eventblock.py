from block import HatBlock
from ir import IR, IRDropdown
from translator import Translator


class EventBlock(HatBlock):
    """Handles event hat blocks that have fields needing translation:
    - KEY_OPTION: 'space', 'left arrow', etc. translated via EVENT_WHENKEYPRESSED_* keys
    Regular letter/number keys pass through unchanged."""

    # Reuses the same key translations as sensing
    _key_special = {
        "space": "EVENT_WHENKEYPRESSED_SPACE",
        "left arrow": "EVENT_WHENKEYPRESSED_LEFT",
        "right arrow": "EVENT_WHENKEYPRESSED_RIGHT",
        "down arrow": "EVENT_WHENKEYPRESSED_DOWN",
        "up arrow": "EVENT_WHENKEYPRESSED_UP",
        "any": "EVENT_WHENKEYPRESSED_ANY",
    }

    def _decode_fields_ir(self, blocksAST: dict) -> list[IR]:
        """Translate KEY_OPTION and WHENGREATERTHANMENU field values."""
        result = []
        for name, val in self.fields.items():
            if name == "KEY_OPTION":
                key = self._key_special.get(val[0])
                if key:
                    result.append(IRDropdown(value=Translator().translateOpcode(key)))
                else:
                    # Regular key (a-z, 0-9) - pass through
                    result.append(IRDropdown(value=val[0]))
            elif name == "WHENGREATERTHANMENU":
                # "LOUDNESS" -> EVENT_WHENGREATERTHAN_LOUDNESS
                key = f"EVENT_WHENGREATERTHAN_{val[0].upper()}"
                result.append(IRDropdown(value=Translator().translateOpcode(key)))
            else:
                result.append(IRDropdown(value=val[0]))
        return result
