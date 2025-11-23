import argparse
import sys
import zipfile
import json
from doctest import debug_script
from logging import exception
from dataclasses import dataclass
from textwrap import indent
import re
from pprint import pprint


@dataclass(frozen=True)
class Monitor:
    id: str
    mode: str
    opcode: str
    params: dict
    value: str
    width: int
    height: int
    x: int
    y: int
    visible: bool
    sliderMin: int|None
    sliderMax: int|None
    isDiscrete: bool|None
    def dumpInfo(self ):
        #pprint(self, indent=2)
        print(self.opcode + ": " + self.params.get('LIST' if self.mode=="list" else 'VARIABLE',"?") )
        match self.mode:
            case "default":
                print(f"Value: {self.value}")
            case "large":
                print(f"Value: {self.value}")
            case "list":
                print(f"List: {self.value}")
            case "slider":
                print(f"Slider: {self.value}")
                print(f"   Min: {self.sliderMin}  Max: {self.sliderMax}  Discrete: {self.isDiscrete}")
        print(f"Visible: {self.visible} \n")

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
                outputBlocks(block, 0, self.blocksAST, args)


@dataclass
class Block:
    """Block class to store the scratch block information"""
    opcode: str  # English text describing the block
    next: str  # Next block
    parent: str  # Parent block
    inputs: dict  # Input fields but also points to substacks in case of if-then-else blocks
    fields: dict  # Field values
    shadow: bool  # Shadow block
    topLevel: bool  # is this a top level block
    x: int  # X coordinate
    y: int  # Y coordinate

def list2block(block):
    """ block store as an array instead of a dict.
    This is for variables,list and direct values like numbers,angles,strings,colors,..."""
    print(f"list2block {block}")
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
        x = None
        y = None
        if len(block) > 3:
            x = block[3]
            y = block[4]
        print(f"variable:  '{val}' id:{id}")
    elif block[0] == 13:
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


translate = {}
opcodetranslate = {}
data = {}


def read_translation_files(args: dict):
    #read the translation files
    global translate
    global opcodetranslate

    with open(f"{args.language}.json") as f:
        translate = json.load(f)
    #some of the opcodes have a different key in the i10n files
    #so we have this extra json
    with open("opcode.json") as f:
        opcodetranslate = json.load(f)


# Function to replace %digit with corresponding value used to resolve the translation string
def replace_placeholders(text, values):
    try:
        re.sub(r'%(\d+)', lambda m: "(" + str(values[int(m.group(1)) - 1]) + ")", text)
    except IndexError:
        print("Error: Not enough values for placeholders in translation string")

    return re.sub(r'%(\d+)', lambda m: "(" + str(values[int(m.group(1)) - 1]) + ")", text)


def decodeBlocksField(input: dict, blocksAST: dict):
    fields = []
    for name, val in input.items():
        fields.append(val[0])
    return fields


def decocodeInputArray(arr, blocksAST: dict):
    if isinstance(arr, str):
        #this is a shadow block, so the string is the block name
        shad = blocksAST[arr]
        #quick hack to get fields
        n = ""
        for fname, fval in shad.fields.items():
            n += fval[0]
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


def decodeBlocksInput(input: dict, blocksAST: dict):
    stack1 = None
    stack2 = None
    params = []
    for name, arr in input.items():
        if name == 'SUBSTACK':
            stack1 = arr[1]
        elif name == 'SUBSTACK2':
            stack2 = arr[1]
        else:
            if arr[0] == 1:  # input is a shadow
                (numid, val, id) = decocodeInputArray(arr[1], blocksAST)
            elif arr[0] == 2:  # there is no shadow
                (numid, val, id) = decocodeInputArray(arr[1], blocksAST)
            elif arr[0] == 3:  # there is a shadow but obscured by the input
                (numid, val, id) = decocodeInputArray(arr[1], blocksAST)
            params.append(val)
    return (stack1, stack2, params)


def translateOpcode(opcode):
    """Translate the block opcode to the selected language as human readable string"""
    global translate
    global opcodetranslate
    if opcode in translate:
        return translate[opcode]
    elif opcode in opcodetranslate:
        return translateOpcode(opcodetranslate[opcode])
    return opcode


def outputBlocks(block: Block, ident: int, blocksAST: dict, args: argparse.Namespace):
    while block != None:
        # First the translated text for this opcode
        description = " " * ident
        name = block.opcode.upper()
        # And for translation purposes there is already a special case...
        if name == "CONTROL_IF_ELSE":
            name = "CONTROL_IF"

        description += translateOpcode(name)

        # These are the fields and inputs for this block
        substack1 = None
        substack2 = None
        fields = []
        inputs = []

        # decode the fields if any are specified
        if len(block.fields) > 0:
            fields = decodeBlocksField(block.fields, blocksAST)

        # decode the inputs if any are specified
        if len(block.inputs) > 0:
            (substack1, substack2, inputs) = decodeBlocksInput(block.inputs, blocksAST)
            #Quick fix for some translations
            if block.opcode.upper() == "MOTION_TURNLEFT":
                inputs.insert(0, translateOpcode("left"))
            elif block.opcode.upper() == "MOTION_TURNRIGHT":
                inputs.insert(0, translateOpcode("right"))
        #Quick fix flag clicked translation
        if block.opcode.upper() == "EVENT_WHENFLAGCLICKED":
            inputs.insert(0, translateOpcode("green flag"))

        #combine the fields and inputs and update the description with the placeholders
        inputs = [*fields, *inputs]
        if len(inputs) > 0:
            description = replace_placeholders(description, inputs)

        #print the final translated description
        print(description)

        # Check if there is a first C-mouth (while,loop,if-then)
        if substack1 is not None:
            outputBlocks(blocksAST[substack1], ident + 4, blocksAST, args)
        # Check if there is a second C-mouth (if-then-else)
        if substack2 is not None:
            print(" " * ident + translateOpcode("CONTROL_ELSE"))
            outputBlocks(blocksAST[substack2], ident + 4, blocksAST, args)

        block = blocksAST[block.next] if block.next != None else None


def parse_cli_arguments():
    parser = argparse.ArgumentParser(
        description="Scratch sb3 parser to provide a text or latex representation of the code blocks in the SB3 file")
    parser.add_argument('sb3file',
                        help="The sb3 scratch file to parse")
    parser.add_argument('outfile', nargs='?',
                        help="Outputfile, otherwise stdout is used")
    parser.add_argument("-v", "--verbosity", action="count", default=0,
                        help="Increase verbosity while parsing")
    parser.add_argument("-f", "--format", choices=["text", "latex"],
                        help="Outputformat to use")
    parser.add_argument("-l", "--language", default="en",
                        help="Language used to show blocks\nTry to use the environments langue if not selected")
    parser.add_argument("-s", "--sprite", action="append",
                        help="Select individual sprite to show, otherwise all sprites are shown\nMultiple -s can be specified")
    parser.add_argument("-b", "--hatblocksonly", action="store_true",
                        help="Only show programs starting with a hatblock")

    args = parser.parse_args()
    return args


def get_json_info(filename):
    """Extract and parse the project.json file from the sb3 archive"""
    with zipfile.ZipFile(filename) as archive:
        with archive.open("project.json") as file:
            data = json.loads(file.read())
            return data


def buildAST(blocks, args):
    """Builds a the list of scratch blocks.
    They are stored in a dictionary with the block name as key, but using
    the next,inputs and fields pointers the are in effect an Abstract Syntax Tree (AST)

    Note that sometimes blocks are not dicts but lists"""
    blocksAST = {}
    for name, block in blocks.items():
        print(f"Building AST for block {name} {block}")
        if isinstance(block, dict):
            blocksAST[name] = Block(block['opcode'],
                                block['next'],
                                block['parent'],
                                block['inputs'],
                                block['fields'],
                                block['shadow'],
                                block['topLevel'],
                                block.get('x'),
                                block.get('y'))
        elif isinstance(block, list):
            #blocksAST[name] = None
            list2block(block)

    return blocksAST


def create_monitor(monitor: dict, args):
    return Monitor(monitor['id'],
                   monitor['mode'],
                   monitor['opcode'],
                   monitor['params'],
                   monitor['value'],
                   monitor['width'],
                   monitor['height'],
                   monitor['x'],
                   monitor['y'],
                   monitor['visible'],
                   monitor.get('sliderMin',None),
                   monitor.get('sliderMax',None),
                   monitor.get('isDiscrete',None)
                   )


def create_sprite(target, args):
    sprite = Sprite(target['isStage'],
                    target['name'],
                    target['variables'],
                    target['lists'],
                    target['broadcasts'],
                    {},  # blocks
                    {},  # comments
                    target['currentCostume'],
                    target['costumes'],
                    target['sounds'],
                    target['layerOrder'],
                    target['volume']
                    )

    """get the codeblocks from this sprite and print them out"""
    #print(json.dumps(target['blocks'], indent=2))
    sprite.blocksAST = buildAST(target['blocks'], args)
    return sprite

def print_boxed(title: str):
    print("+-" + "-" * len(title) + "-+")
    print(f"| {title} |")
    print("+-" + "-" * len(title) + "-+")

def print_underlined(title: str):
    print(f"\n\n {title} ")
    print("=" * max (20, 2 + len(title)) )



def main(args):
    global data
    try:
        data = get_json_info(args.sb3file)
    except Exception as e:
        print(e)
        sys.exit(1)

    print_boxed("Monitors")
    for monitor in data['monitors']:
        monitor_object = create_monitor(monitor, args)
        monitor_object.dumpInfo()

    print_boxed("Targets")
    for target in data['targets']:
        if not args.sprite or target['name'] in args.sprite:
            print_underlined(target['name'])
            sprite_object = create_sprite(target, args)
            sprite_object.dumpBlocks(args)

    print_boxed("Metadata")
    for target in data['meta']:
        print(f"{target:>7}: {data['meta'][target]}")

    if args.verbosity:
        print("\n\n")
        print_underlined("Dump of project.json")
        print(json.dumps(data, indent=2))


if __name__ == '__main__':
    args = parse_cli_arguments()
    read_translation_files(args)
    main(args)
