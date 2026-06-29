import sys
from dataclasses import dataclass
from itertools import count
import re
import json
from scratch3 import SCRATCH3, OPCODE_TO_CATEGORY
from translator import Translator
from ir import (IR, IRScript, IRBlock, IRCMouth, IRValue,
                IRDropdown, IRVariable, IRList, IROperator, IRHatBlock,
                build_ir_script)


def replace_placeholders(text, values):
    """
    Replace %digit with corresponding value used to resolve the translation string.
    These strings are used in the l10n files. ex: "say %1 for %2 seconds"
    """
    try:
        return re.sub(r'%(\d+)', lambda m: str(values[int(m.group(1)) - 1]), text)
    except IndexError:
        print("Error: Not enough values for placeholders in translation string")
        return text


def replace_markers(text):
    """
    Utility for procedure definition strings.
    Replace both %s and %b in order of appearance.
    ex: "dance speed %s rotate %b sing %b" => "dance speed %1 rotate %2 sing %3"

    Scratch 3 only uses %s (string/number) and %b (boolean) in proccodes.
    Scratch 2 had %n for numbers, but that was merged into %s in Scratch 3.
    """
    c = count(1)
    return re.sub(r'%[sb]', lambda m: f"%{next(c)}", text)


def replace_namedinput(text: str, inputs: dict):
    """Replace [NAME] placeholders with values from inputs dict."""
    return re.sub(r'(?<!\x1b)\[([^\]]+)\]', lambda m: str(inputs[m.group(1)]), text)


@dataclass(kw_only=True)
class Block:
    """Block class to store the scratch block information"""

    # Following fields are directly related to the blockinfo in the 'project.json' file
    opcode: str          # Opcode identifying the block type
    next: str            # Next block in chain
    parent: str          # Parent block
    inputs: dict         # Input fields, also points to substacks for C-mouth blocks
    fields: dict         # Field values (dropdowns, static selections)
    shadow: bool         # True if this is a shadow block
    topLevel: bool       # True if this block has no parent (start of a script)
    x: int               # X coordinate on canvas
    y: int               # Y coordinate on canvas
    mutation: dict|None  # Extra data for custom blocks (My Blocks)
    # Category color name, set by factory()
    color: str = ""

    def to_ir(self, blocksAST: dict) -> IR:
        """Phase 1: Convert this block to an IR node.
        Base implementation handles simple blocks (no C-mouth).
        Text keeps %1, %2 placeholders - the renderer resolves them in Phase 2."""
        text = self._get_translated_text()
        inputs_ir = self._decode_inputs_ir(blocksAST)
        fields_ir = self._decode_fields_ir(blocksAST)
        # Combine fields and inputs as positional parameters
        all_params = [*fields_ir, *inputs_ir]
        return IRBlock(opcode=self.opcode, category=self.color,
                       text=text, inputs=all_params, fields=[])

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        """Phase 1: Convert this shadow block to an inline IR node.
        Called when this block appears as an input inside another block."""
        # Default: try to decode as a menu shadow
        if self.opcode.endswith("_MENU"):
            for name, val in self.fields.items():
                if isinstance(val, list):
                    return IRDropdown(value=val[0])
                return IRDropdown(value=str(val))
        # Fallback: translate the opcode
        return IRDropdown(value=Translator().translateOpcode(self.opcode))

    def _get_translated_text(self) -> str:
        """Get the translated description for this block's opcode."""
        name = self.opcode
        # Special case: IF_ELSE uses the IF translation (else is separate)
        if name == "CONTROL_IF_ELSE":
            name = "CONTROL_IF"
        # Custom blocks use the proccode from mutation
        if isinstance(self.mutation, dict) and 'proccode' in self.mutation:
            name = replace_markers(self.mutation['proccode'])
        return Translator().translateOpcode(name)

    def _decode_inputs_ir(self, blocksAST: dict) -> list[IR]:
        """Decode the inputs dict into a list of IR nodes.
        Skips SUBSTACK/SUBSTACK2 (those are handled by C-mouth blocks)."""
        params = []
        for name, arr in self.inputs.items():
            if name in ('SUBSTACK', 'SUBSTACK2'):
                continue
            params.append(self._decode_input_array_ir(arr, blocksAST))
        return params

    def _decode_fields_ir(self, blocksAST: dict) -> list[IR]:
        """Decode the fields dict into a list of IR nodes."""
        result = []
        for name, val in self.fields.items():
            if name == "VARIABLE":
                result.append(IRVariable(name=val[0]))
            elif name == "LIST":
                result.append(IRList(name=val[0]))
            elif name in ("BROADCAST_OPTION", "STYLE", "KEY_OPTION",
                          "EFFECT", "FRONT_BACK", "FORWARD_BACKWARD",
                          "BACKDROP"):
                result.append(IRDropdown(value=val[0]))
            else:
                result.append(IRDropdown(value=val[0]))
        return result

    def _decode_input_array_ir(self, arr: list, blocksAST: dict) -> IR:
        """Decode a single input array entry [shadow_type, value_or_id, ...]."""
        if arr[0] == 1:
            # Shadow block present (simple constant or menu)
            return self._decode_input_value_ir(arr[1], blocksAST)
        elif arr[0] == 2:
            # No shadow - actual reporter block plugged in
            return self._decode_input_value_ir(arr[1], blocksAST)
        elif arr[0] == 3:
            # Shadow exists but obscured by reporter - use the reporter
            return self._decode_input_value_ir(arr[1], blocksAST)
        return IRValue(value=str(arr), kind="unknown")

    def _decode_input_value_ir(self, val, blocksAST: dict) -> IR:
        """Decode a single input value - either a block ID (str) or literal array."""
        if isinstance(val, str):
            # Block ID - look up the shadow/reporter block
            shadow = blocksAST[val]
            return shadow.shadow_to_ir(blocksAST)
        if isinstance(val, list):
            # Literal value array [type_id, value, ...]
            type_id = val[0]
            value = val[1] if len(val) > 1 else ""
            if type_id in (4, 5, 6, 7, 8):
                return IRValue(value=str(value), kind="number")
            elif type_id == 9:
                return IRValue(value=str(value), kind="color")
            elif type_id == 10:
                return IRValue(value=str(value), kind="string")
            elif type_id == 11:
                return IRValue(value=str(value), kind="broadcast")
            elif type_id == 12:
                return IRVariable(name=str(value))
            elif type_id == 13:
                return IRList(name=str(value))
            return IRValue(value=str(value), kind="unknown")
        if val is None:
            return IRValue(value="", kind="empty")
        return IRValue(value=str(val), kind="unknown")

    @staticmethod
    def convert_list_to_block(block):
        """Block stored as an array instead of a dict.
        This is for variables, lists and direct values like numbers, angles,
        strings, colors, broadcast messages."""
        opcode = "DATA_VARIABLE"
        x = None
        y = None
        if block[0] > 3 and block[0] < 9:
            # 4=number, 5=positive number, 6=positive integer, 7=integer, 8=angle
            pass
        elif block[0] == 9:
            # color
            pass
        elif block[0] == 10:
            # string
            pass
        elif block[0] == 11:
            # broadcast message
            pass
        elif block[0] == 12:
            # variable
            if len(block) > 3:
                x = block[3]
                y = block[4]
        elif block[0] == 13:
            # list
            opcode = "DATA_LISTCONTENTS"
            if len(block) > 3:
                x = block[3]
                y = block[4]

        return Block(opcode=opcode,
                     next=None,
                     parent=None,
                     inputs={},
                     fields={},
                     shadow=False,
                     topLevel=False,
                     x=x,
                     y=y,
                     mutation=None)

    @staticmethod
    def factory(block: dict):
        """Factory method: create the appropriate Block subclass based on opcode.
        Dispatches to specialized classes based on the category and opcode."""
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

                case "sound":
                    blk = SoundBlock(**paramdict)

                case "operators":
                    blk = OperatorBlock(**paramdict)

                case "sensing":
                    blk = SensingBlock(**paramdict)

                case "variable":
                    blk = VariableBlock(**paramdict)

                case "list":
                    blk = ListBlock(**paramdict)

                case "penExtension":
                    blk = PenBlock(**paramdict)

                case "my":
                    blk = MyBlock(**paramdict)

                case "event":
                    match opcode:
                        case "EVENT_BROADCAST" | "EVENT_BROADCASTANDWAIT":
                            blk = SimpleBlock(**paramdict)
                        case "EVENT_WHENKEYPRESSED" | "EVENT_WHENGREATERTHAN":
                            blk = EventBlock(**paramdict)
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
                        blk = ControlBlock(**paramdict)
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
    """A standard block with no C-mouth. Uses base to_ir() as-is."""
    pass


class SingleMouthBlock(Block):
    """A block with one C-mouth (repeat, forever, if, repeat_until)."""

    def to_ir(self, blocksAST: dict) -> IR:
        text = self._get_translated_text()
        inputs_ir = self._decode_inputs_ir(blocksAST)
        fields_ir = self._decode_fields_ir(blocksAST)
        all_params = [*fields_ir, *inputs_ir]

        # inputs entries are [shadow_type, value] arrays, so [1] is the block ID.
        # Default [None, None] prevents IndexError when SUBSTACK is absent (empty body).
        substack_id = self.inputs.get('SUBSTACK', [None, None])[1]
        if substack_id is not None:
            body = build_ir_script(blocksAST[substack_id], blocksAST)
        else:
            body = IRScript(blocks=[])

        return IRCMouth(opcode=self.opcode, category=self.color,
                        text=text, inputs=all_params, body=body)


class DoubleMouthBlock(Block):
    """A block with two C-mouths (if-else)."""

    def to_ir(self, blocksAST: dict) -> IR:
        text = self._get_translated_text()
        inputs_ir = self._decode_inputs_ir(blocksAST)
        fields_ir = self._decode_fields_ir(blocksAST)
        all_params = [*fields_ir, *inputs_ir]

        # inputs entries are [shadow_type, value] arrays, so [1] is the block ID.
        # Default [None, None] prevents IndexError when SUBSTACK is absent (empty body).
        substack1_id = self.inputs.get('SUBSTACK', [None, None])[1]
        if substack1_id is not None:
            body = build_ir_script(blocksAST[substack1_id], blocksAST)
        else:
            body = IRScript(blocks=[])

        substack2_id = self.inputs.get('SUBSTACK2', [None, None])[1]
        if substack2_id is not None:
            else_body = build_ir_script(blocksAST[substack2_id], blocksAST)
        else:
            else_body = IRScript(blocks=[])

        return IRCMouth(opcode=self.opcode, category=self.color,
                        text=text, inputs=all_params,
                        body=body, else_body=else_body)


class HatBlock(Block):
    """A top-level event block (rounded top, no block snaps above it)."""

    def to_ir(self, blocksAST: dict) -> IR:
        text = self._get_translated_text()
        inputs_ir = self._decode_inputs_ir(blocksAST)
        fields_ir = self._decode_fields_ir(blocksAST)
        all_params = [*fields_ir, *inputs_ir]

        # Special case: flag clicked event uses a green flag emoji as %1
        if self.opcode == "EVENT_WHENFLAGCLICKED":
            all_params.insert(0, IRValue(value="\U0001f3f3\ufe0f\u200d\U0001f7e9", kind="symbol"))

        return IRHatBlock(opcode=self.opcode, category=self.color,
                          text=text, inputs=all_params)


class TurnLeftRightBlock(SimpleBlock):
    """Motion turn block - inserts a unicode arrow as first parameter."""
    arrow: str

    def __init__(self, **kwargs):
        left = kwargs.pop('left', True)
        super().__init__(**kwargs)
        self.arrow = "\u27F2" if left else "\u27F3"

    def to_ir(self, blocksAST: dict) -> IR:
        text = self._get_translated_text()
        inputs_ir = self._decode_inputs_ir(blocksAST)
        fields_ir = self._decode_fields_ir(blocksAST)
        # Insert arrow as first parameter, shift others to %2, %3, ...
        all_params = [IRValue(value=self.arrow, kind="symbol"), *fields_ir, *inputs_ir]

        return IRBlock(opcode=self.opcode, category=self.color,
                       text=text, inputs=all_params, fields=[])


class VariableBlock(Block):
    """A variable reporter block."""

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        for name, val in self.fields.items():
            if name == "VARIABLE":
                return IRVariable(name=val[0])
        return IRVariable(name=self.opcode)


class ListBlock(Block):
    """A list block. Handles list reporter blocks when used as shadows,
    and translates the LIST field to IRList for proper rendering.
    List blocks have their LIST field as the LAST placeholder (%2, %3)
    while inputs (INDEX, ITEM) come first."""

    def _decode_fields_ir(self, blocksAST: dict) -> list[IR]:
        """LIST field becomes IRList, other fields pass through."""
        result = []
        for name, val in self.fields.items():
            if name == "LIST":
                result.append(IRList(name=val[0]))
            else:
                result.append(IRDropdown(value=val[0]))
        return result

    def to_ir(self, blocksAST: dict) -> IR:
        """Override to put inputs BEFORE fields - list blocks use
        'verb %1 of %2' where %1 is the input and %2 is the LIST field."""
        text = self._get_translated_text()
        inputs_ir = self._decode_inputs_ir(blocksAST)
        fields_ir = self._decode_fields_ir(blocksAST)
        # Inputs first, then fields (LIST name comes last in translation)
        all_params = [*inputs_ir, *fields_ir]
        return IRBlock(opcode=self.opcode, category=self.color,
                       text=text, inputs=all_params, fields=[])

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        """When used as a reporter in another block's input (e.g. length of list,
        item of list), produce an IROperator with the translated template."""
        reporter_opcodes = (
            "DATA_ITEMOFLIST", "DATA_LENGTHOFLIST",
            "DATA_ITEMNUMOFLIST", "DATA_LISTCONTAINSITEM",
        )
        if self.opcode in reporter_opcodes:
            text = Translator().translateOpcode(self.opcode)
            inputs_ir = self._decode_inputs_ir(blocksAST)
            fields_ir = self._decode_fields_ir(blocksAST)
            # Inputs first, then fields (LIST name comes last)
            operands = [*inputs_ir, *fields_ir]
            return IROperator(opcode=self.opcode, category=self.color,
                              text=text, operands=operands)
        # Plain list reference (variable-style reporter)
        for name, val in self.fields.items():
            if name == "LIST":
                return IRList(name=val[0])
        return IRList(name=self.opcode)


class MyBlock(Block):
    """Custom block (My Blocks) - procedures definition and call."""

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        """When used as shadow (PROCEDURES_PROTOTYPE), decode the proccode."""
        if self.opcode == "PROCEDURES_PROTOTYPE":
            result = self.mutation["proccode"]
            c = count(0)
            def replace_param(match):
                arg_name = json.loads(self.mutation["argumentnames"])[next(c)]
                return f"( {arg_name} )"
            return IRDropdown(value=re.sub(r'%[sb]', replace_param, result))
        # ARGUMENT_REPORTER_STRING_NUMBER / ARGUMENT_REPORTER_BOOLEAN
        if 'VALUE' in self.fields:
            return IRValue(value=self.fields['VALUE'][0], kind="argument")
        return IRDropdown(value=self.opcode)

    def to_ir(self, blocksAST: dict) -> IR:
        """PROCEDURES_DEFINITION uses the 'define %1' translation.
        PROCEDURES_CALL uses the proccode with %s/%b markers converted to
        positional placeholders and arguments decoded in argumentids order."""
        text = self._get_translated_text()
        inputs_ir = self._decode_inputs_ir(blocksAST)
        fields_ir = self._decode_fields_ir(blocksAST)
        all_params = [*fields_ir, *inputs_ir]

        # PROCEDURES_DEFINITION is a hat block (rounded top)
        if self.opcode == "PROCEDURES_DEFINITION":
            return IRHatBlock(opcode=self.opcode, category=self.color,
                              text=text, inputs=all_params)

        # PROCEDURES_CALL: proccode contains %s (string/number) and %b (boolean)
        # markers which we convert to %1, %2, ... for the renderer to fill in.
        if self.opcode == "PROCEDURES_CALL" and self.mutation:
            proccode = self.mutation["proccode"]
            arg_ids = json.loads(self.mutation["argumentids"])
            # Decode each argument input in the order specified by argumentids
            ordered_inputs = []
            for aid in arg_ids:
                if aid in self.inputs:
                    ordered_inputs.append(self._decode_input_array_ir(self.inputs[aid], blocksAST))
                else:
                    ordered_inputs.append(IRValue(value="?", kind="unknown"))
            text = replace_markers(proccode)
            return IRBlock(opcode=self.opcode, category=self.color,
                           text=text, inputs=ordered_inputs, fields=[])

        return IRBlock(opcode=self.opcode, category=self.color,
                       text=text, inputs=all_params, fields=[])


# Subclass imports at the bottom to avoid circular imports.
# These files define specialized shadow_to_ir() overrides per category.
from penblock import PenBlock
from motionblock import MotionBlock
from operatorblock import OperatorBlock
from looksblock import LooksBlock
from sensingblock import SensingBlock
from soundblock import SoundBlock
from controlblock import ControlBlock
from eventblock import EventBlock
