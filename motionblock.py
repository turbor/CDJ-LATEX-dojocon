from block import SimpleBlock,replace_markers,replace_placeholders,replace_namedinput
from deco import Deco
from translator import Translator
import argparse
import sys

class MotionBlock(SimpleBlock):
    def decodeShadowBlock(self, blocksAST: dict, parentblock ):
        if self.opcode.endswith("_MENU"):
            keyname={
                "MOTION_POINTTOWARDS_MENU": 'TOWARDS',
                "MOTION_GOTO_MENU": 'TO',
                "MOTION_GLIDETO_MENU": 'TO',
            }
            if self.opcode in keyname:
                destination = self.fields[ keyname[self.opcode] ]
            else:
                raise Exception(f"Unknown shadow block {self.opcode}")
            if isinstance(destination,list):
                match destination[0]:
                    case "_random_":
                        destination = Translator().translateOpcode("MOTION_GOTO_RANDOM")
                    case "_mouse_":
                        destination = Translator().translateOpcode("MOTION_GOTO_POINTER")
                    case _:
                        destination=destination[0] # name of sprite to go to
                return destination
        if self.opcode in ["MOTION_DIRECTION"]:
            return Translator().translateOpcode(self.opcode)
        sys.exit(1)
