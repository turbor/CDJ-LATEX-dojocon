import json

#Implement singleton (anti?)pattern as metaclass
class Singleton(type):
    _instances={}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton,cls).__call__(*args,**kwargs)
        return cls._instances[cls]

class Translator(object,metaclass=Singleton):
    translate = {}
    opcodetranslate = {}

    def read_translation_files(self, args: dict):
        with open(f"{args.language}.json") as f:
            self.translate = json.load(f)
        #some of the opcodes have a different key in the i10n files
        #so we have this extra json
        with open("opcode.json") as f:
            self.opcodetranslate = json.load(f)

    def translateOpcode(self, opcode):
        """Translate the block opcode to the selected language as human readable string"""
        if opcode in self.translate:
            return self.translate[opcode]
        elif opcode in self.opcodetranslate:
            return self.translateOpcode(self.opcodetranslate[opcode])
        return opcode

