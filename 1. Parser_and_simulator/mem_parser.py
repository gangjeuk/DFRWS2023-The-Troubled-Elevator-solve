import os
import xml.etree.ElementTree as ET
import argparse
from collections import namedtuple
import subprocess


# PLC Memory structure
ON_CHIP_BEGIN = 0x0
ON_CHIP_END = 0x1FFFF

EXTN_RAM_BEGIN = 0x7000000
EXTN_RAM_END = 0x707FFFF

ON_CHIP_ROM_BEGIN = 0xFFF00000
ON_CHIP_ROM_END = 0xFFF7FFFF

# r7 register
# Address of the block of data object
R7_ADDR = 0x7018000

WAS_AT_FLOOR_4 = 0x0001
WAS_AT_FLOOR_1 = 0x0002
WAS_AT_FLOOR_2 = 0x0004
WAS_AT_FLOOR_3 = 0x0008

FLOOR_1_CALL = 0x0010
FLOOR_2_CALL = 0x0020
FLOOR_3_CALL = 0x0040

AT_FLOOR_1 = 0x0080
AT_FLOOR_2 = 0x0100
AT_FLOOR_3 = 0x0200

FLOOR_4_CALL = 1 << 10
AT_FLOOR_4 = 1 << 11
DOOR_CNT = 1 << 12

MAYBE_FLOOR_ARRIVED = 1 << 20
MAYBE_ELEVATER_MOVING = 1 << 21

FLOOR_1_LATCH = 1 << 30
FLOOR_2_LATCH = 1 << 31
FLOOR_3_LATCH = 1 << 32


SAME_FLOOR_CALL = 1 << 60

# r13 register
# Address of Output

# r12 register
# Address of Input
FIRST_BLOCK = namedtuple(
    "CONFIG1",
    [
        "config2_addr",
        "config2_size",
        "padding1",
        "zip_file_addr",
        "zip_file_size",
        "padding2",
        "data_block_addr",
    ],
)

SECOND_BLOCK = namedtuple(
    "CONFIG2",
    [
        "config1_addr",
        "config1_size",
        "padding1",
        "data_block_addr",
        "data_block_size",
        "padding2",
        "code_block_addr",
        "code_block_size",
    ],
)

PROJECT_INFO = namedtuple(
    "PROJECT_INFO",
    [
        "ip_addr",
        "subnet",
        "version",
        "plc_model",
        "project_name",
    ],
)

ELEVATOR_MAX_HEIGHT = 3
ELEVATOR_HEIGHT = 13
ELEVATOR_HEIGHT_PADDING = 2
ELEVATOR_WIDTH = 40
ELEVATOR_WIDTH_PADDING = 5

LOG_WIDTH = 100
LOG_HEIGHT = ELEVATOR_HEIGHT * 3 + ELEVATOR_HEIGHT_PADDING * 2
log_buf = [[" " for _ in range(LOG_WIDTH)] for _ in range(LOG_HEIGHT)]

WIDTH = LOG_WIDTH + ELEVATOR_WIDTH + ELEVATOR_WIDTH_PADDING * 2 + 5
HEIGHT = ELEVATOR_HEIGHT * 3 + ELEVATOR_HEIGHT_PADDING * 2 + 2
frame_buf = [[" " for _ in range(WIDTH)] for _ in range(HEIGHT)]


""" Elevator buf 
heght |     width
  2   |====================================
  39  |= pad(5) wid(40) pad(5) = log(100) = 
  2   |====================================
"""


def fill_log(root, external_data, internal_data):
    addr = R7_ADDR - EXTN_RAM_BEGIN
    depth = 0
    first = external_data[addr : addr + 1]
    print("first ", ord(first))
    project_info = parse_internal_data(internal_data)
    check_list = [
        WAS_AT_FLOOR_4,
        WAS_AT_FLOOR_1,
        WAS_AT_FLOOR_2,
        WAS_AT_FLOOR_3,
        FLOOR_1_CALL,
        FLOOR_2_CALL,
        FLOOR_3_CALL,
        AT_FLOOR_1,
        AT_FLOOR_2,
        AT_FLOOR_3,
        FLOOR_4_CALL,
        AT_FLOOR_4,
        DOOR_CNT,
        FLOOR_1_LATCH,
        FLOOR_2_LATCH,
        FLOOR_3_LATCH,
        SAME_FLOOR_CALL,
    ]

    def write_buf(depth, log):
        for i, j in enumerate(log):
            log_buf[depth][i] = j

    def write_buf_left(depth, log):
        for i, j in enumerate(log):
            log_buf[depth][i] = j

    def write_buf_right(depth, log):
        for i, j in enumerate(log):
            log_buf[depth][50 + i] = j

    for i in range(LOG_WIDTH):
        write_buf(
            depth,
            "{0:^100}".format(
                root.find("GlobalProperties")
                .find("ProjectInformations")
                .find("Name")
                .text
            ),
        )
    depth += 2

    for i in range(LOG_WIDTH):
        format = "{0:^50}".format("Input")
        write_buf_left(depth, format)
    depth += 1

    for i, j in enumerate(root[0][0].findall("I")):
        write_buf_left(
            depth,
            "IDX: {0: <2} - {1: <15} - {2: <10}".format(
                i, j.find("Comment").text, j.find("Symbol").text
            ),
        )
        depth += 1

    depth += 1
    for i in range(LOG_WIDTH):
        format = "{0:^50}".format("Output")
        write_buf_left(depth, format)
    depth += 1

    for i, j in enumerate(root[0][0].findall("Q")):
        write_buf_left(
            depth,
            "IDX: {0: <2} - {1: <15} - {2: <10}".format(
                i, "None", j.find("Symbol").text
            ),
        )
        depth += 1

    depth += 1
    for i in range(LOG_WIDTH):
        format = "{0:^50}".format("POU")
        write_buf_left(depth, format)
    depth += 1

    for i, j in enumerate(root.find("Pous").findall("PouMetadata")):
        write_buf_left(depth, "IDX: {0: <2} - {1: <15}".format(i, j.find("Name").text))
        depth += 1

    depth += 1
    for i in range(LOG_WIDTH):
        format = "{0:^50}".format("Timer")
        write_buf_left(depth, format)
    depth += 1

    def mfind(node, keyword):
        if node.find(keyword) is not None:
            return node.find(keyword).text
        else:
            return "None"

    for i, j in enumerate(root.findall("T")):
        write_buf_left(
            depth,
            "IDX: {0: <2}, Preset: {1: <5}, Base: {2: <10}".format(
                mfind(j, "Index"), mfind(j, "Preset"), mfind(j, "Base")
            ),
        )
        depth += 1

    depth += 1
    for i in range(LOG_WIDTH):
        format = "{0:^50}".format("Counter")
        write_buf_left(depth, format)
    depth += 1

    for i, j in enumerate(root.findall("C")):
        write_buf_left(
            depth,
            "IDX: {0: <2}, Preset: {1: <15}".format(
                j.find("Index").text, j.find("Preset").text
            ),
        )
        depth += 1

    # reset depth
    depth = 2

    for i in range(LOG_WIDTH):
        format = "{0:^50}".format("Project Info")
        write_buf_right(depth, format)
    depth += 1

    for i, j in enumerate(project_info._asdict()):
        print(i, j)
        format = "{0: <13}: {1: <10}".format(j, project_info._asdict()[j])
        write_buf_right(depth, format)
        depth += 1

    depth += 1
    for i in range(LOG_WIDTH):
        format = "{0:^50}".format("Memory")
        write_buf_right(depth, format)
    depth += 1

    for i, j in enumerate(root.findall("MB")):
        format = "IDX: {0: <2} - {1: <15} - {2: <10} - [{3}]".format(
            i,
            mfind(j, "Comment"),
            mfind(j, "Symbol"),
            "O" if ord(first) & check_list[i] else "x",
        )
        write_buf_right(depth, format)
        symbol = mfind(j, "Symbol")
        depth += 1


def fill_log_on_frame():
    for i in range(LOG_HEIGHT):
        for j in range(LOG_WIDTH):
            frame_buf[1 + i][
                4 + ELEVATOR_WIDTH + ELEVATOR_WIDTH_PADDING * 2 + j
            ] = log_buf[i][j]


def fill_elevator(height):
    # Elevator size 30 x 40
    for h in range(ELEVATOR_HEIGHT):
        for w in range(ELEVATOR_WIDTH):
            if w == (ELEVATOR_WIDTH / 2) - 1 or w == (ELEVATOR_WIDTH / 2):
                frame_buf[
                    ELEVATOR_HEIGHT_PADDING
                    + (ELEVATOR_MAX_HEIGHT - height) * ELEVATOR_HEIGHT
                    + h
                ][w + ELEVATOR_WIDTH_PADDING + 1] = "|"
            elif (
                w == 0 or w == ELEVATOR_WIDTH - 1 or h == 0 or h == ELEVATOR_HEIGHT - 1
            ):
                frame_buf[
                    ELEVATOR_HEIGHT_PADDING
                    + (ELEVATOR_MAX_HEIGHT - height) * ELEVATOR_HEIGHT
                    + h
                ][w + ELEVATOR_WIDTH_PADDING + 1] = "="


def fill_frame():
    for j in range(HEIGHT):
        for i in range(WIDTH):
            # Left and Right
            if i == 0 or i == WIDTH - 1:
                frame_buf[j][i] = "|"
            # Middle line
            elif i == 3 + ELEVATOR_WIDTH_PADDING * 2 + ELEVATOR_WIDTH:
                frame_buf[j][i] = "|"
            # Up and Down
            elif j == 0 or j == HEIGHT - 1:
                frame_buf[j][i] = "="


def dump_status(root, external_data, internal_data):
    fill_frame()
    fill_log(root, external_data, internal_data)
    fill_log_on_frame()
    position_info = get_r7_info(external_data)
    if position_info['at'] != 0:
        fill_elevator(get_r7_info(external_data)["at"])
    else:
        fill_elevator(get_r7_info(external_data)["was_at"])

    for j in range(HEIGHT):
        for i in range(WIDTH):
            print(frame_buf[j][i], end="")
        print()


def parse_internal_data(internal_data: bytes):
    idx = internal_data.find(b"TM221")

    data = internal_data[idx - 70 : idx + 60]
    data = list(filter(lambda x: len(x) > 2, data.split(b"\n")))
    data = list(map(lambda x: x.decode(), data))

    project_name = data[-3]
    plc_model = f"{data[-2]} {data[-1]}"
    version = data[-5]
    ip_addr = data[-8]
    subnet_mask = data[-7]

    return PROJECT_INFO(ip_addr, subnet_mask, version, plc_model, project_name)

def get_r7_info(extern_data):
    addr = R7_ADDR - EXTN_RAM_BEGIN
    first = extern_data[addr : addr + 1]
    was_at, at, call = 0, 0, 0

    print(hex(ord(first)))
    if ord(first) & WAS_AT_FLOOR_4:
        was_at = 4
    elif ord(first) & WAS_AT_FLOOR_3:
        was_at = 3
    elif ord(first) & WAS_AT_FLOOR_2:
        was_at = 2
    elif ord(first) & WAS_AT_FLOOR_1:
        was_at = 1

    if ord(first) & FLOOR_1_CALL:
        call = 1
    elif ord(first) & FLOOR_2_CALL:
        call = 2
    elif ord(first) & FLOOR_3_CALL:
        call = 3
    elif ord(first) & AT_FLOOR_1:
        at = 1

    second = extern_data[addr + 1 : addr + 2]
    print("first", hex(ord(first)))
    print("second", hex(ord(second)))
    if ord(second) & AT_FLOOR_2 >> 8:
        at = 2
    elif ord(second) & AT_FLOOR_3 >> 8:
        at = 3
    elif ord(second) & FLOOR_4_CALL >> 8:
        call = 4
    elif ord(second) & AT_FLOOR_4 >> 8:
        at = 4

    return {"at": at, "was_at": was_at, "call": call}

def get_code_info(extern_data, intern_data):
    conf2_addr = int.from_bytes(intern_data[0x1FF3C:0x1FF40], 'little')
    
    conf2_addr = conf2_addr - EXTN_RAM_BEGIN + 0x7C
    # hardcoded;;
    code_addr = int.from_bytes(extern_data[conf2_addr: conf2_addr + 4], 'little')
    code_size = int.from_bytes(extern_data[conf2_addr + 4: conf2_addr + 6], 'little')
    
    return code_addr, code_size
    

def extram_unpack(external_ram: str):
    dir_name = "_" + external_ram + ".extracted"
    if not os.path.exists(dir_name):
        subprocess.run(["binwalk", "-e", external_ram])
    if not os.path.exists(os.path.join(dir_name, "entry")):
        subprocess.run(["rm", "-rf", dir_name])
        subprocess.run(["binwalk", "-e", external_ram])


def delete_unpack(external_ram: str):
    dir_name = "_" + external_ram + ".extracted"

    if os.path.exists(os.path.join(dir_name, "entry")):
        subprocess.run(["rm", "-rf", dir_name])


def mem_parse(ext_file_name, int_file_name):
    external_data = b""
    internal_data = b""

    with open(ext_file_name, "rb") as f:
        external_data = f.read()
    with open(int_file_name, "rb") as f:
        internal_data = f.read()
    
    # r7 info
    extram_unpack(ext_file_name)

    dir_name = "_" + ext_file_name + ".extracted"
    xml_tree = ET.parse(os.path.join(dir_name, "entry"))

    delete_unpack(ext_file_name)

    r7_info = get_r7_info(external_data)
    
    # timer info
    timer_info = []

    for t in xml_tree.getroot().findall("T"):
        index = t.find("Index").text if t.find("Index") is not None else None
        preset = t.find("Preset").text if t.find("Preset") is not None else None
        base = t.find("Base").text if t.find("Base") is not None else "OneSecond"
        timer_info.append({"index": index, "preset": preset, "base": base})

    assert index is not None
    
    # code info
    code_addr, code_size = get_code_info(external_data, internal_data)

    # hardcoded;;
    code_addr -= EXTN_RAM_BEGIN
    
    return r7_info, timer_info, {"code_addr": code_addr, "code_size": code_size}


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        prog="PLC Memory parser",
        description="Parse and display status of plc memory",
    )

    parser.add_argument("--external", type=str)

    parser.add_argument("--internal", type=str)

    args = parser.parse_args()

    external_data = b""
    internal_data = b""

    with open(args.external, "rb") as f:
        external_data = f.read()
    with open(args.internal, "rb") as f:
        internal_data = f.read()

    extram_unpack(args.external)

    dir_name = "_" + args.external + ".extracted"
    xml_tree = ET.parse(os.path.join(dir_name, "entry"))

    dump_status(xml_tree.getroot(), external_data, internal_data)

    delete_unpack(args.external)
