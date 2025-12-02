from dataclasses import dataclass
from importlib.metadata import pass_none
from pprint import pprint,pformat

import colorize
from colorize import Colorize
from translator import Translator
from traceback import clear_frames
from itertools import count
import re
import json

# Function to replace %digit with corresponding value used to resolve the translation string
def replace_placeholders(text, values):
    try:
        return re.sub(r'%(\d+)', lambda m: str(values[int(m.group(1)) - 1]) , text)
    except IndexError:
        print("Error: Not enough values for placeholders in translation string")

def replace_markers(text):
    c=count(1)   # from itertools!
    # Replace both %s and %b in order of appearance
    return re.sub(r'%[sb]', lambda m: f"%{next(c)}", text)


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
        name = self.opcode.upper()
        # And for translation purposes there is already a special case...
        if name == "CONTROL_IF_ELSE":
            name = "CONTROL_IF"
        if isinstance(self.mutation, dict):
            name = replace_markers(self.mutation['proccode'])

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
        if arr[0] == 1:  # input is a shadow aka simple round input with constant in it
            val = cls.decodeInputFieldValue(arr[1], blocksAST)
            #color these black on white background
            val = Colorize.color("white") +f" {val} "
        elif arr[0] == 2:  # there is no shadow
            val = cls.decodeInputFieldValue(arr[1], blocksAST)
        elif arr[0] == 3:  # there is a shadow but obscured by the input
            val = cls.decodeInputFieldValue(arr[1], blocksAST)
        return val

    def decodeShadowBlock(self, blocksAST: dict):
        if self.opcode.upper() == "PROCEDURES_PROTOTYPE":
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
        if self.opcode.upper().endswith("_MENU"):
            retfields = []
            for name, val in self.fields.items():
                if name == "VARIABLE":
                    retfields.append(Colorize.color("amber") + f" {val[0]} " + Colorize.color(block.color))
                elif name == "LIST":
                    retfields.append(Colorize.color("orange") + f"| {val[0]} v|" + Colorize.color(block.color))
                else:
                    retfields.append("==unknown fieldtype==" + val[0])
            return ''.join(retfields)
        else:
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
              y=y,
              mutation=None)

    @staticmethod
    def factory(block: dict):
        scratch3={}
        scratch3["motion"] ={"opcodes": [
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
        ],"color":"blueberry","rgb":"4c97ff"}
        scratch3["looks"] ={"opcodes": [
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
        ],"color":"lightviolet","rgb":"#9966ff"}
        scratch3["sound"] ={"opcodes":  [
            "sound_playuntildone",
            "sound_play",
            "sound_stopallsounds",
            "sound_changeeffectby",
            "sound_seteffectto",
            "sound_cleareffects",
            "sound_changevolumeby",
            "sound_setvolumeto",
            "sound_volume"
        ],"color":"magenta","rgb":"#cf5acf"}
        scratch3["event"] ={"opcodes":  [
            "event_whenflagclicked",
            "event_whenkeypressed",
            "event_whenthisspriteclicked",
            "event_whenstageclicked",
            "event_whenbackdropswitchesto",
            "event_whengreaterthan",
            "event_whenbroadcastreceived",
            "event_broadcast",
            "event_broadcastandwait"
        ],"color":"amber","rgb":"#ffbf00"}
        scratch3["control"] ={"opcodes":  [
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
        ],"color":"brightyellow","rgb":"#ffab19"}
        scratch3["sensing"] ={"opcodes":  [
            "sensing_touchingobject",
            "sensing_touchingcolor",
            "sensing_coloristouchingcolor",
            "sensing_distanceto",
            "sensing_askandwait",
            "sensing_answer",
            "sensing_keypressed",
            "sensing_mousedown",
            "sensing_mousex",
            "sensing_mousey",
            "sensing_setdragmode",
            "sensing_loudness",
            "sensing_timer",
            "sensing_resettimer",
            "sensing_of",
            "sensing_current",
            "sensing_dayssince2000",
            "sensing_username"
        ],"color":"moderateblue","rgb":"#5cb1d6"}
        scratch3["operators"] ={"opcodes":  [
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
            ],"color":"coolgreen","rgb":"#52b55a"}
        scratch3["variable"] ={"opcodes":  [
            "data_variable",
            "data_setvariableto",
            "data_changevariableby",
            "data_showvariable",
            "data_hidevariable"
        ],"color":"mango","rgb":"#ff8c1a"}
        scratch3["list"] ={"opcodes":  [
            "data_deletealloflist",
            "data_insertatlist",
            "data_replaceitemoflist",
            "data_itemoflist",
            "data_itemnumoflist",
            "data_lengthoflist",
            "data_listcontainsitem",
            "data_showlist",
            "data_hidelist"
        ],"color":"orange","rgb":"#ff4c00"}
        scratch3["my"] ={"opcodes":  [
            "procedures_definition",
            "procedures_call",
            "argument_reporter_string_number",
            "argument_reporter_boolean"
        ],"color":"hotpink","rgb":"#ff4d88"}
        scratch3["musicextension"] ={"opcodes":  [
            "music_playDrumForBeats",
            "music_restForBeats",
            "music_playNoteForBeats",
            "music_setInstrument",
            "music_setTempo",
            "music_changeTempo",
            "music_getTempo"
        ],"color":"limegreen","rgb":"#0fbd8c"}
        scratch3["penExtension"] ={"opcodes":  [
            "pen_clear",
            "pen_stamp",
            "pen_penDown",
            "pen_penUp",
            "pen_setPenColorToColor",
            "pen_changePenColorParamBy",
            "pen_setPenColorParamTo",
            "pen_changePenSizeBy",
            "pen_setPenSizeTo"
        ],"color":"limegreen","rgb":"#0fbd8c"}
        scratch3["videoExtension"] ={"opcodes":  [
            "videoSensing_whenMotionGreaterThan",
            "videoSensing_videoOn",
            "videoSensing_videoToggle",
            "videoSensing_setVideoTransparency"
        ],"color":"limegreen","rgb":"#0fbd8c"}
        scratch3["faceSensingExtension"] ={"opcodes":  [
            "faceSensing_goToPart",
            "faceSensing_pointInFaceTiltDirection",
            "faceSensing_setSizeToFaceSize",
            "faceSensing_whenTilted",
            "faceSensing_whenSpriteTouchesPart",
            "faceSensing_whenFaceDetected",
            "faceSensing_faceIsDetected",
            "faceSensing_faceTilt",
            "faceSensing_faceSize"
        ],"color":"limegreen","rgb":"#0fbd8c"}
        scratch3["textToSpeechExtension"] ={"opcodes":  [
            "text2speech_speakAndWait",
            "text2speech_setVoice",
            "text2speech_setLanguage"
        ],"color":"limegreen","rgb":"#0fbd8c"}
        scratch3["translateExtension"] ={"opcodes":  [
            "translate_getTranslate",
            "translate_getViewerLanguage"
        ],"color":"limegreen","rgb":"#0fbd8c"}
        scratch3["makeyMakeyExtension"] ={"opcodes":  [
            "makeymakey_whenMakeyKeyPressed",
            "makeymakey_whenCodePressed"
        ],"color":"limegreen","rgb":"#0fbd8c"}
        scratch3["microbitExtension"] ={"opcodes":  [
            "microbit_whenButtonPressed",
            "microbit_isButtonPressed",
            "microbit_whenGesture",
            "microbit_displaySymbol",
            "microbit_displayText",
            "microbit_displayClear",
            "microbit_whenTilted",
            "microbit_isTilted",
            "microbit_getTiltAngle",
            "microbit_whenPinConnected"
        ],"color":"limegreen","rgb":"#0fbd8c"}
        scratch3["goDirectForceExtension"] ={"opcodes":  [
            "gdxfor_whenGesture",
            "gdxfor_whenForcePushedOrPulled",
            "gdxfor_getForce",
            "gdxfor_whenTilted",
            "gdxfor_isTilted",
            "gdxfor_getTilt",
            "gdxfor_isFreeFalling",
            "gdxfor_getSpinSpeed",
            "gdxfor_getAcceleration"
        ],"color":"limegreen","rgb":"#0fbd8c"}
        scratch3["legoMindstormsEV3Extension"] ={"opcodes":  [
            "ev3_motorTurnClockwise",
            "ev3_motorTurnCounterClockwise",
            "ev3_motorSetPower",
            "ev3_getMotorPosition",
            "ev3_whenButtonPressed",
            "ev3_whenDistanceLessThan",
            "ev3_whenBrightnessLessThan",
            "ev3_buttonPressed",
            "ev3_getDistance",
            "ev3_getBrightness",
            "ev3_beep"
        ],"color":"limegreen","rgb":"#0fbd8c"}
        scratch3["legoBoostExtension"] ={"opcodes": [
            "boost_motorOnFor",
            "boost_motorOnForRotation",
            "boost_motorOn",
            "boost_motorOff",
            "boost_setMotorPower",
            "boost_setMotorDirection",
            "boost_getMotorPosition",
            "boost_whenColor",
            "boost_seeingColor",
            "boost_whenTilted",
            "boost_getTiltAngle",
            "boost_setLightHue"
        ],"color":"limegreen","rgb":"#0fbd8c"}
        scratch3["legoWeDoExtension"] ={"opcodes": [
            "wedo2_motorOnFor",
            "wedo2_motorOn",
            "wedo2_motorOff",
            "wedo2_startMotorPower",
            "wedo2_setMotorDirection",
            "wedo2_setLightHue",
            "wedo2_whenDistance",
            "wedo2_whenTilted",
            "wedo2_getDistance",
            "wedo2_isTilted",
            "wedo2_getTiltAngle"
        ],"color":"limegreen","rgb":"#0fbd8c"}

        if isinstance(block, dict):
            a = block.get('mutation')
            if not a == None:
                pprint(a)
            paramdict={ "opcode" : block['opcode'],
                        "next" : block['next'],
                        "parent" : block['parent'],
                        "inputs" : block['inputs'],
                        "fields" : block['fields'],
                        "shadow" : block['shadow'],
                        "topLevel" : block['topLevel'],
                        "x" : block.get('x'),
                        "y" : block.get('y'),
                        "mutation" : block.get('mutation')
                        }
            if block['opcode']=='procedures_prototype':
                pass

            if block['opcode'] in scratch3["motion"]["opcodes"]:
                # The motion turnleft/turnright blocks are special because they have a different icon
                # So the have a specialized class, the other are regular MotionBlock instances
                blk = None
                match block['opcode'].upper():
                    case "MOTION_TURNLEFT":
                        blk = TurnLeftRightBlock(**paramdict, left=True)
                    case "MOTION_TURNRIGHT":
                        blk = TurnLeftRightBlock(**paramdict, left=False)
                    case _:
                        blk = MotionBlock(**paramdict)
                blk.color = scratch3["motion"]["color"]
                return blk
            elif block['opcode'] in scratch3["looks"]["opcodes"]:
                blk = SimpleBlock(**paramdict)
                blk.color = scratch3["looks"]["color"]
                return blk
            elif block['opcode'] in scratch3["operators"]["opcodes"]:
                blk = OperatorBlock(**paramdict)
                blk.color=scratch3["operators"]["color"]
                return blk
            elif block['opcode'] in scratch3["sound"]["opcodes"]:
                blk = SimpleBlock(**paramdict)
                blk.color=scratch3["sound"]["color"]
                return blk
            elif block['opcode'] in scratch3["variable"]["opcodes"]:
                blk = VariableBlock(**paramdict)
                blk.color=scratch3["variable"]["color"]
                return blk
            elif block['opcode'] in scratch3["list"]["opcodes"]:
                blk = ListBlock(**paramdict)
                blk.color = scratch3["list"]["color"]
                return blk
            elif block['opcode'] in scratch3["penExtension"]["opcodes"]:
                blk = PenBlock(**paramdict)
                blk.color = scratch3["penExtension"]["color"]
                return blk
            elif block['opcode'] in scratch3["my"]["opcodes"]:
                blk = MyBlock(**paramdict)
                blk.color=scratch3["my"]["color"]
                return blk
            elif block['opcode'] in scratch3["event"]["opcodes"]:
                match block['opcode'].upper():
                    case "event_broadcast":
                        blk=SimpleBlock(**paramdict)
                    case "event_broadcastandwait":
                        blk = SimpleBlock(**paramdict)
                    case _:
                        blk = HatBlock(**paramdict)
                blk.color = scratch3["event"]["color"]
                return blk
            elif block['opcode'] in scratch3["control"]["opcodes"]:
                op=block['opcode'].replace("control_","")
                blk=None
                if op in ['repeat','forever','if','repeat_until'] :
                    blk = SingleMouthBlock(**paramdict)
                elif op == 'if_else':
                    blk = DoubleMouthBlock(**paramdict)
                elif op in ['wait','wait_until','create_clone_of']:
                    blk = SimpleBlock(**paramdict)
                elif op == 'start_as_clone':
                    blk = HatBlock(**paramdict)
                elif op in ['delete_this_clone','stop']:
                    #no end blocks for now so use simpleblock
                    blk = SimpleBlock(**paramdict)
                else:
                    raise Exception(f"Unknown control block {op}")
                blk.color = scratch3["control"]["color"]
                return blk
            else:
                for group in ["sensing","variable",
                                "list", "my", "musicextension",
                                "videoExtension", "faceSensingExtension",
                                "textToSpeechExtension", "translateExtension",
                                "makeyMakeyExtension", "microbitExtension",
                                "goDirectForceExtension", "legoMindstormsEV3Extension",
                                "legoBoostExtension", "legoWeDoExtension"]:
                    if block['opcode'] in scratch3[group]["opcodes"]:
                        blk = SimpleBlock(**paramdict)
                        blk.color = scratch3[group]["color"]
                        return blk
                    if block['opcode'].endswith("menu"):
                        blk = SimpleBlock(**paramdict)
                        blk.color = scratch3[group]["color"]
                        return blk

                #raise Exception(f"unknown opcode to make block from {block['opcode']}")
                return Block(**paramdict)
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
    def decodeShadowBlock(self, blocksAST: dict):
        pass

class ListBlock(Block):
    def decodeShadowBlock(self, blocksAST: dict):
        pass

class MyBlock(Block):
    def decodeShadowBlock(self, blocksAST: dict):
        val = f"MyBlock decodeShadowBlock {self.opcode}"
        if self.opcode=="argument_reporter_string_number":
            val = Colorize.color(self.color)+self.fields['VALUE'][0]
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

class MotionBlock(SimpleBlock):
    pass



class OperatorBlock(SimpleBlock):
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
        operator_inputs=[]
        inp="==None=="
        for name in self.inputNames[self.opcode]:
            try:
                if name in self.inputs:
                    inp = self.decodeInputFieldArray(self.inputs[name], blocksAST)
                else:
                    #inp = self.decodeInputFieldArray(self.fields[name], blocksAST)
                    inp = self.fields[name][0]
            except KeyError:
                raise Exception(f"Missing input {name} for operator {self.opcode} : \n"+pformat(self,indent=3,compact=True))
            #add to list but make sure that we switch back to our own color!!
            operator_inputs.append(inp+Colorize.color(self.color))
        opername = self.opcode.upper().replace("TOR_", "TORS_")
        val = Translator().translateOpcode(opername)
        val = replace_placeholders(val, operator_inputs)
        #now colorize some triangles in front and back
        val = Colorize.color(self.color) + "< "+ val + Colorize.color(self.color) + " >"
        return val


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
        # And for translation purposes there is already a special case...
        if isinstance(self.mutation, dict):
            name = replace_markers(self.mutation['proccode'])
        return ident + Colorize.color(self.color) + f"\u270e | " + Translator().translateOpcode(name) + " " + Colorize.reset
