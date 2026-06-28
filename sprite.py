from dataclasses import dataclass
from block import Block
from ir import build_ir_script, IRScript

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
        """
        scripts = []
        for name, block in self.blocksAST.items():
            if block.topLevel:
                scripts.append(build_ir_script(block, self.blocksAST))
        return scripts
