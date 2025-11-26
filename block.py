from dataclasses import dataclass
from importlib.metadata import pass_none
from pprint import pprint,pformat
from colorize import Colorize
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
        return ident + Colorize.color(self.color) + " " + Translator().translateOpcode(name) + " " + Colorize.reset

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
        val = "(unknown decodeInputFieldArray first element \"" + pformat(arr) + "\")"
        if arr[0] == 1:  # input is a shadow
            val = cls.decodeInputFieldValue(arr[1], blocksAST)
        elif arr[0] == 2:  # there is no shadow
            val = cls.decodeInputFieldValue(arr[1], blocksAST)
        elif arr[0] == 3:  # there is a shadow but obscured by the input
            val = cls.decodeInputFieldValue(arr[1], blocksAST)
        return val

    def decodeShadowBlock(self, blocksAST: dict):
        return "No specific decode for " + Translator().translateOpcode(self.opcode.upper())

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
        scratch3_motionblocks = [
            "motion_movesteps",
            "motion_turnright",
            "motion_turnleft",
            "motion_goto",
            "motion_gotoxy",
            "motion_glideto",
            "motion_glidesecstoxy",
            "motion_pointindirection",
            "motion_pointtowards",
            "motion_changexby",
            "motion_setx",
            "motion_changeyby",
            "motion_sety",
            "motion_ifonedgebounce",
            "motion_setrotationstyle",
            "motion_xposition",
            "motion_yposition",
            "motion_direction"
        ]
        scratch3_looksblocks = [
            "looks_sayforsecs",
            "looks_say",
            "looks_thinkforsecs",
            "looks_think",
            "looks_switchcostumeto",
            "looks_nextcostume",
            "looks_switchbackdropto",
            "looks_switchbackdroptoandwait",
            "looks_nextbackdrop",
            "looks_changesizeby",
            "looks_setsizeto",
            "looks_changeeffectby",
            "looks_seteffectto",
            "looks_cleargraphiceffects",
            "looks_show",
            "looks_hide",
            "looks_gotofrontback",
            "looks_goforwardbackwardlayers",
            "looks_costumenumbername",
            "looks_backdropnumbername",
            "looks_size"
        ]
        scratch3_soundblocks = [
            "sound_playuntildone",
            "sound_play",
            "sound_stopallsounds",
            "sound_changeeffectby",
            "sound_seteffectto",
            "sound_cleareffects",
            "sound_changevolumeby",
            "sound_setvolumeto",
            "sound_volume"
        ]
        scratch3_eventblocks = [
            "event_whenflagclicked",
            "event_whenkeypressed",
            "event_whenthisspriteclicked",
            "event_whenstageclicked",
            "event_whenbackdropswitchesto",
            "event_whengreaterthan",
            "event_whenbroadcastreceived",
            "event_broadcast",
            "event_broadcastandwait"
        ]
        scratch3_controlblocks = [
            "control_wait",
            "control_repeat",
            "control_forever",
            "control_if",
            "control_if_else",
            "control_wait_until",
            "control_repeat_until",
            "control_stop",
            "control_start_as_clone",
            "control_create_clone_of",
            "control_delete_this_clone"
        ]
        scratch3_operators = [
            "operator_add",
            "operator_subtract",
            "operator_multiply",
            "operator_divide",
            "operator_lt",
            "operator_equals",
            "operator_gt",
            "operator_and",
            "operator_or",
            "operator_not",
            "operator_random",
            "operator_join",
            "operator_letter_of",
            "operator_length",
            "operator_contains",
            "operator_mod",
            "operator_round",
            "operator_mathop",
            ]
        if isinstance(block, dict):
            if block['opcode'] in scratch3_motionblocks:
                # The motion turnleft/turnright blocks are special because they have a different icon
                # So the have a specialized class, the other are regular MotionBlock instances
                match block['opcode'].upper():
                    case "MOTION_TURNLEFT":
                        return TurnLeftRightBlock(opcode=block['opcode'],
                                                  next=block['next'],
                                                  parent=block['parent'],
                                                  inputs=block['inputs'],
                                                  fields=block['fields'],
                                                  shadow=block['shadow'],
                                                  topLevel=block['topLevel'],
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
                                                  topLevel=block['topLevel'],
                                                  x=block.get('x'),
                                                  y=block.get('y'),
                                                  left=False)
                    case _:
                        return MotionBlock(opcode=block['opcode'],
                                next=block['next'],
                                parent=block['parent'],
                                inputs=block['inputs'],
                                fields=block['fields'],
                                shadow=block['shadow'],
                                topLevel=block['topLevel'],
                                x=block.get('x'),
                                y=block.get('y'))
            elif block['opcode'] in scratch3_looksblocks:
                return LooksBlock(opcode=block['opcode'],
                                     next=block['next'],
                                     parent=block['parent'],
                                     inputs=block['inputs'],
                                     fields=block['fields'],
                                     shadow=block['shadow'],
                                     topLevel=block['topLevel'],
                                     x=block.get('x'),
                                     y=block.get('y'))
            elif block['opcode'] in scratch3_operators:
                return OperatorBlock(opcode=block['opcode'],
                                     next=block['next'],
                                     parent=block['parent'],
                                     inputs=block['inputs'],
                                     fields=block['fields'],
                                     shadow=block['shadow'],
                                     topLevel=block['topLevel'],
                                     x=block.get('x'),
                                     y=block.get('y'))
            elif block['opcode'] in scratch3_soundblocks:
                blk = SimpleBlock(opcode=block['opcode'],
                                     next=block['next'],
                                     parent=block['parent'],
                                     inputs=block['inputs'],
                                     fields=block['fields'],
                                    shadow=block['shadow'],
                                    topLevel=block['topLevel'],
                                    x=block.get('x'),
                                    y=block.get('y'))
                blk.color="pink"
                return blk
            elif block['opcode'] in scratch3_eventblocks:
                match block['opcode'].upper():
                    case "event_broadcast":
                        blk=SimpleBlock(opcode=block['opcode'],
                                  next=block['next'],
                                  parent=block['parent'],
                                  inputs=block['inputs'],
                                  fields=block['fields'],
                                  shadow=block['shadow'],
                                  topLevel=block['topLevel'],
                                  x=block.get('x'),
                                  y=block.get('y'))
                    case "event_broadcastandwait":
                        blk = SimpleBlock(opcode=block['opcode'],
                                  next=block['next'],
                                  parent=block['parent'],
                                  inputs=block['inputs'],
                                  fields=block['fields'],
                                  shadow=block['shadow'],
                                  topLevel=block['topLevel'],
                                  x=block.get('x'),
                                  y=block.get('y'))
                    case _:
                        blk = HatBlock(opcode=block['opcode'],
                                  next=block['next'],
                                  parent=block['parent'],
                                  inputs=block['inputs'],
                                  fields=block['fields'],
                                  shadow=block['shadow'],
                                  topLevel=block['topLevel'],
                                  x=block.get('x'),
                                  y=block.get('y'))
                blk.color = "yellow"
                return blk
            elif block['opcode'] in scratch3_controlblocks:
                op=block['opcode'].replace("control_","")
                blk=None
                if op in ['repeat','forever','if','repeat_until'] :
                    blk = SingleMouthBlock(opcode=block['opcode'],
                                        next=block['next'],
                                        parent=block['parent'],
                                        inputs=block['inputs'],
                                        fields=block['fields'],
                                        shadow=block['shadow'],
                                        topLevel=block['topLevel'],
                                        x=block.get('x'),
                                        y=block.get('y'))
                elif op == 'if_else':
                    blk = DoubleMouthBlock(opcode=block['opcode'],
                                        next=block['next'],
                                        parent=block['parent'],
                                        inputs=block['inputs'],
                                        fields=block['fields'],
                                        shadow=block['shadow'],
                                        topLevel=block['topLevel'],
                                        x=block.get('x'),
                                        y=block.get('y'))
                elif op in ['wait','wait_until','create_clone_of']:
                    blk = SimpleBlock(opcode=block['opcode'],
                                           next=block['next'],
                                           parent=block['parent'],
                                           inputs=block['inputs'],
                                           fields=block['fields'],
                                           shadow=block['shadow'],
                                           topLevel=block['topLevel'],
                                           x=block.get('x'),
                                           y=block.get('y'))
                elif op == 'start_as_clone':
                    blk = HatBlock(opcode=block['opcode'],
                                            next=block['next'],
                                            parent=block['parent'],
                                            inputs=block['inputs'],
                                            fields=block['fields'],
                                            shadow=block['shadow'],
                                            topLevel=block['topLevel'],
                                            x=block.get('x'),
                                            y=block.get('y'))
                elif op in ['delete_this_clone','stop']:
                    #no end blocks for now so use simpleblock
                    blk = SimpleBlock(opcode=block['opcode'],
                                      next=block['next'],
                                      parent=block['parent'],
                                      inputs=block['inputs'],
                                      fields=block['fields'],
                                      shadow=block['shadow'],
                                      topLevel=block['topLevel'],
                                      x=block.get('x'),
                                      y=block.get('y'))
                else:
                    raise Exception(f"Unknown control block {op}")
                blk.color = "amber"
                return blk
            else:
                return Block(opcode=block['opcode'],
                                    next=block['next'],
                                    parent=block['parent'],
                                    inputs=block['inputs'],
                                    fields=block['fields'],
                                    shadow=block['shadow'],
                                    topLevel=block['topLevel'],
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

class EventBlock(HatBlock):
    color = "lightyellow"

class MotionBlock(SimpleBlock):
    color = "blue"

class LooksBlock(SimpleBlock):
    color = "purple"

class OperatorBlock(SimpleBlock):
    color = "green"
    inputNames = {
        "operator_add": ["NUM1","NUM2"],
        "operator_subtract": ["NUM1","NUM2"],
        "operator_multiply": ["NUM1","NUM2"],
        "operator_divide": ["NUM1","NUM2"],
        "operator_lt": ["OPERAND1","OPERAND2"],
        "operator_equals": ["OPERAND1","OPERAND2"],
        "operator_gt": ["OPERAND1","OPERAND2"],
        "operator_and": ["OPERAND1","OPERAND2"],
        "operator_or": ["OPERAND1","OPERAND2"],
        "operator_not": ["OPERAND"],
        "operator_random": ["FROM","TO"],
        "operator_join": ["STRING1","STRING2"],
        "operator_letter_of": ["LETTER","STRING"],
        "operator_length": ["STRING"],
        "operator_contains": ["STRING1","STRING2"],
        "operator_mod": ["NUM1","NUM2"],
        "operator_round": ["NUM"],
        "operator_mathop": ["OPERATOR", "NUM"]
    }
    def decodeShadowBlock(self, blocksAST: dict):
        if self.opcode.startswith("operator_"):
            operator_inputs=[]
            for name in self.inputNames[self.opcode]:
                try:
                    if name in self.inputs:
                        inp = self.decodeInputFieldArray(self.inputs[name], blocksAST)
                    else:
                        #inp = self.decodeInputFieldArray(self.fields[name], blocksAST)
                        inp = self.fields[name][0]
                except KeyError:
                    raise Exception(f"Missing input {name} for operator {self.opcode} : \n"+pformat(self,indent=3,compact=True))
                operator_inputs.append(inp)
            opername = self.opcode.upper().replace("TOR_", "TORS_")
            val = Translator().translateOpcode(opername)
            val = replace_placeholders(val, operator_inputs)
            return val
