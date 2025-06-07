import pyxel
from assembler.module import Arch242Assembler
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
        pyxel.init(720,320,title="Arch-242 LED Matrix", fps=700) #fps -> clock speed of emulator
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
            print("skrrrttt")

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
            self.ACC = (self.MEM[(self.RB << 4) + self.RA]) & 0xF
            self.CURINST = 'from-mba'

        elif inst == 5: # to-mba
            self.MEM[(self.RB << 4) + self.RA] = self.ACC
            self.CURINST = 'to-mba'

        elif inst == 6: # from-mdc
            self.ACC = (self.MEM[(self.RD << 4) + self.RC]) & 0xF
            self.CURINST = 'from-mdc'

        elif inst == 7: # to-mdc
            self.MEM[(self.RD << 4) + self.RC] = self.ACC
            self.CURINST = 'to-mdc'

        self.PC += 1

    def c_inst(self, inst):
        if inst == 8: # addc-mba
            calc = self.ACC + self.MEM[(self.RB << 4) + self.RA] + self.CF
            self.CF = (calc >> 4 & 1)
            self.ACC = calc & 0xF
            self.CURINST = 'addc-mba'

        elif inst == 9: # add-mba
            calc = self.ACC + self.MEM[(self.RB << 4) + self.RA]
            self.CF = (calc >> 4 & 1)
            self.ACC = calc & 0xF
            self.CURINST = 'add-mba'

        elif inst == 10: # subc-mba
            calc = self.ACC - self.MEM[(self.RB << 4) + self.RA] + self.CF
            self.CF = 1 if calc < 0 else 0 #paano ba undeflow bit?
            self.ACC = calc & 0xF #might not work?
            self.CURINST = 'subc-mba'


        elif inst == 11: # sub-mba
            calc = self.ACC - self.MEM[(self.RB << 4) + self.RA]
            self.CF = (calc >> 4 & 1) #paano ba undeflow bit?
            self.ACC = calc & 0xF #might not work?
            self.CURINST = 'sub-mba'

        self.PC += 1

    def d_inst(self, inst): #WARN: ASSUMING EACH MEMORY ADDRESS HOLDS 4 BITS. IF NOT, CHANGE 0XF
        if inst == 12: # inc*mba
            self.MEM[(self.RB << 4) + self.RA] = (self.MEM[(self.RB << 4) + self.RA] + 1) & 0xF
            self.CURINST = 'inc*-mba'

        elif inst == 13: # dec*mba
            self.MEM[(self.RB << 4) + self.RA] = (self.MEM[(self.RB << 4) + self.RA] - 1) & 0xF
            self.CURINST = 'dec*-mba'

        elif inst == 14: # inc*mdc
            self.MEM[(self.RD << 4) + self.RC] = (self.MEM[(self.RD << 4) + self.RC] + 1) & 0xF
            self.CURINST = 'inc-mdc'

        elif inst == 15: # dec*mdc
            self.MEM[(self.RD << 4) + self.RC] = (self.MEM[(self.RD << 4) + self.RC] - 1) & 0xF
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
            self.ACC = (self.ACC & self.MEM[(self.RB << 4) + self.RA]) & 0xF
            self.CURINST = 'and-ba'
        elif inst == 27: # xor-ba
            self.ACC = (self.ACC ^ self.MEM[(self.RB << 4) + self.RA]) & 0xF
            self.CURINST = 'xor-ba'
        elif inst == 28: # or-ba
            self.ACC = (self.ACC | self.MEM[(self.RB << 4) + self.RA]) & 0xF
            self.CURINST = 'or-ba'
        elif inst == 29: # and*-mba
            self.MEM[(self.RB << 4) + self.RA] = self.ACC & self.MEM[(self.RB << 4) + self.RA]
            self.CURINST = 'and*-mba'
        elif inst == 30: # xor*-mba
            self.MEM[(self.RB << 4) + self.RA] = self.ACC ^ self.MEM[(self.RB << 4) + self.RA]
            self.CURINST = 'xor*-mba'
        elif inst == 31: # or*-mba
            self.MEM[(self.RB << 4) + self.RA] = self.ACC | self.MEM[(self.RB << 4) + self.RA]
            self.CURINST = 'or*-mba'

        self.PC += 1

    def f_inst(self, inst):
        # changing, initially self.mem[self.RA] = self.ACC siya
        # it's supposed to be self.RA = self.ACC and follow the patter to others
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
        self.ACC = (self.ACC - 1) & 0xF #todo: underflow
        self.PC += 1
        self.CURINST = 'dec'

    def i_inst(self, inst):
        next_instruction = int(self.ASM_MEM[self.PC+1], base=16)

        if inst == 64: # add imm
            result = self.ACC + (next_instruction & 0xF)
            self.ACC = result & 0xF
            self.CURINST = 'add imm'
        elif inst == 65: # sub imm
            result = self.ACC - (next_instruction & 0xF)
            self.ACC = result & 0xF
            self.CURINST = 'sub imm'
        elif inst == 66: # and imm
            self.ACC = self.ACC & (next_instruction & 0xF)
            self.CURINST = 'and imm'
        elif inst == 67: # xor imm
            self.ACC = self.ACC ^ (next_instruction & 0xF)
            self.CURINST = 'xor imm'
        elif inst == 68: # or imm
            self.ACC = self.ACC | (next_instruction & 0xF)
            self.CURINST = 'or imm'
        elif inst == 69: # -
            self.nop(1)
        elif inst == 70: # r4 imm
            self.RE = next_instruction & 0xF
            self.CURINST = 'r4 imm'
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
            self.CURINST = 'rarb'
        elif 96 <= inst <= 111: # rcrd
            self.RC = (inst - 96) & 0xF
            self.RD = next_instruction & 0xF
            self.CURINST = 'rcrd'
        
        self.CYCLESKIP = True    
        self.PC += 2
        
    def acc(self, inst): # acc
        self.ACC = (inst-112)
        self.PC += 1
        self.CURINST = 'acc'

    def b_bit(self, inst, next_instruction): # b-bit
        bit_position = (inst >> 3) & 0x3
        if (self.ACC >> bit_position) & 1:
            address = ((inst & 0x7) << 8) | next_instruction
            self.PC = (self.PC & 0xF800) | address
        else:
            self.PC += 2

        self.CURINST = 'b-bit'
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
            self.CURINST = 'bnz-a imm'
        elif 168 <= inst <= 175: # bnz-b imm
            if self.RB != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
            self.CURINST = 'bnz-b imm'
        elif 176 <= inst <= 183: # beqz imm
            if self.ACC == 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
            self.CURINST = 'beqz imm'
        elif 184 <= inst <= 191: # bnez imm
            if self.ACC != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
            self.CURINST = 'bnez imm'
        elif 192 <= inst <= 199: # beqz-cf imm
            if self.CF == 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
            self.CURINST = 'beqz-cf imm'
        elif 200 <= inst <= 207: # bnez-cf imm
            if self.CF != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
            self.CURINST = 'bnez-cf imm'
        elif 208 <= inst <= 215: # -
            self.nop(1)
        elif 216 <= inst <= 223: # bnz-d
            if self.RD != 0:
                self.PC = decode_next_address()
            else:
                self.PC += 2
            self.CURINST = 'bnz-d'
        elif 224 <= inst <= 239: # b
            self.PC = decode_next_address(0xF000)
            self.CURINST = 'b'

        elif 240 <= inst <= 255: # call
            self.TEMP = self.PC + 2
            self.PC = decode_next_address(0xF000)
            self.CURINST = 'call'

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

        if pyxel.btn(pyxel.KEY_Q):
            print("Quitting Emulator...")
            quit()

        #print(f'Current value of IOA: {bin(self.IOA)}') # IO DEBUG
        #self.LED_CHECK() #LED DEBUG
        
    # ---/ LED MATRIX DRAW CODE /---

    def draw(self):
        pyxel.cls(0)

        rowval = 0
        colval = 0
        j = 192

        food_row = self.MEM[0x85] & 0xF
        food_col = self.MEM[0x86] & 0xF
        head_row = self.MEM[0x81] & 0xF
        head_col = self.MEM[0x82] & 0xF
        
        for i in self.MEM[192:242]:
            if colval == 20: 
                rowval += 1
                colval = 0

            for c in range(4):
                bit_on = (i >> c) & 1
                
                x_pos = (c + colval) * 32
                y_pos = rowval * 32
                
                element_type = self.get_led_element_type(j, c, bit_on, food_row, food_col, head_row, head_col)
                sprite_x, sprite_y = self.get_sprite_position(element_type)
                pyxel.blt(x_pos, y_pos, 0, sprite_x, sprite_y, 32, 32, 0)
                
                if self.DEBUG:
                    game_pos = self.led_to_game_coords(j, c)
                    if game_pos:
                        pyxel.text(x_pos + 2, y_pos + 2, f'({game_pos[0]},{game_pos[1]})', 3)
                    pyxel.text(x_pos + 2, y_pos + 24, f'({j:02X})', 3)

            colval += 4
            j += 1

        self.draw_debug_info()

    def get_sprite_position(self, element_type):
        sprite_map = {
            "off_background": (0, 0), # background nung snake game itself
            "food": (32, 0),           # food sprite
            "bg_score": (64, 0),       # bg of scoreboard, turned off led
            "score": (96, 0),          # score led turned on
            "border": (128, 0),        # border sprite
            "snake": (160, 0),         # snake sprite
        }
        return sprite_map.get(element_type, (192, 0))

    def get_led_element_type(self, addr, bit_pos, bit_on, food_row, food_col, head_row, head_col):
        # address ng borderss
        border_addresses = {
            0xC0, 0xC1, 0xC2, 0xC3, 0xC4,  # top border
            0xC7, 0xCC, 0xD1, 0xD6, 0xDB, 0xE0, 0xE5, 0xEA,  #sSide borders
            0xED, 0xEE, 0xEF, 0xF0, 0xF1   # bottom border
        }
        
        # display score address
        score_addresses = {
            0xCD, 0xCE,
            0xD2, 0xD3, 0xD7, 0xD8, 0xDC, 0xDD,
            0xE1, 0xE2, 0xE6, 0xE7
        }
        
        # check muna if border
        if addr in border_addresses:
            return "border"

        if addr in score_addresses:
            if bit_on:
                return "score"
            else:
                return "bg_score"

        game_coords = self.led_to_game_coords(addr, bit_pos)
        if game_coords:
            row, col = game_coords
            
            if bit_on:
                if row == food_row and col == food_col and food_row != 0xF:
                    return "food"
                else:
                    return "snake"
            else:
                return "off_background"
        
        return "bg_score"

    def led_to_game_coords(self, addr, bit_pos):
        game_grid_mapping = {
            # row 0 - addresses 197-198 (0xC5-0xC6)
            (0xC5, 0): (0, 0), (0xC5, 1): (0, 1), (0xC5, 2): (0, 2), (0xC5, 3): (0, 3),
            (0xC6, 0): (0, 4), (0xC6, 1): (0, 5), (0xC6, 2): (0, 6), (0xC6, 3): (0, 7),
            # row 1 - addresses 202-203 (0xCA-0xCB)
            (0xCA, 0): (1, 0), (0xCA, 1): (1, 1), (0xCA, 2): (1, 2), (0xCA, 3): (1, 3),
            (0xCB, 0): (1, 4), (0xCB, 1): (1, 5), (0xCB, 2): (1, 6), (0xCB, 3): (1, 7),
            # row 2 - addresses 207-208 (0xCF-0xD0)
            (0xCF, 0): (2, 0), (0xCF, 1): (2, 1), (0xCF, 2): (2, 2), (0xCF, 3): (2, 3),
            (0xD0, 0): (2, 4), (0xD0, 1): (2, 5), (0xD0, 2): (2, 6), (0xD0, 3): (2, 7),
            # row 3 - addresses 212-213 (0xD4-0xD5)
            (0xD4, 0): (3, 0), (0xD4, 1): (3, 1), (0xD4, 2): (3, 2), (0xD4, 3): (3, 3),
            (0xD5, 0): (3, 4), (0xD5, 1): (3, 5), (0xD5, 2): (3, 6), (0xD5, 3): (3, 7),
            # row 4 - addresses 217-218 (0xD9-0xDA)
            (0xD9, 0): (4, 0), (0xD9, 1): (4, 1), (0xD9, 2): (4, 2), (0xD9, 3): (4, 3),
            (0xDA, 0): (4, 4), (0xDA, 1): (4, 5), (0xDA, 2): (4, 6), (0xDA, 3): (4, 7),
            # row 5 - addresses 222-223 (0xDE-0xDF)
            (0xDE, 0): (5, 0), (0xDE, 1): (5, 1), (0xDE, 2): (5, 2), (0xDE, 3): (5, 3),
            (0xDF, 0): (5, 4), (0xDF, 1): (5, 5), (0xDF, 2): (5, 6), (0xDF, 3): (5, 7),
            # row 6 - addresses 227-228 (0xE3-0xE4)
            (0xE3, 0): (6, 0), (0xE3, 1): (6, 1), (0xE3, 2): (6, 2), (0xE3, 3): (6, 3),
            (0xE4, 0): (6, 4), (0xE4, 1): (6, 5), (0xE4, 2): (6, 6), (0xE4, 3): (6, 7),
            # row 7 - addresses 232-233 (0xE8-0xE9)
            (0xE8, 0): (7, 0), (0xE8, 1): (7, 1), (0xE8, 2): (7, 2), (0xE8, 3): (7, 3),
            (0xE9, 0): (7, 4), (0xE9, 1): (7, 5), (0xE9, 2): (7, 6), (0xE9, 3): (7, 7),
        }
        
        return game_grid_mapping.get((addr, bit_pos))

    def get_led_element_type_enhanced(self, addr, bit_pos, bit_on, food_row, food_col, head_row, head_col):
        base_type = self.get_led_element_type(addr, bit_pos, bit_on, food_row, food_col, head_row, head_col)
        
        if base_type == "snake":
            game_coords = self.led_to_game_coords(addr, bit_pos)
            if game_coords:
                row, col = game_coords
                if row == head_row and col == head_col:
                    return "snake"
        
        return base_type

    def draw_debug_info(self):
        pyxel.text(640, 2, 'Arch-242 Emulator', 3)
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
        
        pyxel.text(640, 234, 'GAME STATE:', 3)
        pyxel.text(640, 242, f'Head: ({self.MEM[0x81]},{self.MEM[0x82]})', 3)
        pyxel.text(640, 250, f'Tail: ({self.MEM[0x83]},{self.MEM[0x84]})', 3)
        pyxel.text(640, 258, f'Food: ({self.MEM[0x85]},{self.MEM[0x86]})', 3)
        pyxel.text(640, 266, f'Score: {self.MEM[0x89]}', 3)
        pyxel.text(640, 274, f'Dir: {self.MEM[0x80]}', 3)


if __name__ == "__main__":
    init()
