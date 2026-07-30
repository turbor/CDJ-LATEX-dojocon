#!/usr/bin/env python3
"""
Translate variable, list, broadcast, and sprite names in a Scratch .sb3 file.

Reads a translation JSON file (same format as sb3docbuilder's -t flag)
and produces a new .sb3 with all names replaced.

Usage:
    python3 sb3translate.py <input.sb3> <translations.json> <language> <output.sb3>

Example:
    python3 sb3translate.py examples/robocup-simpel.sb3 examples/robocup-simpel-vars.json fr /tmp/robocup-fr.sb3

Translation file format:
    {
      "snelheid": {"fr": "vitesse", "en": "speed"},
      "Sprite1.snelheid": {"fr": "vitesse joueur 1"},
      "broadcast.start": {"fr": "commencer"},
      "sprite.Soccer Ball": {"fr": "Ballon de foot"}
    }

Prefixes:
    SpriteName.varname  - sprite-specific variable override
    broadcast.name      - broadcast-specific (when a var and broadcast share a name)
    sprite.name         - rename a sprite (updates all references)
"""

import sys
import json
import zipfile
import io


def load_translations(json_path: str, language: str) -> dict:
    """Load translation file and return {(sprite, name): translated_name} lookup.
    sprite is empty string for generic entries."""
    with open(json_path, encoding='utf-8') as f:
        raw = json.load(f)

    translations = {}
    for key, langs in raw.items():
        if language not in langs:
            continue
        translated = langs[language]
        if '.' in key:
            sprite, name = key.split('.', 1)
            translations[(sprite, name)] = translated
        else:
            translations[('', key)] = translated
    return translations


def translate_name(name: str, sprite: str, translations: dict, is_broadcast: bool = False) -> str:
    """Look up translation: sprite-specific first, then 'broadcast.' prefix, then generic.
    The 'broadcast.' prefix allows disambiguation when a variable and broadcast share a name."""
    # Sprite-specific override (only meaningful when sprite is set)
    if sprite:
        result = translations.get((sprite, name))
        if result:
            return result
    # For broadcasts, try "broadcast.name" before the generic fallback
    if is_broadcast:
        result = translations.get(('broadcast', name))
        if result:
            return result
    # Generic fallback
    result = translations.get(('', name))
    if result:
        return result
    return name


def translate_project(data: dict, translations: dict):
    """Translate all variable/list/broadcast/sprite name references in project.json in-place."""
    # Build sprite name mapping: old_name -> new_name
    sprite_renames = {}
    for target in data.get('targets', []):
        if not target['isStage']:
            new_name = translations.get(('sprite', target['name']))
            if new_name:
                sprite_renames[target['name']] = new_name

    # Rename sprites in target definitions
    for target in data.get('targets', []):
        if target['name'] in sprite_renames:
            target['name'] = sprite_renames[target['name']]

    # Translate monitors (update spriteName references too)
    for monitor in data.get('monitors', []):
        sprite = monitor.get('spriteName') or ''
        if sprite in sprite_renames:
            monitor['spriteName'] = sprite_renames[sprite]
        if 'VARIABLE' in monitor.get('params', {}):
            monitor['params']['VARIABLE'] = translate_name(
                monitor['params']['VARIABLE'], sprite, translations)
        if 'LIST' in monitor.get('params', {}):
            monitor['params']['LIST'] = translate_name(
                monitor['params']['LIST'], sprite, translations)

    # Translate each target (variables, lists, broadcasts, blocks)
    for target in data.get('targets', []):
        # Use the ORIGINAL sprite name for variable translation context
        # (the translation keys reference original names)
        orig_name = target['name']
        for old, new in sprite_renames.items():
            if new == orig_name:
                orig_name = old
                break
        sprite = orig_name if not target['isStage'] else ''
        translate_target(target, sprite, translations, sprite_renames)


def translate_target(target: dict, sprite: str, translations: dict, sprite_renames: dict):
    """Translate variable/list names within a single target."""
    # 1. Variable definitions: {id: [name, value]}
    for vid, val in target.get('variables', {}).items():
        val[0] = translate_name(val[0], sprite, translations)

    # 2. List definitions: {id: [name, [contents]]}
    for lid, val in target.get('lists', {}).items():
        val[0] = translate_name(val[0], sprite, translations)

    # 3. Broadcast definitions: {id: name}
    broadcasts = target.get('broadcasts', {})
    for bid in list(broadcasts.keys()):
        broadcasts[bid] = translate_name(broadcasts[bid], '', translations, is_broadcast=True)

    # 4. Block fields and inputs
    blocks = target.get('blocks', {})
    for bid, block in blocks.items():
        if isinstance(block, list):
            # Top-level variable/list shorthand: [12, name, id, ...] or [13, name, id, ...]
            if block[0] in (12, 13) and len(block) >= 2:
                block[1] = translate_name(block[1], sprite, translations)
        elif isinstance(block, dict):
            translate_block(block, sprite, translations, blocks, sprite_renames)


def translate_block(block: dict, sprite: str, translations: dict, all_blocks: dict, sprite_renames: dict):
    """Translate variable/list/broadcast references within a single block."""
    # Fields: VARIABLE and LIST hold [name, id], BROADCAST_OPTION holds [name, id]
    fields = block.get('fields', {})
    if 'VARIABLE' in fields:
        fields['VARIABLE'][0] = translate_name(fields['VARIABLE'][0], sprite, translations)
    if 'LIST' in fields:
        fields['LIST'][0] = translate_name(fields['LIST'][0], sprite, translations)
    if 'BROADCAST_OPTION' in fields:
        # Broadcasts are global - no sprite context needed
        fields['BROADCAST_OPTION'][0] = translate_name(fields['BROADCAST_OPTION'][0], '', translations, is_broadcast=True)

    # Sprite name references in menu fields
    # These appear in goto/glideto/pointtowards/touching/distanceto/clone/sensing_of menus
    for field_name in ('OBJECT', 'TO', 'TOWARDS', 'TOUCHINGOBJECTMENU',
                       'DISTANCETOMENU', 'CLONE_OPTION'):
        if field_name in fields:
            val = fields[field_name][0]
            if val in sprite_renames:
                fields[field_name][0] = sprite_renames[val]

    # PROPERTY field in sensing_of blocks references another sprite's variable.
    # Translate using the target sprite from the OBJECT shadow block.
    if 'PROPERTY' in fields and block.get('opcode') == 'sensing_of':
        target_sprite = _get_sensing_of_target(block, all_blocks, sprite)
        fields['PROPERTY'][0] = translate_name(fields['PROPERTY'][0], target_sprite, translations)

    # Inputs: scan for [12, name, id] and [13, name, id] arrays
    # and [11, name, id] (broadcast) arrays
    for iname, ival in block.get('inputs', {}).items():
        if isinstance(ival, list):
            translate_input_array(ival, sprite, translations)


def translate_input_array(arr: list, sprite: str, translations: dict):
    """Recursively scan an input array for variable/list/broadcast references."""
    for i, item in enumerate(arr):
        if isinstance(item, list):
            # Broadcast reference: [11, name, id]
            if len(item) >= 3 and item[0] == 11:
                item[1] = translate_name(item[1], '', translations, is_broadcast=True)
            # Variable reference: [12, name, id, x?, y?]
            elif len(item) >= 3 and item[0] == 12:
                item[1] = translate_name(item[1], sprite, translations)
            # List reference: [13, name, id, x?, y?]
            elif len(item) >= 3 and item[0] == 13:
                item[1] = translate_name(item[1], sprite, translations)
            else:
                # Recurse into nested arrays
                translate_input_array(item, sprite, translations)


def _get_sensing_of_target(block: dict, all_blocks: dict, default_sprite: str) -> str:
    """Determine the target sprite for a sensing_of block by looking up
    the OBJECT input's shadow block which holds the sprite name."""
    obj_input = block.get('inputs', {}).get('OBJECT')
    if obj_input and isinstance(obj_input, list) and len(obj_input) >= 2:
        shadow_id = obj_input[1]
        if isinstance(shadow_id, str) and shadow_id in all_blocks:
            shadow = all_blocks[shadow_id]
            if isinstance(shadow, dict):
                obj_field = shadow.get('fields', {}).get('OBJECT')
                if obj_field and isinstance(obj_field, list):
                    return obj_field[0]
    return default_sprite


def main():
    # A simple interface without the usual argparse stuff
    if len(sys.argv) != 5:
        print(__doc__.strip())
        sys.exit(1)

    input_sb3, translations_json, language, output_sb3 = sys.argv[1:5]

    # Read the translations
    translations = load_translations(translations_json, language)
    if not translations:
        print(f"No translations found for language '{language}' in {translations_json}", file=sys.stderr)
        sys.exit(1)

    # Read the sb3 zip, modify project.json, write to new zip
    with zipfile.ZipFile(input_sb3, 'r') as zin:
        data = json.loads(zin.read('project.json'))
        translate_project(data, translations)

        with zipfile.ZipFile(output_sb3, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == 'project.json':
                    zout.writestr(item, json.dumps(data))
                else:
                    zout.writestr(item, zin.read(item.filename))
            zout.comment = (
                f"Translated by sb3translate.py (lang={language})\n"
                f"https://github.com/turbor/CDJ-LATEX-dojocon"
            ).encode('utf-8')

    print(f"Translated sb3 written to {output_sb3}")


if __name__ == '__main__':
    main()
