from block import SimpleBlock
from ir import IR, IRBlock, IRHatBlock, IRDropdown
from translator import Translator


class ExtensionBlock(SimpleBlock):
    """Base class for extension blocks.
    All Scratch extensions share the same pattern:
    - Opcodes map to dot-notation l10n keys (e.g. "music.playDrumForBeats")
    - Translation text uses named [PLACEHOLDER] inputs instead of %1
    - Each extension has an icon prefix shown before the block text

    Subclasses define _opcode_to_l10n (dict), _icon (str), and _hat_opcodes (set)."""

    _opcode_to_l10n: dict = {}
    _icon: str = ""
    _hat_opcodes: set = set()

    def to_ir(self, blocksAST: dict) -> IR:
        # Extension l10n strings use [NAME] placeholders (e.g. "play drum [DRUM] for [BEATS] beats")
        # rather than positional %1, %2. We convert them to %N based on the order inputs
        # appear in self.inputs, so the renderer's _fill_text handles substitution uniformly.
        l10n_key = self._opcode_to_l10n.get(self.opcode, self.opcode)
        text = Translator().translateOpcode(l10n_key)

        if self._icon:
            text = self._icon + " " + text

        # Decode inputs preserving their order
        input_names = []
        input_nodes = []
        for name, arr in self.inputs.items():
            if name in ('SUBSTACK', 'SUBSTACK2'):
                continue
            input_names.append(name)
            input_nodes.append(self._decode_input_array_ir(arr, blocksAST))

        # Convert [NAME] placeholders to %1, %2, ...
        for i, name in enumerate(input_names):
            text = text.replace(f"[{name}]", f"%{i + 1}")

        # Hat blocks (when ... events)
        if self.opcode in self._hat_opcodes:
            return IRHatBlock(opcode=self.opcode, category=self.color,
                              text=text, inputs=input_nodes)

        return IRBlock(opcode=self.opcode, category=self.color,
                       text=text, inputs=input_nodes, fields=[])

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        """Extension reporters used as inputs in other blocks.
        Translates via the l10n mapping and renders as a dropdown."""
        l10n_key = self._opcode_to_l10n.get(self.opcode)
        if l10n_key:
            text = Translator().translateOpcode(l10n_key)
            # If the text has [PLACEHOLDER]s, decode inputs and substitute
            input_names = []
            input_nodes = []
            for name, arr in self.inputs.items():
                input_names.append(name)
                input_nodes.append(self._decode_input_array_ir(arr, blocksAST))
            for i, name in enumerate(input_names):
                text = text.replace(f"[{name}]", f"%{i + 1}")
            if input_nodes:
                from ir import IROperator
                return IROperator(opcode=self.opcode, category=self.color,
                                  text=text, operands=input_nodes)
            return IRDropdown(value=text)
        # Fallback: try fields as a simple menu
        for name, val in self.fields.items():
            if isinstance(val, list):
                return IRDropdown(value=val[0])
        return IRDropdown(value=Translator().translateOpcode(self.opcode))


class PenBlock(ExtensionBlock):
    _icon = "\u270e"
    _hat_opcodes = set()
    _opcode_to_l10n = {
        "PEN_CLEAR": "pen.clear",
        "PEN_STAMP": "pen.stamp",
        "PEN_PENDOWN": "pen.penDown",
        "PEN_PENUP": "pen.penUp",
        "PEN_SETPENCOLORTOCOLOR": "pen.setColor",
        "PEN_CHANGEPENCOLORPARAMBY": "pen.changeColorParam",
        "PEN_SETPENCOLORPARAMTO": "pen.setColorParam",
        "PEN_CHANGEPENSIZEBY": "pen.changeSize",
        "PEN_SETPENSIZETO": "pen.setSize",
    }

    def shadow_to_ir(self, blocksAST: dict) -> IR:
        """Handle PEN_MENU_COLORPARAM shadow (dropdown for color/saturation/etc)."""
        if self.opcode == "PEN_MENU_COLORPARAM":
            val = self.fields.get("colorParam", [None])[0]
            if val:
                key = f"pen.colorMenu.{val}"
                return IRDropdown(value=Translator().translateOpcode(key))
            return IRDropdown(value="?")
        return super().shadow_to_ir(blocksAST)


class MusicBlock(ExtensionBlock):
    _icon = "\u266b"
    _hat_opcodes = set()
    _opcode_to_l10n = {
        "MUSIC_PLAYDRUMFORBEATS": "music.playDrumForBeats",
        "MUSIC_RESTFORBEATS": "music.restForBeats",
        "MUSIC_PLAYNOTEFORBEATS": "music.playNoteForBeats",
        "MUSIC_SETINSTRUMENT": "music.setInstrument",
        "MUSIC_SETTEMPO": "music.setTempo",
        "MUSIC_CHANGETEMPO": "music.changeTempo",
        "MUSIC_GETTEMPO": "music.getTempo",
    }


class VideoSensingBlock(ExtensionBlock):
    _icon = "\U0001f3a5"
    _hat_opcodes = {"VIDEOSENSING_WHENMOTIONGREATERTHAN"}
    _opcode_to_l10n = {
        "VIDEOSENSING_WHENMOTIONGREATERTHAN": "videoSensing.whenMotionGreaterThan",
        "VIDEOSENSING_VIDEOON": "videoSensing.videoOn",
        "VIDEOSENSING_VIDEOTOGGLE": "videoSensing.videoToggle",
        "VIDEOSENSING_SETVIDEOTRANSPARENCY": "videoSensing.setVideoTransparency",
    }


class FaceSensingBlock(ExtensionBlock):
    _icon = "\U0001f642"
    _hat_opcodes = {"FACESENSING_WHENFACEDETECTED", "FACESENSING_WHENSPRITETOUCHESPART",
                    "FACESENSING_WHENTILTED"}
    _opcode_to_l10n = {
        "FACESENSING_GOTOPART": "faceSensing.goToPart",
        "FACESENSING_POINTINFACETILTDIRECTION": "faceSensing.pointInFaceTiltDirection",
        "FACESENSING_SETSIZETOFACESIZE": "faceSensing.setSizeToFaceSize",
        "FACESENSING_WHENTILTED": "faceSensing.whenTilted",
        "FACESENSING_WHENSPRITETOUCHESPART": "faceSensing.whenSpriteTouchesPart",
        "FACESENSING_WHENFACEDETECTED": "faceSensing.whenFaceDetected",
        "FACESENSING_FACEISDETECTED": "faceSensing.faceDetected",
        "FACESENSING_FACETILT": "faceSensing.faceTilt",
        "FACESENSING_FACESIZE": "faceSensing.faceSize",
    }


class Text2SpeechBlock(ExtensionBlock):
    _icon = "\U0001f4ac"
    _hat_opcodes = set()
    _opcode_to_l10n = {
        "TEXT2SPEECH_SPEAKANDWAIT": "text2speech.speakAndWaitBlock",
        "TEXT2SPEECH_SETVOICE": "text2speech.setVoiceBlock",
        "TEXT2SPEECH_SETLANGUAGE": "text2speech.setLanguageBlock",
    }


class TranslateBlock(ExtensionBlock):
    _icon = "\U0001f310"
    _hat_opcodes = set()
    _opcode_to_l10n = {
        "TRANSLATE_GETTRANSLATE": "translate.translateBlock",
        "TRANSLATE_GETVIEWERLANGUAGE": "translate.viewerLanguage",
    }


class MakeyMakeyBlock(ExtensionBlock):
    _icon = "\u2328"
    _hat_opcodes = {"MAKEYMAKEY_WHENMAKEYKEYPRESSED", "MAKEYMAKEY_WHENCODEPRESSED"}
    _opcode_to_l10n = {
        "MAKEYMAKEY_WHENMAKEYKEYPRESSED": "makeymakey.whenKeyPressed",
        "MAKEYMAKEY_WHENCODEPRESSED": "makeymakey.whenKeysPressedInOrder",
    }


class MicrobitBlock(ExtensionBlock):
    _icon = "\u25a3"
    _hat_opcodes = {"MICROBIT_WHENBUTTONPRESSED", "MICROBIT_WHENGESTURE",
                    "MICROBIT_WHENTILTED", "MICROBIT_WHENPINCONNECTED"}
    _opcode_to_l10n = {
        "MICROBIT_WHENBUTTONPRESSED": "microbit.whenButtonPressed",
        "MICROBIT_ISBUTTONPRESSED": "microbit.isButtonPressed",
        "MICROBIT_WHENGESTURE": "microbit.whenGesture",
        "MICROBIT_DISPLAYSYMBOL": "microbit.displaySymbol",
        "MICROBIT_DISPLAYTEXT": "microbit.displayText",
        "MICROBIT_DISPLAYCLEAR": "microbit.clearDisplay",
        "MICROBIT_WHENTILTED": "microbit.whenTilted",
        "MICROBIT_ISTILTED": "microbit.isTilted",
        "MICROBIT_GETTILTANGLE": "microbit.tiltAngle",
        "MICROBIT_WHENPINCONNECTED": "microbit.whenPinConnected",
    }


class GdxForBlock(ExtensionBlock):
    _icon = "\u2699"
    _hat_opcodes = {"GDXFOR_WHENGESTURE", "GDXFOR_WHENFORCEPUSHEDORPULLED",
                    "GDXFOR_WHENTILTED"}
    _opcode_to_l10n = {
        "GDXFOR_WHENGESTURE": "gdxfor.whenGesture",
        "GDXFOR_WHENFORCEPUSHEDORPULLED": "gdxfor.whenForcePushedOrPulled",
        "GDXFOR_GETFORCE": "gdxfor.getForce",
        "GDXFOR_WHENTILTED": "gdxfor.whenTilted",
        "GDXFOR_ISTILTED": "gdxfor.isTilted",
        "GDXFOR_GETTILT": "gdxfor.getTilt",
        "GDXFOR_ISFREEFALLING": "gdxfor.isFreeFalling",
        "GDXFOR_GETSPINSPEED": "gdxfor.getSpin",
        "GDXFOR_GETACCELERATION": "gdxfor.getAcceleration",
    }


class EV3Block(ExtensionBlock):
    _icon = "\U0001f916"
    _hat_opcodes = {"EV3_WHENBUTTONPRESSED", "EV3_WHENDISTANCELESSTHAN",
                    "EV3_WHENBRIGHTNESSLESSTHAN"}
    _opcode_to_l10n = {
        "EV3_MOTORTURNCLOCKWISE": "ev3.motorTurnClockwise",
        "EV3_MOTORTURNCOUNTERCLOCKWISE": "ev3.motorTurnCounterClockwise",
        "EV3_MOTORSETPOWER": "ev3.motorSetPower",
        "EV3_GETMOTORPOSITION": "ev3.getMotorPosition",
        "EV3_WHENBUTTONPRESSED": "ev3.whenButtonPressed",
        "EV3_WHENDISTANCELESSTHAN": "ev3.whenDistanceLessThan",
        "EV3_WHENBRIGHTNESSLESSTHAN": "ev3.whenBrightnessLessThan",
        "EV3_BUTTONPRESSED": "ev3.buttonPressed",
        "EV3_GETDISTANCE": "ev3.getDistance",
        "EV3_GETBRIGHTNESS": "ev3.getBrightness",
        "EV3_BEEP": "ev3.beepNote",
    }


class BoostBlock(ExtensionBlock):
    _icon = "\U0001f9e9"
    _hat_opcodes = {"BOOST_WHENCOLOR", "BOOST_WHENTILTED"}
    _opcode_to_l10n = {
        "BOOST_MOTORONFOR": "boost.motorOnFor",
        "BOOST_MOTORONFORROTATION": "boost.motorOnForRotation",
        "BOOST_MOTORON": "boost.motorOn",
        "BOOST_MOTOROFF": "boost.motorOff",
        "BOOST_SETMOTORPOWER": "boost.setMotorPower",
        "BOOST_SETMOTORDIRECTION": "boost.setMotorDirection",
        "BOOST_GETMOTORPOSITION": "boost.getMotorPosition",
        "BOOST_WHENCOLOR": "boost.whenColor",
        "BOOST_SEEINGCOLOR": "boost.seeingColor",
        "BOOST_WHENTILTED": "boost.whenTilted",
        "BOOST_GETTILTANGLE": "boost.getTiltAngle",
        "BOOST_SETLIGHTHUE": "boost.setLightHue",
    }


class WeDo2Block(ExtensionBlock):
    _icon = "\U0001f9e9"
    _hat_opcodes = {"WEDO2_WHENDISTANCE", "WEDO2_WHENTILTED"}
    _opcode_to_l10n = {
        "WEDO2_MOTORONFOR": "wedo2.motorOnFor",
        "WEDO2_MOTORON": "wedo2.motorOn",
        "WEDO2_MOTOROFF": "wedo2.motorOff",
        "WEDO2_STARTMOTORPOWER": "wedo2.startMotorPower",
        "WEDO2_SETMOTORDIRECTION": "wedo2.setMotorDirection",
        "WEDO2_SETLIGHTHUE": "wedo2.setLightHue",
        "WEDO2_WHENDISTANCE": "wedo2.whenDistance",
        "WEDO2_WHENTILTED": "wedo2.whenTilted",
        "WEDO2_GETDISTANCE": "wedo2.getDistance",
        "WEDO2_ISTILTED": "wedo2.isTilted",
        "WEDO2_GETTILTANGLE": "wedo2.getTiltAngle",
    }
