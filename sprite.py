from dataclasses import dataclass
from block import Block
from translator import Translator
import argparse
import re

# Function to replace %digit with corresponding value used to resolve the translation string
def replace_placeholders(text, values):
    try:
        re.sub(r'%(\d+)', lambda m: "(" + str(values[int(m.group(1)) - 1]) + ")", text)
    except IndexError:
        print("Error: Not enough values for placeholders in translation string")

    return re.sub(r'%(\d+)', lambda m: "(" + str(values[int(m.group(1)) - 1]) + ")", text)


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

    def decodeBlocksField(self, input: dict, blocksAST: dict):
        fields = []
        for name, val in input.items():
            fields.append(val[0])
        return fields

    def decodeBlocksInput(self, inputfield: dict, blocksAST: dict):
        stack1 = None
        stack2 = None
        params = []
        for name, arr in inputfield.items():
            if name == 'SUBSTACK':
                stack1 = arr[1]
            elif name == 'SUBSTACK2':
                stack2 = arr[1]
            else:
                val = Block.decodeInputFieldArray(arr,blocksAST)
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
                fields = self.decodeBlocksField(block.fields, blocksAST)

            if block.opcode.upper() == "MOTION_TURNRIGHT":
                # pass for debug break purposes
                pass
            # decode the inputs if any are specified
            if len(block.inputs) > 0:
                (substack1, substack2, inputs) = self.decodeBlocksInput(block.inputs, blocksAST)
            #Quick fix flag clicked translation
            if block.opcode.upper() == "EVENT_WHENFLAGCLICKED":
                inputs.insert(0, Translator().translateOpcode("green flag"))

            #combine the fields and inputs and update the description with the placeholders
            inputs = [*fields, *inputs]
            if len(inputs) > 0:
                description = replace_placeholders(description, inputs)

            #print the final translated description
            print(description)

            # Check if there is a first C-mouth (while,loop,if-then)
            if substack1 is not None:
                self.outputBlocks(blocksAST[substack1], ident + "    ", blocksAST, args)
            # Check if there is a second C-mouth (if-then-else)
            if substack2 is not None:
                print(ident + Translator().translateOpcode("CONTROL_ELSE"))
                self.outputBlocks(blocksAST[substack2], ident + "    ", blocksAST, args)

            block = blocksAST[block.next] if block.next != None else None

