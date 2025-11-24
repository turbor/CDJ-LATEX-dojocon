from dataclasses import dataclass


@dataclass
class Block:
    """Block class to store the scratch block information"""
    opcode: str  # English text describing the block
    next: str  # Next block
    parent: str  # Parent block
    inputs: dict  # Input fields but also points to substacks in case of if-then-else blocks
    fields: dict  # Field values
    shadow: bool  # Shadow block
    topLevel: bool  # is this a top level block
    x: int  # X coordinate
    y: int  # Y coordinate

    @staticmethod
    def convert_list_to_block(block):
        """ block store as an array instead of a dict.
        This is for variables,list and direct values like numbers,angles,strings,colors,..."""
        print(f"convert_list_to_block {block}")
        opcode="data_variable" # most cases are single value variables
        x = None
        y = None
        if block[0] >3 and block[0] <9:
            #4=number,5=positive number,6=positive integer,7=integer,8=angle
            val = block[1]
            print(f"const:  {val}")
        elif block[0] == 9:
            #9=color
            val = block[1]
            print(f"color:  {val}")
        elif block[0] == 10:
            #string
            val = block[1]
            print(f"string:  {val}")
        elif block[0] == 11:
            #Broadcast message
            val = block[1]
            print(f"broadcast:  {val}")
        elif block[0] == 12:
            #variable
            val = block[1]
            id = block[2]
            if len(block) > 3:
                x = block[3]
                y = block[4]
            print(f"variable:  '{val}' id:{id}")
        elif block[0] == 13:
            opcode="data_listcontents"
            val = block[1]
            id = block[2]
            x = None
            y = None
            if len(block) > 3:
                x = block[3]
                y = block[4]
            print(f"list:  '{val}' id:{id}")
        else:
            print(f"unknown listblock {block}")
        return Block(opcode,
              "", #block['next']
              "", #block['parent']
              {}, #block['inputs'],
              {}, #block['fields'],
              False, #block['shadow'],
              False, #block['topLevel'],
              x,
              y)
