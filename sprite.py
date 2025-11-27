from dataclasses import dataclass
from block import Block
from colorize import Colorize
from translator import Translator
import argparse
import re

# Function to replace %digit with corresponding value used to resolve the translation string
def replace_placeholders(text, values):
    try:
        return re.sub(r'%(\d+)', lambda m: " " + str(values[int(m.group(1)) - 1]) + " ", text)
    except IndexError:
        print("Error: Not enough values for placeholders in translation string")

    # return re.sub(r'%(\d+)', lambda m: "(" + str(values[int(m.group(1)) - 1]) + ")", text)


@dataclass
class Sprite:
    isStage: bool
    name: str
    variables: dict
    lists: dict
    broadcasts: dict
    blocksAST: dict
    comments: dict
    currentCostume: int
    costumes: list
    sounds: list
    layerOrder: int
    volume: int

    def dumpBlocks(self, args):
        for name, block in self.blocksAST.items():
            if block.topLevel:
                print()
                self.outputBlocks(block, "", self.blocksAST, args)

    def decodeBlocksField(self, block: Block, blocksAST: dict):
        retfields = []
        for name, val in block.fields.items():
            if name == "VARIABLE":
                retfields.append(Colorize.color("amber")+f" {val[0]} "+Colorize.color(block.color))
            else:
                retfields.append(val[0])
        return retfields

    def decodeBlocksInput(self, block: Block, blocksAST: dict):
        stack1 = None
        stack2 = None
        params = []
        for name, arr in block.inputs.items():
            if name == 'SUBSTACK':
                stack1 = arr[1]
            elif name == 'SUBSTACK2':
                stack2 = arr[1]
            else:
                val = Block.decodeInputFieldArray(arr,blocksAST)
                val = val + Colorize.color(block.color)
                params.append(val)
        return (stack1, stack2, params)

    def decocodeInputFieldValue(self, arr, blocksAST: dict):
        if isinstance(arr, str):
            # this is a shadow block, so the string is the block name
            shad = blocksAST[arr]
            n = shad.decodeShadowBlock(blocksAST) # recursively decode the shadow block
            return (n, n, n)
        if isinstance(arr, list):
            numid = arr[0]
            val = arr[1]
            id = None
            if len(arr) > 2:
                id = arr[2]
            return (numid, val, id)

        print("unknown input array")
        return ("", "", "")

    def outputBlocks(self, block: Block, ident: str, blocksAST: dict, args: argparse.Namespace):
        while block != None:
            # First the translated text for this opcode
            description = block.getDescription(ident)

            # These are the fields and inputs for this block
            substack1 = None
            substack2 = None
            fields = []
            inputs = []

            # decode the fields if any are specified
            if len(block.fields) > 0:
                fields = self.decodeBlocksField(block, blocksAST)

            if block.opcode.upper() == "MOTION_TURNRIGHT":
                # pass for debug break purposes
                pass
            # decode the inputs if any are specified
            if len(block.inputs) > 0:
                (substack1, substack2, inputs) = self.decodeBlocksInput(block, blocksAST)
            #Quick fix flag clicked translation
            if block.opcode.upper() == "EVENT_WHENFLAGCLICKED":
                #inputs.insert(0, Translator().translateOpcode("green flag"))
                inputs.insert(0,"\U0001f3f3\ufe0f\u200d\U0001f7e9")
                              #combine the fields and inputs and update the description with the placeholders
            inputs = [*fields, *inputs]
            if len(inputs) > 0:
                description = replace_placeholders(description, inputs)

            #print the final translated description
            print(description)

            # Check if there is a first C-mouth (while,loop,if-then)
            newindent = ident + Colorize.color(block.color) + "   " + Colorize.reset + " "
            if substack1 is not None:
                self.outputBlocks(blocksAST[substack1], newindent, blocksAST, args)
                # Check if there is a second C-mouth (if-then-else)
                if substack2 is not None:
                    print(ident + Colorize.color(block.color) + " " + Translator().translateOpcode("CONTROL_ELSE") + " " + Colorize.reset)
                    self.outputBlocks(blocksAST[substack2], newindent , blocksAST, args)
                print(ident + Colorize.color(block.color) + "_"*8 +Colorize.reset)

            block = blocksAST[block.next] if block.next != None else None

