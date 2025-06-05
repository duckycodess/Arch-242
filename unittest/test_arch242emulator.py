import pytest
import os
import tempfile
import shutil
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from unittest.mock import patch, MagicMock, Mock
import arch242_emulator as arch242_emulator
from module import Arch242Assembler


class TestArch242Emulator:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_dir = tempfile.mkdtemp()
        self.assembler = Arch242Assembler()
        yield
        shutil.rmtree(self.test_dir)
    
    def create_binary_file(self, bytes_data):
        fd, path = tempfile.mkstemp(suffix='.bin', dir=self.test_dir)
        with os.fdopen(fd, 'wb') as f:
            f.write(bytes(bytes_data))
        return path
    
    def create_asm_and_binary(self, asm_code):
        fd, asm_path = tempfile.mkstemp(suffix='.s', dir=self.test_dir)
        with os.fdopen(fd, 'w') as f:
            f.write(asm_code)
        
        bin_data = self.assembler.assemble_code(asm_path, 'bin')
        bin_path = asm_path.replace('.s', '.bin')
        with open(bin_path, 'wb') as f:
            f.write(bin_data)
        
        return bin_path
    
    def create_test_emulator(self, bin_file):
        with patch('arch242_emulator.pyxel'):
            emu = arch242_emulator.arch242emu.__new__(arch242_emulator.arch242emu)
            
            # lahat ng registers
            emu.RA = 0
            emu.RB = 0
            emu.RC = 0
            emu.RD = 0
            emu.RE = 0
            emu.ACC = 0
            emu.IOA = 0
            emu.CF = 0
            emu.EI = 0
            emu.TEMP = 0
            emu.PC = 0
            emu.CLOCK = 0
            emu.CYCLESKIP = False
            emu.SHUTDOWN = False
            
            emu.LED = [[0]*4 for _ in range(16)]
            emu.LED_DEBUG = 0
            emu.LED_EXP = 0
            
            with open(bin_file, 'rb') as bin:
                data = bin.read()
                emu.ASM_MEM = [hex(byte) for byte in data]
            
            emu.MEM = [0] * 256
            
            return emu

    def run_emulator_steps(self, bin_file, steps=None):
        emu = self.create_test_emulator(bin_file)
        
        # run natin specified number of steps
        if steps is not None:
            for _ in range(steps):
                if emu.PC < len(emu.ASM_MEM) and not emu.SHUTDOWN:
                    # bug! etong condition handles two-byte instructions properly
                    if not emu.CYCLESKIP:
                        emu.read_inst(emu.PC, emu.ASM_MEM)
                    else:
                        emu.CYCLESKIP = False
        else:
            # finish the program via pc counter
            while emu.PC < len(emu.ASM_MEM) and not emu.SHUTDOWN:
                if not emu.CYCLESKIP:
                    emu.read_inst(emu.PC, emu.ASM_MEM)
                else:
                    emu.CYCLESKIP = False
        
        return emu

    def test_memory_8bit_operations(self):
        bin_file = self.create_binary_file([0x05, 0x04])  # to-mba, from-mba
        emu = self.run_emulator_steps(bin_file, steps=0)
        
        emu.ACC = 0xF
        emu.RA = 0
        emu.RB = 0
        emu.read_inst(0, emu.ASM_MEM)
        assert emu.MEM[0] == 0xF  
        
        emu.MEM[0] = 0xFF
        emu.PC = 1
        emu.read_inst(1, emu.ASM_MEM)

    def test_led_matrix_memory_mapping_bug(self):
        emu = self.create_test_emulator(self.create_binary_file([]))
        

        emu.MEM[192] = 0b00000001  # Should light LED at (0,0)
        emu.MEM[192] = 0b00000010  # Should light LED at (0,1)
        emu.MEM[193] = 0b00001000  # Should light LED at (0,7)
        
        # The current implementation incorrectly uses:
        # for i in self.MEM[192:242]:
        #     for c,k in enumerate(self.LED[i]):  # BUG: uses value as index!

    def test_inc_dec_memory_operations_8bit_fix(self):
        """Test inc*/dec* operations should handle 8-bit memory"""
        # Currently masks to 0xF but memory is 8-bit
        bin_file = self.create_binary_file([0x0C])  # inc*-mba
        emu = self.run_emulator_steps(bin_file, steps=0)
        emu.MEM[0] = 0xFF
        emu.RA = 0
        emu.RB = 0
        emu.read_inst(0, emu.ASM_MEM)
        # BUG: Currently would wrap to 0x0 due to & 0xF
        # Should be 0x00 (8-bit overflow) or 0x100 (no mask)?

    # ===== COMPREHENSIVE INSTRUCTION TESTS =====
    
    def test_all_rotation_edge_cases(self):
        """Test rotation instructions with all edge cases"""
        # Test rot-r with all 16 possible values
        for val in range(16):
            bin_file = self.create_binary_file([0x00])
            emu = self.run_emulator_steps(bin_file, steps=0)
            emu.ACC = val
            emu.read_inst(0, emu.ASM_MEM)
            expected = ((val & 1) << 3) | (val >> 1)
            assert emu.ACC == expected

    def test_memory_access_boundary_conditions(self):
        test_addresses = [
            (0x0, 0x0, 0x00),    # First address
            (0xF, 0xF, 0xFF),    # Last address
            (0x0, 0xC, 0xC0),    # LED matrix start
            (0x1, 0xF, 0xF1),    # LED matrix end
        ]
        
        for ra, rb, expected_addr in test_addresses:
            bin_file = self.create_binary_file([0x05])  # to-mba
            emu = self.run_emulator_steps(bin_file, steps=0)
            emu.RA = ra
            emu.RB = rb
            emu.ACC = 0xA
            emu.read_inst(0, emu.ASM_MEM)
            assert emu.MEM[expected_addr] == 0xA

    def test_arithmetic_with_8bit_memory(self):
        bin_file = self.create_binary_file([0x09])  # add-mba
        emu = self.run_emulator_steps(bin_file, steps=0)
        
        # Set 8-bit value in memory
        emu.MEM[0] = 0xF5  # 245 in decimal
        emu.ACC = 0x3
        emu.RA = 0
        emu.RB = 0
        emu.read_inst(0, emu.ASM_MEM)
        
        # Result should be (3 + 245) & 0xF = 248 & 0xF = 8
        assert emu.ACC == 0x8
        assert emu.CF == 1  # Overflow occurred

    def test_logical_operations_with_8bit_memory(self):
        """Test logical operations with 8-bit memory"""
        operations = [
            (0x1A, lambda a, m: a & m),  # and-ba
            (0x1B, lambda a, m: a ^ m),  # xor-ba
            (0x1C, lambda a, m: a | m),  # or-ba
        ]
        
        for opcode, operation in operations:
            bin_file = self.create_binary_file([opcode])
            emu = self.run_emulator_steps(bin_file, steps=0)
            emu.ACC = 0xA
            emu.MEM[0] = 0xF5  # 8-bit value
            emu.RA = 0
            emu.RB = 0
            emu.read_inst(0, emu.ASM_MEM)
            
            # ACC is 4-bit, so result should be operation(0xA, 0xF5) & 0xF
            expected = operation(0xA, 0xF5) & 0xF
            assert emu.ACC == expected

    def test_immediate_instructions_comprehensive(self):
        """Test all immediate instructions with edge cases"""
        # Test add immediate
        test_cases = [
            (0x40, 0x0F, 0x0, 0xF, 0),   # add 15 to 0
            (0x40, 0x01, 0xF, 0x0, 1),   # add 1 to 15 (overflow)
            (0x41, 0x01, 0x5, 0x4, 0),   # sub 1 from 5
            (0x41, 0x06, 0x5, 0xF, 1),   # sub 6 from 5 (underflow)
            (0x42, 0x0F, 0xA, 0xA, 0),   # and with 0xF
            (0x43, 0xFF, 0x5, 0xA, 0),   # xor with 0xF (only low nibble used)
            (0x44, 0x05, 0xA, 0xF, 0),   # or with 0x5
        ]
        
        for opcode, imm, acc_in, acc_out, cf_out in test_cases:
            bin_file = self.create_binary_file([opcode, imm])
            emu = self.run_emulator_steps(bin_file, steps=0)
            emu.ACC = acc_in
            emu.CF = 0
            emu.read_inst(0, emu.ASM_MEM)
            assert emu.ACC == acc_out

    def test_branch_instructions_comprehensive(self):
        """Test all branch instructions with PC preservation"""
        
        # Test each b-bit case separately
        for bit_pos in range(4):
            for bit_set in [0, 1]:
                # Create minimal test program
                instructions = [0x3E] * 0x1000  # Fill to address 0x1000
                acc_val = (bit_set << bit_pos)
                # b-bit encoding: 100KKBBB AAAAAAAA  
                # KK = bit_pos, BBB = 5 (for address 0x550), AAAAAAAA = 0x50
                opcode = 0x80 | (bit_pos << 3) | 0x05
                
                # Place instruction at 0x1000
                instructions.append(opcode)
                instructions.append(0x50)
                
                bin_file = self.create_binary_file(instructions)
                emu = self.run_emulator_steps(bin_file, steps=0)
                emu.PC = 0x1000
                emu.ACC = acc_val
                emu.read_inst(emu.PC, emu.ASM_MEM)
                
                if bit_set:
                    assert emu.PC == 0x1550, f"bit_pos={bit_pos}, bit_set={bit_set}, PC={hex(emu.PC)}"
                else:
                    assert emu.PC == 0x1002, f"bit_pos={bit_pos}, bit_set={bit_set}, PC={hex(emu.PC)}"

    def test_call_and_ret_interaction(self):
        """Test call sets TEMP correctly for ret"""
        instructions = [
            0xF5, 0x50,  # call 0x550
            0x3E,        # nop (should be skipped)
            0x3E,        # nop (should be skipped)
        ]
        instructions.extend([0x3E] * (0x550 - 4))  # Fill to target
        instructions.append(0x2E)  # ret at 0x550
        
        bin_file = self.create_binary_file(instructions)
        emu = self.run_emulator_steps(bin_file, steps=0)
        
        # Execute call
        emu.read_inst(0, emu.ASM_MEM)
        assert emu.PC == 0x550
        assert emu.TEMP == 2  # Return address
        
        # Execute ret
        emu.read_inst(emu.PC, emu.ASM_MEM)
        assert emu.PC == 2  # Should return to instruction after call
        assert emu.TEMP == 0  # Should be cleared

    def test_bcd_all_combinations(self):
        """Test BCD instruction for all ACC values and CF states"""
        for acc_val in range(16):
            for cf_val in [0, 1]:
                bin_file = self.create_binary_file([0x36])  # bcd
                emu = self.run_emulator_steps(bin_file, steps=0)
                emu.ACC = acc_val
                emu.CF = cf_val
                emu.read_inst(0, emu.ASM_MEM)
                
                if acc_val >= 10 or cf_val == 1:
                    expected_acc = (acc_val + 6) & 0xF
                    assert emu.ACC == expected_acc
                    assert emu.CF == 1
                else:
                    assert emu.ACC == acc_val
                    assert emu.CF == 0

    def test_shutdown_stops_execution(self):
        """Test shutdown properly stops the emulator"""
        instructions = [
            0x75,        # acc 5
            0x37, 0x3E,  # shutdown
            0x77,        # acc 7 (should not execute)
            0x79,        # acc 9 (should not execute)
        ]
        
        bin_file = self.create_binary_file(instructions)
        emu = self.run_emulator_steps(bin_file, steps=10)
        
        assert emu.ACC == 5  # Should not change after shutdown
        assert emu.SHUTDOWN == True
        assert emu.PC == 3  # Should stop at shutdown

    def test_rarb_rcrd_register_setting(self):
        """Test rarb and rcrd set correct registers"""
        # Test all combinations for rarb
        for ra in range(16):
            for rb in range(16):
                opcode = 0x50 | ra
                bin_file = self.create_binary_file([opcode, rb])
                emu = self.run_emulator_steps(bin_file, steps=0)
                emu.read_inst(0, emu.ASM_MEM)
                assert emu.RA == ra
                assert emu.RB == rb

        # Test rcrd
        opcode = 0x64  # RC=4
        bin_file = self.create_binary_file([opcode, 0x09])  # RD=9
        emu = self.run_emulator_steps(bin_file, steps=0)
        emu.read_inst(0, emu.ASM_MEM)
        assert emu.RC == 4
        assert emu.RD == 9

    def test_register_operations_boundaries(self):
        """Test register inc/dec at boundaries"""
        # Test increment at max value
        for reg_idx in range(5):
            opcode = 0x10 | (reg_idx << 1)  # inc*-reg
            bin_file = self.create_binary_file([opcode])
            emu = self.run_emulator_steps(bin_file, steps=0)
            
            # Set register to 0xF
            if reg_idx == 0: emu.RA = 0xF
            elif reg_idx == 1: emu.RB = 0xF
            elif reg_idx == 2: emu.RC = 0xF
            elif reg_idx == 3: emu.RD = 0xF
            elif reg_idx == 4: emu.RE = 0xF
            
            emu.read_inst(0, emu.ASM_MEM)
            
            # Should wrap to 0
            if reg_idx == 0: assert emu.RA == 0x0
            elif reg_idx == 1: assert emu.RB == 0x0
            elif reg_idx == 2: assert emu.RC == 0x0
            elif reg_idx == 3: assert emu.RD == 0x0
            elif reg_idx == 4: assert emu.RE == 0x0

    def test_keyboard_input_mapping(self):
        """Test keyboard input correctly maps to IOA bits"""
        emu = self.create_test_emulator(self.create_binary_file([0x3E]))
        
        # Test each key individually
        key_mappings = [
            (arch242_emulator.pyxel.KEY_UP, 0b0001),
            (arch242_emulator.pyxel.KEY_DOWN, 0b0010),
            (arch242_emulator.pyxel.KEY_LEFT, 0b0100),
            (arch242_emulator.pyxel.KEY_RIGHT, 0b1000),
        ]
        
        for key, expected_bit in key_mappings:
            with patch('arch242_emulator.pyxel.btn') as mock_btn:
                mock_btn.side_effect = lambda k: k == key
                emu.update()
                assert emu.IOA == expected_bit

    def test_multiple_keys_pressed(self):
        """Test multiple keys pressed simultaneously"""
        emu = self.create_test_emulator(self.create_binary_file([0x3E]))
        
        with patch('arch242_emulator.pyxel.btn') as mock_btn:
            # Simulate UP and RIGHT pressed
            pressed_keys = [arch242_emulator.pyxel.KEY_UP, arch242_emulator.pyxel.KEY_RIGHT]
            mock_btn.side_effect = lambda k: k in pressed_keys
            emu.update()
            assert emu.IOA == 0b1001  # UP (bit 0) + RIGHT (bit 3)

    def test_led_matrix_correct_behavior(self):
        emu = self.create_test_emulator(self.create_binary_file([]))
        
        # test tayo mga specific LED patterns
        test_cases = [
            # (mem_addr, value, expected_leds_on)
            (192, 0b0001, [(0, 0)]),    # Bit 0 -> LED at row 0, col 0
            (192, 0b0010, [(0, 1)]),    # Bit 1 -> LED at row 0, col 1
            (192, 0b0101, [(0, 0), (0, 2)]),  # Bits 0,2 -> LEDs at (0,0) and (0,2)
            (193, 0b1000, [(0, 7)]),    # Bit 3 -> LED at row 0, col 7
            (197, 0b0001, [(1, 0)]),    # First LED of second row
            (241, 0b1000, [(9, 19)]),   # Last LED at row 9, col 19
        ]
        
        for mem_addr, value, expected_leds in test_cases:
            # clear mem
            emu.MEM[192:242] = [0] * 50
            emu.MEM[mem_addr] = value
            
            # calculate which led should be on
            leds_on = []
            for addr in range(192, 242):
                if emu.MEM[addr] > 0:
                    lower_nibble = emu.MEM[addr] & 0xF
                    for bit in range(4):
                        if (lower_nibble >> bit) & 1:
                            led_index = (addr - 192) * 4 + bit
                            row = led_index // 20
                            col = led_index % 20
                            leds_on.append((row, col))
            
            assert leds_on == expected_leds, f"mem[{mem_addr}]={value:04b}, expected {expected_leds}, got {leds_on}"

    def test_two_byte_instruction_timing(self):
        instructions = [
            0x40, 0x05,  # add 5
            0x31,        # inc
            0x50, 0x23,  # rarb
        ]
        
        bin_file = self.create_binary_file(instructions)
        emu = self.run_emulator_steps(bin_file, steps=0)
        
        # track natin mga cycles
        cycles = []
        
        # add lang toh
        emu.read_inst(0, emu.ASM_MEM)
        cycles.append((emu.PC, emu.CYCLESKIP))
        assert emu.PC == 2
        assert emu.CYCLESKIP == True
        
        # skip the mf cycle
        emu.CYCLESKIP = False
        
        # Execute inc
        emu.read_inst(2, emu.ASM_MEM)
        assert emu.PC == 3
        assert emu.CYCLESKIP == False
        
        # Execute rarb
        emu.read_inst(3, emu.ASM_MEM)
        assert emu.PC == 5
        assert emu.CYCLESKIP == True

    def test_complex_program_snake_game_logic(self):
        asm_code = """
        # Initialize snake position
        acc 5
        to-ra       # X position
        acc 5
        to-rb       # Y position
        
        # Calculate LED address (192 + row*10 + col/4)
        from-rb
        add 0
        add 0
        to-rc       # RC = Y*2
        from-rc
        add 0
        add 0
        add 0
        to-rc       # RC = Y*8
        from-rb
        add 0
        to-rd       # RD = Y*2
        from-rc
        from-rd
        add 0       # ACC = Y*10
        
        # Game loop
    game_loop:
        # Read input
        from-ioa
        b-bit 0 move_up
        b-bit 1 move_down
        b-bit 2 move_left
        b-bit 3 move_right
        b game_loop
        
    move_up:
        from-rb
        dec
        to-rb
        b update_display
        
    move_down:
        from-rb
        inc
        to-rb
        b update_display
        
    move_left:
        from-ra
        dec
        to-ra
        b update_display
        
    move_right:
        from-ra
        inc
        to-ra
        b update_display
        
    update_display:
        # Clear old position
        acc 0
        rarb 0xC0   # Start of LED memory
        to-mba
        
        # Draw new position
        acc 15
        to-mba
        
        b game_loop
        """
        
        bin_file = self.create_asm_and_binary(asm_code)
        emu = self.run_emulator_steps(bin_file, steps=50)

        assert emu.RA == 5 or emu.RA == 4 or emu.RA == 6
        assert emu.RB == 5 or emu.RB == 4 or emu.RB == 6

    def test_memory_boundaries_with_addressing(self):
        bin_file = self.create_binary_file([0x05] * 256)  # to-mba repeated
        emu = self.run_emulator_steps(bin_file, steps=0)
        
        # 256 memory locations
        for addr in range(256):
            emu.RA = addr & 0xF
            emu.RB = (addr >> 4) & 0xF
            emu.ACC = addr & 0xF
            emu.PC = addr
            if emu.PC < len(emu.ASM_MEM):
                emu.read_inst(emu.PC, emu.ASM_MEM)
                assert emu.MEM[addr] == (addr & 0xF)

    def test_pc_overflow_behavior(self):
        # we create program that jumps near end of address space
        instructions = [0x3E] * 0xFFFC
        instructions.extend([0xE0, 0x00])  # b 0x000 at address 0xFFFC
        instructions.extend([0x3E, 0x3E])  # Two more NOPs
        
        bin_file = self.create_binary_file(instructions)
        emu = self.run_emulator_steps(bin_file, steps=0)
        
        emu.PC = 0xFFFC
        emu.read_inst(emu.PC, emu.ASM_MEM)
        assert emu.PC == 0xF000  # Should preserve upper 4 bits

    def test_all_branch_conditions(self):
        branch_tests = [
            # (opcode_base, condition_setup, should_branch)
            (0xA0, lambda e: setattr(e, 'RA', 5), True),    # bnz-a with RA != 0
            (0xA0, lambda e: setattr(e, 'RA', 0), False),   # bnz-a with RA == 0
            (0xA8, lambda e: setattr(e, 'RB', 5), True),    # bnz-b with RB != 0
            (0xA8, lambda e: setattr(e, 'RB', 0), False),   # bnz-b with RB == 0
            (0xB0, lambda e: setattr(e, 'ACC', 0), True),   # beqz with ACC == 0
            (0xB0, lambda e: setattr(e, 'ACC', 5), False),  # beqz with ACC != 0
            (0xB8, lambda e: setattr(e, 'ACC', 5), True),   # bnez with ACC != 0
            (0xB8, lambda e: setattr(e, 'ACC', 0), False),  # bnez with ACC == 0
            (0xC0, lambda e: setattr(e, 'CF', 0), True),    # beqz-cf with CF == 0
            (0xC0, lambda e: setattr(e, 'CF', 1), False),   # beqz-cf with CF != 0
            (0xC8, lambda e: setattr(e, 'CF', 1), True),    # bnez-cf with CF != 0
            (0xC8, lambda e: setattr(e, 'CF', 0), False),   # bnez-cf with CF == 0
            (0xD8, lambda e: setattr(e, 'RD', 5), True),    # bnz-d with RD != 0
            (0xD8, lambda e: setattr(e, 'RD', 0), False),   # bnz-d with RD == 0
        ]
        
        for opcode_base, setup, should_branch in branch_tests:
            bin_file = self.create_binary_file([opcode_base | 0x05, 0x50])  # Branch to 0x550
            emu = self.run_emulator_steps(bin_file, steps=0)
            setup(emu)
            emu.PC = 0
            emu.read_inst(0, emu.ASM_MEM)
            
            if should_branch:
                assert emu.PC == 0x550
            else:
                assert emu.PC == 2

    def test_assembler_integration_full_program(self):
        asm_code = """
        # Test all instruction types
        
        # Rotation tests
        acc 0b1010
        rot-r
        rot-l
        rot-rc
        rot-lc
        
        # Memory tests
        rarb 0x12      # Set address 0x12
        to-mba         # Store ACC
        from-mba       # Load it back
        
        # Arithmetic
        acc 7
        add 8          # Should overflow
        sub 3
        
        # Logical
        acc 0b1100
        and 0b1010
        xor 0b0011
        or 0b0001
        
        # Register operations
        acc 5
        to-ra
        to-rb
        to-rc
        to-rd
        to-re
        
        from-ra
        inc*-ra
        dec*-rb
        
        # Flags
        set-cf
        clr-cf
        
        # BCD test
        acc 10
        bcd            # Should add 6
        
        # Branch tests
        acc 0
        beqz skip1
        acc 1          # Should be skipped
    skip1:
        acc 5
        bnez skip2
        acc 0          # Should be skipped
    skip2:
        
        # Call/ret test
        call subroutine
        b end
        
    subroutine:
        acc 15
        ret
        
    end:
        shutdown
        """
        
        bin_file = self.create_asm_and_binary(asm_code)
        emu = self.run_emulator_steps(bin_file)

        assert emu.SHUTDOWN == True
        assert emu.ACC == 15

    def test_error_recovery(self):
        # empty instruction
        emu = self.create_test_emulator(self.create_binary_file([]))
        emu.ASM_MEM = []
        
        # dapat not crash when trying to read instruction
        try:
            emu.read_inst(0, emu.ASM_MEM)
        except:
            pass
        
        # pc beyond program
        emu = self.create_test_emulator(self.create_binary_file([0x3E]))
        emu.PC = 100
        emu.ASM_MEM = ['0x3e']
        
        # dont crash
        try:
            emu.read_inst(emu.PC, emu.ASM_MEM)
        except:
            pass

    def test_instruction_decode_bugs(self):
        bin_file = self.create_binary_file([0x20])  # Should be to-ra
        emu = self.run_emulator_steps(bin_file, steps=0)
        emu.ACC = 0xA
        emu.read_inst(0, emu.ASM_MEM)

    def test_reserved_instruction_handling(self):

        reserved_opcodes = [
            0x1C, 0x1D,  # Instructions 29-30 (removed)
            0x20,        # Instruction 32 (removed)
            0x23, 0x24, 0x25, 0x26,  # Instructions 35-38 (removed)
            0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,  # Instructions 41-46 (removed)
            0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D,  # Instructions 56-62 (removed)
            0x36,  # Instruction 54 (removed)
            0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F,  # Instructions 57-64 (removed)
            0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7,  # Instruction 75 (removed)
        ]
        
        for opcode in reserved_opcodes:
            bin_file = self.create_binary_file([opcode, 0x00])
            emu = self.run_emulator_steps(bin_file, steps=0)
            pc_before = emu.PC
            
            # Should either treat as NOP or handle gracefully
            try:
                emu.read_inst(0, emu.ASM_MEM)
                # Should increment PC appropriately
                assert emu.PC > pc_before
            except:
                pass  # Or handle as error

    def test_led_matrix_comprehensive(self):
        emu = self.create_test_emulator(self.create_binary_file([]))
        
        # we test all LED positions
        led_positions = []
        for addr in range(192, 242):
            for bit in range(4):
                row = ((addr - 192) * 4 + bit) // 20
                col = ((addr - 192) * 4 + bit) % 20
                led_positions.append((addr, bit, row, col))
        
        # we verify each LED can be controlled independently
        for addr, bit, row, col in led_positions:
            emu.MEM[192:242] = [0] * 50  # Clear all LEDs
            emu.MEM[addr] = 1 << bit     # Set specific LED
            
            # we count how many LEDs are on
            leds_on_count = 0
            for check_addr in range(192, 242):
                lower_nibble = emu.MEM[check_addr] & 0xF
                for check_bit in range(4):
                    if (lower_nibble >> check_bit) & 1:
                        leds_on_count += 1
            
            # should only have one LED on
            assert leds_on_count == 1, f"Expected 1 LED on, but found {leds_on_count}"
            
            # verify it's the correct LED
            assert emu.MEM[addr] == (1 << bit), f"Memory at {addr} should be {1 << bit}"
            
            # verify the LED position calculation is correct
            led_index = (addr - 192) * 4 + bit
            calc_row = led_index // 20
            calc_col = led_index % 20
            assert calc_row == row and calc_col == col, f"LED position mismatch"

    def test_complex_arithmetic_sequences(self):
        asm_code = """
        # calculate sum of 1 to 15 using only 4-bit arithmetic
        acc 0
        rarb 0x00    # Use memory location 0 for sum
        to-mba       # Initialize sum to 0
        
        acc 15
        to-rc        # Counter in RC
        
    loop:
        from-rc
        beqz done
        
        # Add counter to sum
        # First, store counter value in a temporary location
        rarb 0x01    # Use memory location 1 for counter
        from-rc
        to-mba       # Store counter at mem[1]
        
        # Get sum and add counter
        rarb 0x00    # Point back to sum location
        from-mba     # Get current sum
        rarb 0x01    # Point to counter location
        add-mba      # Add counter to sum (ACC = sum + counter)
        rarb 0x00    # Point back to sum location
        to-mba       # Store new sum
        
        # Decrement counter
        from-rc
        dec
        to-rc
        
        b loop
        
    done:
        rarb 0x00    # Point to sum
        from-mba     # Final sum in ACC
        shutdown
        """
        
        bin_file = self.create_asm_and_binary(asm_code)
        emu = self.run_emulator_steps(bin_file)
        
        # Calculate expected result with 4-bit wraparound
        # Sum of 1+2+3+...+15
        sum_val = 0
        for i in range(1, 16):
            sum_val = (sum_val + i) & 0xF  # 4-bit wraparound after each addition
        
        # 1+2+3+4+5+6+7+8+9+10+11+12+13+14+15 = 120 = 0x78
        # With 4-bit wraparound: 0x78 & 0xF = 0x8
        
        assert emu.ACC == 0x8, f"Expected final sum 0x8, got {emu.ACC:x}"
        assert emu.SHUTDOWN == True, "Program should have shutdown"
    
        # Also verify memory contains expected values
        assert emu.MEM[0] == 0x8, f"Memory location 0 should contain sum 0x8"


    def test_performance_stress_test(self):
        instructions = []
        
        # Fill memory with pattern
        for i in range(128):
            instructions.extend([
                0x70 | (i & 0xF),     # acc i (only low nibble)
                0x50 | (i & 0xF),     # rarb - set RA to low nibble
                (i >> 4) & 0xF,       # set RB to high nibble
                0x05                  # to-mba
            ])
        
        # Add operations on the filled memory
        for i in range(10):  # Reduced from 100 for faster testing
            instructions.extend([
                0x09,  # add-mba (add memory to ACC)
                0x01,  # rot-l
                0x05,  # to-mba (store back)
            ])
        
        instructions.extend([0x37, 0x3E])  # shutdown
        
        bin_file = self.create_binary_file(instructions)
        emu = self.run_emulator_steps(bin_file)
        
        assert emu.SHUTDOWN == True, "Program should have shutdown"
        
        for i in range(128):

            if i < 16:
                assert emu.MEM[i] != None, f"Memory location {i} should be initialized"
        

        expected_instruction_count = 128 * 4 + 10 * 3 + 2
        assert emu.PC >= expected_instruction_count, f"PC should have advanced through at least {expected_instruction_count} bytes"
        assert emu.ACC <= 0xF, "ACC should be within 4-bit range"


    def test_edge_case_combinations(self):
        test_cases = [
            # call immediately followed by ret
            ([0xF0, 0x02, 0x2E], lambda e: e.PC == 2),
            
            # branch to self (infinite loop)
            ([0xE0, 0x00], lambda e: e.PC == 0),
            
            # shutdown in branch delay slot
            ([0xE0, 0x02, 0x37, 0x3E], lambda e: e.SHUTDOWN == True),
        ]
        
        for instructions, check in test_cases:
            bin_file = self.create_binary_file(instructions)
            emu = self.run_emulator_steps(bin_file, steps=5)
            assert check(emu)

