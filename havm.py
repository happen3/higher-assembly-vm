import time
import sys
import ast
import argparse
import os
import re
import tkinter.messagebox as mb

memory = [""] * 1024
stack = []
reg = [00] * 17
counters =  [0] * 4

exceptions = []

base = ""

NOEXEC = False
LABEL_IN = False
VER_MODE = False
STANDARD_LIB_PATH = os.getcwd() + "\\lib"
SIMPLE_MODE = False
VM_VERSION = "1.00"
QUIET = False
INCLUDES = []
INC_PREPRO = []
DUMP_MEM = False
DUMP_REG = False
INFO_MODE = False
DUMP_STA = False
MANIFEST_VERSION = 1
RETP = 0x00
RETCODE = 0

"""rom = [
    "LABEL",
    "PUTS", "i+", "Hello, world!", "", 
    "END DATA",
    "RETC",
    "END LABEL",
    "SRA", 13,
    "JUMP", 1, 
    "NOP"
]"""

# Utils
def writereg(register: int, value: any):
    reg[register] = value

try:
        parser = argparse.ArgumentParser(description="Higher Assembly Virtual Machine")
        parser.add_argument("file", help="HAS file to be ran.")
        parser.add_argument("-i", "--info", action="store_true", help="Shows info on the current file.")
        parser.add_argument("-v", "--version", action="store_true", help="Shows HAVM Version.")
        parser.add_argument("-S", "--simple", action="store_true", help="Enables simple mode output.")
        parser.add_argument("-Q", "--quiet", action="store_true", help="Quiet modes disables all verbose messages at the end and beginging of the execution.")
        parser.add_argument("-dM", "--dump_mem", action="store_true", help="Dumps the memory at the end of execution.")
        parser.add_argument("-dR", "--dump_reg", action="store_true", help="Dumps the registers at the end of execution.")
        parser.add_argument("-dS", "--dump_stack", action="store_true", help="Dumps the stack at the end of execution.")
        parser.add_argument("-dOut", metavar="OUTPUT_FILE", type=str, help="Output dumped data to user-provided path.")
        
        args = parser.parse_args()
        if args.dOut is None:
            if args.dump_mem or args.dump_reg or args.dump_stack:
                parser.error("Argument -dOut is positional when using -dM, -dR, or -dS.")

        filename = args.file
        SIMPLE_MODE = args.simple
        DUMP_MEM = args.dump_mem
        DUMP_REG = args.dump_reg
        DUMP_STA = args.dump_stack
        VER_MODE = args.version
        INFO_MODE = args.info
        QUIET = args.quiet

        if VER_MODE:
            print(f"HAVM Version {VM_VERSION}.\n\nHigher Assembly Virtual Machine\n(C) Copyright 2024 happen3")
            sys.exit(0)

        # Open the .has file in read mode
        with open(filename, 'r') as fh:
            # Read the entire contents of the file as a string
            fc = fh.read()
            for item in ast.literal_eval(fc):
                if isinstance(item, dict):
                    ManifestPresence = True # Set Manifest V1 mode
                    rom = ast.literal_eval(fc)[1]
                    metadata = ast.literal_eval(fc)[0]
                    break
                else:
                    ManifestPresence = False # Set legacy mode
                    rom = ast.literal_eval(fc)

except FileNotFoundError:
    mb.showerror("HAVM error", "Exception 0x10 (FileNotFoundError) ; execution therefore cannot continue.")
    print(f"HAVM Fatal error; exception 0x10 execution cannot continue.")
    sys.exit(16)

if INFO_MODE:
    if ManifestPresence:
        includes_indexes = [index + 1 for index, word in enumerate(rom) if word == "@INCLUDE"]
        includes = []
        for index in includes_indexes:
            includes.append(rom[index].replace("<", "").replace(">", ""))
        #print(includes_indexes)
        print(f"Showing info on {filename}:\n")
        print(f"Name: {metadata["name"]}")
        print(f"Description: {metadata["desc"]}")
        print(f"Version: {metadata["version"][0] if 'version' in metadata else "N/A"}")
        if 'version' in metadata:
            if len(metadata['version']) == 2:
                print(f"Build: {metadata['version'][1]}")
        print(f"\nCopyright: {metadata["copyright"]}")
        print(f"Includes: {includes}")
        sys.exit(0)
    else:
        print("No manifest was found.")
        print(f"Filename: {filename}")
        sys.exit(0)

if not SIMPLE_MODE and not QUIET:
    #for l in range(0, len(memory) + 1):
    #    print(f"MEMTEST: {l} numbers available in memory.", end="\r")
    if ManifestPresence:
        print("Now reading", metadata["artifact"] + f".has\nName: {metadata["name"]}, description: {metadata["desc"]}")
    else:
        print(f"Now reading {sys.argv[1]}...")
    print("")
    for b in range(0, len(rom)):
        print(f"{hex(b)} instructions used in ROM.", end="\r")
    print("\n\n")
 
#program loader
timestart = time.time_ns()

position = 0
while position < len(rom):
    ncommand = str(rom[position])
    command = rom[position - 1]  # Get the current command
            
    if ";" in str(command):
        position += 1  # Skip comments
        continue
    
    if NOEXEC == False and LABEL_IN == False:
        afnc = rom[position + 1]
        if str(afnc).startswith("$"):
            register_index = int(str(afnc)[1:])
            if 0 <= register_index < len(reg):
                rom[position + 1] = reg[register_index]
            else:
                print(f"Error: Invalid register index '{register_index}' at position {position}.")
                sys.exit(19)
        if str(afnc).startswith("#"):
            register_index = int(str(afnc)[1:])
            if 0 <= register_index < len(reg):
                rom[position + 1] = memory[register_index]
            else:
                print(f"Error: Invalid register index '{register_index}' at position {position}.")
                sys.exit(19)
        
        if command == "@INCLUDE":
            try:
                if "<" in rom[position] and ">" in rom[position]:
                    INCLUDES.append(rom[position].replace("<", "").replace(">", ""))
                    with open(STANDARD_LIB_PATH + "\\" + rom[position].replace("<", "").replace(">", "") + ".hae") as fh:
                        INC_PREPRO.append(fh.read())
                else:
                    INCLUDES.append(rom[position])
                    with open(rom[position]) as fh:
                        INC_PREPRO.append(fh.read())
            except FileNotFoundError:
                print(f"Program failure - Unable to link module.")
                sys.exit(10)
        if command == "NOP":
            for _ in range(0, 768):
                pass
        elif command == "HLT":
            position = len(rom)
        elif command == "STA":
            reg[15] = rom[position + 1]
        elif command == "LOAD":
            NOEXEC = True
            memory[int(rom[position])] = rom[position + 1]
        elif command == "DELOAD":
            reg[10] = memory[rom[position]]
        elif command == "PUTS":
            NOEXEC = True
            if rom[position] == "l+":
                print(reg[10])
            elif rom[position] == "i+":
                print(rom[position + 1])
        elif command == "READ":
            rarg = input("")
            reg[11] = rarg
        elif command == "PUTSN":
            NOEXEC = True
            if rom[position] == "l+":
                print(reg[10], end="")
            elif rom[position] == "i+":
                print(rom[position + 1], end="")
        elif command == "LOADR":
            NOEXEC = True
            memory[int(rom[position])] = reg[rom[position + 1]]
        elif command == "EXPORT":
            if rom[position] == "i+":
                with open(rom[position + 1], rom[position + 2]) as fh:
                    fh.write(rom[position + 2])
            elif rom[position] == "l+":
                with open(rom[position + 1], rom[position + 2]) as fh:
                    fh.write(reg[10])
        elif command == "IMPORT":
            if rom[position] == "i+":
                with open(rom[position + 1], rom[position + 2]) as fh:
                    reg[12] = fh.read()
            elif rom[position] == "l+":
                with open(rom[position + 1], rom[position + 2]) as fh:
                    reg[12] = fh.read()
        elif command == "CONCAT":
            NOEXEC = True
            reg[1] = rom[position] + rom[position + 1]
        elif command == "RCONCAT":
            reg[1] = reg[rom[position]] + reg[rom[position + 1]]
        elif command == "SPUSH":
            NOEXEC = True
            stack.append(rom[position])
        elif command == "SLOADR":
            reg[7] = stack[-1]
            del stack[-1]
        elif command == "ADD":
            reg[16] = reg[1] + reg[2]
            reg[16] = reg[1] + reg[2]
        elif command == "SUB":
            reg[16] = reg[1] - reg[2]
            reg[16] = reg[1] - reg[2]
        elif command == "MULT":
            reg[16] = reg[1] * reg[2]
            reg[16] = reg[1] * reg[2]
        elif command == "DIV":
            reg[16] = reg[1] / reg[2]
            reg[16] = reg[1] / reg[2]
        elif command == "XOR":
            reg[16] = reg[1] ^ reg[2]
            reg[16] = reg[1] ^ reg[2]
        elif command == "NOT":
            reg[16] = ~reg[1]
            reg[16] = ~reg[1]
        elif command == "OR":
            reg[16] = reg[1] | reg[2]
        elif command == "MOD":
            reg[16] = reg[1] % reg[2]
            reg[16] = reg[1] % reg[2]
        elif command == "POW":
            reg[16] = reg[1] ** reg[2]
            reg[16] = reg[1] ** reg[2]
        elif command == "PUSHA":
            exec(f"rom[{rom[position]}] = reg[{rom[position + 1]}]")
        elif command == "PUSH":
            NOEXEC = True
            reg[rom[position]] = rom[position + 1]
        elif command == "RCPY":
            reg[rom[position]] = reg[rom[position + 1]]
        elif command == "MCPY":
            memory[rom[position]] = memory[rom[position + 1]]
        elif command == "DEL":
            reg[rom[position]] = 0
        elif command == "DELM":
            memory[rom[position]] = ""
        elif command == "JUMP":
            position = rom[position]
        elif command == "CMP":
            NOEXEC = True
            a = rom[position]
            b = rom[position + 1]
            if a == b:
                reg[6] = True
            elif a != b:
                reg[6] = False

            if isinstance(a, float) or isinstance(a, int):
                if isinstance(b, float) or isinstance(b, int):
                    if a == 0:
                        reg[5] = True
                    elif a != 0:
                        reg[5] = False
                    if a > b:
                        reg[4] = True
                    elif a < b:
                        reg[4] = False
        elif command == "RCMP":
            a = reg[rom[position]]
            b = reg[rom[position + 1]]
            if a == b:
                reg[6] = True
            elif a != b:
                reg[6] = False
                
            if isinstance(a, float) or isinstance(a, int):
                if isinstance(b, float) or isinstance(b, int):
                    if a == 0:
                        reg[5] = True
                    elif a != 0:
                        reg[5] = False
                    if a > b:
                        reg[4] = True
                    elif a < b:
                        reg[4] = False
        elif command == "JG":
            if reg[4] == True:
                position = rom[position]
        elif command == "JL":
            if reg[4] == False:
                position = rom[position]
        elif command == "JE":
            if reg[6] == True:
                position = rom[position]
        
        elif command == "JZ":
            if reg[5] == True:
                position = rom[position]

        elif command == "JNZ":
            if reg[5] == False:
                position = rom[position]

        elif command == "JNE":
            if reg[6] == False:
                position = rom[position] - 1
        
        elif command == "INC":
            counter = rom[position]
            counters[counter] = counters[counter] + 1
        elif command == "DEC":
            counter = rom[position]
            counters[counter] = counters[counter] - 1
        elif command == "GCN":
            reg[13] = counters[rom[position]]
        elif command == "LABEL":
            LABEL_IN = True
        elif command == "SRET":
            RETP = position
        elif command == "RETC":
            position = RETP
        elif command == "SRA":
            RETP = rom[position]
        elif command == "NEW":
            NOEXEC = True
            if rom[position].lower() == "exception":
                exceptions.append({'C': rom[position + 1], 'N': rom[position + 2], 'D': rom[position + 3]})
        elif command == "RAISE":
            print(f"{exceptions[rom[position]]['N']}: {exceptions[rom[position]]['D']}\nERRNO: {exceptions[rom[position]]['C']}")
            RETCODE = exceptions[rom[position]]['C']
            position = len(rom)
        elif command == "GENV":
            var = rom[position]
            reg[3] = os.getenv(var)
        else:
            for e in INC_PREPRO:
                exec(f"""{e}""")

    elif command == "END DATA":
        NOEXEC = False
    elif command == "END LABEL":
        LABEL_IN = False
    
    position += 1  # Move to the next instruction

timeend = time.time_ns()
completion_time = timeend - timestart

if not QUIET:
    print("")
    print(f"Program execution completed in {'less than one' if completion_time == 0 else completion_time} ns.\nAnd returned a code of {RETCODE}\n")
    if not SIMPLE_MODE:
        print("Registers  : ", reg)
        print("Stack      : ", stack)
        print("Includes   : ", INCLUDES)
        print("Exceptions : ", exceptions)
        print("RetADDR    : ", RETP, "at ROM instruction:", rom[RETP - 1])
    if DUMP_MEM:
        with open("memory_" + args.dOut, "w") as fh:
            fh.write(str(memory))
    if DUMP_REG:
        with open("registers_" + args.dOut, "w") as fh:
            fh.write(str(reg))
    if DUMP_STA:
        with open("stack_" + args.dOut, "w") as fh:
            fh.write(str(stack))
