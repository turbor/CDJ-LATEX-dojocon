from dataclasses import dataclass

"""
Intermediate Representation (IR) for Scratch block programs.

The IR is the bridge between parsing (Phase 1) and rendering (Phase 2).
Phase 1 produces a tree of these nodes from the raw AST - no formatting decisions.
Phase 2 (renderers) walks this tree and produces formatted output.

This separation allows multiple output formats (plain, ANSI, LaTeX) without
duplicating the block-decoding logic.
"""


@dataclass
class IR:
    """Base for intermediate representation nodes"""
    pass


@dataclass
class IRScript(IR):
    blocks: list[IR]


@dataclass
class IRBlock(IR):
    opcode: str
    category: str  # "motion", "control", etc.
    text: str  # translated text with placeholders filled
    inputs: list[IR]  # resolved input values (nested IRs)
    fields: list[IR]


@dataclass
class IRCMouth(IR):
    """A block with one or two substacks (if/repeat/forever)"""
    opcode: str
    category: str
    text: str
    inputs: list[IR]
    body: IRScript
    else_body: IRScript | None = None


@dataclass
class IRValue(IR):
    """A literal value in a round input"""
    value: str
    kind: str  # "number", "string", "color", "angle"


@dataclass
class IRDropdown(IR):
    """A menu selection.
    When is_variable_ref is True, the value is a user-defined variable name
    shown in a dropdown (e.g. in 'property of sprite'). Renderers apply
    variable name translation (-t) to these while keeping dropdown styling.
    ref_sprite optionally specifies which sprite the variable belongs to,
    for correct sprite-specific translation lookups in 'property of' blocks.
    is_broadcast marks broadcast names, allowing 'broadcast.' prefix disambiguation
    when a variable and broadcast share the same name."""
    value: str  # translated display text
    is_variable_ref: bool = False
    ref_sprite: str = ""  # target sprite for translation context (empty = use current)
    is_broadcast: bool = False


@dataclass
class IRVariable(IR):
    name: str


@dataclass
class IRList(IR):
    name: str


@dataclass
class IROperator(IR):
    opcode: str
    category: str
    text: str  # e.g. "%1 + %2" with placeholders resolved
    operands: list[IR]


@dataclass
class IRHatBlock(IR):
    """A top-level event/hat block (when flag clicked, when key pressed, etc.)"""
    opcode: str
    category: str
    text: str
    inputs: list[IR]


@dataclass
class IRDefineHat(IR):
    """The 'define' hat block for a custom block (My Blocks / procedures_definition).
    Rendered differently from event hats: pink 'moreblocks' color, with the
    custom block name+parameters shown in a dented block shape (not a dropdown).
    prototype holds the custom block's name and argument placeholders."""
    category: str
    text: str          # the translated "define %1" template
    prototype: IR      # IRProcedurePrototype for the %1 placeholder


@dataclass
class IRProcedurePrototype(IR):
    """A custom block's name and argument shape, shown inside a define hat
    or as the label of the block being defined. Rendered as a dented block
    shape (\\namemoreblocks in LaTeX), not a dropdown."""
    text: str          # proccode with %s/%b converted, args shown as ( name )


def build_ir_script(block, blocksAST: dict) -> IRScript:
    """Walk a chain of blocks (following 'next' pointers) and return an IRScript.
    Each block's to_ir() method produces the appropriate IR node."""
    nodes = []
    while block is not None:
        nodes.append(block.to_ir(blocksAST))
        block = blocksAST[block.next] if block.next is not None else None
    return IRScript(blocks=nodes)
