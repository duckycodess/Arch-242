import pyxel
import os
from assembler import Arch242Assembler

#implementation details here

# instruction addresses -> 16 bits -> 2 bytes
# memory addresses -> 8 bits -> 1 byte

# an instruction is 1 or 2 bytes
# pc + 1 or 2 bytes depending on the last instruction unless branch instruction

# Main registers, 6 in total, 4 bits
#   0 -> RA
#   1 -> RB
#   2 -> RC
#   3 -> RD
#   4 -> RE
#   5 -> RD

# Special registers
#   ACC -> Stores result of most instr. 4 bits
#   CF  -> Carry flag. 1 bit

# IO Registers, 4 bits
#   IOA
#   IOB
#   IOC

# Miscellaneous Information

# TIMER -> 8-bit timer
# Incremented by 1 every 4 positive clock edges, set PC -> 4

# All + and - operations discard most significant bits past destination register bit width if overflowing

# Memory address 192 -> 255 memory-mapped to LED Matrix
# Each nibble correspond to an LED 

# phase 1: arch242 emulator

class arch242emu():
    def __init__(self, binfile):
        #initialize registers and other components
        #will be in binary for now, but ill see if i can just somehow convert them into integers during emulation process

        self.RA = 0b0000
        self.RB = 0b0000
        self.RC = 0b0000
        self.RD = 0b0000
        self.RE = 0b0000

        self.ACC = 0b0000
        self.IOA = 0b0000
        self.IOB = 0b0000
        self.IOC = 0b0000

        self.TIMER = 0b00000000
        self.CF = 0b0

        self.EI = 0b0 #?

        self.PC = 0 #use this to iterate through ASM_MEM

        #retrieve the asm file and store it into ASM_MEM
        #note: this assumes that the bin file will be fed directly into the emulator, which isnt the case in the project specificiations.
        # If it were to take in a .asm file, then link the assembler.py file here and work on the assembled code after
        with open(binfile, 'rb') as bin:
            data = bin.read()

            PRE_MEM = [hex(byte) for byte in data]

            print("wait")

            self.ASM_MEM = self.preprocess_mem(PRE_MEM)
            
        MEM = [0b00000000]*256 #assuming byte-addressible memory

        while self.PC != len(self.ASM_MEM): #missing edge case: shutdown instruction
            self.read_inst(self.PC, self.ASM_MEM)
            # self.PC += 1 # this will fuck up branch instructions, better to put this inside individual instruction functions maybe?

    def preprocess_mem(self, asm):
        #notes for unfixed_instruction ranges:
        # rarb: 80 -> 95 (als rcrd??? how tf do we differentiate between the two)
        # rcrd: 96 -> 111 (assuming rcrd is actually 0110XXXX)
        # b-bit: 128 -> 159
        # bnz-a: 160 -> 167
        # bnz-b: 168 -> 175
        # beqz: 176 -> 183
        # bnez: 184 -> 191
        # beqz-cf: 192 -> 199
        # bnez-cf: 200 -> 207
        # b-timer: 208 -> 215
        # bnz-d: 216 -> 223
        # b: 224 -> 239
        # call: 240 -> 255

        fixed_inst = [55, 64, 65, 66, 67, 68, 69, 70, 71]
        processed = []

        i = 0
        while i < len(asm):
            val = int(asm[i], base=16)
            if val in fixed_inst:
                processed.append((asm[i], asm[i+1]))
                i += 2
            elif ((80 <= val) and (val <= 111)) or val >= 128:
                processed.append((asm[i], asm[i+1]))
                i += 2
            else:
                processed.append((asm[i],))
                i += 1

        return processed


    def read_inst(self, pc, inst):
        #read instruction from ASM_MEM
        #check case is in order of instructions listed in the project specification page
        #note: remove print statements when everything is done(or leave them in as debug messages?)

        # group 1 (0-3):
        # rot-r, rot-l, rot-rc, rot-lc
        val = int(inst[pc][0], base=16) #use int(inst[pc][1] to access 2 byte instruction's second byte)
        if val <= 3:
            print('group 1 instruction detected')
            self.a_inst(val)

        # group 2 (4-7):
        # from-mba, to-mda, from-mdc, to-mdc
        elif val <= 7:
            print('group 2 instruction detected')
            self.b_inst(val)

        # group 3 (8-11):
        # addc-mba, add-mba, subc-mba, sub-mba
        elif val <= 11:
            print('group 3 instruction detected')
            self.c_inst(val)

        # group 4 (12-25):
        # inc*-mba, dec*-mba, inc*-mdc, dec*-mdc, inc*-reg, dec*-reg
        elif val <= 25:
            print('group 4 instruction detected')
            self.d_inst(val)

        # group 5 (26-31):
        # and-ba, xor-ba, or-ba, and*-mba, xor*-mba, or*-mba
        elif val <= 31:
            print('group 5 instruction detected')
            self.e_inst(val)

        # group 6 (32 - 41):
        # to-reg, from-reg
        elif val <= 41:
            print('group 6 instruction detected')
            self.e_inst(val)

        # group 7 (42-45):
        # clr-cf, set-cf, set-ei, clr-ei
        elif val <= 45:
            print('group 7 instruction detected')
            self.f_inst(val)

        # group 8 (46-47):
        # ret, retc
        elif val <= 47:
            print('group 8 instruction detected')
            self.g_inst(val)
                
        # group 9 (48-52):
        # from-pa, inc, to-ioa, to-iob, to-ioc, undefined_inst#38
        elif val <= 53:
            print('group 9 instruction detected')
            self.h_inst(val)

        elif val == 54:
            print('bcd detected')

        elif val == 55:
            print('shutdown detected')
            self.shutdown(int(inst[pc][1], base=16))

        # group 10 (56-57):
        # timer-start, timer-end
        elif val <= 57:
            print('group 10 instruction detected')
            self.i_inst(val)

        # group 11 (58-61):
        # from-timerl, from-timerh, to-timerl, to-timerh
        elif val <= 61:
            print('group 11 instruction detected')
            self.j_inst(val)

        elif val == 62:
            print('nop detected')

        elif val == 63:
            print('dec detected')

        # group 12 (64-71):
        # add, sub, and, xor, or, undefined_inst#54, r4, timer
        elif val <= 71:
            print('group 12 instruction detected')
            self.k_inst(val)

        # group 13 (72-79)
        # undefined instructions
        elif val <= 79:
            print('group 13 instruction detected')
            self.l_inst(val)

        # group 14 (80-111):
        # rarb, rcrd
        elif val <= 111:
            print('group 14 instruction detected')
            self.m_inst(val)

        elif val <= 127:
            print('acc detected')
            self.acc(val)

        elif val <= 159:
            print('b-bit detected')

        # group 15 (160-255):
        # bnz-a, bnz-b, beqz, bnez, beqz-cf, bnez-cf, b-timer, bnz-d, b, call
        elif val <= 255:
            print('group 15 instruction detected')
            self.n_inst(val)

        # individual instructions:
        # bcd, shutdown, nop, dec, YYY, acc, b-bit

        else: # unknown instruction
            print('illegal instruction detected')

    def _overflowe(self, val): #for overflow fixing
        #this might be problematic btw
        # if val >= 16:
        #     return val-16
        # else:
        #     return val

        #really shitty workaround for now, i cant math
        if val >= 16:
            conv = bin(val)
            return int(conv[-4:], base=2)
        else:
            return val

    def a_inst(self, inst):
        if inst == 0:
            swapbit = (self.ACC & 1)*8
            self.ACC = (self.ACC >> 1) + swapbit

        elif inst == 1:
            swapbit = ((self.ACC >> 3) & 1)
            self.ACC = self._overflowe(self.ACC << 1) + swapbit

        elif inst == 2:
            swapbit = self.CF*8
            self.CF = (self.ACC & 1)
            self.ACC = (self.ACC >> 1) + swapbit

        elif inst == 3:
            swapbit = self.CF
            self.CF = ((self.ACC >> 3) & 1)
            self.ACC = self._overflowe(self.ACC << 1) + swapbit

        self.PC += 1

    def b_inst(self, inst):
        ...

    def c_inst(self, inst):
        ...

    def d_inst(self, inst):
        ...

    def e_inst(self, inst):
        ...

    def f_inst(self, inst):
        if inst == 42:
            self.CF = 0
        elif inst == 43:
            self.CF = 1
        elif inst == 44:
            self.EI = 1
        elif inst == 45:
            self.EI = 0

        self.PC += 1

    def g_inst(self, inst):
        ...

    def h_inst(self, inst):
        ...

    def i_inst(self, inst):
        ...

    def j_inst(self, inst):
        ...

    def k_inst(self, inst):
        ...

    def l_inst(self, inst):
        ...

    def m_inst(self, inst):
        ...

    def n_inst(self, inst):
        ...

    def bcd(self):
        if self.ACC >= 10 or self.CF:
            self.ACC = self._overflowe(self.ACC + 6)
            self.CF = 1

    def shutdown(self, inst2):
        if inst2 == 62:
            print('closing emulator...')
            self.PC += 1
            quit()
        else:
            print('illegal instruction detected')

    def acc(self, inst):
        self.ACC = (inst-112)
        self.PC += 1

# phase 2: Pyxel window for LED Matrix (i think the emulator has to be inside here now that i think about it...)

class window():
    def __init__(self):
        pyxel.init(512,512,title="Arch-242 LED Matrix")
        pyxel.run(self.update, self.draw)

    def update(self):
        #only supports arrow keys, although the project specificiations mentions having a keyboard for an I/O. Ill deal with that next time.
        #somehow probe all of these into the emulator. Future me will handle this I trust
        if pyxel.btn(pyxel.KEY_UP):
            print("UP KEY PRESSED")
        elif pyxel.btn(pyxel.KEY_DOWN):
            print("DOWN KEY PRESSED")
        elif pyxel.btn(pyxel.KEY_LEFT):
            print("LEFT KEY PRESSED")
        elif pyxel.btn(pyxel.KEY_RIGHT):
            print("RIGHT KEY PRESSED")

    def draw(self):
        #TODO: Make a 20x10 column LED Matrix.
        #somehow probe all of these into the emulator. Future me will handle this I trust
        pyxel.cls(0)

arch242emu('test2.bin')
window()

    