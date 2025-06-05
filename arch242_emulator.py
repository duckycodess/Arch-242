import pyxel
from module import Arch242Assembler
import sys

def init(): #consider placing this as a separate file?
    if len(sys.argv) != 2:
        print("Usage: python arch242_emulator.py <input_file.asm | input_file.bin>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]

    arch242emu(input_file)

class arch242emu:

    # ---/ INITIALIZE PYXEL AND EMULATOR ELEMENTS /---

    def __init__(self, file):
        pyxel.init(640,320,title="Arch-242 LED Matrix", fps=30) #fps -> clock speed of emulator
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

        # ---/ ASSEMBLE & LOAD PROGRAM /---

        if file[-3:] == 'asm':
            print('Loaded assembly file!')
            asmfile = file
            
            print('Initializing assembler...')
            assembler = Arch242Assembler()

            print('Assembler loaded! Assembling program...')
            output_data = assembler.assemble_code(asmfile, 'bin')
            assembler.write_output(output_data, asmfile, 'bin')

            binfile = f'{asmfile[:-4]}.bin'
        else:
            print('Loaded bin file!')
            binfile = file

        print('Loading program...')
        with open(binfile, 'rb') as bin:
            data = bin.read()
            self.ASM_MEM = [hex(byte) for byte in data]
            
        self.MEM = [0b0]*256

        print('Starting Emulator...')
        pyxel.run(self.update, self.draw)

    # ---/ EMULATOR: INSTRUCTION MATCHING /---

    def read_inst(self, pc, inst):
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

    # ---/ EMULATOR: EMULATED INSTRUCTIONS /---

    def a_inst(self, inst):
        if inst == 0: # rot-r
            swapbit = (self.ACC & 1)*8
            self.ACC = (self.ACC >> 1) + swapbit

        elif inst == 1: # rot-l
            swapbit = ((self.ACC >> 3) & 1)
            self.ACC = ((self.ACC << 1) & 0xF) + swapbit

        elif inst == 2: # rot-rc
            swapbit = self.CF*8
            self.CF = (self.ACC & 1)
            self.ACC = (self.ACC >> 1) + swapbit

        elif inst == 3: # rot-lc
            swapbit = self.CF
            self.CF = ((self.ACC >> 3) & 1)
            self.ACC = ((self.ACC << 1) & 0xF) + swapbit

        self.PC += 1

    def b_inst(self, inst):
        if inst == 4: # from-mda
            self.ACC = (self.MEM[(self.RB << 4) + self.RA]) & 0xF

        elif inst == 5: # to-mda
            self.MEM[(self.RB << 4) + self.RA] = self.ACC

        elif inst == 6: # from-mdc
            self.ACC = (self.MEM[(self.RD << 4) + self.RC]) & 0xF

        elif inst == 7: # to-mdc
            self.MEM[(self.RD << 4) + self.RC] = self.ACC

        self.PC += 1

    def c_inst(self, inst):
        if inst == 8: # addc-mba
            calc = self.ACC + self.MEM[(self.RB << 4) + self.RA] + self.CF
            self.CF = (calc >> 4 & 1)
            self.ACC = calc & 0xF

        elif inst == 9: # add-mba
            calc = self.ACC + self.MEM[(self.RB << 4) + self.RA]
            self.CF = (calc >> 4 & 1)
            self.ACC = calc & 0xF

        elif inst == 10: # subc-mba
            calc = self.ACC - self.MEM[(self.RB << 4) + self.RA] + self.CF
            self.CF = 1 if calc < 0 else 0 #paano ba undeflow bit?
            self.ACC = calc & 0xF #might not work?

        elif inst == 11: # sub-mba
            calc = self.ACC - self.MEM[(self.RB << 4) + self.RA]
            self.CF = (calc >> 4 & 1) #paano ba undeflow bit?
            self.ACC = calc & 0xF #might not work?

        self.PC += 1

    def d_inst(self, inst): #WARN: ASSUMING EACH MEMORY ADDRESS HOLDS 4 BITS. IF NOT, CHANGE 0XF
        if inst == 12: # inc*mba
            self.MEM[(self.RB << 4) + self.RA] = (self.MEM[(self.RB << 4) + self.RA] + 1) & 0xF

        elif inst == 13: # dec*mba
            self.MEM[(self.RB << 4) + self.RA] = (self.MEM[(self.RB << 4) + self.RA] - 1) & 0xF

        elif inst == 14: # inc*mdc
            self.MEM[(self.RD << 4) + self.RC] = (self.MEM[(self.RD << 4) + self.RC] + 1) & 0xF

        elif inst == 15: # dec*mdc
            self.MEM[(self.RD << 4) + self.RC] = (self.MEM[(self.RD << 4) + self.RC] - 1) & 0xF

        elif inst <= 25: 
            if inst == 16: # inc*-RA
                self.RA = (self.RA + 1) & 0xF
            elif inst == 17: # dec*-RA
                self.RA = (self.RA - 1) & 0xF
            elif inst == 18: # inc*-RB
                self.RB = (self.RB + 1) & 0xF
            elif inst == 19: # dec*-RB
                self.RB = (self.RB - 1) & 0xF
            elif inst == 20: # inc*-RC
                self.RC = (self.RC + 1) & 0xF
            elif inst == 21: # dec*-RC
                self.RC = (self.RC - 1) & 0xF
            elif inst == 22: # inc*-RD
                self.RD = (self.RD + 1) & 0xF
            elif inst == 23: # dec*-RD
                self.RD = (self.RD - 1) & 0xF
            elif inst == 24: # inc*-RE
                self.RE = (self.RE + 1) & 0xF
            elif inst == 25: # inc*-RE
                self.RE = (self.RE - 1) & 0xF

        self.PC += 1

    def e_inst(self, inst):
        if inst == 26: # and-ba
            self.ACC = (self.ACC & self.MEM[(self.RB << 4) + self.RA]) & 0xF
        elif inst == 27: # xor-ba
            self.ACC = (self.ACC ^ self.MEM[(self.RB << 4) + self.RA]) & 0xF
        elif inst == 28: # or-ba
            self.ACC = (self.ACC | self.MEM[(self.RB << 4) + self.RA]) & 0xF
        elif inst == 29: # and*-mba
            self.MEM[(self.RB << 4) + self.RA] = self.ACC & self.MEM[(self.RB << 4) + self.RA]
        elif inst == 30: # xor*-mba
            self.MEM[(self.RB << 4) + self.RA] = self.ACC ^ self.MEM[(self.RB << 4) + self.RA]
        elif inst == 31: # or*-mba
            self.MEM[(self.RB << 4) + self.RA] = self.ACC | self.MEM[(self.RB << 4) + self.RA]

        self.PC += 1

    def f_inst(self, inst):
        # changing, initially self.mem[self.RA] = self.ACC siya
        # it's supposed to be self.RA = self.ACC and follow the patter to others
        if inst == 32: # to-RA
            self.RA = self.ACC
        elif inst == 33: # from-RA
            self.ACC = self.RA
        elif inst == 34: # to-RB
            self.RB = self.ACC
        elif inst == 35: # from-RB
            self.ACC = self.RB
        elif inst == 36: # to-RC
            self.RC = self.ACC
        elif inst == 37: # from-RC
            self.ACC = self.RC
        elif inst == 38: # to-RD
            self.RD = self.ACC
        elif inst == 39: # from-RD
            self.ACC = self.RD
        elif inst == 40: # to-RE
            self.RE = self.ACC
        elif inst == 41: # from-RE
            self.ACC = self.RE

        self.PC += 1

    def g_inst(self, inst):
        if inst == 42: #clr-cf
            self.CF = 0 
        elif inst == 43: #set-cf
            self.CF = 1
        elif inst == 44: #set-ei
            self.EI = 1
        elif inst == 45: #clr-ei
            self.EI = 0

        self.PC += 1

    def ret(self):
        self.PC = ((self.PC >> 12) << 12) + (self.TEMP & 0xFFF)
        self.TEMP = 0

    def h_inst(self, inst):
        if inst == 48: # -
            self.nop(1)
        elif inst == 49: # inc
            self.ACC = (self.ACC + 1) & 0xF
        elif inst == 50: # from-ioa
            self.ACC = self.IOA
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
        
        self.PC += 1

    def shutdown(self, inst2): # shutdown
        if inst2 == 62:
            print('closing emulator...')
            self.PC += 2
            self.CYCLESKIP = True
            self.SHUTDOWN = True
        else:
            print('illegal instruction detected')

    def nop(self, bitwidth): # nop
        if bitwidth == 1:
            self.PC += 1
        elif bitwidth == 2:
            self.PC += 2

    def dec(self): # dec
        self.ACC = (self.ACC - 1) & 0xF #todo: underflow
        self.PC += 1

    def i_inst(self, inst):
        next_instruction = int(self.ASM_MEM[self.PC+1], base=16)

        if inst == 64: # add imm
            result = self.ACC + (next_instruction & 0xF)
            self.ACC = result & 0xF
        elif inst == 65: # sub imm
            result = self.ACC - (next_instruction & 0xF)
            self.ACC = result & 0xF
        elif inst == 66: # and imm
            self.ACC = self.ACC & (next_instruction & 0xF)
        elif inst == 67: # xor imm
            self.ACC = self.ACC ^ (next_instruction & 0xF)
        elif inst == 68: # or imm
            self.ACC = self.ACC | (next_instruction & 0xF)
        elif inst == 69: # -
            self.nop(1)
        elif inst == 70: # r4 imm
            self.RE = next_instruction & 0xF
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
        elif 96 <= inst <= 111: # rcrd
            self.RC = (inst - 96) & 0xF
            self.RD = next_instruction & 0xF
        
        self.CYCLESKIP = True    
        self.PC += 2
        
    def acc(self, inst): # acc
        self.ACC = (inst-112)
        self.PC += 1

    def b_bit(self, inst, next_instruction): # b-bit
        bit_position = (inst >> 3) & 0x3
        if (self.ACC >> bit_position) & 1:
            address = ((inst & 0x7) << 8) | next_instruction
            self.PC = (self.PC & 0xF800) | address
        else:
            self.PC += 2

        self.CYCLESKIP = True

    def k_inst(self, inst):
        next_instruction = int(self.ASM_MEM[self.PC+1], base=16)

        def decode_next_address(offset: int =0xF800):
            address = ((inst & 0x7) << 8) | next_instruction
            return (self.PC & offset) | address

        if 160 <= inst <= 167: # bnz-a imm
            if self.RA != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 168 <= inst <= 175: # bnz-b imm
            if self.RB != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 176 <= inst <= 183: # beqz imm
            if self.ACC == 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 184 <= inst <= 191: # bnez imm
            if self.ACC != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 192 <= inst <= 199: # beqz-cf imm
            if self.CF == 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 200 <= inst <= 207: # bnez-cf imm
            if self.CF != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 208 <= inst <= 215: # -
            self.nop(1)
        elif 216 <= inst <= 223: # bnz-d
            if self.RD != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
        elif 224 <= inst <= 239: # b
            self.PC = decode_next_address(0xF000)

        elif 240 <= inst <= 255: # call
            self.TEMP = self.PC + 2
            self.PC = decode_next_address(0xF000)

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
        #emulator runs here

        self.CLOCK += 1

        if not self.CYCLESKIP:
            if self.PC < len(self.ASM_MEM):
                self.read_inst(self.PC, self.ASM_MEM)

            if self.SHUTDOWN:
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

        #print(f'Current value of IOA: {bin(self.IOA)}') # IO DEBUG
        #self.LED_CHECK() #LED DEBUG
        
    # ---/ LED MATRIX DRAW CODE /---

    def draw(self):
        pyxel.cls(0)

        rowval = 0
        colval = 0

        for i in self.MEM[192:242]:
            if colval == 20: 
                rowval += 1
                colval = 0

            for c,k in enumerate(self.LED[i]):
                if k:
                    pyxel.blt((c+colval)*32,rowval*32,0,32,0,32,32,0)
                else:
                    pyxel.blt((c+colval)*32,rowval*32,0,0,0,32,32,0)
            colval += 4

            # just commenting here just in case i'm wrong, suggestion lang tho
            # can make your own, rough idea implementation lang to that i didn't really test
            '''
            for i in self.MEM[192:242]:
            if colval == 20: 
                rowval += 1
                colval = 0

            lower_nibble = i & 0xF  # should only use lower 4 bits kasi nibble
            for bit_pos in range(4):  # we cehck each bit position
                if (lower_nibble >> bit_pos) & 1:  # check if bit is set
                    pyxel.blt((bit_pos+colval)*32,rowval*32,0,32,0,32,32,0)
                else:
                    pyxel.blt((bit_pos+colval)*32,rowval*32,0,0,0,32,32,0)
            colval += 4
            '''

if __name__ == "__main__":
    init()
