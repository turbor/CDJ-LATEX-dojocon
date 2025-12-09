import argparse
import sys
import textwrap
import zipfile
import json
from deco import Deco
from doctest import debug_script
from logging import exception
from dataclasses import dataclass
from textwrap import indent
import re
from pprint import pprint
from block import  Block
from colorize import Color
from sprite import Sprite
from monitor import Monitor
from translator import Translator
from dumpAst import dumpAst

data = {}

def check_python_version():
    """
    This program uses the match-case construct available since python 3.10
    So check if we meet this minimum requirement.
    """
    if sys.version_info.major < 3 and sys.version_info.minor < 10:
        print("This program requires Python 3.10 or higher")
        sys.exit(1)

def parse_cli_arguments():
    """
    Check the command line arguments
    """
    parser = argparse.ArgumentParser(
        description = textwrap.dedent("""\
        Scratch sb3 parser to provide a text or latex representation of the code blocks in the SB3 file.
        It uses the translation files of the scratch3 project to display he blocks in the correct language.
        
        Using an xterm with the FiraCode Nerd Font for the extra unicode chars is recommended.
        This program is a work in progress. 
        Please report bugs (preferably together with the sb3 file causing the error).
        
        """),formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('sb3file',
                        help="The sb3 scratch file to parse")
    parser.add_argument('outfile', nargs='?',
                        help="Outputfile, otherwise stdout is used")
    parser.add_argument("-v", "--verbosity", action="count", default=0,
                        help="Increase verbosity while parsing")
    parser.add_argument("-f", "--format", choices=["plain", "ansi", "latex"],
                        default="ansi",
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
        #print(f"Building AST for block {name} {block}")
        blocksAST[name] = Block.factory(block)

    return blocksAST


def create_monitor(monitor: dict, args):
    """
    From the project.json we build the list of monitors.
    These are the variable views you can have in your program execution window in scratch
    They are variables or list
    Variables can be represent as sliders so there are extra possible parameters for this.
    """
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
    """
    The project.json contains targets, being the sprites and the stage/background
    which can be programmed using blocks.
    """
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
    #debug info
    dumpAst(sprite.blocksAST)
    return sprite


def main(args):
    global data
    try:
        # Read the json from the sb3 file specified
        data = get_json_info(args.sb3file)
    except Exception as e:
        # Something went wrong so quit.
        print(e)
        sys.exit(1)

    # If we did not ask for a specific sprite we print a lot of the extra info present in the json.
    if not args.sprite:
        # Show the list of extensions used in this projects
        Deco.print_boxed("Extensions used")
        if len(data['extensions']) == 0:
            print("No extra extensions used.")
        else:
            for ext in data['extensions']:
                print(f"* {ext}")
        print()

        # Show the monitors/variables used in this projects
        Deco.print_boxed("Monitors")
        for monitor in data['monitors']:
            monitor_object = create_monitor(monitor, args)
            monitor_object.dumpInfo()

        Deco.print_boxed("Targets")

    # now print  the codeblocks for the sprites specified on the command line
    # if none specified print all sprites
    for target in data['targets']:
        if not args.sprite or target['name'] in args.sprite:
            Deco.print_underlined(target['name'])
            sprite_object = create_sprite(target, args)
            sprite_object.dumpBlocks(args)

    # The final metadata in the project
    if not args.sprite:
        Deco.print_boxed("Metadata")
        for target in data['meta']:
            print(f"{target:>7}: {data['meta'][target]}")

    # To help debugging we can dump the entire json
    if args.verbosity:
        print("\n\n")
        Deco.print_underlined("Dump of project.json")
        print(json.dumps(data, indent=2))


if __name__ == '__main__':
    check_python_version()
    Color.contrastletters()
    args = parse_cli_arguments()
    Deco.output=args.format
    Translator().read_translation_files(args)
    main(args)
