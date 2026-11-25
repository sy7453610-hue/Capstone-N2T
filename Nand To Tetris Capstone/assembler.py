#!/usr/bin/env python3
"""Hack assembler (Nand2Tetris Project 6) -- K = 49.

K mod 3 = 1  ->  extra feature: for a wrong line, print a clear message
with the line number (e.g. "Line 7: invalid instruction") instead of
crashing. All errors are reported; no .hack file is written if any exist.

Usage:  python assembler.py Prog.asm [Prog.hack]
"""
import os
import re
import sys

COMP = {
    "0": "0101010", "1": "0111111", "-1": "0111010",
    "D": "0001100", "A": "0110000", "!D": "0001101", "!A": "0110001",
    "-D": "0001111", "-A": "0110011", "D+1": "0011111", "A+1": "0110111",
    "D-1": "0001110", "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
    "A-D": "0000111", "D&A": "0000000", "D|A": "0010101",
    "M": "1110000", "!M": "1110001", "-M": "1110011", "M+1": "1110111",
    "M-1": "1110010", "D+M": "1000010", "D-M": "1010011", "M-D": "1000111",
    "D&M": "1000000", "D|M": "1010101",
}
# commutative spellings (A+D, M+D, A&D, ...) map to the same bits
COMP.update({"A+D": COMP["D+A"], "M+D": COMP["D+M"],
             "A&D": COMP["D&A"], "M&D": COMP["D&M"],
             "A|D": COMP["D|A"], "M|D": COMP["D|M"]})
DEST = {"": "000", "M": "001", "D": "010", "MD": "011",
        "A": "100", "AM": "101", "AD": "110", "AMD": "111"}
JUMP = {"": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
        "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111"}

PREDEFINED = {
    "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
    "SCREEN": 16384, "KBD": 24576,
    **{f"R{i}": i for i in range(16)},
}

SYMBOL_RE = re.compile(r"^[A-Za-z_.$:][A-Za-z0-9_.$:]*$")


class AsmError(Exception):
    pass


def clean(line):
    """Remove comments and all whitespace."""
    return line.split("//")[0].replace(" ", "").replace("\t", "").strip()


def first_pass(lines, errors):
    """Record every (LABEL) with the address of the next real instruction."""
    symbols = dict(PREDEFINED)
    rom = 0
    for num, text in enumerate(lines, 1):
        code = clean(text)
        if not code:
            continue
        if code.startswith("("):
            name = code[1:-1]
            if not code.endswith(")") or not SYMBOL_RE.match(name):
                errors.append(f"Line {num}: invalid label '{code}'")
            elif name in symbols:
                errors.append(f"Line {num}: label '{name}' is already defined")
            else:
                symbols[name] = rom
        else:
            rom += 1
    return symbols


def translate_c(code):
    dest, comp, jump = "", code, ""
    if "=" in comp:
        dest, comp = comp.split("=", 1)
    if ";" in comp:
        comp, jump = comp.split(";", 1)
    if dest not in DEST:
        raise AsmError(f"invalid destination '{dest}'")
    if comp not in COMP:
        raise AsmError(f"invalid computation '{comp}'")
    if jump not in JUMP:
        raise AsmError(f"invalid jump '{jump}'")
    return "111" + COMP[comp] + DEST[dest] + JUMP[jump]


def translate_a(code, symbols, state):
    sym = code[1:]
    if sym == "":
        raise AsmError("invalid instruction: '@' has no value")
    if sym.isdigit():
        value = int(sym)
        if value > 32767:
            raise AsmError(f"value {value} is too large (max 32767)")
    else:
        if not SYMBOL_RE.match(sym):
            raise AsmError(f"invalid instruction: bad symbol '{sym}'")
        if sym not in symbols:
            symbols[sym] = state["next_var"]
            state["next_var"] += 1
        value = symbols[sym]
    return format(value, "016b")


def second_pass(lines, symbols, errors):
    out = []
    state = {"next_var": 16}
    for num, text in enumerate(lines, 1):
        code = clean(text)
        if not code or code.startswith("("):
            continue
        try:
            if code.startswith("@"):
                out.append(translate_a(code, symbols, state))
            else:
                out.append(translate_c(code))
        except AsmError as e:
            errors.append(f"Line {num}: {e}")
    return out


def assemble(src, dst=None):
    dst = dst or os.path.splitext(src)[0] + ".hack"
    try:
        with open(src) as f:
            lines = f.read().splitlines()
    except OSError as e:
        print(f"Error: cannot read {src}: {e.strerror}")
        return 1
    errors = []
    symbols = first_pass(lines, errors)
    binary = second_pass(lines, symbols, errors)
    if errors:
        errors.sort(key=lambda m: int(m.split(':')[0].split()[1]))
        for msg in errors:
            print(msg)
        print(f"{len(errors)} error(s) found, no output written.")
        return 1
    with open(dst, "w") as f:
        f.write("\n".join(binary) + "\n")
    print(f"{src} -> {dst}  ({len(binary)} instructions)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python assembler.py Prog.asm [Prog.hack]")
        sys.exit(1)
    sys.exit(assemble(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
