from block import SimpleBlock
from ir import IR, IRBlock, IRValue
from translator import Translator
import re


class PenBlock(SimpleBlock):
    """Handles pen extension blocks. Overrides to_ir() because pen blocks
    use dot-notation l10n keys (e.g. "pen.clear") and named input placeholders
    like [COLOR] instead of positional %1 placeholders.
    We convert [NAME] placeholders to %N so the renderer can handle them uniformly."""

    # Maps uppercased pen opcodes to their l10n translation keys
    _opcode_to_l10n = {
        "PEN_CLEAR": "pen.clear",
        "PEN_STAMP": "pen.stamp",
        "PEN_PENDOWN": "pen.penDown",
        "PEN_PENUP": "pen.penUp",
        "PEN_SETPENCOLORTOCOLOR": "pen.setColor",
        "PEN_CHANGEPENCOLORPARAMBY": "pen.changeColorParam",
        "PEN_SETPENCOLORPARAMTO": "pen.setColorParam",
        "PEN_CHANGEPENSIZEBY": "pen.changeSize",
        "PEN_SETPENSIZETO": "pen.setSize",
    }

    def to_ir(self, blocksAST: dict) -> IR:
        """Convert named [PLACEHOLDER] text to positional %N format so the
        renderer handles all substitution uniformly."""
        l10n_key = self._opcode_to_l10n.get(self.opcode, self.opcode)
        text = Translator().translateOpcode(l10n_key)

        # Pen icon prefix
        text = "\u270e : " + text

        # Decode inputs preserving their order
        input_names = []
        input_nodes = []
        for name, arr in self.inputs.items():
            input_names.append(name)
            input_nodes.append(self._decode_input_array_ir(arr, blocksAST))

        # Convert [NAME] placeholders to %1, %2, ... in the order inputs appear
        # so the renderer can substitute them with proper formatting
        for i, name in enumerate(input_names):
            text = text.replace(f"[{name}]", f"%{i + 1}")

        return IRBlock(opcode=self.opcode, category=self.color,
                       text=text, inputs=input_nodes, fields=[])
