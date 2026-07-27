# sb3docbuilder

Parse Scratch `.sb3` files and produce text or LaTeX representations of the code blocks.

## Purpose

This program extracts the block programs from a Scratch 3 project file and renders them in a human-readable format. It supports multiple output formats including compilable LaTeX that draws Scratch-style blocks using the [scratch3](https://ctan.org/pkg/scratch3) package.

Blocks are displayed in the language of your choice, using the official [scratch-l10n](https://github.com/scratchfoundation/scratch-l10n) translation files.

## Origin

This tool was born from a collaboration between Benoit de Bioley (who demonstrated drawing Scratch blocks in LaTeX) and David Heremans, after participants at a CoderDojo presentation expressed the need to extract block info directly from sb3 files rather than retyping them manually.

## Requirements

- Python 3.10+ (uses match/case syntax)
- inkscape (optional, for converting SVG sprite costumes to PNG in LaTeX mode)

## Installation

```
git clone <this-repo>
cd CDJ-LATEX-dojocon
```

No dependencies beyond the Python standard library. The `scratch-l10n` translation files are included in the repository.

## Usage

```
python3 sb3docbuilder.py [options] <file.sb3>
```

### Options

| Flag | Description |
|------|-------------|
| `-f FORMAT` | Output format: `plain`, `ansi` (default), `nerdfont`, `latex` |
| `-l LANG` | Language for block text (default: `en`). E.g. `nl`, `fr`, `de` |
| `-s SPRITE` | Show only this sprite (repeatable for multiple sprites) |
| `-t FILE` | JSON file with variable/list name translations (see below) |
| `-b` | Only show scripts starting with a hat block |
| `-o DIR` | Output directory for LaTeX mode (creates `DIR/<name>.tex` + `DIR/sprites/`) |
| `-v` | Increase verbosity (`-v`: file list, `-vv`: AST, `-vvv`: full JSON) |

### Examples

```bash
# Terminal output with colors (default)
python3 sb3docbuilder.py project.sb3

# Plain ASCII, Dutch language
python3 sb3docbuilder.py -f plain -l nl project.sb3

# LaTeX output with sprite images
python3 sb3docbuilder.py -f latex -o output/ project.sb3
cd output && pdflatex project.tex

# Only hat-block scripts from a specific sprite
python3 sb3docbuilder.py -b -s Sprite1 project.sb3

# Nerd Font enhanced output (requires FiraCode Nerd Font or similar)
python3 sb3docbuilder.py -f nerdfont project.sb3

# Translate variable names to French
python3 sb3docbuilder.py -l fr -t examples/robocup-simpel-vars.json robocup-simpel.sb3
```

## Output Formats

| Format | Description |
|--------|-------------|
| `plain` | ASCII text, no colors. Suitable for piping or plain text files |
| `ansi` | Colored terminal output with category-colored blocks |
| `nerdfont` | Enhanced colored output using Powerline glyphs for block shapes |
| `latex` | Compilable LaTeX using the scratch3 package (v0.19) |

### LaTeX output

The LaTeX renderer produces a self-contained document using the `scratch3` CTAN package. It handles:

- All block categories with correct `\blockmove`, `\blocklook`, etc. commands
- Loops (`\blockrepeat`, `\blockinfloop`), conditionals (`\blockif`, `\blockifelse`)
- Hat blocks (`\blockinit`), stop blocks (`\blockstop`)
- Operators (`\booloperator`, `\ovaloperator`), variables, lists, dropdowns
- Color swatches via `\definecolor` + `\pencolor`
- Sprite costume images in the top-right corner (requires inkscape for SVG conversion)

## Translating Variable and List Names

The `-l` flag translates Scratch block text (move, repeat, if-then, etc.) but not user-created variable and list names. The `-t` flag provides a JSON file that maps variable/list names to translated equivalents.

This is useful when sharing projects across language groups: a Dutch project with variables like `snelheid` and `richting` can be rendered in French as `vitesse` and `direction`.

### Translation file format

```json
{
  "snelheid": {"fr": "vitesse", "en": "speed", "de": "Geschwindigkeit"},
  "stappenplan": {"fr": "plan d'action", "en": "step plan"},
  "Sprite1.snelheid": {"fr": "vitesse joueur 1"}
}
```

Each key is a variable or list name. The value is a dict mapping language codes to translations. The `-l` flag selects which language to use.

### Sprite-specific overrides

When the same variable name means different things in different sprites, use `SpriteName.varname` as the key. This takes priority over the generic entry:

```json
{
  "sentir": {"nl": "voelen"},
  "Hond.sentir": {"nl": "ruiken"}
}
```

In this example, `sentir` renders as "ruiken" for the Hond sprite but "voelen" everywhere else.

### What gets translated

- Variable blocks (`{ varname }` in output)
- List blocks (`[ listname ]` in output)
- Variable references in "property of sprite" dropdowns
- Local variable listings per sprite

### Example file

See `examples/robocup-simpel-vars.json` for a working example with per-sprite overrides.

## Architecture

Two-phase pipeline:

```
sb3 zip -> project.json -> Block.factory() -> AST -> to_ir() -> IR -> Renderer -> output
```

1. **Phase 1 (AST -> IR):** Each block's `to_ir()` method produces semantic IR nodes (no formatting)
2. **Phase 2 (IR -> Output):** A Renderer subclass walks the IR tree and produces formatted output

### Project structure

```
sb3docbuilder.py       Entry point, CLI, orchestration
block.py               Core Block dataclass, factory, base IR conversion
scratch3.py            Opcode registry (categories, colors)
ir.py                  IR node dataclasses (IRScript, IRBlock, IRCMouth, ...)
sprite.py              Sprite dataclass, builds IR scripts from AST
translator.py          Singleton l10n loader
extensionblock.py      ExtensionBlock base + all extension subclasses
motionblock.py         MotionBlock (menu shadows, rotation style)
looksblock.py          LooksBlock (costume/backdrop, effects)
operatorblock.py       OperatorBlock (math/logic/string reporters)
sensingblock.py        SensingBlock (sensing reporters, menus)
soundblock.py          SoundBlock (effect field translation)
controlblock.py        ControlBlock (stop/clone options)
eventblock.py          EventBlock (key/loudness fields)
monitor.py             Monitor dataclass
dumpAst.py             Debug AST tree printer

renderers/
    __init__.py        Package exports
    base.py            Renderer ABC
    plain.py           PlainRenderer
    ansi.py            AnsiRenderer
    nerdfont.py        NerdFontRenderer
    latex.py           LatexRenderer
```

## References

- https://en.scratch-wiki.info/wiki/Scratch_File_Format
- https://en.scratch-wiki.info/wiki/Scratch_File_Format#Blocks
- https://en.scratch-wiki.info/wiki/List_of_Block_Opcodes
- https://github.com/scratchfoundation/scratch-l10n/tree/master/editor/blocks
- https://ctan.org/pkg/scratch3
