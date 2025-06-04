import pyxel
import os

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
#   5 -> RF

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

# phase 1: arch242 emulator (inside Pyxel class)


# phase 2: Pyxel window for LED Matrix (i think the emulator has to be inside here now that i think about it...)
#NOTE: If theres an error: [pyo3_runtime.PanicException: Unknown resource file version] when running this in Visual Studio Code, run this in the terminal instead...

class window():
    def __init__(self, binfile):
        pyxel.init(320,640,title="Arch-242 LED Matrix")
        pyxel.load('assets/assets.pyxres')
        #initialize registers and other components
        #will be in binary for now, but ill see if i can just somehow convert them into integers during emulation process

        #sidenote: taena i assumed for now na positive ints lang ung data sa mga registers
        # if it supports 2c numbers im going to end it all

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
        self.TACTIVE = False
        self.CF = 0b0

        self.EI = 0b0 #?
        self.PA = 0b0 #?

        self.PC = 0 #use this to iterate through ASM_MEM

        #retrieve the asm file and store it into ASM_MEM
        #note: this assumes that the bin file will be fed directly into the emulator, which isnt the case in the project specificiations.
        # If it were to take in a .asm file, then link the assembler.py file here and work on the assembled code after
        with open(binfile, 'rb') as bin:
            data = bin.read()

            self.ASM_MEM = [hex(byte) for byte in data]

            #PRE_MEM = [hex(byte) for byte in data]
            #self.ASM_MEM = self.preprocess_mem(PRE_MEM)
            
        self.MEM = [0b00000000]*256 #assuming byte-addressible memory

    # def preprocess_mem(self, asm): #unused
    #     #notes for unfixed_instruction ranges:
    #     # rarb: 80 -> 95 (als rcrd??? how tf do we differentiate between the two)
    #     # rcrd: 96 -> 111 (assuming rcrd is actually 0110XXXX)
    #     # b-bit: 128 -> 159
    #     # bnz-a: 160 -> 167
    #     # bnz-b: 168 -> 175
    #     # beqz: 176 -> 183
    #     # bnez: 184 -> 191
    #     # beqz-cf: 192 -> 199
    #     # bnez-cf: 200 -> 207
    #     # b-timer: 208 -> 215
    #     # bnz-d: 216 -> 223
    #     # b: 224 -> 239
    #     # call: 240 -> 255

    #     fixed_inst = [55, 64, 65, 66, 67, 68, 69, 70, 71]
    #     processed = []

    #     i = 0
    #     while i < len(asm):
    #         val = int(asm[i], base=16)
    #         if val in fixed_inst:
    #             processed.append((asm[i], asm[i+1]))
    #             i += 2
    #         elif ((80 <= val) and (val <= 111)) or val >= 128:
    #             processed.append((asm[i], asm[i+1]))
    #             i += 2
    #         else:
    #             processed.append((asm[i],))
    #             i += 1

    #     return processed


        pyxel.run(self.update, self.draw)

    def read_inst(self, pc, inst):
        #read instruction from ASM_MEM
        #check case is in order of instructions listed in the project specification page
        #note: remove print statements when everything is done(or leave them in as debug messages?)

        #val = int(inst[pc][0], base=16) #use int(inst[pc][1] to access 2 byte instruction's second byte)
        val = int(inst[pc], base=16)

        # group 1 (0-3):
        # rot-r, rot-l, rot-rc, rot-lc
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
            self.bcd()

        elif val == 55:
            print('shutdown detected')
            #self.shutdown(int(inst[pc][1], base=16))
            self.shutdown(int(inst[pc+1], base=16))

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
            self.nop(1)

        elif val == 63:
            print('dec detected')
            self.dec()

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
            #next_instruction = int(self.ASM_MEM[pc][1], base=16)
            next_instruction = int(self.ASM_MEM[pc+1], base=16)
            self.b_bit(val, next_instruction)

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

    #TODO: _underflowe

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
        if inst == 4:
            self.ACC = self.MEM[(self.RB << 4) + self.RA]

        elif inst == 5:
            self.MEM[(self.RB << 4) + self.RA] = self.ACC

        elif inst == 6:
            self.ACC = self.MEM[(self.RD << 4) + self.RC]

        elif inst == 7:
            self.MEM[(self.RD << 4) + self.RC] = self.ACC

        self.PC += 1


    def c_inst(self, inst):
        if inst == 8:
            calc = self.ACC + self.MEM[(self.RB << 4) + self.RA] + self.CF
            self.CF = (calc >> 4 & 1)
            self.ACC = self._overflowe(calc)

        elif inst == 9:
            calc = self.ACC + self.MEM[(self.RB << 4) + self.RA]
            self.CF = (calc >> 4 & 1)
            self.ACC = self._overflowe(calc)

        elif inst == 10:
            calc = self.ACC - self.MEM[(self.RB << 4) + self.RA] + self.CF
            self.CF = (calc >> 4 & 1) #paano ba undeflow bit?
            self.ACC = self._overflowe(calc) #might not work?

        elif inst == 11:
            calc = self.ACC - self.MEM[(self.RB << 4) + self.RA]
            self.CF = (calc >> 4 & 1) #paano ba undeflow bit?
            self.ACC = self._overflowe(calc) #might not work?

        self.PC += 1

    def d_inst(self, inst):
        if inst == 12:
            self.MEM[(self.RB << 4) + self.RA] = self._overflowe(self.MEM[(self.RB << 4) + self.RA] + 1)

        elif inst == 13:
            self.MEM[(self.RB << 4) + self.RA] = self._overflowe(self.MEM[(self.RB << 4) + self.RA] - 1) #TODO: underflow

        elif inst == 14:
            self.MEM[(self.RD << 4) + self.RC] = self._overflowe(self.MEM[(self.RD << 4) + self.RC] + 1)

        elif inst == 15:
            self.MEM[(self.RD << 4) + self.RC] = self._overflowe(self.MEM[(self.RD << 4) + self.RC] - 1) #TODO: underflow

        elif inst <= 25:
            #panget neto amp
            if inst == 16:
                self.RA = self._overflowe(self.RA + 1)
            elif inst == 17:
                self.RA = self._overflowe(self.RA - 1) #TODO: underflow
            elif inst == 18:
                self.RB = self._overflowe(self.RB + 1)
            elif inst == 19:
                self.RB = self._overflowe(self.RB - 1) #TODO: underflow
            elif inst == 20:
                self.RC = self._overflowe(self.RC + 1)
            elif inst == 21:
                self.RC = self._overflowe(self.RC - 1) #TODO: underflow
            elif inst == 22:
                self.RD = self._overflowe(self.RD + 1)
            elif inst == 23:
                self.RD = self._overflowe(self.RD - 1) #TODO: underflow
            elif inst == 24:
                self.RE = self._overflowe(self.RE + 1)
            elif inst == 25:
                self.RE = self._overflowe(self.RE - 1) #TODO: underflow

        self.PC += 1

    def e_inst(self, inst):
        if inst == 26:
            self.ACC = self.ACC & self.MEM[(self.RB << 4) + self.RA]
        elif inst == 27:
            self.ACC = self.ACC ^ self.MEM[(self.RB << 4) + self.RA]
        elif inst == 28:
            self.ACC = self.ACC | self.MEM[(self.RB << 4) + self.RA]
        elif inst == 29:
            self.MEM[(self.RB << 4) + self.RA] = self.ACC & self.MEM[(self.RB << 4) + self.RA]
        elif inst == 30:
            self.MEM[(self.RB << 4) + self.RA] = self.ACC ^ self.MEM[(self.RB << 4) + self.RA]
        elif inst == 31:
            self.MEM[(self.RB << 4) + self.RA] = self.ACC | self.MEM[(self.RB << 4) + self.RA]
        elif inst <= 41:
            #panget to ren amp
            if inst == 32:
                self.MEM[self.RA] = self.ACC
            elif inst == 33:
                self.ACC = self.MEM[self.RA]
            elif inst == 34:
                self.MEM[self.RB] = self.ACC
            elif inst == 35:
                self.ACC = self.MEM[self.RB]
            elif inst == 36:
                self.MEM[self.RC] = self.ACC
            elif inst == 37:
                self.ACC = self.MEM[self.RC]
            elif inst == 38:
                self.MEM[self.RD] = self.ACC
            elif inst == 39:
                self.ACC = self.MEM[self.RD]
            elif inst == 40:
                self.MEM[self.RE] = self.ACC
            elif inst == 41:
                self.ACC = self.MEM[self.RE]

        self.PC += 1
        
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
        if inst == 46:
            ...
        elif inst == 47:
            ...

    def h_inst(self, inst):
        if inst == 48:
            self.ACC = self.PA
        elif inst == 49:
            self.ACC = self._overflowe(self.ACC + 1)
        elif inst == 50:
            self.IOA = self.ACC
        elif inst == 51:
            self.IOB = self.ACC
        elif inst == 52:
            self.IOC = self.ACC
    
        self.PC += 1

    def i_inst(self, inst):
        if inst == 56:
            self.TACTIVE = True
        elif inst == 57:
            self.TACTIVE = False

    def j_inst(self, inst):
        if inst == 58:
            self.ACC = int(bin(self.TIMER)[-4:], base=2)
        elif inst == 59:
            self.ACC = int(bin(self.TIMER)[2:6], base=2)
        elif inst == 60:
            self.TIMER = int(bin(self.TIMER)[:6] + bin(self.ACC)[2:], base=2)
        elif inst == 61:
            self.TIMER = int(bin(self.ACC) + bin(self.TIMER)[6:], base=2)
        

    def k_inst(self, inst):
        #next_instruction = int(self.ASM_MEM[self.PC][1], base=16)
        next_instruction = int(self.ASM_MEM[self.PC+1], base=16)

        if inst == 64: # add <imm>
            result = self.ACC + (next_instruction & 0xF)
            self.ACC = result & 0xF
        elif inst == 65: # sub <imm>
            result = self.ACC - (next_instruction & 0xF)
            self.ACC = result & 0xF
        elif inst == 66: # and <imm>
            self.ACC = self.ACC & (next_instruction & 0xF)
        elif inst == 67: # xor <imm>
            self.ACC = self.ACC ^ (next_instruction & 0xF)
        elif inst == 68: # or <imm>
            self.ACC = self.ACC | (next_instruction & 0xF)
        elif inst == 69: # wala
            print("undefined inst :(")
        elif inst == 70: # r4 <imm>
            self.RE = next_instruction & 0xF
        elif inst == 71: # timer <imm>
            self.TIMER = next_instruction & 0xF
        self.PC += 2        


    def l_inst(self, inst):
        if inst == 72:
            self.nop(1)
        elif inst == 73:
            self.nop(1)
        elif inst == 74:
            self.nop(1)
        elif inst == 75:
            self.nop(1)
        elif inst == 76: #todo-cycle check
            self.nop(1)
        elif inst == 77:
            self.nop(1)
        elif inst == 78:
            self.nop(1)
        elif inst == 79:
            self.nop(1)

    def m_inst(self, inst):
        #next_instruction = int(self.ASM_MEM[self.PC][1], base=16)
        next_instruction = int(self.ASM_MEM[self.PC+1], base=16)
        if 80 <= inst <= 95: # rarb
            self.RA = (inst - 80) & 0xF
            self.RB = next_instruction & 0xF
        elif 96 <= inst <= 111: # rcrd
            self.RC = (inst - 96) & 0xF
            self.RD = next_instruction & 0xF
        self.PC += 2

    def n_inst(self, inst):

        #next_instruction = int(self.ASM_MEM[self.PC][1], base=16)
        next_instruction = int(self.ASM_MEM[self.PC+1], base=16)

        def decode_next_address(offset: int =0xF800):
            address = ((inst & 0x7) << 8) | next_instruction
            return (self.PC & offset) | address

        if 160 <= inst <= 167: # bnz-a <imm>
            if self.RA != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 168 <= inst <= 175: # bnz-b <imm>
            if self.RB != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 176 <= inst <= 183: # beqz <imm>
            if self.ACC == 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 184 <= inst <= 191: # bnez <imm>
            if self.ACC != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 192 <= inst <= 199: # beqz-cf <imm>
            if self.CF == 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 200 <= inst <= 207: # bnez-cf <imm>
            if self.CF != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 208 <= inst <= 215: # b-timer
            if self.TIMER_RUNNING: # TODO checker if timer is running thanks mansur
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 216 <= inst <= 223: # bnz-d
            if self.RD != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 224 <= inst <= 239: # b
            self.PC = decode_next_address(0xF000)

        elif 240 <= inst <= 255: # call
            self.PC = decode_next_address(0xF000)

    def b_bit(self, inst, next_instruction):
        bit_position = (inst >> 3) & 0x3
        if (self.ACC >> bit_position) & 1:
            address = ((inst & 0x7) << 8) | next_instruction
            self.PC = (self.PC & 0xF800) | address
        else:
            self.PC += 2

    def dec(self):
        self.ACC = self.ACC - 1 #todo: underflow
        
    def nop(self, bitwidth):
        if bitwidth == 1:
            self.PC += 1
        elif bitwidth == 2:
            self.PC += 2

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

    def update(self):
        #only supports arrow keys, although the project specificiations mentions having a keyboard for an I/O. Ill deal with that next time.
        #somehow probe all of these into the emulator. Future me will handle this I trust
        if self.PC < len(self.ASM_MEM):
            self.read_inst(self.PC, self.ASM_MEM)
            # self.PC += 1 # this will fuck up branch instructions, better to put this inside individual instruction functions maybe?

        if pyxel.btn(pyxel.KEY_UP):
            print("UP KEY PRESSED")
            self.IOA = 1    #correct me if im wrong
        elif pyxel.btn(pyxel.KEY_DOWN):
            print("DOWN KEY PRESSED")
            self.IOA = 2
        elif pyxel.btn(pyxel.KEY_LEFT):
            print("LEFT KEY PRESSED")
            self.IOA = 4
        elif pyxel.btn(pyxel.KEY_RIGHT):
            print("RIGHT KEY PRESSED")
            self.IOA = 8
        else:
            self.IOA = 0

    def draw(self):
        #TODO: Make a 20x10 column LED Matrix.
        #somehow probe all of these into the emulator. Future me will handle this I trust
        pyxel.cls(0)

        #idea: since led values on the matrix are fixed, directly access the memory values and check for their values
        for i in range(10):
            for j in range(20):
                pyxel.blt(i*32,j*32,0,0,0,32,32,0)


window('test2.bin')

    