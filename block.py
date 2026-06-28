import sys
from dataclasses import dataclass
from importlib.metadata import pass_none
from pprint import pprint,pformat
from deco import Deco
import colorize
from colorize import Color
from translator import Translator
from traceback import clear_frames
from itertools import count
import re
import json
import argparse
from scratch3 import SCRATCH3, OPCODE_TO_CATEGORY


def replace_placeholders(text, values):
    """
    Function to replace %digit with corresponding value used to resolve the translation string
    These strings are used in the l10n files. ex:  "say %1 for %2 seconds"
    """
    try:
        return re.sub(r'%(\d+)', lambda m: str(values[int(m.group(1)) - 1]) , text)
    except IndexError:
        print("Error: Not enough values for placeholders in translation string")

def replace_markers(text):
    """
    Utility for procedure definition strings
    Replace both %s and %b in order of appearance
    ex: "dance speed %s rotate %b sing %b" => "dance speed %1 rotate %2 sing %3"
    """
    c=count(1)   # from itertools!
    return re.sub(r'%[sb]', lambda m: f"%{next(c)}", text)

def replace_namedinput(text:str, inputs:dict):
    return re.sub(r'(?<!\x1b)\[([^\]]+)\]', lambda m: str(inputs[m.group(1)]), text)

@dataclass(kw_only=True)
class Block:
    """Block class to store the scratch block information"""

    # Following fields are directly related to the blockinfo in the 'project.json' file
    opcode: str  # English text describing the block
    next: str  # Next block
    parent: str  # Parent block
    inputs: dict  # Input fields but also points to substacks in case of if-then-else blocks
    fields: dict  # Field values
    shadow: bool  # Shadow block
    topLevel: bool  # is this a top level block
    x: int  # X coordinate
    y: int  # Y coordinate
    mutation: dict|None # mutation for MyBlocks
    # These are extra variable that are used in all subclasses
    color=""



    def getDescription(self,ident):
        """
        Main purpose of this method is to get the translated version
        of the opcode of this block. No '%1,'%2' replacement
        or '[inputname]' resolving yet.
        """
        name = self.opcode
        # And for translation purposes there is already a special case...
        if name == "CONTROL_IF_ELSE":
            name = "CONTROL_IF"
        if isinstance(self.mutation, dict):
            if 'proccode' in self.mutation:
                name = replace_markers(self.mutation['proccode'])
        return ident + Deco.rator("blok",Translator().translateOpcode(name),self)

    def decodeBlocksInput(self, blocksAST: dict):
        stack1 = None
        stack2 = None
        params = []
        for name, arr in self.inputs.items():
            if name == 'SUBSTACK':
                stack1 = arr[1]
            elif name == 'SUBSTACK2':
                stack2 = arr[1]
            else:
                val = Block.decodeInputFieldArray(arr,blocksAST,self)
                val = val # + Color.color(block.color)
                params.append(val)
        return (stack1, stack2, params)


    def decodeBlocksField(self, blocksAST: dict):
        retfields = []
        for name, val in self.fields.items():
            if name == "VARIABLE":
                #retfields.append(Colorize.color("amber")+f" {val[0]} "+Colorize.color(block.color))
                retfields.append(Deco.rator("var",val[0],self))
            elif name == "LIST":
                #retfields.append(Colorize.color("orange")+f"| {val[0]} v|"+Colorize.color(block.color))
                retfields.append(Deco.rator("|v|", val[0], self))
            elif name == "BROADCAST_OPTION":
                # retfields.append(Colorize.color("orange")+f"| {val[0]} v|"+Colorize.color(block.color))
                retfields.append(Deco.rator("|v|", val[0], self))
            elif name == "STYLE": # rotation style
                retfields.append(Deco.rator("|v|",val[0],self))
            elif name == "KEY_OPTION": # keypressed option
                retfields.append(Deco.rator("|v|", val[0], self))
            elif name == "EFFECT": # looks_changeeffectby
                retfields.append(Deco.rator("|v|", val[0], self))
            elif name == "FRONT_BACK": # looks_gotofrontback
                retfields.append(Deco.rator("|v|", val[0], self))
            elif name == "FORWARD_BACKWARD": # looks_goforwardbackwardlayers
                retfields.append(Deco.rator("|v|", val[0], self))
            elif name == "BACKDROP": # event_whenbackdropswitchesto
                retfields.append(Deco.rator("|v|", val[0], self))
            else:
                retfields.append("==unknown fieldtype=="+val[0])
        return retfields


    def textDecodeBlock(self, ident: str, blocksAST: dict, args: argparse.Namespace):
        # First the translated text for this opcode
        description = self.getDescription(ident)

        # These are the fields and inputs for this block
        substack1 = None
        substack2 = None
        fields = []
        inputs = []

        # decode the fields if any are specified
        if len(self.fields) > 0:
            fields = self.decodeBlocksField(blocksAST)

        if self.opcode == "LOOKS_CHANGEEFFECTBY":
            # pass for debug break purposes
            pass
        # decode the inputs if any are specified
        if len(self.inputs) > 0:
            (substack1, substack2, inputs) = self.decodeBlocksInput(blocksAST)
        # Quick fix flag clicked translation
        if self.opcode == "EVENT_WHENFLAGCLICKED":
            # inputs.insert(0, Translator().translateOpcode("green flag"))
            inputs.insert(0, "\U0001f3f3\ufe0f\u200d\U0001f7e9")
            # combine the fields and inputs and update the description with the placeholders

        inputs = [*fields, *inputs]
        if len(inputs) > 0:
            description = replace_placeholders(description, inputs)

        # print the final translated description
        print(description)

        # Check if there is a first C-mouth (while,loop,if-then)
        newindent = Deco.indent(ident, self)
        if substack1 is not None:
            blocksAST[substack1].outputBlocks( newindent, blocksAST, args)
            # Check if there is a second C-mouth (if-then-else)
            if substack2 is not None:
                print(ident + Color.color(self.color) + " " + Translator().translateOpcode(
                    "CONTROL_ELSE") + " " + Color.reset)
                blocksAST[substack2].outputBlocks(newindent, blocksAST, args)
            print(ident + Color.color(self.color) + "_" * 8 + Color.reset)

    def outputBlocks(self, ident: str, blocksAST: dict, args: argparse.Namespace):
        block = self
        while block != None:
            block.textDecodeBlock(ident, blocksAST, args)
            block = blocksAST[block.next] if block.next != None else None

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

    @classmethod
    def decodeInputFieldArray(cls, arr: list, blocksAST: dict, block):
        val = "(unknown decodeInputFieldArray first element \"" + pformat(arr) + "\")"
        if arr[0] == 1:  # input is a shadow block aka simple round input with constant in it
            val = cls.decodeInputFieldValue(arr[1], blocksAST,block)
            #color these black on white background
            #val = Colorize.color("white") +f" {val} "
            val=Deco.rator("()",val,block)
        elif arr[0] == 2:  # there is no shadow
            val = cls.decodeInputFieldValue(arr[1], blocksAST,block)
        elif arr[0] == 3:  # there is a shadow but obscured by the input
            val = cls.decodeInputFieldValue(arr[1], blocksAST,block)
        return val

    def decodeShadowBlock(self, blocksAST: dict, parentblock ):
        if self.opcode == "PROCEDURES_PROTOTYPE":
            result=self.mutation["proccode"]
            c=count(0)
            def replace_param(match):
                if match.group(0)=="%s":
                    sub=" ( "+json.loads(self.mutation["argumentnames"])[next(c)] + " ) "
                elif match.group(0) == "%b":
                    sub = " ( " + json.loads(self.mutation["argumentnames"])[next(c)] + " ) "
                else:
                    sub = " ??" + json.loads(self.mutation["argumentnames"])[next(c)] + "?? "
                return sub

            return re.sub(r'%[sb]', replace_param, result)
        simplemenus=['sound_sounds_menu','control_create_clone_of_menu']
        if self.opcode in simplemenus:
            for name,val in self.fields.items():
             return f"| {val[0]} VV|"
        else:
          if self.opcode.endswith("_MENU"):
            retfields = []
            for name, val in self.fields.items():
                if name == "VARIABLE":
                    retfields.append(Color.color("amber") + f" {val[0]} " + Color.color(self.color))
                elif name == "LIST":
                    retfields.append(Color.color("orange") + f"| {val[0]} v|" + Color.color(self.color))
                else:
                    retfields.append(f"==unknown fieldtype== at {__file__}:{sys._getframe().f_lineno}  {name}:{val}")
            return ''.join(retfields)
          else:
            return "No specific decode for " + Translator().translateOpcode(self.opcode)

    @staticmethod
    def convert_list_to_block(block):
        """ block store as an array instead of a dict.
        This is for variables,list and direct values like numbers,angles,strings,colors,..."""
        print(f"convert_list_to_block {block}")
        opcode="data_variable" # most cases are single value variables
        x = None
        y = None
        if block[0] >3 and block[0] <9:
            #4=number,5=positive number,6=positive integer,7=integer,8=angle
            val = block[1]
            print(f"const:  {val}")
        elif block[0] == 9:
            #9=color
            val = block[1]
            print(f"color:  {val}")
        elif block[0] == 10:
            #string
            val = block[1]
            print(f"string:  {val}")
        elif block[0] == 11:
            #Broadcast message
            val = block[1]
            print(f"broadcast:  {val}")
        elif block[0] == 12:
            #variable
            val = block[1]
            id = block[2]
            if len(block) > 3:
                x = block[3]
                y = block[4]
            print(f"variable:  '{val}' id:{id}")
        elif block[0] == 13:
            opcode="data_listcontents"
            val = block[1]
            id = block[2]
            x = None
            y = None
            if len(block) > 3:
                x = block[3]
                y = block[4]
            print(f"list:  '{val}' id:{id}")
        else:
            print(f"unknown listblock {block}")
        return Block(opcode=opcode,
              next="", #block['next']
              parent="", #block['parent']
              inputs={}, #block['inputs'],
              fields={}, #block['fields'],
              shadow=False, #block['shadow'],
              topLevel=False, #block['topLevel'],
              x=x,
              y=y,
              mutation=None)

    @staticmethod
    def factory(block: dict):
        if isinstance(block, dict):
              paramdict = {
                  "opcode": block['opcode'].upper(),
                  "next": block['next'],
                  "parent": block['parent'],
                  "inputs": block['inputs'],
                  "fields": block['fields'],
                  "shadow": block['shadow'],
                  "topLevel": block['topLevel'],
                  "x": block.get('x'),
                  "y": block.get('y'),
                  "mutation": block.get('mutation')
              }

              opcode = paramdict['opcode']
              cat_color = OPCODE_TO_CATEGORY.get(opcode)

              if cat_color is None:
                  if opcode.endswith("MENU"):
                      # Unknown menu shadow block - guess color from prefix
                      prefix = opcode.split("_")[0]
                      for cat, info in SCRATCH3.items():
                          if any(op.startswith(prefix) for op in info["opcodes"]):
                              blk = SimpleBlock(**paramdict)
                              blk.color = info["color"]
                              return blk
                      blk = SimpleBlock(**paramdict)
                      blk.color = "white"
                      return blk
                  return Block(**paramdict)

              category, color = cat_color

              match category:
                  case "motion":
                      match opcode:
                          case "MOTION_TURNLEFT":
                              blk = TurnLeftRightBlock(**paramdict, left=True)
                          case "MOTION_TURNRIGHT":
                              blk = TurnLeftRightBlock(**paramdict, left=False)
                          case _:
                              blk = MotionBlock(**paramdict)

                  case "looks":
                      blk = LooksBlock(**paramdict)

                  case "operators":
                      blk = OperatorBlock(**paramdict)

                  case "sensing":
                      blk = SensingBlock(**paramdict)

                  case "variable":
                      blk = VariableBlock(**paramdict)

                  case "list":
                      blk = ListBlock(**paramdict)

                  case "penextension":
                      blk = PenBlock(**paramdict)

                  case "my":
                      blk = MyBlock(**paramdict)

                  case "event":
                      match opcode:
                          case "EVENT_BROADCAST" | "EVENT_BROADCASTANDWAIT":
                              blk = SimpleBlock(**paramdict)
                          case _:
                              blk = HatBlock(**paramdict)

                  case "control":
                      op = opcode.replace("CONTROL_", "")
                      if op in ['REPEAT', 'FOREVER', 'IF', 'REPEAT_UNTIL']:
                          blk = SingleMouthBlock(**paramdict)
                      elif op == 'IF_ELSE':
                          blk = DoubleMouthBlock(**paramdict)
                      elif op in ['WAIT', 'WAIT_UNTIL', 'CREATE_CLONE_OF']:
                          blk = SimpleBlock(**paramdict)
                      elif op == 'START_AS_CLONE':
                          blk = HatBlock(**paramdict)
                      elif op in ['DELETE_THIS_CLONE', 'STOP', 'CREATE_CLONE_OF_MENU']:
                          blk = SimpleBlock(**paramdict)
                      else:
                          raise Exception(f"Unknown control block {op}")

                  case _:
                      blk = SimpleBlock(**paramdict)

              blk.color = color
              return blk

        elif isinstance(block, list):
              return Block.convert_list_to_block(block)

        raise Exception("Unknown block type")




class SimpleBlock(Block):
    pass

class SingleMouthBlock(Block):
    pass

class DoubleMouthBlock(Block):
    pass

class VariableBlock(Block):
    def decodeShadowBlock(self, blocksAST: dict ,parentblock: Block):
        pass

class ListBlock(Block):
    def decodeShadowBlock(self, blocksAST: dict ,parentblock: Block):
        pass

class MyBlock(Block):
    def decodeShadowBlock(self, blocksAST: dict ,parentblock: Block):
        val = f"MyBlock decodeShadowBlock {self.opcode}"
        if self.opcode=="argument_reporter_string_number":
            val = Color.color(self.color) + self.fields['VALUE'][0]
        return val

    def getDescription(self,ident):
        desc=super().getDescription(ident)
        return desc


class HatBlock(Block):
    pass

class TurnLeftRightBlock(SimpleBlock):
    arrow:str
    def __init__(self,**kwargs):
        #extract our custom parameter without breaking the base kwargs
        left=kwargs.pop('left',True)
        # the rest is for the base class
        super().__init__(**kwargs)
        #unicde for turn left and right symbol used in description
        self.arrow = f"\u27F2" if left else f"\u27F3"
        # maybe use
        # self.arrow=Translator().translateOpcode("right") if left else Translator().translateOpcode("right")
        # if no unicode support


    def getDescription(self,ident):
        desc=super().getDescription(ident)
        desc=replace_placeholders(desc,[self.arrow,"%1"])
        return desc

class EventBlock(HatBlock):
    pass






from penblock import PenBlock
from motionblock import MotionBlock
from operatorblock import OperatorBlock
from looksblock import LooksBlock
from sensingblock import SensingBlock
