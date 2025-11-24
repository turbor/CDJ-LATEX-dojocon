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
from block import  Block
from sprite import Sprite
from monitor import Monitor
from translator import Translator




data = {}














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
            blocksAST[name] = Block.convert_list_to_block(block)

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

    print_boxed("Extensions used")
    if len(data['extensions']) == 0:
        print("No extra extensions used.")
    else:
        for ext in data['extensions']:
            print(f"* {ext}")
    print()

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
    Translator().read_translation_files(args)
    main(args)
