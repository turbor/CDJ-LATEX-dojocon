from dataclasses import dataclass
from importlib.metadata import pass_none
from pprint import pprint

from translator import Translator
from traceback import clear_frames
import re

# Function to replace %digit with corresponding value used to resolve the translation string
def replace_placeholders(text, values):
    try:
        return re.sub(r'%(\d+)', lambda m: str(values[int(m.group(1)) - 1]) , text)
    except IndexError:
        print("Error: Not enough values for placeholders in translation string")




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
    # These are extra variable that are used in all subclasses
    color=""

    def getDescription(self,ident):
        name = self.opcode.upper()
        # And for translation purposes there is already a special case...
        if name == "CONTROL_IF_ELSE":
            name = "CONTROL_IF"
        return ident + Translator().translateOpcode(name)

    @classmethod
    def decodeInputFieldValue(self, arr, blocksAST: dict):
        if isinstance(arr, str):
            # this is a shadow block, so the string is the block name
            shad = blocksAST[arr]
            return shad.decodeShadowBlock(blocksAST) # recursively decode the shadow block
        if isinstance(arr, list):
            numid = arr[0]
            val = arr[1]
            id = None
            if len(arr) > 2:
                id = arr[2]
            return val
        return "Block.decodeInputFieldValue() failed"

    @classmethod
    def decodeInputFieldArray(cls, arr: list, blocksAST: dict):
        val = "unknown decodeInputFieldArray first element"
        if arr[0] == 1:  # input is a shadow
            val = cls.decodeInputFieldValue(arr[1], blocksAST)
        elif arr[0] == 2:  # there is no shadow
            val = cls.decodeInputFieldValue(arr[1], blocksAST)
        elif arr[0] == 3:  # there is a shadow but obscured by the input
            val = cls.decodeInputFieldValue(arr[1], blocksAST)
        return val

    def decodeShadowBlock(self, blocksAST: dict):
        if self.opcode.startswith("operator_"):
            op = self.opcode.replace("operator_", "")
            if op == "add" or op == "subtract" or op == "multiply" or op == "divide" \
                or op == "random" or op == "lt" or op == "equals" or op == "join" \
                or op == "letter_of" or op == "contains" or op == "mod":
                    #these are all operators that have two input fields
                    if not "NUM1" in self.inputs:
                        pprint(self.inputs)
                        o_one = self.inputs["OPERAND1"]
                        o_two = self.inputs["OPERAND2"]
                    else:
                        o_one = self.inputs["NUM1"]
                        o_two = self.inputs["NUM2"]
                    o_one = self.decodeInputFieldValue(o_one, blocksAST)
                    o_two = self.decodeInputFieldValue(o_two, blocksAST)
                    val = Translator().translateOpcode("OPERATORS_"+op.upper())
                    val = replace_placeholders(val,[o_one,o_two])
                    return val
            return Translator().translateOpcode(self.opcode.upper())


        return "No decode implement yet"

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
              y=y)

    @staticmethod
    def factory(block: dict):
        if isinstance(block, dict):
            match block['opcode'].upper():
                case "MOTION_TURNLEFT":
                    return TurnLeftRightBlock(opcode=block['opcode'],
                                next=block['next'],
                                parent=block['parent'],
                                inputs=block['inputs'],
                                fields=block['fields'],
                                shadow=block['shadow'],
                                topLevel=['topLevel'],
                                x=block.get('x'),
                                y=block.get('y'),
                                left=True)
                case "MOTION_TURNRIGHT":
                    return TurnLeftRightBlock(opcode=block['opcode'],
                                next=block['next'],
                                parent=block['parent'],
                                inputs=block['inputs'],
                                fields=block['fields'],
                                shadow=block['shadow'],
                                topLevel=['topLevel'],
                                x=block.get('x'),
                                y=block.get('y'),
                                left=False)
                case _:
                    return Block(opcode=block['opcode'],
                                next=block['next'],
                                parent=block['parent'],
                                inputs=block['inputs'],
                                fields=block['fields'],
                                shadow=block['shadow'],
                                topLevel=['topLevel'],
                                x=block.get('x'),
                                y=block.get('y'))
        elif isinstance(block, list):
            return Block.convert_list_to_block(block)
        raise Exception("Unknown block type")

class SimpleBlock(Block):
    color = "lightblue"

class SingleMouthBlock(Block):
    color = "lightgreen"

class DoubleMouthBlock(Block):
    color = "lightgreen"

class HatBlock(Block):
    color = "lightblue"

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
