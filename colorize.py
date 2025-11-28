import re

class Colorize:
    reset='\033[0m'
    bold='\033[1m'
    underline='\033[4m'

    colorvals={
            "blueberry":"\033[38;5;15;48;5;75m",
            "lightviolet": "\033[38;5;15;48;5;141m",
            "magenta": "\033[38;5;15;48;5;176m",
            "amber":"\033[38;5;15;48;5;220m",
            "brightyellow": "\033[38;5;15;48;5;214m",
            "moderateblue": "\033[38;5;15;48;5;110m",
            "coolgreen": "\033[38;5;15;48;5;114m",
            "mango":"\033[38;5;0;48;5;215m",
            "orange":"\033[38;5;0;48;5;202m",
            "hotpink":"\033[38;5;0;48;5;211m",
            "limegreen":"\033[38;5;0;48;5;43m",
            "white": "\033[38;5;0;48;5;15m"
        }

    @staticmethod
    def contrastletters():
        for key,name in Colorize.colorvals.items():
            result=re.sub("38;5;(\d+);?","",name)
            cl = re.search("48;5;(\d+)",result).group(1)
            cl = int(cl)-16
            r,g,b = cl//36,(cl//6)%6,cl%6
            cl = 16 if (r*r+g*g+b*b)>36 else 231
            result = result.replace("[",f"[38;5;{cl};")
            Colorize.colorvals[key]=result


    @staticmethod
    def color(text):
        if not text=="" and not text in Colorize.colorvals:
            print("Colorize unknown color:",text)
            sys.exit(1)


        colorval=Colorize.colorvals.get(text,"\033[38;5;160;48;5;180m")
        return colorval # + text + '\033[0m'
