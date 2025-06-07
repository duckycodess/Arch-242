# arch242_emulator.py (modified version with logging)
import pyxel
from assembler.module import Arch242Assembler
import sys
import os
from datetime import datetime

def init(): #consider placing this as a separate file?
    if len(sys.argv) != 2:
        print("Usage: python arch242_emulator.py <input_file.asm | input_file.bin>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]

    arch242emu(input_file)

class arch242emu:

    # ---/ INITIALIZE PYXEL AND EMULATOR ELEMENTS /---

    def __init__(self, file):
        pyxel.init(720,320,title="Arch-242 LED Matrix", fps=250) #fps -> clock speed of emulator
        pyxel.load('assets/assets.pyxres')

        print("Initializing Emulator...")
        self.RA = 0b0000
        self.RB = 0b0000
        self.RC = 0b0000
        self.RD = 0b0000
        self.RE = 0b0000

        self.ACC = 0b0000
        self.IOA = 0b0000

        self.CF = 0b0
        self.EI = 0b0 #?
        self.TEMP = 0b0 

        self.CLOCK = 0
        self.CYCLESKIP = False #assuming 1 clock tick == 1 cycle for this implementation to work
        self.SHUTDOWN = False
        self.PC = 0

        self.LED = [
            [0,0,0,0], #0
            [1,0,0,0], #1
            [0,1,0,0], #2
            [1,1,0,0], #3
            [0,0,1,0], #4
            [1,0,1,0], #5
            [0,1,1,0], #6
            [1,1,1,0], #7
            [0,0,0,1], #8
            [1,0,0,1], #9
            [0,1,0,1], #10
            [1,1,0,1], #11
            [0,0,1,1], #12
            [1,0,1,1], #13
            [0,1,1,1], #14
            [1,1,1,1], #15
        ]

        self.LED_DEBUG = 0
        self.LED_EXP = 0
        self.DEBUG = False
        self.CURINST = ''
        self.TITLE = file[:-4]

        # ---/ LOGGING AND DEBUGGING FEATURES /---
        self.LOGGING_ENABLED = False
        self.DEBUG_MODE = True
        self.BREAKPOINT_HIT = False
        self.STEP_MODE = True
        self.LOG_FILE = None
        self.INSTRUCTION_COUNT = 0
        self.ASM_LINES = []  # Store original assembly lines
        self.PC_TO_LINE_MAP = {}  # Map PC to assembly line numbers
        self.MEMORY_ACCESSES = []  # Track memory accesses

        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            print(f"Created {logs_dir} directory")
        
        # Initialize log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(logs_dir, f"arch242_debug_{self.TITLE}_{timestamp}.log")
        try:
            self.LOG_FILE = open(log_filename, 'w')
            self.log_write(f"=== Arch-242 Emulator Debug Log ===")
            self.log_write(f"Program: {file}")
            self.log_write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_write("="*50)
            self.log_write("")
            print(f"Log file created: {log_filename}")
        except Exception as e:
            print(f"Warning: Could not create log file {log_filename}: {e}")
            self.LOGGING_ENABLED = False

        # ---/ ASSEMBLE & LOAD PROGRAM /---

        if file[-3:] == 'asm':
            print('Loaded assembly file!')
            asmfile = file
            
            # Read assembly file to store original lines
            try:
                with open(asmfile, 'r') as f:
                    self.ASM_LINES = f.readlines()
            except:
                self.ASM_LINES = []
            
            print('Initializing assembler...')
            assembler = Arch242Assembler()

            print('Assembler loaded! Assembling program...')
            output_data = assembler.assemble_code(asmfile, 'bin')
            assembler.write_output(output_data, asmfile, 'bin')

            binfile = f'{asmfile[:-4]}.bin'
            
            # Build PC to line number mapping
            self.build_pc_to_line_map(assembler)
        else:
            print('Loaded bin file!')
            binfile = file

        print('Loading program...')
        with open(binfile, 'rb') as bin:
            data = bin.read()
            self.ASM_MEM = [hex(byte) for byte in data]
            
        self.MEM = [0b0]*256

        print('Starting Emulator...')
        print("\n=== DEBUG CONTROLS ===")
        print("D - Toggle debug mode")
        print("S - Step mode (when in debug)")
        print("C - Continue (when paused)")
        print("L - Toggle logging")
        print("Q - Quit")
        print("=====================\n")
        
        pyxel.run(self.update, self.draw)

    def build_pc_to_line_map(self, assembler: Arch242Assembler):
        current_pc = 0
        
        for line_num, line in enumerate(self.ASM_LINES, 1):
            parsed = assembler.parse_line(line)
            if not parsed:
                continue
                
            assembler.current_line_number = line_num
            assembler.current_line_content = line
            
            command_type, data = parsed
            
            if command_type == 'label':
                continue
            elif command_type == 'inline_label':
                label, instruction_data = data
                parsed_instruction = assembler.parse_line(instruction_data)
                if parsed_instruction:
                    self.PC_TO_LINE_MAP[current_pc] = (line_num, line.strip())
                    _, instruction_info = parsed_instruction
                    if parsed_instruction[0] == 'byte':
                        current_pc += 1
                    elif parsed_instruction[0] == 'instruction':
                        encoded = assembler.encode_instruction(instruction_info, 1)
                        current_pc += len(encoded)
            elif command_type == 'byte':
                self.PC_TO_LINE_MAP[current_pc] = (line_num, line.strip())
                current_pc += 1
            elif command_type == 'instruction':
                self.PC_TO_LINE_MAP[current_pc] = (line_num, line.strip())
                encoded = assembler.encode_instruction(data, 1)
                current_pc += len(encoded)

    def log_write(self, message):
        if self.LOGGING_ENABLED and self.LOG_FILE:
            self.LOG_FILE.write(message + '\n')
            self.LOG_FILE.flush()

    def log_state_before_instruction(self):
        if not self.LOGGING_ENABLED:
            return
            
        self.log_write(f"\n{'='*60}")
        self.log_write(f"INSTRUCTION #{self.INSTRUCTION_COUNT} | PC: {self.PC} (0x{self.PC:04X})")
        
        # Get assembly line info
        if self.PC in self.PC_TO_LINE_MAP:
            line_num, line_content = self.PC_TO_LINE_MAP[self.PC]
            self.log_write(f"Assembly Line {line_num}: {line_content}")
        
        # Current instruction bytes
        if self.PC < len(self.ASM_MEM):
            inst_byte = self.ASM_MEM[self.PC]
            if self.PC + 1 < len(self.ASM_MEM) and self.is_two_byte_instruction(int(inst_byte, 16)):
                self.log_write(f"Instruction Byte(s): {inst_byte} {self.ASM_MEM[self.PC + 1]}")
            else:
                self.log_write(f"Instruction Byte(s): {inst_byte}")
        
        self.log_write(f"\n--- State BEFORE Execution ---")
        self.log_register_state()
        
    def log_state_after_instruction(self):
        if not self.LOGGING_ENABLED:
            return
            
        self.log_write(f"\n--- State AFTER Execution ---")
        self.log_write(f"Instruction Executed: {self.CURINST}")
        self.log_register_state()
        
        # Log memory accesses if any
        if self.MEMORY_ACCESSES:
            self.log_write(f"\nMemory Accesses:")
            for access in self.MEMORY_ACCESSES:
                self.log_write(f"  {access}")
            self.MEMORY_ACCESSES = []
        
        self.log_write(f"Next PC: {self.PC}")
        self.log_write("="*60)
        
    def log_register_state(self):
        self.log_write(f"Registers:")
        self.log_write(f"  RA: {self.RA:04b} ({self.RA:d})  RB: {self.RB:04b} ({self.RB:d})  RC: {self.RC:04b} ({self.RC:d})  RD: {self.RD:04b} ({self.RD:d})  RE: {self.RE:04b} ({self.RE:d})")
        self.log_write(f"  ACC: {self.ACC:04b} ({self.ACC:d})  CF: {self.CF}  IOA: {self.IOA:04b}")
        self.log_write(f"  TEMP: {self.TEMP:016b} ({self.TEMP:d})")
        
    def log_memory_access(self, address, value, is_write=False):
        access_type = "WRITE" if is_write else "READ"
        self.MEMORY_ACCESSES.append(f"{access_type} MEM[{address:03d} (0x{address:02X})] = {value:04b} ({value:d})")
        
    def is_two_byte_instruction(self, opcode):
        # Two-byte instructions based on your implementation
        if opcode == 0x37:  # shutdown first byte
            return True
        if 0x40 <= opcode <= 0x46:  # add, sub, and, xor, or, r4
            return True
        if 0x50 <= opcode <= 0x6F:  # rarb, rcrd
            return True
        if 0x80 <= opcode <= 0xFF:  # branch instructions
            return True
        return False

    # ---/ EMULATOR: INSTRUCTION MATCHING /---

    def read_inst(self, pc, inst):
        # Log state before execution
        self.log_state_before_instruction()
        self.INSTRUCTION_COUNT += 1
        
        val = int(inst[pc], base=16)

        if val <= 3: #(0-3): rot-r, rot-l, rot-rc, rot-lc
            self.a_inst(val)

        elif val <= 7: # (4-7): from-mba, to-mda, from-mdc, to-mdc
            self.b_inst(val)
        
        elif val <= 11: # (8-11): addc-mba, add-mba, subc-mba, sub-mba
            self.c_inst(val)

        elif val <= 25: # (12-25): inc*-mba, dec*-mba, inc*-mdc, dec*-mdc, inc*-reg, dec*-reg
            self.d_inst(val)

        elif val <= 31: # (26-31): and-ba, xor-ba, or-ba, and*-mba, xor*-mba, or*-mba
            self.e_inst(val)

        elif val <= 41: # (32 - 41): to-reg, from-reg
            self.f_inst(val) #shift this

        elif val <= 45: # (42-45): clr-cf, set-cf, set-ei, clr-ei
            self.g_inst(val)
        
        elif val <= 47: # (46-47): ret, retc (deprecated)
            self.ret()
                
        elif val <= 53: # (48-53): from-ioa, inc, to-ioa (deprecated), to-iob (deprecated), to-ioc (deprecated), undefined_inst#38 (deprecated)
            self.h_inst(val)

        elif val == 54: # (54): bcd
            self.bcd()

        elif val == 55: # (55): shutdown
            self.shutdown(int(inst[pc+1], base=16))

        elif val <= 61: # (56-61): timer-start, timer-end, from-timerl, from-timerh, to-timerl, to-timerh (deprecated)
            self.nop(1)

        elif val == 62: # (62): nop
            self.nop(1)
            # NOP used as breakpoint - pause execution
            if self.DEBUG_MODE:
                self.log_write("\n*** BREAKPOINT HIT AT NOP ***")
                self.BREAKPOINT_HIT = True
                self.STEP_MODE = True
                print("BREAKPOINT: Hit NOP instruction - Paused. Press 'S' to step or 'C' to continue.")

        elif val == 63: # (63): dec
            self.dec()

        elif val <= 71: # (64-71): add, sub, and, xor, or, undefined_inst#54, r4, timer
            self.i_inst(val)

        elif val <= 79: # (72-79): undefined instructions, YYY instructions (deprecated)
            self.nop(1)

        elif val <= 111: # (80-111): rarb, rcrd
            self.j_inst(val)

        elif val <= 127: # (127): acc
            self.acc(val)

        elif val <= 159: # (128-159): b-bit
            next_instruction = int(self.ASM_MEM[pc+1], base=16)
            self.b_bit(val, next_instruction)

        elif val <= 255: # (160-255): bnz-a, bnz-b, beqz, bnez, beqz-cf, bnez-cf, b-timer (deprecated), bnz-d, b, call
            self.k_inst(val)

        else: # unknown instruction
            print('illegal instruction detected')
            
        # Log state after execution
        self.log_state_after_instruction()

    # ---/ EMULATOR: EMULATED INSTRUCTIONS /---

    def a_inst(self, inst):
        if inst == 0: # rot-r
            swapbit = (self.ACC & 1)*8
            self.ACC = (self.ACC >> 1) + swapbit
            self.CURINST = 'rot-r'

        elif inst == 1: # rot-l
            swapbit = ((self.ACC >> 3) & 1)
            self.ACC = ((self.ACC << 1) & 0xF) + swapbit
            self.CURINST = 'rot-l'

        elif inst == 2: # rot-rc
            swapbit = self.CF*8
            self.CF = (self.ACC & 1)
            self.ACC = (self.ACC >> 1) + swapbit
            self.CURINST = 'rot-rc'

        elif inst == 3: # rot-lc
            swapbit = self.CF
            self.CF = ((self.ACC >> 3) & 1)
            self.ACC = ((self.ACC << 1) & 0xF) + swapbit
            self.CURINST = 'rot-lc'

        self.PC += 1

    def b_inst(self, inst):
        if inst == 4: # from-mba
            address = (self.RB << 4) + self.RA
            value = self.MEM[address] & 0xF
            self.log_memory_access(address, value, False)
            self.ACC = value
            self.CURINST = 'from-mba'

        elif inst == 5: # to-mba
            address = (self.RB << 4) + self.RA
            self.log_memory_access(address, self.ACC, True)
            self.MEM[address] = self.ACC
            self.CURINST = 'to-mba'

        elif inst == 6: # from-mdc
            address = (self.RD << 4) + self.RC
            value = self.MEM[address] & 0xF
            self.log_memory_access(address, value, False)
            self.ACC = value
            self.CURINST = 'from-mdc'

        elif inst == 7: # to-mdc
            address = (self.RD << 4) + self.RC
            self.log_memory_access(address, self.ACC, True)
            self.MEM[address] = self.ACC
            self.CURINST = 'to-mdc'

        self.PC += 1

    def c_inst(self, inst):
        if inst == 8: # addc-mba
            address = (self.RB << 4) + self.RA
            value = self.MEM[address]
            self.log_memory_access(address, value, False)
            calc = self.ACC + value + self.CF
            self.CF = (calc >> 4 & 1)
            self.ACC = calc & 0xF
            self.CURINST = 'addc-mba'

        elif inst == 9: # add-mba
            address = (self.RB << 4) + self.RA
            value = self.MEM[address]
            self.log_memory_access(address, value, False)
            calc = self.ACC + value
            self.CF = (calc >> 4 & 1)
            self.ACC = calc & 0xF
            self.CURINST = 'add-mba'

        elif inst == 10: # subc-mba
            address = (self.RB << 4) + self.RA
            value = self.MEM[address]
            self.log_memory_access(address, value, False)
            calc = self.ACC - value + self.CF
            self.CF = 1 if calc < 0 else 0
            self.ACC = calc & 0xF
            self.CURINST = 'subc-mba'

        elif inst == 11: # sub-mba
            address = (self.RB << 4) + self.RA
            value = self.MEM[address]
            self.log_memory_access(address, value, False)
            calc = self.ACC - value
            self.CF = 1 if calc < 0 else 0
            self.ACC = calc & 0xF
            self.CURINST = 'sub-mba'

        self.PC += 1

    def d_inst(self, inst): #WARN: ASSUMING EACH MEMORY ADDRESS HOLDS 4 BITS. IF NOT, CHANGE 0XF
        if inst == 12: # inc*mba
            address = (self.RB << 4) + self.RA
            old_value = self.MEM[address]
            new_value = (old_value + 1) & 0xF
            self.log_memory_access(address, old_value, False)
            self.log_memory_access(address, new_value, True)
            self.MEM[address] = new_value
            self.CURINST = 'inc*-mba'

        elif inst == 13: # dec*mba
            address = (self.RB << 4) + self.RA
            old_value = self.MEM[address]
            new_value = (old_value - 1) & 0xF
            self.log_memory_access(address, old_value, False)
            self.log_memory_access(address, new_value, True)
            self.MEM[address] = new_value
            self.CURINST = 'dec*-mba'

        elif inst == 14: # inc*mdc
            address = (self.RD << 4) + self.RC
            old_value = self.MEM[address]
            new_value = (old_value + 1) & 0xF
            self.log_memory_access(address, old_value, False)
            self.log_memory_access(address, new_value, True)
            self.MEM[address] = new_value
            self.CURINST = 'inc-mdc'

        elif inst == 15: # dec*mdc
            address = (self.RD << 4) + self.RC
            old_value = self.MEM[address]
            new_value = (old_value - 1) & 0xF
            self.log_memory_access(address, old_value, False)
            self.log_memory_access(address, new_value, True)
            self.MEM[address] = new_value
            self.CURINST = 'dec*-mdc'

        elif inst <= 25: 
            if inst == 16: # inc*-RA
                self.RA = (self.RA + 1) & 0xF
                self.CURINST = 'inc*-ra'
            elif inst == 17: # dec*-RA
                self.RA = (self.RA - 1) & 0xF
                self.CURINST = 'dec*-ra'
            elif inst == 18: # inc*-RB
                self.RB = (self.RB + 1) & 0xF
                self.CURINST = 'inc*-rb'
            elif inst == 19: # dec*-RB
                self.RB = (self.RB - 1) & 0xF
                self.CURINST = 'dec*-rb'
            elif inst == 20: # inc*-RC
                self.RC = (self.RC + 1) & 0xF
                self.CURINST = 'inc*-rc'
            elif inst == 21: # dec*-RC
                self.RC = (self.RC - 1) & 0xF
                self.CURINST = 'dec*-rc'
            elif inst == 22: # inc*-RD
                self.RD = (self.RD + 1) & 0xF
                self.CURINST = 'inc*-rd'
            elif inst == 23: # dec*-RD
                self.RD = (self.RD - 1) & 0xF
                self.CURINST = 'dec*-rd'
            elif inst == 24: # inc*-RE
                self.RE = (self.RE + 1) & 0xF
                self.CURINST = 'inc*-re'
            elif inst == 25: # dec*-RE
                self.RE = (self.RE - 1) & 0xF
                self.CURINST = 'dec*-re'

        self.PC += 1

    def e_inst(self, inst):
        if inst == 26: # and-ba
            address = (self.RB << 4) + self.RA
            value = self.MEM[address]
            self.log_memory_access(address, value, False)
            self.ACC = (self.ACC & value) & 0xF
            self.CURINST = 'and-ba'
        elif inst == 27: # xor-ba
            address = (self.RB << 4) + self.RA
            value = self.MEM[address]
            self.log_memory_access(address, value, False)
            self.ACC = (self.ACC ^ value) & 0xF
            self.CURINST = 'xor-ba'
        elif inst == 28: # or-ba
            address = (self.RB << 4) + self.RA
            value = self.MEM[address]
            self.log_memory_access(address, value, False)
            self.ACC = (self.ACC | value) & 0xF
            self.CURINST = 'or-ba'
        elif inst == 29: # and*-mba
            address = (self.RB << 4) + self.RA
            old_value = self.MEM[address]
            new_value = self.ACC & old_value
            self.log_memory_access(address, old_value, False)
            self.log_memory_access(address, new_value, True)
            self.MEM[address] = new_value
            self.CURINST = 'and*-mba'
        elif inst == 30: # xor*-mba
            address = (self.RB << 4) + self.RA
            old_value = self.MEM[address]
            new_value = self.ACC ^ old_value
            self.log_memory_access(address, old_value, False)
            self.log_memory_access(address, new_value, True)
            self.MEM[address] = new_value
            self.CURINST = 'xor*-mba'
        elif inst == 31: # or*-mba
            address = (self.RB << 4) + self.RA
            old_value = self.MEM[address]
            new_value = self.ACC | old_value
            self.log_memory_access(address, old_value, False)
            self.log_memory_access(address, new_value, True)
            self.MEM[address] = new_value
            self.CURINST = 'or*-mba'

        self.PC += 1

    # Keep all other instruction methods the same, but add memory logging where appropriate
    # For brevity, I'll show the pattern for a few more methods

    def f_inst(self, inst):
        if inst == 32: # to-RA
            self.RA = self.ACC
            self.CURINST = 'to-ra'
        elif inst == 33: # from-RA
            self.ACC = self.RA
            self.CURINST = 'from-ra'
        elif inst == 34: # to-RB
            self.RB = self.ACC
            self.CURINST = 'to-rb'
        elif inst == 35: # from-RB
            self.ACC = self.RB
            self.CURINST = 'from-rb'
        elif inst == 36: # to-RC
            self.RC = self.ACC
            self.CURINST = 'to-rc'
        elif inst == 37: # from-RC
            self.ACC = self.RC
            self.CURINST = 'from-rc'
        elif inst == 38: # to-RD
            self.RD = self.ACC
            self.CURINST = 'to-rd'
        elif inst == 39: # from-RD
            self.ACC = self.RD
            self.CURINST = 'from-rd'
        elif inst == 40: # to-RE
            self.RE = self.ACC
            self.CURINST = 'to-re'
        elif inst == 41: # from-RE
            self.ACC = self.RE
            self.CURINST = 'from-re'

        self.PC += 1

    def g_inst(self, inst):
        if inst == 42: #clr-cf
            self.CF = 0 
            self.CURINST = 'clr-cf'
        elif inst == 43: #set-cf
            self.CF = 1
            self.CURINST = 'set-cf'
        elif inst == 44: #set-ei
            self.EI = 1
            self.CURINST = 'set-ei'
        elif inst == 45: #clr-ei
            self.EI = 0
            self.CURINST = 'clr-ei'

        self.PC += 1

    def ret(self):
        self.PC = ((self.PC >> 12) << 12) + (self.TEMP & 0xFFF)
        self.TEMP = 0
        self.CURINST = 'ret'

    def h_inst(self, inst):
        if inst == 48: # -
            self.nop(1)
        elif inst == 49: # inc
            self.ACC = (self.ACC + 1) & 0xF
            self.CURINST = 'inc'
        elif inst == 50: # from-ioa
            self.ACC = self.IOA
            self.CURINST = 'from-ioa'
        elif inst == 51: # -
            self.nop(1)
        elif inst == 52: # -
            self.nop(1)
        elif inst == 53: # -
            self.nop(1)
    
        self.PC += 1

    def bcd(self): # bcd
        if self.ACC >= 10 or self.CF:
            self.ACC = (self.ACC + 6) & 0xF
            self.CF = 1
            self.CURINST = 'bcd'
        
        self.PC += 1

    def shutdown(self, inst2): # shutdown
        if inst2 == 62:
            print('Closing emulator...')
            self.log_write("\n*** SHUTDOWN INSTRUCTION EXECUTED ***")
            self.PC += 2
            self.CYCLESKIP = True
            self.SHUTDOWN = True
            self.CURINST = 'shutdown'
        else:
            print('illegal instruction detected')

    def nop(self, bitwidth): # nop
        if bitwidth == 1:
            self.PC += 1
        elif bitwidth == 2:
            self.PC += 2
        self.CURINST = 'nop'

    def dec(self): # dec
        self.ACC = (self.ACC - 1) & 0xF
        self.PC += 1
        self.CURINST = 'dec'

    def i_inst(self, inst):
        next_instruction = int(self.ASM_MEM[self.PC+1], base=16)

        if inst == 64: # add imm
            result = self.ACC + (next_instruction & 0xF)
            self.ACC = result & 0xF
            self.CURINST = f'add {next_instruction & 0xF}'
        elif inst == 65: # sub imm
            result = self.ACC - (next_instruction & 0xF)
            self.ACC = result & 0xF
            self.CURINST = f'sub {next_instruction & 0xF}'
        elif inst == 66: # and imm
            self.ACC = self.ACC & (next_instruction & 0xF)
            self.CURINST = f'and {next_instruction & 0xF}'
        elif inst == 67: # xor imm
            self.ACC = self.ACC ^ (next_instruction & 0xF)
            self.CURINST = f'xor {next_instruction & 0xF}'
        elif inst == 68: # or imm
            self.ACC = self.ACC | (next_instruction & 0xF)
            self.CURINST = f'or {next_instruction & 0xF}'
        elif inst == 69: # -
            self.nop(1)
        elif inst == 70: # r4 imm
            self.RE = next_instruction & 0xF
            self.CURINST = f'r4 {next_instruction & 0xF}'
        elif inst == 71: # -
            self.nop(1)

        if not (inst == 69 or inst == 71):
            self.CYCLESKIP = True
            self.PC += 2   

    def j_inst(self, inst):
        next_instruction = int(self.ASM_MEM[self.PC+1], base=16)
        if 80 <= inst <= 95: # rarb
            self.RA = (inst - 80) & 0xF
            self.RB = next_instruction & 0xF
            self.CURINST = f'rarb {((next_instruction & 0xF) << 4) | ((inst - 80) & 0xF)}'
        elif 96 <= inst <= 111: # rcrd
            self.RC = (inst - 96) & 0xF
            self.RD = next_instruction & 0xF
            self.CURINST = f'rcrd {((next_instruction & 0xF) << 4) | ((inst - 96) & 0xF)}'
        
        self.CYCLESKIP = True    
        self.PC += 2
        
    def acc(self, inst): # acc
        self.ACC = (inst-112)
        self.CURINST = f'acc {inst-112}'
        self.PC += 1

    def b_bit(self, inst, next_instruction): # b-bit
        bit_position = (inst >> 3) & 0x3
        if (self.ACC >> bit_position) & 1:
            address = ((inst & 0x7) << 8) | next_instruction
            self.PC = (self.PC & 0xF800) | address
            self.CURINST = f'b-bit {bit_position} {address} (taken)'
        else:
            self.PC += 2
            self.CURINST = f'b-bit {bit_position} {((inst & 0x7) << 8) | next_instruction} (not taken)'

        self.CYCLESKIP = True

    def k_inst(self, inst):
        next_instruction = int(self.ASM_MEM[self.PC+1], base=16)

        def decode_next_address(offset: int =0xF800):
            address = ((inst & 0x7) << 8) | next_instruction
            return (self.PC & offset) | address

        if 160 <= inst <= 167: # bnz-a imm
            target = decode_next_address()
            if self.RA != 0:
                self.PC = target
                self.CURINST = f'bnz-a {target & 0x7FF} (taken)'
            else:
                self.PC += 2
                self.CURINST = f'bnz-a {target & 0x7FF} (not taken)'
        elif 168 <= inst <= 175: # bnz-b imm
            target = decode_next_address()
            if self.RB != 0:
                self.PC = target
                self.CURINST = f'bnz-b {target & 0x7FF} (taken)'
            else:
                self.PC += 2
                self.CURINST = f'bnz-b {target & 0x7FF} (not taken)'
        elif 176 <= inst <= 183: # beqz imm
            target = decode_next_address()
            if self.ACC == 0:
                self.PC = target
                self.CURINST = f'beqz {target & 0x7FF} (taken)'
            else:
                self.PC += 2
                self.CURINST = f'beqz {target & 0x7FF} (not taken)'
        elif 184 <= inst <= 191: # bnez imm
            target = decode_next_address()
            if self.ACC != 0:
                self.PC = target
                self.CURINST = f'bnez {target & 0x7FF} (taken)'
            else:
                self.PC += 2
                self.CURINST = f'bnez {target & 0x7FF} (not taken)'
        elif 192 <= inst <= 199: # beqz-cf imm
            target = decode_next_address()
            if self.CF == 0:
                self.PC = target
                self.CURINST = f'beqz-cf {target & 0x7FF} (taken)'
            else:
                self.PC += 2
                self.CURINST = f'beqz-cf {target & 0x7FF} (not taken)'
        elif 200 <= inst <= 207: # bnez-cf imm
            target = decode_next_address()
            if self.CF != 0:
                self.PC = target
                self.CURINST = f'bnez-cf {target & 0x7FF} (taken)'
            else:
                self.PC += 2
                self.CURINST = f'bnez-cf {target & 0x7FF} (not taken)'
        elif 208 <= inst <= 215: # -
            self.nop(1)
        elif 216 <= inst <= 223: # bnz-d
            target = decode_next_address()
            if self.RD != 0:
                self.PC = target
                self.CURINST = f'bnz-d {target & 0x7FF} (taken)'
            else:
                self.PC += 2
                self.CURINST = f'bnz-d {target & 0x7FF} (not taken)'
        elif 224 <= inst <= 239: # b
            target = decode_next_address(0xF000)
            self.PC = target
            self.CURINST = f'b {target & 0xFFF}'

        elif 240 <= inst <= 255: # call
            target = decode_next_address(0xF000)
            self.TEMP = self.PC + 2
            self.PC = target
            self.CURINST = f'call {target & 0xFFF}'

        self.CYCLESKIP = True

    # ---/ LED MATRIX DEBUG /---

    def LED_CHECK(self):
        if self.LED_DEBUG + 192 <= 241:
            if self.MEM[192 + self.LED_DEBUG] == 8:
                self.MEM[192 + self.LED_DEBUG] = 0
                self.LED_DEBUG += 1
                self.LED_EXP = 0

            self.MEM[192 + self.LED_DEBUG] = 2**self.LED_EXP
            self.LED_EXP += 1
        else:
            self.LED_DEBUG = 0

        print(f'Memory of Memory Address {192 + self.LED_DEBUG}: {bin(self.MEM[192 + self.LED_DEBUG])}')

    # ---/ KEYBOARD IO + EMULATOR ROOT CODE /---

    def update(self):
        # Handle debug controls
        if pyxel.btnp(pyxel.KEY_D):
            self.DEBUG_MODE = not self.DEBUG_MODE
            self.DEBUG = self.DEBUG_MODE  # Keep compatibility with existing DEBUG flag
            print(f"Debug mode: {'ON' if self.DEBUG_MODE else 'OFF'}")
            self.log_write(f"\n*** DEBUG MODE {'ENABLED' if self.DEBUG_MODE else 'DISABLED'} ***")
            
        if pyxel.btnp(pyxel.KEY_L):
            self.LOGGING_ENABLED = not self.LOGGING_ENABLED
            print(f"Logging: {'ON' if self.LOGGING_ENABLED else 'OFF'}")
            
        if self.DEBUG_MODE and self.STEP_MODE:
            if pyxel.btnp(pyxel.KEY_S):
                # Execute one instruction
                pass  # Will continue to execution below
            elif pyxel.btnp(pyxel.KEY_C):
                self.STEP_MODE = False
                self.BREAKPOINT_HIT = False
                print("Continuing execution...")
            else:
                return  # Don't execute if in step mode and no step command

        #emulator runs here
        self.CLOCK += 1

        if not self.CYCLESKIP:
            if self.PC < len(self.ASM_MEM) and not self.SHUTDOWN:
                self.read_inst(self.PC, self.ASM_MEM)

            if self.SHUTDOWN:
                # Close log file before quitting
                if self.LOG_FILE:
                    self.log_write(f"\n=== Emulator Shutdown ===")
                    self.log_write(f"Total instructions executed: {self.INSTRUCTION_COUNT}")
                    self.log_write(f"Final PC: {self.PC}")
                    self.log_write(f"Clock cycles: {self.CLOCK}")
                    self.LOG_FILE.close()
                quit()
        else:
            self.CLOCK += 1
            self.CYCLESKIP = False

        #IO check
        self.IOA &= 0b0000

        if pyxel.btn(pyxel.KEY_UP):
            self.IOA |= 1
        if pyxel.btn(pyxel.KEY_DOWN):
            self.IOA |= 2
        if pyxel.btn(pyxel.KEY_LEFT):
            self.IOA |= 4
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.IOA |= 8

        if pyxel.btn(pyxel.KEY_Q):
            print("Quitting Emulator...")
            # Close log file before quitting
            if self.LOG_FILE:
                self.log_write(f"\n=== Emulator Quit by User ===")
                self.log_write(f"Total instructions executed: {self.INSTRUCTION_COUNT}")
                self.log_write(f"Final PC: {self.PC}")
                self.log_write(f"Clock cycles: {self.CLOCK}")
                self.LOG_FILE.close()
            quit()

        #print(f'Current value of IOA: {bin(self.IOA)}') # IO DEBUG
        #self.LED_CHECK() #LED DEBUG
        
    # ---/ LED MATRIX DRAW CODE /---

    def draw(self):
        pyxel.cls(0)

        rowval = 0
        colval = 0
        j = 192

        for i in self.MEM[192:242]:
            if colval == 20: 
                rowval += 1
                colval = 0

            for c,k in enumerate(self.LED[i]):
                if k:
                    pyxel.blt((c+colval)*32,rowval*32,0,32,0,32,32,0)
                else:
                    pyxel.blt((c+colval)*32,rowval*32,0,0,0,32,32,0)

                if self.DEBUG:
                    pyxel.text((c+colval)*32, rowval*32, f'({c+colval},{rowval})', 3)
                    pyxel.text((c+colval)*32, rowval*32 + 8, f'({j})', 3)

            colval += 4
            j += 1

        # ---/ DEBUG INFORMATION DRAW CODE /---

        pyxel.text(640, 2, 'Arch-242 Emulator', 3)

        # Add debug status indicators
        if self.DEBUG_MODE:
            pyxel.text(640, 10, '[DEBUG MODE]', 8)
        if self.STEP_MODE:
            pyxel.text(640, 10, '[STEP MODE]', 11)
        if self.LOGGING_ENABLED:
            pyxel.text(720-50, 2, '[LOG ON]', 10)

        pyxel.text(640, 18, 'Program Name:', 3)
        pyxel.text(640, 26, self.TITLE, 3)

        pyxel.text(640, 42, 'Current Instruction:', 3)

        if self.PC < len(self.ASM_MEM):
            pyxel.text(640, 50, self.CURINST, 3)
        else:
            pyxel.text(640, 50, 'END OF PROGRAM', 3)

        pyxel.text(640, 66, 'CPU CLOCK COUNT:', 3)
        pyxel.text(640, 74, str(self.CLOCK), 3)

        pyxel.text(640, 90, 'PROGRAM COUNTER:', 3)
        pyxel.text(640, 98, str(self.PC), 3)

        pyxel.text(640, 114, 'REGISTERS:', 3)

        pyxel.text(640, 130, f'ACC: {bin(self.ACC)}', 3)

        pyxel.text(640, 146, f'RA: {bin(self.RA)}', 3)
        pyxel.text(640, 154, f'RB: {bin(self.RB)}', 3)
        pyxel.text(640, 162, f'RC: {bin(self.RC)}', 3)
        pyxel.text(640, 170, f'RD: {bin(self.RD)}', 3)
        pyxel.text(640, 178, f'RE: {bin(self.RE)}', 3)

        pyxel.text(640, 194, f'IOA: {bin(self.IOA)}', 3)
        pyxel.text(640, 202, f'TEMP: {bin(self.TEMP)}', 3)
        pyxel.text(640, 210, f'CF: {bin(self.CF)}', 3)
        pyxel.text(640, 218, f'EI: {bin(self.EI)}', 3)

        # Add instruction count
        pyxel.text(640, 234, f'INST#: {self.INSTRUCTION_COUNT}', 3)

        # Debug controls reminder
        if self.DEBUG_MODE:
            pyxel.text(640, 250, 'Controls:', 3)
            pyxel.text(640, 258, 'S-Step C-Continue', 3)
            pyxel.text(640, 266, 'D-Debug L-Log Q-Quit', 3)

        # Breakpoint indicator
        if self.BREAKPOINT_HIT:
            pyxel.rect(635, 280, 80, 20, 8)
            pyxel.text(640, 285, 'BREAKPOINT!', 7)

    def __del__(self):
        if hasattr(self, 'LOG_FILE') and self.LOG_FILE:
            self.LOG_FILE.close()

if __name__ == "__main__":
    init()