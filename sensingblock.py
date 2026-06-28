from block import SimpleBlock,Block,replace_markers,replace_placeholders,replace_namedinput
from deco import Deco
from translator import Translator
import argparse

class SensingBlock(SimpleBlock):
    inputNames = {
        "OPERATOR_MATHOP": ["OPERATOR", "NUM"]
    }
    def decodeShadowBlock(self, blocksAST: dict, parentblock: Block):
        operator_inputs=[]
        if self.opcode=="SENSING_TOUCHINGOBJECT":
            val = Translator().translateOpcode(self.opcode.upper())
            item = self.inputs["TOUCHINGOBJECTMENU"]
            item = self.decodeInputFieldValue(item,blocksAST,self)
            item = Translator().translateOpcode(item)
            val = replace_placeholders(val, operator_inputs)
            val = Deco.rator("()", val, self)
            return val
        if self.opcode == "SENSING_CURRENT":
            val = Translator().translateOpcode(self.opcode.upper())
            item = self.opcode.upper() + "_" + self.fields["CURRENTMENU"][0]
            item = Translator().translateOpcode(item)
            operator_inputs.append(item)
            val = replace_placeholders(val, operator_inputs)
            val = Deco.rator("()", val, self)
            return val
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
        opername = self.opcode.replace("TOR_", "TORS_")
        val = Translator().translateOpcode(opername)
        val = replace_placeholders(val, operator_inputs)
        #now colorize some triangles in front and back
        val = Color.color(self.color) + "< " + val + Color.color(self.color) + " >"
        val = Deco.rator("<>",val,self)
        return val


    @classmethod
    def decodeInputFieldValue(self, arr, blocksAST: dict, block):
        if isinstance(arr, str):
            # this is a shadow block, so the string is the block name
            shad = blocksAST[arr]
            return shad.decodeShadowBlock(blocksAST,block) # recursively decode the shadow block
        if isinstance(arr, list):
            numid = arr[0]
            val = arr[1]
            id = None
            if len(arr) > 2:
                id = arr[2]
            return val
        return "Block.decodeInputFieldValue() failed"