import sys
#from block import Block
from colorize import Color

class Deco:
    output="plain"

    def print_boxed(title: str):
        match Deco.output:
            case "ansi":
                print()
                print(Color.bluebg + " " * (4 + len(title)) + Color.reset)
                print(Color.bluebg + Color.underline + f"  {title}  " + Color.reset)
            case _:
                print("+-" + "-" * len(title) + "-+")
                print(f"| {title} |")
                print("+-" + "-" * len(title) + "-+")

    def print_underlined(title: str):
        match Deco.output:
            case "ansi":
                print(f"\n\n  " + Color.bold + Color.underline + f" {title} ")
                print(Color.reset)
            case _:
                print(f"\n\n {title} ")
                print("=" * max(20, 2 + len(title)))

    def indent(oldident:str, block):
        match Deco.output:
            case "plain":
                return f"{oldident}  | "
            case "ansi":
                return oldident + Color.color(block.color) + "   " + Color.reset + " "
            case "latex":
                return f"{oldident}    "
            case _:
                return f"unknown output decoration {ouput} for {item}"


    @staticmethod
    def rator(purpose:str, item: str, block):
        match Deco.output:
            case "plain":
                return Deco.plain(purpose,item,block)
            case "ansi":
                return Deco.ansi(purpose,item,block)
            case "latex":
                return Deco.latex(purpose,item,block)
            case _:
                return f"unknown output decoration {ouput} for {item}"

    @staticmethod
    def plain(purpose:str, item: str, block):
        match purpose:
            case "blok": #single block
                return f" {item} "
            case "(": # open input
                return f"( {item}"
            case "()": # open and close input
                return f"( {item} )"
            case ")": # close input
                return f"{item} )"
            case "<": #open operator
                return f"<{item}"
            case "<>": #open and close operator
                return f"<{item}>"
            case ">": #close operator
                return f"{item}>"
            case "list": #list name
                return f"[ {item} ]"
            case "var": #variable
                return '{ '+item+' }'
            case "|v|": #dropdownmenu
                return f"| {item} v|"
            case _:
                return f"unknown decoration {purpose} for {item}"

    @staticmethod
    def ansi(purpose:str, item: str, block):
        match purpose:
            case "blok":  # single block
                return Color.color(block.color) + f" {item} " + Color.reset
            case "(": # open input
                return f"( {item}"
            case "()": # open and close input
                return Color.fg_white + "\ue0b6" + Color.color(
                    "white") + f" {item} " + Color.color(block.color,"b") + Color.fg_white + "\ue0b4" + Color.color(block.color)
            case ")": # close input
                return f"{item} )"
            case "<": #open operator
                return f"<{item}"
            case "<>": #open and close operator
                #parentcolor=getParentColor(block)
                parentcolor="white"
                if parentcolor==block.color:
                    #green on green...
                    val=Color.color(block.color)+"\u2bc9"+item+"\u2b9e"
                else:
                    val=Color.color(block.color,"f")+ "\U0001f780" + Color.color(block.color) + \
                        '{ '+item+' }' + Color.color(block.color,"f") + \
                        Color.color(parentcolor,"b") + "\U0001f782" + Color.color(parentcolor)
                return f"<{item}>"
            case ">": #close operator
                return f"{item}>"
            case "list": #list name
                return f"[ {item} ]"
            case "var": #variable
                #parentcolor=getParentColor(block)
                parentcolor="white"
                return Color.color(block.color,"f")+ "\ue0b6" + Color.color(block.color) + \
                        '{ '+item+' }' + Color.color(block.color,"f") + \
                        Color.color(parentcolor,"b") + "\ue0b4" +Color.color(parentcolor)
            case "|v|": #dropdownmenu
                return f"| {item} v|"
            case _:
                return f"unknown decoration {purpose} for {item}"
    @staticmethod
    def latex(purpose:str, item: str, block):
        print(f"geen LaTeX output ge-implementeerd op dit moment")
        sys.exit(1)