from dataclasses import dataclass
from block import Block
from colorize import Color
from translator import Translator
import argparse
import re
from deco import Deco

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



    def outputBlocks(self, block: Block, ident: str, blocksAST: dict, args: argparse.Namespace):
        while block != None:
            block.textDecodeBlock(ident, blocksAST, args)
            block = blocksAST[block.next] if block.next != None else None




