from dataclasses import dataclass

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
        #pprint(self, indent=2)
        print(self.opcode + ": " + self.params.get('LIST' if self.mode=="list" else 'VARIABLE',"?") )
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
