from dataclasses import dataclass
from translator import Translator

# Monitors are the variable/list displays visible on the Scratch stage during execution.
# They show the current value of a variable, list, or built-in sensor (timer, current date, etc.).
# The project.json stores them separately from blocks because they are not part of any script.

@dataclass(frozen=True)
class Monitor:
    id: str
    mode: str
    opcode: str
    params: dict
    value: str
    width: int
    height: int
    x: int
    y: int
    visible: bool
    sliderMin: int|None
    sliderMax: int|None
    isDiscrete: bool|None

    def dumpInfo(self ):
        if self.mode == "list":
            name = self.params.get('LIST', self.id)
        elif 'VARIABLE' in self.params:
            name = self.params['VARIABLE']
        elif 'CURRENTMENU' in self.params:
            menu = self.params['CURRENTMENU']
            key = f"SENSING_CURRENT_{menu}"
            name = Translator().translateOpcode(key)
        else:
            # Try uppercase opcode first (works for sensing_username etc.)
            name = Translator().translateOpcode(self.opcode.upper())
            # If untranslated, try dot-notation for extensions (e.g. faceSensing_faceTilt -> faceSensing.faceTilt)
            if name == self.opcode.upper() and '_' in self.opcode:
                dot_key = self.opcode.replace('_', '.', 1)
                translated = Translator().translateOpcode(dot_key)
                if translated != dot_key:
                    name = translated
        print(f"Name: {name}")
        match self.mode:
            case "default":
                print(f"Value: {self.value}")
            case "large":
                print(f"Value: {self.value}")
            case "list":
                print(f"List: {self.value}")
            case "slider":
                print(f"Slider: {self.value}")
                print(f"   Min: {self.sliderMin}  Max: {self.sliderMax}  Discrete: {self.isDiscrete}")
        print(f"Visible: {self.visible} \n")
