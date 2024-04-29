import argparse
from mem_parser import mem_parse, get_code_info
from generator import generate
import subprocess

def gen_simulation_c(position_info, timer_info, elevator_code):
    

    # fill header
    header = f"""
    #include "simulator.h"

    int carry_flag = 0;
    unsigned long long r14 = 0;
    unsigned long long idx = 0;
    int stack[100];
    unsigned long long start_time = 0;

    unsigned long long r11 = 0;
    unsigned long long r13 = 0;
    unsigned long long r12 = 0;
    unsigned long long r7 = 0;
    unsigned int door_level;
    unsigned int elevator_floor;
    """

    for i in range(len(timer_info)):
        header += f"static struct TON timer{i};"
    
    if position_info['at'] == 0:
        position_info['at'] = position_info['was_at']

    # fill init_state
    init_state = f"""
        SET(r7, shift_cnt(WAS_AT_FLOOR_{int(position_info["was_at"])}));
        SET(r7, shift_cnt(AT_FLOOR_{int(position_info['at'])}));


        elevator_floor = {int(position_info['at']) * 10};
        door_level = 0;
    """

    for timer in timer_info:
        print(timer)
        index, preset, base = int(timer["index"]), int(timer["preset"]), timer["base"]

        if preset >= 1000:
            preset //= 1000

        init_state += f"timer{index}.sec_preset = {preset};\n"

    # final output
    return f"""
{header}

void init_state(){{
{init_state}    
}}

void what_floor(){{
{elevator_code}
}}
"""

def do_objdump(file_name, start_addr, stop_addr):
    with open(file_name + '.objdump', 'w') as f:
        subprocess.run(f"rx-elf-objdump.exe -b binary -m rx -D  --start-address={start_addr} --stop-address={stop_addr} {file_name}", stdout=f, shell=True)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        prog="Simulator code generator",
        description="Parse PLC memory and generate simulator code",
    )

    parser.add_argument("--external", type=str)

    parser.add_argument("--internal", type=str)

    parser.add_argument("-c", "--code_file", type=str, required=False, default='')
    args = parser.parse_args()
    
    position_info, timer_info, code_info = mem_parse(args.external, args.internal)
    
    if len(args.code_file) != 0:   
        c_code = gen_simulation_c(position_info, timer_info, generate(args.code_file))
    else:
        do_objdump(args.external, code_info['code_addr'], code_info['code_addr'] + code_info['code_size'])
        c_code = gen_simulation_c(position_info, timer_info, generate(args.external + '.objdump'))

    with open("./simulator/simulator.c", "w") as f:
        f.write(c_code)
