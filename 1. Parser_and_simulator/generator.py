import os, sys
from collections import namedtuple
import subprocess
import re

Token = namedtuple("Token", ["offset", "hex", "assemble", "code"])


def set_timer(output, timer_count):
    append = "static struct TON timer1, timer2"

    for i in range(timer_count):
        append += " timer" + i
    append += ";"

    return output + append


def str_lstrip(line, idx):
    r = re.compile("\s")
    while r.match(line[idx]) is not None:
        idx += 1
    return idx


def token_eater(line):
    idx = 0
    offset, hex, assemble = "", "", ""

    def eat_offset():
        nonlocal idx, line
        eat = ""
        r = re.compile("([a-f0-9]|\s)")
        while r.match(line[idx]) is not None:
            eat += line[idx]
            idx += 1
        if line[idx] != ":":
            return False
        # pass ":" token
        idx += 1
        return eat

    def eat_hex():
        nonlocal idx, line
        eat = ""
        r = re.compile("[a-f0-9]{2}\s")
        while r.match(line[idx : idx + 3]) is not None:
            eat += line[idx : idx + 3]
            idx += 3
        idx += 1
        if line[idx] != " ":
            return False
        return eat

    offset = eat_offset()
    idx = str_lstrip(line, idx)

    hex = eat_hex()
    idx = str_lstrip(line, idx)

    assemble = line[idx:]

    if offset == False or hex == False:
        return False

    return offset, hex, assemble


def gen_code(opcode, operand):
    code = ""

    def calc_r7_offset(op1, op2):
        if op1.find("[") != -1:
            offset, _ = op1.split("[")
            return f"(char)(r7 >> (8 * {offset}))"
        elif op2.find("[") != -1:
            offset, reg = op2.split("[")
            reg = reg.split("]")[0]
            return f"8 * {offset} + {op1}"

    def handle_two_op(opcode, op1, op2):
        code = ""

        op1 = op1.strip()
        op2 = op2.strip()
        op1 = op1.strip("#")
        op2 = op2.strip("#")

        # if reg is r7
        if op2.find("r7") != -1:
            op1 = calc_r7_offset(op1, op2)
            op2 = "r7"

        elif op1.find("r7") != -1:
            op1 = calc_r7_offset(op1, op2)

        if opcode == "mov.l" or opcode == "mov.b":
            code = f"MOV({op1}, {op2})"
        elif opcode == "bmc":
            code = f"BMC({op2}, {op1})"
        # btst, bset, bclr
        else:
            opcode = opcode[1:]
            code = f"{opcode.upper()}({op2}, {op1})"

        return code

    def handle_one_op(opcode, op1):
        code = ""
        # branch
        if opcode == "bnc.b":
            addr = op1.split("x")[-1]
            code = f"BNC(x{addr})"
        elif opcode == "bc.b":
            addr = op1.split("x")[-1]
            code = f"BC(x{addr})"
        elif opcode == "push.l":
            code = f"PUSH({op1})"
        elif opcode == "setpsw":
            code = "carry_flag = 1"
        elif opcode == "jsr":
            code = "JSR_r14()"
        else:
            code = f"{opcode.upper()}({op1})"
        return code

    # 2 operand
    if operand.find(",") != -1:
        op1, op2 = operand.split(",")
        code = handle_two_op(opcode, op1, op2)
    # 1 operand
    else:
        op1 = operand
        code = handle_one_op(opcode, op1)

    return code


def translate_asm(tokens):
    idx = 0
    while len(tokens) > idx:
        offset, hex, assemble, _ = tokens[idx]

        assemble = assemble.strip()
        hex = hex.strip()

        if hex == "00" or hex == "37" or hex == "02" or hex == "0c":
            idx += 1
            continue

        # seperate
        opcode, operand = assemble.split("\t")

        opcode = opcode.strip()
        operand = operand.strip()

        # timer function block
        if hex == "7f 1a":
            # get timer index
            timer_idx = int(tokens[idx + 3].hex.strip())
            # divide block into two group: in/output
            in_tokens_idx, out_tokens_idx = [], []

            idx += 4
            nxt_hex = tokens[idx].hex.strip()
            while nxt_hex != "7f 1a":
                in_tokens_idx.append(idx)
                idx += 1
                nxt_hex = tokens[idx].hex.strip()

            idx += 2
            nxt_hex = tokens[idx].hex.strip()
            while nxt_hex != "7f 1a":
                out_tokens_idx.append(idx)
                idx += 1
                nxt_hex = tokens[idx].hex.strip()
            # ignore last 2 tokens in input group
            for in_idx in in_tokens_idx[:-2]:
                opcode, operand = tokens[in_idx].assemble.strip().split("\t")
                code = gen_code(opcode, operand)
                tokens[in_idx] = tokens[in_idx]._replace(code=code)

            # add handle_timer
            tokens[in_tokens_idx[-2]] = tokens[in_tokens_idx[-2]]._replace(
                code=f"handle_timer(&timer{timer_idx})"
            )
            # ignore first token in output group
            for out_idx in out_tokens_idx[1:]:
                opcode, operand = tokens[out_idx].assemble.strip().split("\t")
                code = gen_code(opcode, operand)
                tokens[out_idx] = tokens[out_idx]._replace(code=code)

            idx += 2
            continue
            """
            _, nxt_hex, _, _ = tokens[idx+1]
            nxt_hex = nxt_hex.strip()
            if nxt_hex == '10':
                idx += 4
            elif nxt_hex == '11':
                idx += 2
            continue
            """

        code = gen_code(opcode, operand)

        tokens[idx] = tokens[idx]._replace(code=code)
        idx += 1


def generate(file_name):
    ret = ""

    if not os.path.exists(file_name):
        print("File not exist")
        exit()

    with open(file_name, "r") as f:
        lines = f.readlines()

    tokens = []
    # gen token and filter useless line
    for line in lines:
        if line == "\n":
            continue
        token = token_eater(line)
        if token == False:
            continue
        tokens.append(Token(*token, code=""))

    # generate code
    translate_asm(tokens)
    for token in tokens:
        ret += "x{0}:/* {1: <25}*/{2: >23};\n".format(
            token.offset.strip(), token.assemble.strip().replace("\t", " "), token.code
        )
    return ret


# subprocess.run(['gcc main.c -L./simulator -lsimulator -o main'])

if __name__ == "__main__":
    with open("./ExtRAM_20230629160538.objdump.bin", "r") as f:
        lines = f.readlines()

    tokens = []
    # gen token and filter useless line
    for line in lines:
        if line == "\n":
            continue
        token = token_eater(line)
        if token == False:
            continue
        tokens.append(Token(*token, code=""))

    # generate code
    translate_asm(tokens)
    for token in tokens:
        print(
            "{0: <7}:/* {1: <25}*/{2: >23};".format(
                token.offset.strip(),
                token.assemble.strip().replace("\t", " "),
                token.code,
            )
        )
