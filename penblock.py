from block import SimpleBlock,replace_markers,replace_placeholders,replace_namedinput
from deco import Deco
from translator import Translator
import argparse


class PenBlock(SimpleBlock):

    def getDescription(self,ident):
        opcode2l10n = {
            "pen_clear": "pen.clear",
            "pen_stamp": "pen.stamp",
            "pen_penDown": "pen.penDown",
            "pen_penUp": "pen.penUp",
            "pen_setPenColorToColor": "pen.setColor",
            "pen_changePenColorParamBy": "pen.changeColorParam",
            "pen_setPenColorParamTo": "pen.setColorParam",
            "pen_changePenSizeBy": "pen.changeSize",
            "pen_setPenSizeTo": "pen.setSize",
            #    "pen.categoryName",
            #    "pen.changeHue",
            #    "pen.changeShade",
            #    "pen.colorMenu.brightness",
            #    "pen.colorMenu.color",
            #    "pen.colorMenu.saturation",
            #    "pen.colorMenu.transparency",
            #    "pen.setHue",
            #    "pen.setShade",
            }

        name = opcode2l10n[self.opcode]
        text = Translator().translateOpcode(name)
        return ident + Deco.rator("blok", f"\u270e : " + text + " " ,self)

    def textDecodeBlock(self, ident: str, blocksAST: dict, args: argparse.Namespace):
        # First the translated text for this opcode
        description = self.getDescription(ident)

        #pen blocks have no C-mouth, so simply coded

        # These are the fields and inputs for this block
        inputs = {}

        # decode the fields if any are specified
        if len(self.fields) > 0:
            print("No fields in pen blocks")
            sys.exit(1)

        # decode the inputs if any are specified
        if len(self.inputs) > 0:
            for name, arr in self.inputs.items():
                val = self.decodeInputFieldArray(arr,blocksAST,self)
                inputs[name]=val

        if len(inputs) > 0:
            description = replace_namedinput(description, inputs)

        # print the final translated description
        print(description)

