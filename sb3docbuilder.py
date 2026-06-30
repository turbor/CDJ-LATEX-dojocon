import argparse
import os
import re
import subprocess
import sys
import textwrap
import zipfile
import json
from block import  Block
from sprite import Sprite
from monitor import Monitor
from translator import Translator
from dumpAst import dumpAst
from ir import build_ir_script
from renderer import PlainRenderer, AnsiRenderer, LatexRenderer, NerdFontRenderer

data = {}

def check_python_version():
    """
    This program uses the match-case construct available since python 3.10
    So check if we meet this minimum requirement.
    """
    if sys.version_info.major < 3 and sys.version_info.minor < 10:
        print("This program requires Python 3.10 or higher")
        sys.exit(1)


def get_renderer(format_name: str):
    """Return the appropriate renderer for the chosen output format."""
    match format_name:
        case "plain":
            return PlainRenderer()
        case "ansi":
            return AnsiRenderer()
        case "nerdfont":
            return NerdFontRenderer()
        case "latex":
            return LatexRenderer()
        case _:
            raise ValueError(f"Unknown output format: '{format_name}'. Expected 'plain', 'ansi', 'nerdfont', or 'latex'.")


def parse_cli_arguments():
    """
    Check the command line arguments
    """
    parser = argparse.ArgumentParser(
        description = textwrap.dedent("""\
        Parse a Scratch .sb3 file and produce a text or LaTeX representation
        of the code blocks.

        Blocks are displayed in the language selected with -l, using the
        scratch-l10n translation files.
        """),formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""\
        output formats:
          plain     ASCII text, no colors
          ansi      colored terminal output (default)
          nerdfont  colored output with Nerd Font glyphs (requires FiraCode or similar)
          latex     compilable LaTeX using the scratch3 package (use with -o)

        examples:
          %(prog)s project.sb3
          %(prog)s -f plain -l nl project.sb3
          %(prog)s -f latex -o output/ project.sb3
          %(prog)s -s Sprite1 -s Sprite2 project.sb3
        """))
    parser.add_argument('sb3file',
                        help="the .sb3 scratch file to parse")
    parser.add_argument("-f", "--format", choices=["plain", "ansi", "nerdfont", "latex"],
                        default="ansi",
                        help="output format (default: ansi)")
    parser.add_argument("-l", "--language", default="en",
                        help="language for block text, e.g. en, nl, fr (default: en)")
    parser.add_argument("-s", "--sprite", action="append",
                        help="show only this sprite (repeatable)")
    parser.add_argument("-o", "--output", default=None,
                        help="output directory for latex mode\ncreates <dir>/<name>.tex + <dir>/sprites/")
    parser.add_argument("-b", "--hatblocksonly", action="store_true",
                        help="only show scripts starting with a hat block")
    parser.add_argument("-v", "--verbosity", action="count", default=0,
                        help="increase verbosity (-v: file list, -vv: AST, -vvv: json)")

    args = parser.parse_args()
    return args

def show_sb3_files(sb3_file: str):
    with zipfile.ZipFile(sb3_file) as archive:
        maxLength=10
        for info in archive.filelist:
            maxLength=max(maxLength,len(info.filename))
        for info in archive.filelist:
            print(f"{info.filename:>{maxLength}} : {info.file_size}")

def get_json_info(filename: str):
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
    if args.verbosity > 1:
        dumpAst(sprite.blocksAST)
    return sprite


def extract_costumes(sb3_file: str, target: dict, output_dir: str) -> list[str]:
    """Extract all costumes for a sprite/stage from the sb3 archive.
    SVG files are converted to PNG using inkscape.
    Returns list of output PNG file paths."""
    os.makedirs(output_dir, exist_ok=True)
    sprite_name = target['name']
    safe_name = re.sub(r'[^\w\-]', '_', sprite_name)
    png_paths = []

    with zipfile.ZipFile(sb3_file) as archive:
        for idx, costume in enumerate(target['costumes']):
            md5ext = costume['md5ext']
            data_format = costume['dataFormat']
            out_base = f"{safe_name}_{idx + 1}"

            if data_format == 'png':
                out_path = os.path.join(output_dir, f"{out_base}.png")
                with archive.open(md5ext) as src, open(out_path, 'wb') as dst:
                    dst.write(src.read())
            elif data_format == 'svg':
                svg_path = os.path.join(output_dir, f"{out_base}.svg")
                out_path = os.path.join(output_dir, f"{out_base}.png")
                with archive.open(md5ext) as src, open(svg_path, 'wb') as dst:
                    dst.write(src.read())
                # Convert SVG to PNG using inkscape
                subprocess.run(
                    ['inkscape', svg_path,
                     '--export-type=png',
                     '--export-filename=' + out_path,
                     '--export-height=200'],
                    capture_output=True
                )
                os.remove(svg_path)
            else:
                continue
            png_paths.append(out_path)

    return png_paths


def main(args):
    global data

    renderer = get_renderer(args.format)

    # If -o is specified, set up output directory and redirect stdout to .tex file
    output_file = None
    if args.output and args.format == "latex":
        os.makedirs(args.output, exist_ok=True)
        tex_name = os.path.splitext(os.path.basename(args.sb3file))[0] + ".tex"
        tex_path = os.path.join(args.output, tex_name)
        output_file = open(tex_path, 'w', encoding='utf-8')
        sys.stdout = output_file

    # LaTeX: configure and emit document preamble
    if hasattr(renderer, 'render_preamble'):
        # The scratch3 LaTeX package defaults "else word" to "sinon" (French)
        # because the package author is francophone. Override to match our language.
        renderer.set_else_word(Translator().translateOpcode("CONTROL_ELSE"))
        print(renderer.render_preamble())

    # To help debugging we can dump the content of the sb3 archive
    if args.verbosity > 0:
        try:
            renderer.print_underlined(f"files in {args.sb3file}")
            show_sb3_files(args.sb3file)
        except Exception as e:
            # Something went wrong so quit.
            print(e)
            sys.exit(1)

    try:
        # Read the json from the sb3 file specified
        data = get_json_info(args.sb3file)
    except Exception as e:
        # Something went wrong so quit.
        print(e)
        sys.exit(1)

    # To help debugging we can dump the entire project.json
    if args.verbosity > 2:
            print("\n\n")
            renderer.print_underlined("Dump of project.json")
            print(json.dumps(data, indent=2))
            print("\n\n")

    # If we did not ask for a specific sprite we print the extra info present in the json.
    if not args.sprite and args.format != "latex":
        # Show the list of extensions used in this projects
        renderer.print_boxed("Extensions used")
        if len(data['extensions']) == 0:
            print("No extra extensions used.")
        else:
            for ext in data['extensions']:
                print(f"* {ext}")
        print()

        # Show the monitors/variables used in this projects
        renderer.print_boxed("Monitors")
        for monitor in data['monitors']:
            monitor_object = create_monitor(monitor, args)
            monitor_object.dumpInfo()

        renderer.print_boxed("Targets")

    # Now render the codeblocks for the sprites specified on the command line
    # if none specified print all sprites
    for target in data['targets']:
        if not args.sprite or target['name'] in args.sprite:
            renderer.print_underlined(target['name'])

            # Extract costumes and show first one in LaTeX output
            if args.format == "latex":
                # Place sprites subdir relative to the output directory
                if args.output:
                    sprites_dir = os.path.join(args.output, "sprites")
                else:
                    sprites_dir = "sprites"
                costume_paths = extract_costumes(args.sb3file, target, sprites_dir)
                if costume_paths:
                    # Use relative path so the .tex + sprites/ dir are portable together
                    if args.output:
                        rel_path = os.path.relpath(costume_paths[0], args.output)
                    else:
                        rel_path = os.path.abspath(costume_paths[0])
                    renderer.render_sprite_image(rel_path)

            sprite_object = create_sprite(target, args)
            # Phase 1: build intermediate representation from AST
            ir_scripts = sprite_object.build_ir_scripts(args)
            # Phase 2: render IR to chosen output format
            for ir_script in ir_scripts:
                print()
                renderer.render_script(ir_script, depth=0)

    # The final metadata in the project
    if not args.sprite and args.format != "latex":
        renderer.print_boxed("Metadata")
        for target in data['meta']:
            print(f"{target:>7}: {data['meta'][target]}")

    # LaTeX: emit document postamble
    if hasattr(renderer, 'render_postamble'):
        print(renderer.render_postamble())

    # Restore stdout and close output file if we redirected
    if output_file:
        sys.stdout = sys.__stdout__
        output_file.close()
        tex_name = os.path.splitext(os.path.basename(args.sb3file))[0] + ".tex"
        print(f"Written to {os.path.join(args.output, tex_name)}", file=sys.stderr)



if __name__ == '__main__':
    check_python_version()
    args = parse_cli_arguments()
    Translator().read_translation_files(args)
    main(args)
