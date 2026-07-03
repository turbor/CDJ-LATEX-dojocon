from dataclasses import dataclass
from block import Block
from ir import build_ir_script, IRScript, IRHatBlock

@dataclass
class Sprite:
    """The sprite class represents the scratch sprites and background stage."""
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
                if args.hatblocksonly and (not script.blocks or not isinstance(script.blocks[0], IRHatBlock)):
                    continue
                scripts.append(script)
        return scripts
