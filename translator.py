import json
from pathlib import Path

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
        p = Path("scratch-l10n")
        q = p / 'editor' / 'blocks' / f"{args.language}.json"
        with q.open() as f:
            self.translate = json.load(f)
        q = p / 'editor' / 'extensions' / f"{args.language}.json"
        with q.open() as f:
            for key, value in json.load(f).items():
                key=key.upper().replace(".","_")
                if key in self.translate:
                    sys.exit("Need to rethink programs, extensions and blocks l10n have same key!")
                self.translate[key] = value
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

