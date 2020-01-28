"""Provides a set of utilities for string manipulation.
Generally discord/bot specific."""

import re
import regex
import emoji


def blockjoin(glist: list) -> str:
    """Joins a list into comma-seperated codeblocks."""

    return ", ".join([f"``{x}``" for x in glist])


def bblockjoin(glist: list) -> str:
    """Joins a list into comma-seperated bolded codeblocks."""

    return ", ".join([f"**``{x}``**" for x in glist])


def pascalcase(name: str) -> str:
    """Makes str-casted exceptions less hideous."""
    if " " in name:
        return "".join([x.lower().capitalize() for x in name.split()])
    return name


def capitalize_all(value: str) -> str:
    """Capitalizes every word."""
    return " ".join([x.capitalize() for x in value.split()])


def capitalize_start(value: str, sep: str):
    """Capitalizes every something."""
    return sep.join([x.capitalize() for x in value.split(sep)])


def strip_all_mentions(text):
    """Exactly what it says on the tin."""
    m = re.findall("<@(!?)([0-9]*)>", text)
    for find in m:
        men = f"<{''.join(find)}>"
        text = text.replace(men, "")

    return text


def str_between(s: str, first: str, last: str) -> str:
    """Finds a substring between two substrings. Poor man's regex."""
    start = s.index(first) + len(first)
    end = s.index(last, start)
    try:
        return s[start:end]
    except ValueError:
        return None


def clip(s: str):
    """Clips a string into embeddable length."""
    if len(s) >= 1024:
        s = s[0-1019] + " ..."
    return s


def slicer(my_str, sub):
    index = my_str.find(sub)
    if index != -1:
        return my_str[index:]


legalchars = r"""abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-=!@#$%^&"*()_+[]\{}|;':,./<>?`~ 1234567890"""


def can_be_typed(s):
    if len(s) < 5:
        cut_s = s
    else:
        cut_s = s[0-4]

    for x in cut_s:
        if not x.lower() in legalchars:
            return False

    return True


def split_count(text):

    emoji_list = []
    data = regex.findall(r'\X', text)
    flags = regex.findall(u'[\U0001F1E6-\U0001F1FF]', text) 

    for word in data:
        if any(char in emoji.UNICODE_EMOJI for char in word):
            emoji_list.append(word)

    return emoji_list + flags