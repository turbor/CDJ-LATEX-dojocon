import json
import sys
from pathlib import Path

# Singleton ensures one shared translation dict across the entire program.
# The Translator is initialized once at startup (read_translation_files) and
# then queried from every block's to_ir/shadow_to_ir method. A fresh instance
# per call would re-read the JSON files each time.
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
        # Block translations (core categories: motion, looks, sound, etc.)
        q = p / 'editor' / 'blocks' / f"{args.language}.json"
        with q.open() as f:
            self.translate = json.load(f)
        # Extension translations (pen, music, video sensing, etc.)
        # These use dot-notation keys like "pen.clear" instead of uppercase.
        q = p / 'editor' / 'extensions' / f"{args.language}.json"
        with q.open() as f:
            for key, value in json.load(f).items():
                if key in self.translate:
                    sys.exit("Need to rethink programs, extensions and blocks l10n have same key!")
                self.translate[key] = value
        # Some opcodes don't match their l10n key directly.
        # opcode.json provides the mapping (e.g. CONTROL_REPEAT_UNTIL -> CONTROL_REPEATUNTIL).
        with open("opcode.json") as f:
            self.opcodetranslate = json.load(f)

    def translateOpcode(self, opcode):
        """Translate the block opcode to the selected language as human readable string"""
        if opcode in self.translate:
            return self.translate[opcode]
        elif opcode in self.opcodetranslate:
            return self.translateOpcode(self.opcodetranslate[opcode])
        return opcode

