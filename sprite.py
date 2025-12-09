from dataclasses import dataclass
from block import Block
import argparse

@dataclass
class Sprite:
    """The sprite class represents the scratch sprites and background stage."""
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
        """
        This will output the coding blocks for this sprite.
         Kind a like the coding tab in the scratch editor window.

         For now it is a random dump of all the coding blocks. We could
         use the x,y coordinates of the toplevel blocks to sort them
         efore printing, but for now simply loop over them and print
         disregarding any visual clues.
         """
        for name, block in self.blocksAST.items():
            if block.topLevel:
                print()
                self.outputBlocks(block, "", self.blocksAST, args)

    def outputBlocks(self, block: Block, ident: str, blocksAST: dict, args: argparse.Namespace):
        """
        Print a block and all the blocks connected below this block.
        The ident is used if you need to print blocks included in a C-group
        """
        while block != None:
            block.textDecodeBlock(ident, blocksAST, args)
            block = blocksAST[block.next] if block.next != None else None
