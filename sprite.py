from dataclasses import dataclass
from block import Block
from ir import build_ir_script, IRScript, IRHatBlock, IRDefineHat

@dataclass
class Sprite:
    """Represents a Scratch sprite or the stage.

    Each sprite owns its block AST (the programs attached to it) and metadata
    like costumes, sounds, and local variables. The stage is a special sprite
    with isStage=True whose variables are global to all sprites."""
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

    def build_ir_scripts(self, args) -> list[IRScript]:
        """Phase 1: Build intermediate representation for all top-level block chains.

        Returns a list of IRScript, one per top-level block (each script is
        a hat block followed by its chain of connected blocks).
        If args.hatblocksonly is set, only scripts starting with a hat block are returned.
        """
        scripts = []
        for name, block in self.blocksAST.items():
            if block.topLevel:
                script = build_ir_script(block, self.blocksAST)
                if args.hatblocksonly and (not script.blocks or not isinstance(script.blocks[0], (IRHatBlock, IRDefineHat))):
                    continue
                scripts.append(script)
        return scripts

    def get_local_variables(self) -> list[tuple[str, str]]:
        """Return list of (name, value) for this sprite's local variables.
        Only meaningful for non-Stage sprites (Stage variables are global)."""
        if self.isStage:
            return []
        return [(val[0], str(val[1])) for val in self.variables.values()]

    def get_local_lists(self) -> list[tuple[str, list]]:
        """Return list of (name, contents) for this sprite's local lists."""
        if self.isStage:
            return []
        return [(val[0], val[1]) for val in self.lists.values()]
