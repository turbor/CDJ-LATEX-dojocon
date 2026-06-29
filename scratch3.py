# This is a module that stores the Scratch3 dict
# The dict is used in block.py in the factorymethod but we do not want to instantiated and populate it for each call, so it is now moved to this module

SCRATCH3 = {"motion": {"opcodes": [
            "MOTION_MOVESTEPS",
            "MOTION_TURNRIGHT",
            "MOTION_TURNLEFT",
            "MOTION_GOTO",
            "MOTION_GOTOXY",
            "MOTION_GLIDETO",
            "MOTION_GLIDESECSTOXY",
            "MOTION_POINTINDIRECTION",
            "MOTION_POINTTOWARDS",
            "MOTION_CHANGEXBY",
            "MOTION_SETX",
            "MOTION_CHANGEYBY",
            "MOTION_SETY",
            "MOTION_IFONEDGEBOUNCE",
            "MOTION_SETROTATIONSTYLE",
            "MOTION_XPOSITION",
            "MOTION_YPOSITION",
            "MOTION_DIRECTION",
            "MOTION_GOTO_MENU", # This is the dropdown menu/shadowblock
            "MOTION_GLIDETO_MENU",  # This is the dropdown menu/shadowblock
            "MOTION_POINTTOWARDS_MENU"  # This is the dropdown menu/shadowblock
        ],"color":"blueberry","rgb":"4c97ff"},
        "looks":{"opcodes": [
            "LOOKS_SAYFORSECS",
            "LOOKS_SAY",
            "LOOKS_THINKFORSECS",
            "LOOKS_THINK",
            "LOOKS_SWITCHCOSTUMETO",
            "LOOKS_NEXTCOSTUME",
            "LOOKS_SWITCHBACKDROPTO",
            "LOOKS_SWITCHBACKDROPTOANDWAIT",
            "LOOKS_NEXTBACKDROP",
            "LOOKS_CHANGESIZEBY",
            "LOOKS_SETSIZETO",
            "LOOKS_CHANGEEFFECTBY",
            "LOOKS_SETEFFECTTO",
            "LOOKS_CLEARGRAPHICEFFECTS",
            "LOOKS_SHOW",
            "LOOKS_HIDE",
            "LOOKS_GOTOFRONTBACK",
            "LOOKS_GOFORWARDBACKWARDLAYERS",
            "LOOKS_COSTUMENUMBERNAME",
            "LOOKS_BACKDROPNUMBERNAME",
            "LOOKS_SIZE",
            "LOOKS_COSTUME", # shadowblock
            "LOOKS_BACKDROPS"  # shadowblock
        ],"color":"lightviolet","rgb":"#9966ff"},
        "sound": {"opcodes":  [
            "SOUND_PLAYUNTILDONE",
            "SOUND_PLAY",
            "SOUND_STOPALLSOUNDS",
            "SOUND_CHANGEEFFECTBY",
            "SOUND_SETEFFECTTO",
            "SOUND_CLEAREFFECTS",
            "SOUND_CHANGEVOLUMEBY",
            "SOUND_SETVOLUMETO",
            "SOUND_VOLUME"
        ],"color":"magenta","rgb":"#cf5acf"},
        "event": {"opcodes":  [
            "EVENT_WHENFLAGCLICKED",
            "EVENT_WHENKEYPRESSED",
            "EVENT_WHENTHISSPRITECLICKED",
            "EVENT_WHENSTAGECLICKED",
            "EVENT_WHENBACKDROPSWITCHESTO",
            "EVENT_WHENGREATERTHAN",
            "EVENT_WHENBROADCASTRECEIVED",
            "EVENT_BROADCAST",
            "EVENT_BROADCASTANDWAIT",
            "EVENT_WHENTOUCHINGOBJECT"
        ],"color":"amber","rgb":"#ffbf00"},
        "control": {"opcodes":  [
            "CONTROL_WAIT",
            "CONTROL_REPEAT",
            "CONTROL_FOREVER",
            "CONTROL_IF",
            "CONTROL_IF_ELSE",
            "CONTROL_WAIT_UNTIL",
            "CONTROL_REPEAT_UNTIL",
            "CONTROL_STOP",
            "CONTROL_START_AS_CLONE",
            "CONTROL_CREATE_CLONE_OF",
            "CONTROL_DELETE_THIS_CLONE",
            "CONTROL_CREATE_CLONE_OF_MENU"
        ],"color":"brightyellow","rgb":"#ffab19"},
        "sensing": {"opcodes":  [
            "SENSING_TOUCHINGOBJECT",
            "SENSING_TOUCHINGCOLOR",
            "SENSING_COLORISTOUCHINGCOLOR",
            "SENSING_DISTANCETO",
            "SENSING_ASKANDWAIT",
            "SENSING_ANSWER",
            "SENSING_KEYPRESSED",
            "SENSING_MOUSEDOWN",
            "SENSING_MOUSEX",
            "SENSING_MOUSEY",
            "SENSING_SETDRAGMODE",
            "SENSING_LOUDNESS",
            "SENSING_TIMER",
            "SENSING_RESETTIMER",
            "SENSING_OF",
            "SENSING_CURRENT",
            "SENSING_DAYSSINCE2000",
            "SENSING_USERNAME",
            "SENSING_TOUCHINGOBJECTMENU",
            "SENSING_DISTANCETOMENU",
            "SENSING_KEYOPTIONS"
        ],"color":"moderateblue","rgb":"#5cb1d6"},
        "operators": {"opcodes":  [
            "OPERATOR_ADD",
            "OPERATOR_SUBTRACT",
            "OPERATOR_MULTIPLY",
            "OPERATOR_DIVIDE",
            "OPERATOR_LT",
            "OPERATOR_EQUALS",
            "OPERATOR_GT",
            "OPERATOR_AND",
            "OPERATOR_OR",
            "OPERATOR_NOT",
            "OPERATOR_RANDOM",
            "OPERATOR_JOIN",
            "OPERATOR_LETTER_OF",
            "OPERATOR_LENGTH",
            "OPERATOR_CONTAINS",
            "OPERATOR_MOD",
            "OPERATOR_ROUND",
            "OPERATOR_MATHOP",
            ],"color":"coolgreen","rgb":"#52b55a"},
        "variable": {"opcodes":  [
            "DATA_VARIABLE",
            "DATA_SETVARIABLETO",
            "DATA_CHANGEVARIABLEBY",
            "DATA_SHOWVARIABLE",
            "DATA_HIDEVARIABLE"
        ],"color":"mango","rgb":"#ff8c1a"},

        "list": {"opcodes":  [
            "DATA_ADDTOLIST",
            "DATA_DELETEOFLIST",
            "DATA_DELETEALLOFLIST",
            "DATA_INSERTATLIST",
            "DATA_REPLACEITEMOFLIST",
            "DATA_ITEMOFLIST",
            "DATA_ITEMNUMOFLIST",
            "DATA_LENGTHOFLIST",
            "DATA_LISTCONTAINSITEM",
            "DATA_SHOWLIST",
            "DATA_HIDELIST"
        ],"color":"orange","rgb":"#ff4c00"},
        "my": {"opcodes":  [
            "PROCEDURES_DEFINITION",
            "PROCEDURES_CALL",
            "PROCEDURES_PROTOTYPE",
            "ARGUMENT_REPORTER_STRING_NUMBER",
            "ARGUMENT_REPORTER_BOOLEAN"
        ],"color":"hotpink","rgb":"#ff4d88"},
        "musicextension": {"opcodes":  [
            "MUSIC_PLAYDRUMFORBEATS",
            "MUSIC_RESTFORBEATS",
            "MUSIC_PLAYNOTEFORBEATS",
            "MUSIC_SETINSTRUMENT",
            "MUSIC_SETTEMPO",
            "MUSIC_CHANGETEMPO",
            "MUSIC_GETTEMPO"
        ],"color":"limegreen","rgb":"#0fbd8c"},
        "penExtension": {"opcodes":  [
            "PEN_CLEAR",
            "PEN_STAMP",
            "PEN_PENDOWN",
            "PEN_PENUP",
            "PEN_SETPENCOLORTOCOLOR",
            "PEN_CHANGEPENCOLORPARAMBY",
            "PEN_SETPENCOLORPARAMTO",
            "PEN_CHANGEPENSIZEBY",
            "PEN_SETPENSIZETO"
        ],"color":"limegreen","rgb":"#0fbd8c"},
        "videoExtension": {"opcodes":  [
            "VIDEOSENSING_WHENMOTIONGREATERTHAN",
            "VIDEOSENSING_VIDEOON",
            "VIDEOSENSING_VIDEOTOGGLE",
            "VIDEOSENSING_SETVIDEOTRANSPARENCY"
        ],"color":"limegreen","rgb":"#0fbd8c"},
        "faceSensingExtension": {"opcodes":  [
            "FACESENSING_GOTOPART",
            "FACESENSING_POINTINFACETILTDIRECTION",
            "FACESENSING_SETSIZETOFACESIZE",
            "FACESENSING_WHENTILTED",
            "FACESENSING_WHENSPRITETOUCHESPART",
            "FACESENSING_WHENFACEDETECTED",
            "FACESENSING_FACEISDETECTED",
            "FACESENSING_FACETILT",
            "FACESENSING_FACESIZE"
        ],"color":"limegreen","rgb":"#0fbd8c"},
        "textToSpeechExtension": {"opcodes":  [
            "TEXT2SPEECH_SPEAKANDWAIT",
            "TEXT2SPEECH_SETVOICE",
            "TEXT2SPEECH_SETLANGUAGE"
        ],"color":"limegreen","rgb":"#0fbd8c"},
        "translateExtension": {"opcodes":  [
            "TRANSLATE_GETTRANSLATE",
            "TRANSLATE_GETVIEWERLANGUAGE"
        ],"color":"limegreen","rgb":"#0fbd8c"},
        "makeyMakeyExtension": {"opcodes":  [
            "MAKEYMAKEY_WHENMAKEYKEYPRESSED",
            "MAKEYMAKEY_WHENCODEPRESSED"
        ],"color":"limegreen","rgb":"#0fbd8c"},
        "microbitExtension": {"opcodes":  [
            "MICROBIT_WHENBUTTONPRESSED",
            "MICROBIT_ISBUTTONPRESSED",
            "MICROBIT_WHENGESTURE",
            "MICROBIT_DISPLAYSYMBOL",
            "MICROBIT_DISPLAYTEXT",
            "MICROBIT_DISPLAYCLEAR",
            "MICROBIT_WHENTILTED",
            "MICROBIT_ISTILTED",
            "MICROBIT_GETTILTANGLE",
            "MICROBIT_WHENPINCONNECTED"
        ],"color":"limegreen","rgb":"#0fbd8c"},
        "goDirectForceExtension": {"opcodes":  [
            "GDXFOR_WHENGESTURE",
            "GDXFOR_WHENFORCEPUSHEDORPULLED",
            "GDXFOR_GETFORCE",
            "GDXFOR_WHENTILTED",
            "GDXFOR_ISTILTED",
            "GDXFOR_GETTILT",
            "GDXFOR_ISFREEFALLING",
            "GDXFOR_GETSPINSPEED",
            "GDXFOR_GETACCELERATION"
        ],"color":"limegreen","rgb":"#0fbd8c"},
        "legoMindstormsEV3Extension": {"opcodes":  [
            "EV3_MOTORTURNCLOCKWISE",
            "EV3_MOTORTURNCOUNTERCLOCKWISE",
            "EV3_MOTORSETPOWER",
            "EV3_GETMOTORPOSITION",
            "EV3_WHENBUTTONPRESSED",
            "EV3_WHENDISTANCELESSTHAN",
            "EV3_WHENBRIGHTNESSLESSTHAN",
            "EV3_BUTTONPRESSED",
            "EV3_GETDISTANCE",
            "EV3_GETBRIGHTNESS",
            "EV3_BEEP"
        ],"color":"limegreen","rgb":"#0fbd8c"},
        "legoBoostExtension": {"opcodes": [
            "BOOST_MOTORONFOR",
            "BOOST_MOTORONFORROTATION",
            "BOOST_MOTORON",
            "BOOST_MOTOROFF",
            "BOOST_SETMOTORPOWER",
            "BOOST_SETMOTORDIRECTION",
            "BOOST_GETMOTORPOSITION",
            "BOOST_WHENCOLOR",
            "BOOST_SEEINGCOLOR",
            "BOOST_WHENTILTED",
            "BOOST_GETTILTANGLE",
            "BOOST_SETLIGHTHUE"
        ],"color":"limegreen","rgb":"#0fbd8c"},
        "legoWeDoExtension": {"opcodes": [
            "WEDO2_MOTORONFOR",
            "WEDO2_MOTORON",
            "WEDO2_MOTOROFF",
            "WEDO2_STARTMOTORPOWER",
            "WEDO2_SETMOTORDIRECTION",
            "WEDO2_SETLIGHTHUE",
            "WEDO2_WHENDISTANCE",
            "WEDO2_WHENTILTED",
            "WEDO2_GETDISTANCE",
            "WEDO2_ISTILTED",
            "WEDO2_GETTILTANGLE"
        ],"color":"limegreen","rgb":"#0fbd8c"}
}

OPCODE_TO_CATEGORY = {}
for cat, info in SCRATCH3.items():
    for op in info["opcodes"]:
        OPCODE_TO_CATEGORY[op] = (cat, info["color"])

