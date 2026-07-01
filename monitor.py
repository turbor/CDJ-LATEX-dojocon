from dataclasses import dataclass
from translator import Translator

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
            name = Translator().translateOpcode(self.opcode.upper())
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
