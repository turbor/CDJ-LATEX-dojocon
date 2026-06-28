from dataclasses import dataclass

"""
This module defines a hierarchy of data structures for representing intermediate
representation (IR) nodes. These nodes are used for constructing, categorizing,
and managing various program components and their relationships.

The IR node classes include representations for scripts, blocks, values,
menu selections, variables, lists, and operators. They offer a framework to
process and resolve translated text, inputs, fields, and additional structural
information needed for IR functionality.

This allows for a two phase process
  Phase 1: Decode to an Intermediate Representation (IR)
    Walk the AST and produce a tree of semantic nodes - no formatting, no colors, no print calls.
  Phase 2: Render the IR
    A separate renderer walks the IR tree and produces output


Classes:
- IR: Base class for intermediate representation nodes.
- IRScript: Represents a script composed of a sequence of IR blocks.
- IRBlock: Represents a single block with specified attributes and nested IR structures.
- IRCMouth: Handles blocks with one or two substacks, such as control flow structures.
- IRValue: Represents a literal value.
- IRDropdown: Represents a menu selection item.
- IRVariable: Represents a program variable.
- IRList: Represents a program list.
- IROperator: Represents operations with operands and resolved expressions.
- IRHatBlock: Represents a top-level event/hat block.
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
    """A menu selection"""
    value: str  # translated display text


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


def build_ir_script(block, blocksAST: dict) -> IRScript:
    """Walk a chain of blocks (following 'next' pointers) and return an IRScript.
    Each block's to_ir() method produces the appropriate IR node."""
    nodes = []
    while block is not None:
        nodes.append(block.to_ir(blocksAST))
        block = blocksAST[block.next] if block.next is not None else None
    return IRScript(blocks=nodes)
