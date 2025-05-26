#!/usr/bin/env python
# -*- coding: utf-8 -*-

import polib
import argparse
import re
from googletrans import Translator

# Regex pattern to match placeholders: either {placeholder} or %(placeholder)s/d.
PLACEHOLDER_PATTERN = re.compile(r'(\{[^}]+\}|%\([^)]+\)[sd])')


def protect_placeholders(text):
    """
    Finds all formatting placeholders in the text and replaces them with unique tokens.
    Returns the modified text along with a mapping from token to original placeholder.
    """
    placeholders = {}

    def repl(match):
        token = f"UNIQ_PH_{len(placeholders)}_UNIQ"
        placeholders[token] = match.group(0)
        return token

    safe_text = PLACEHOLDER_PATTERN.sub(repl, text)
    return safe_text, placeholders


def restore_placeholders(text, placeholders):
    """
    Replaces all tokens in the text (even if their case has been changed)
    back with their original placeholders.
    """
    for token, original in placeholders.items():
        regex = re.compile(re.escape(token), re.IGNORECASE)
        text = regex.sub(original, text)
    return text


def translate_text(translator, text, src_lang, dest_lang):
    """
    Protects placeholders, translates the safe text, and then restores the original placeholders.
    """
    safe_text, placeholders = protect_placeholders(text)
    translation = translator.translate(safe_text, src=src_lang, dest=dest_lang)
    translated_text = translation.text
    final_text = restore_placeholders(translated_text, placeholders)
    return final_text


def translate_po(input_file, output_file, src_lang='en', dest_lang='es'):
    """
    Loads the input PO file, translates untranslated entries (protecting any placeholders),
    and ensures that fuzzy flags are removed so that every translated entry is finalized.

    Parameters:
      input_file (str): Path to the source .po file.
      output_file (str): Path for the translated output .po file.
      src_lang (str): The source language code.
      dest_lang (str): The target language code.
    """
    po = polib.pofile(input_file)
    translator = Translator()

    for entry in po:
        # Only translate if msgid exists and msgstr is empty.
        if entry.msgid and not entry.msgstr.strip():
            try:
                translated = translate_text(translator, entry.msgid, src_lang, dest_lang)
                entry.msgstr = translated
                # Mark the translation as finalized – remove fuzzy flags both in attribute and list.
                entry.fuzzy = False
                if 'fuzzy' in entry.flags:
                    entry.flags.remove('fuzzy')
                print(f"Translated: {entry.msgid} -> {translated}")
            except Exception as e:
                print(f"Error translating '{entry.msgid}': {e}")

    po.save(output_file)
    print(f"Saved translated PO file to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Translate PO files while preserving formatting placeholders (e.g., {term}, %(listing_id)s)\
 and ensuring translations are finalized (no fuzzy tags).'
    )
    parser.add_argument('input_file', help="Path to the input .po file")
    parser.add_argument('output_file', help="Path for the translated output .po file")
    parser.add_argument('--src_lang', default='en', help="Source language code (default: en)")
    parser.add_argument('--dest_lang', default='es', help="Destination language code (default: es)")
    args = parser.parse_args()

    translate_po(args.input_file, args.output_file, args.src_lang, args.dest_lang)


if __name__ == '__main__':
    main()
