from block import Block

class Node:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, child):
        self.children.append(child)
        return child

def print_tree(node:Block, prefix=""):
    print(prefix + node.name)

    child_prefix = prefix.replace("└─ ", "   ").replace("├─ ", "│  ")

    for i, child in enumerate(node.children):
        if i == len(node.children) - 1:
            print_tree(child, child_prefix + "└─ ")
        else:
            print_tree(child, child_prefix + "├─ ")

def makeDumpAstTree(name:str,block:Block, ast:dict):
    root = Node(block.opcode)
    filtered = {nam: blk for nam, blk in ast.items() if blk.parent == name}

    #first shadow blocks
    for subname,subnode in filtered.items():
        if subnode.shadow:
            root.add(makeDumpAstTree(subname,subnode,ast) )
    # then non shadow ones
    for subname, subnode in filtered.items():
        if not subnode.shadow:
            root.add(makeDumpAstTree(subname, subnode, ast))

    return root

def dumpAst(ast: dict):
    for name, block in ast.items():
        if block.topLevel:
            print_tree(makeDumpAstTree(name, block, ast),"")
            print()