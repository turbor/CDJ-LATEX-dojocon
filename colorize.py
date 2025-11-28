class Colorize:
    reset='\033[0m'
    bold='\033[1m'
    underline='\033[4m'

    @staticmethod
    def color(text):
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
        if not text=="" and not text in colorvals:
            print("Colorize unknown color:",text)


        colorval=colorvals.get(text,"\033[38;5;160;48;5;180m")
        return colorval # + text + '\033[0m'
