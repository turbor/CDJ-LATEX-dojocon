from block import SimpleBlock, replace_placeholders
from ir import IR, IROperator, IRValue
from translator import Translator


class OperatorBlock(SimpleBlock):
    """Handles operator blocks (math, logic, string).
    These blocks are typically used as reporters dropped into other blocks' input slots,
    so shadow_to_ir() is the primary method producing an IROperator node."""

    # Maps each operator opcode to its expected input field names (in order)
    _input_names = {
        "OPERATOR_ADD": ["NUM1", "NUM2"],
        "OPERATOR_SUBTRACT": ["NUM1", "NUM2"],
        "OPERATOR_MULTIPLY": ["NUM1", "NUM2"],
        "OPERATOR_DIVIDE": ["NUM1", "NUM2"],
        "OPERATOR_LT": ["OPERAND1", "OPERAND2"],
        "OPERATOR_EQUALS": ["OPERAND1", "OPERAND2"],
        "OPERATOR_GT": ["OPERAND1", "OPERAND2"],
        "OPERATOR_AND": ["OPERAND1", "OPERAND2"],
        "OPERATOR_OR": ["OPERAND1", "OPERAND2"],
        "OPERATOR_NOT": ["OPERAND"],
        "OPERATOR_RANDOM": ["FROM", "TO"],
        "OPERATOR_JOIN": ["STRING1", "STRING2"],
        "OPERATOR_LETTER_OF": ["LETTER", "STRING"],
        "OPERATOR_LENGTH": ["STRING"],
        "OPERATOR_CONTAINS": ["STRING1", "STRING2"],
        "OPERATOR_MOD": ["NUM1", "NUM2"],
        "OPERATOR_ROUND": ["NUM"],
        "OPERATOR_MATHOP": ["OPERATOR", "NUM"],
    }

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        """Decode this operator as an inline reporter.
        Recursively decodes operands and builds the translated expression text."""
        operands = []
        for name in self._input_names.get(self.opcode, []):
            if name in self.inputs:
                operands.append(self._decode_input_array_ir(self.inputs[name], blocksAST))
            elif name in self.fields:
                # Some operators (MATHOP) have a field instead of input for the function name
                operands.append(IRValue(value=self.fields[name][0], kind="string"))
            else:
                operands.append(IRValue(value="?", kind="unknown"))

        # Translation key uses OPERATORS_ (with S) instead of OPERATOR_
        translation_key = self.opcode.replace("TOR_", "TORS_")
        text = Translator().translateOpcode(translation_key)

        # Fill in the placeholders with the operand placeholder texts
        placeholder_values = [self._ir_to_placeholder(op) for op in operands]
        text = replace_placeholders(text, placeholder_values)

        return IROperator(opcode=self.opcode, category=self.color,
                          text=text, operands=operands)
