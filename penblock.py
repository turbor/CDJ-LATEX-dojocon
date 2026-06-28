from block import SimpleBlock, replace_namedinput
from ir import IR, IRBlock, IRValue
from translator import Translator


class PenBlock(SimpleBlock):
    """Handles pen extension blocks. Overrides to_ir() because pen blocks
    use dot-notation l10n keys (e.g. "pen.clear") and named input placeholders
    like [COLOR] instead of positional %1 placeholders."""

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
        """Pen blocks use named placeholders [COLOR], [SIZE] etc. in their
        translation strings instead of positional %1, %2."""
        l10n_key = self._opcode_to_l10n.get(self.opcode, self.opcode)
        text = Translator().translateOpcode(l10n_key)

        # Pen icon prefix
        text = "\u270e : " + text

        # Decode inputs as a name->IR dict for named placeholder replacement
        inputs_by_name = {}
        for name, arr in self.inputs.items():
            inputs_by_name[name] = self._decode_input_array_ir(arr, blocksAST)

        # Replace [NAME] placeholders with the decoded input values
        if inputs_by_name:
            placeholder_strings = {k: self._ir_to_placeholder(v) for k, v in inputs_by_name.items()}
            text = replace_namedinput(text, placeholder_strings)

        return IRBlock(opcode=self.opcode, category=self.color,
                       text=text, inputs=list(inputs_by_name.values()), fields=[])
