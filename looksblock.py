from multiprocessing.util import sub_warning

from block import SimpleBlock,replace_markers,replace_placeholders,replace_namedinput
from deco import Deco
from translator import Translator
import argparse

class LooksBlock(SimpleBlock):
    def decodeShadowBlock(self, blocksAST: dict, parentblock ):
            keyname={
                "LOOKS_BACKDROPS": 'BACKDROP',
                "LOOKS_COSTUME": 'COSTUME',
            }
            if self.opcode in keyname:
                destination = self.fields[ keyname[self.opcode] ]
            else:
                raise Exception(f"{__file__}:{sys._getframe().f_lineno}  Unknown shadow block {self.opcode}")
            if isinstance(destination,list):
                #match destination[0]:
                #    case "_random_":
                #        destination = Translator().translateOpcode("MOTION_GOTO_RANDOM")
                #    case "_mouse_":
                #        destination = Translator().translateOpcode("MOTION_GOTO_POINTER")
                #    case _:
                destination = destination[0] # name of sprite to go to
                return destination

    def decodeBlocksField(self, blocksAST: dict):
        retfields = []
        for name, val in self.fields.items():
            match name:
                case "FRONT_BACK": # looks_gotofrontback LOOKS_GOTOFRONTBACK_
                    effectname = val[0].upper()
                    effectname = Translator().translateOpcode(f"LOOKS_GOTOFRONTBACK_{effectname}")
                    retfields.append(Deco.rator("|v|", effectname, self))
                case "FORWARD_BACKWARD": # looks_goforwardbackwardlayers
                    effectname = val[0].upper()
                    effectname = Translator().translateOpcode(f"LOOKS_GOFORWARDBACKWARDLAYERS_{effectname}")
                    retfields.append(Deco.rator("|v|", effectname, self))
                case "EFFECT": # looks_seteffectto
                    effectname=val[0].upper()
                    effectname=Translator().translateOpcode(f"LOOKS_EFFECT_{effectname}")
                    retfields.append(Deco.rator("|v|", effectname, self))
                case _:
                    retfields.append("==unknown fieldtype=="+val[0])
        return retfields


