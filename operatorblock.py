from block import Block,SimpleBlock,replace_markers,replace_placeholders,replace_namedinput
from deco import Deco
from translator import Translator
from colorize import Color
from pprint import pformat
import argparse

class OperatorBlock(SimpleBlock):
    inputNames = {
        "OPERATOR_ADD": ["NUM1","NUM2"],
        "OPERATOR_SUBTRACT": ["NUM1","NUM2"],
        "OPERATOR_MULTIPLY": ["NUM1","NUM2"],
        "OPERATOR_DIVIDE": ["NUM1","NUM2"],
        "OPERATOR_LT": ["OPERAND1","OPERAND2"],
        "OPERATOR_EQUALS": ["OPERAND1","OPERAND2"],
        "OPERATOR_GT": ["OPERAND1","OPERAND2"],
        "OPERATOR_AND": ["OPERAND1","OPERAND2"],
        "OPERATOR_OR": ["OPERAND1","OPERAND2"],
        "OPERATOR_NOT": ["OPERAND"],
        "OPERATOR_RANDOM": ["FROM","TO"],
        "OPERATOR_JOIN": ["STRING1","STRING2"],
        "OPERATOR_LETTER_OF": ["LETTER","STRING"],
        "OPERATOR_LENGTH": ["STRING"],
        "OPERATOR_CONTAINS": ["STRING1","STRING2"],
        "OPERATOR_MOD": ["NUM1","NUM2"],
        "OPERATOR_ROUND": ["NUM"],
        "OPERATOR_MATHOP": ["OPERATOR", "NUM"]
    }
    def decodeShadowBlock(self, blocksAST: dict, parentblock: Block):
        operator_inputs=[]
        inp="==None=="
        for name in self.inputNames[self.opcode]:
            try:
                if name in self.inputs:
                    inp = self.decodeInputFieldArray(self.inputs[name], blocksAST,self)
                else:
                    #inp = self.decodeInputFieldArray(self.fields[name], blocksAST)
                    inp = self.fields[name][0]
            except KeyError:
                raise Exception(f"Missing input {name} for operator {self.opcode} : \n"+pformat(self,indent=3,compact=True))
            #add to list but make sure that we switch back to our own color!!
            operator_inputs.append(inp + Color.color(self.color))
        opername = self.opcode.upper().replace("TOR_", "TORS_")
        val = Translator().translateOpcode(opername)
        val = replace_placeholders(val, operator_inputs)
        #now colorize some triangles in front and back
        val = Color.color(self.color) + "< " + val + Color.color(self.color) + " >"
        val = Deco.rator("<>",val,self)
        return val

