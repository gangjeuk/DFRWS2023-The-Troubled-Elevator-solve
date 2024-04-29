# Memory parser and PLC Code Simulator

This toolset allows you to visualize the current status of a specific type of PLC (e.g., RX630) and simulate its code execution.

## Usage

### Memory parser
You can visualize the current status of PLC.
It's CLI based, so you have run code in terminal. 

**Note**: All files (memory files) need to be in the same directory as the script you're running.
```
python mem_parser.py --external [External memory file name] --internal [Onchip memory file name]
```

### Simulator
#### Step1: Extract and generate code (if needed)
There is no need for additional Python packages to run the simulator. However, extracting code for the RX630 architecture using the objdump command is currently only supported on Windows.

So, you will need to objdump on Windows and run command on Linux (e.g., WSL environment).

If you can't set such environment, use the `--code_file` option to provide a pre-extracted code file. You can find in the `resource` directory.

**Note**: All files need to be in the same directory as the script you're running.

- If you can't use objdump
```
python main.py --external [External memory file name] --internal [Onchip memory file name] --code_file [Code file name]
```
- If you can use objdump
```
python main.py --external [External memory file name] --internal [Onchip memory file name]
```
#### Step2: Run simulator
This step is simple. Just run the `run_simul.sh` script:

```
bash run_simul.sh
```

### Simulating
While simulating, you can choose the floor you want the PLC to go to, or stop the simulation.

To select a floor, press `1`, `2`, or `3`.
To stop simulating, press `x`.