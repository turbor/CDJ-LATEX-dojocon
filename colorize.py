class Colorize:
    reset='\033[0m'
    bold='\033[1m'
    underline='\033[4m'

    @staticmethod
    def color(text):
        colorvals={
            "amber":"\033[38;5;15;48;5;214m",
            "blue":"\033[38;5;15;48;5;26m",
            "lightblue": "\033[38;5;15;48;5;45m",
            "lightgreen": "\033[38;5;15;48;5;118m",
            "green": "\033[38;5;15;48;5;34m",
            "purple": "\033[38;5;15;48;5;207m",
            "pink": "\033[38;5;15;48;5;128m",
            "lightyellow":"\033[38;5;0;48;5;227m",
            "yellow":"\033[38;5;0;48;5;220m",
            "white": "\033[38;5;0;48;5;15m"
        }
        if not text=="" and not text in colorvals:
            print("Colorize unknown color:",text)


        colorval=colorvals.get(text,"\033[38;5;0;48;5;213m")
        return colorval # + text + '\033[0m'
