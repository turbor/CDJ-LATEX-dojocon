import re

class Color:
    """A heplper class mainly used to help with the anssi colorcodes when printing the blocks"""

    # Some class variables to print some default
    reset='\033[0m'
    bold='\033[1m'
    underline='\033[4m'
    bluebg='\033[97;44m'
    fg_white='\033[97m'

    # A dictionary with the color names used in the scratch wiki for the blocks
    # It contains the colorcode and the color for a contrasting text

    colorvals={
            "blueberry":[15,75],  # Name : [textcolor, bgcolor]
            "lightviolet": [15,141],
            "magenta": [15,176],
            "amber":[15,220],
            "brightyellow": [15,214],
            "moderateblue": [15,110],
            "coolgreen": [15,114],
            "mango":[0,215],
            "orange":[0,202],
            "hotpink":[0,211],
            "limegreen":[0,43],
            "white": [0,15]
        }

    @staticmethod
    def contrastletters():
        """
        Calculate the optimal text color to contrast against the background
        """
        for key,name in Color.colorvals.items():
            fg,bg= name
            cl = int(bg)-16
            r,g,b = cl//36,(cl//6)%6,cl%6
            fg = 16 if (r*r+g*g+b*b)>36 else 231
            Color.colorvals[key]=[fg,bg]


    @staticmethod
    def color(text,val="fb"):
        """
        Get the ansicode for the given color.
        By default the ansii code for both text/foreground color and background color is returned
        However you can ask for only setting the foreground or background color,
        """
        if not text=="" and not text in Color.colorvals:
            print("Colorize unknown color:",text)
            sys.exit(1)

        fg,bg = Color.colorvals[text]
        match val:
            case "bf":
                colorval = f"\033[38;5;{bg};48;5;{fg}m"
            case "b":
                colorval = f"\033[48;5;{bg}m"
            case _:
                colorval=f"\033[38;5;{fg};48;5;{bg}m"
        return colorval # + text + '\033[0m'
