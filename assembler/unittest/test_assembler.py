import pytest
import os
import tempfile
import shutil
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from module import Arch242Assembler
from exception_handler_assembler import *


class TestArch242Assembler:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_dir = tempfile.mkdtemp()
        self.assembler = Arch242Assembler()
        yield
        shutil.rmtree(self.test_dir)
    
    def create_test_file(self, content):
        fd, path = tempfile.mkstemp(suffix='.s', dir=self.test_dir)
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return path
    
    def assemble_and_compare(self, asm_code, expected_bytes, format='bin'):
        test_file = self.create_test_file(asm_code)
        result = self.assembler.assemble_code(test_file, format)
        
        if format == 'bin':
            assert result == bytes(expected_bytes), f"Expected {expected_bytes}, got {list(result)}"
        else:  # hex
            hex_lines = []
            for i in range(0, len(expected_bytes), 16):
                chunk = expected_bytes[i:i+16]
                hex_line = ' '.join(f'{b:02x}' for b in chunk)
                hex_lines.append(hex_line)
            expected_hex = '\n'.join(hex_lines).encode('ascii')
            assert result == expected_hex, f"Expected {expected_hex}, got {result}"
    
    # test single-byte
    def test_single_byte_instructions(self):
        test_cases = [
            ('rot-r', [0x00]),
            ('rot-l', [0x01]),
            ('rot-rc', [0x02]),
            ('rot-lc', [0x03]),
            ('from-mba', [0x04]),
            ('to-mba', [0x05]),
            ('from-mdc', [0x06]),
            ('to-mdc', [0x07]),
            ('addc-mba', [0x08]),
            ('add-mba', [0x09]),
            ('subc-mba', [0x0A]),
            ('sub-mba', [0x0B]),
            ('inc*-mba', [0x0C]),
            ('dec*-mba', [0x0D]),
            ('inc*-mdc', [0x0E]),
            ('dec*-mdc', [0x0F]),
            ('and-ba', [0x1A]),
            ('xor-ba', [0x1B]),
            ('or-ba', [0x1C]),
            ('and*-mba', [0x1D]),
            ('xor*-mba', [0x1E]),
            ('or*-mba', [0x1F]),
            ('clr-cf', [0x2A]),
            ('set-cf', [0x2B]),
            ('set-ei', [0x2C]),
            ('clr-ei', [0x2D]),
            ('ret', [0x2E]),
            ('retc', [0x2F]),
            ('from-pa', [0x30]),
            ('inc', [0x31]),
            ('to-ioa', [0x32]),
            ('to-iob', [0x33]),
            ('to-ioc', [0x34]),
            ('bcd', [0x36]),
            ('timer-start', [0x38]),
            ('timer-end', [0x39]),
            ('from-timerl', [0x3A]),
            ('from-timerh', [0x3B]),
            ('to-timerl', [0x3C]),
            ('to-timerh', [0x3D]),
            ('nop', [0x3E]),
            ('dec', [0x3F]),
        ]
        
        for instruction, expected in test_cases:
            self.assemble_and_compare(instruction, expected)
    
    def test_shutdown_instruction(self):
        self.assemble_and_compare('shutdown', [0x37, 0x3E])
    
    def test_register_instructions(self):
        # inc*-reg instructions
        for reg, idx in [('ra', 0), ('rb', 1), ('rc', 2), ('rd', 3), ('re', 4)]:
            expected = [0x10 + (idx << 1)]
            self.assemble_and_compare(f'inc*-{reg}', expected)
        
        # dec*-reg instructions  
        for reg, idx in [('ra', 0), ('rb', 1), ('rc', 2), ('rd', 3), ('re', 4)]:
            expected = [0x11 + (idx << 1)]
            self.assemble_and_compare(f'dec*-{reg}', expected)
        
        # to-reg instructions
        for reg, idx in [('ra', 0), ('rb', 1), ('rc', 2), ('rd', 3), ('re', 4)]:
            expected = [0x20 + (idx << 1)]
            self.assemble_and_compare(f'to-{reg}', expected)
        
        # from-reg instructions
        for reg, idx in [('ra', 0), ('rb', 1), ('rc', 2), ('rd', 3), ('re', 4)]:
            expected = [0x21 + (idx << 1)]
            self.assemble_and_compare(f'from-{reg}', expected)
    
    def test_immediate_instructions(self):
        test_cases = [
            ('add 5', [0x40, 0x05]),
            ('add 15', [0x40, 0x0F]),
            ('sub 10', [0x41, 0x0A]),
            ('and 7', [0x42, 0x07]),
            ('xor 3', [0x43, 0x03]),
            ('or 12', [0x44, 0x0C]),
            ('r4 9', [0x46, 0x09]),
        ]
        
        for instruction, expected in test_cases:
            self.assemble_and_compare(instruction, expected)
        
        
        # test acc instruction
        self.assemble_and_compare('acc 0', [0x70])
        self.assemble_and_compare('acc 15', [0x7F])
        
        # test rarb and rcrd instructions
        self.assemble_and_compare('rarb 0', [0x50, 0x00])
        self.assemble_and_compare('rarb 255', [0x5F, 0x0F])
        self.assemble_and_compare('rcrd 128', [0x60, 0x08])
    
    def test_branch_instructions(self):
        asm_code = """
                start:
                    nop
                    bnz-a loop
                    bnz-b loop
                    beqz loop
                    bnez loop
                    beqz-cf loop
                    bnez-cf loop
                    b-timer loop
                    bnz-d loop
                loop:
                    nop
                """
        expected = [
            0x3E,
            0xA0, 0x11,
            0xA8, 0x11,
            0xB0, 0x11,
            0xB8, 0x11,
            0xC0, 0x11,
            0xC8, 0x11,
            0xD0, 0x11,
            0xD8, 0x11,
            0x3E
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_b_and_call_instructions(self):
        asm_code = """
                    b target
                    call function
                    nop
                target:
                    nop
                function:
                    ret
                """
        expected = [
            0xE0, 0x05,
            0xF0, 0x06,
            0x3E,
            0x3E,
            0x2E
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_b_bit_instruction(self):
        asm_code = """
                    b-bit 0 target
                    b-bit 1 target
                    b-bit 2 target
                    b-bit 3 target
                target:
                    nop
                """
        expected = [
            0x80, 0x08,
            0x88, 0x08,
            0x90, 0x08,
            0x98, 0x08,
            0x3E
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_byte_directive(self):
        asm_code = """
                    .byte 0x00
                    .byte 0xFF
                    .byte 0x42
                    .byte 255
                    .byte 0b11110000
                """
        expected = [0x00, 0xFF, 0x42, 0xFF, 0xF0]
        self.assemble_and_compare(asm_code, expected)
    

    def test_labels(self):
        asm_code = """
                    start:
                        nop
                    loop1: nop
                        b loop2
                    loop2:
                        b start
                    """
        expected = [
            0x3E,
            0x3E,
            0xE0, 0x04,
            0xE0, 0x00
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_inline_labels(self):
        asm_code = """
                    start: nop
                    loop: inc
                    end: dec
                    """
        expected = [0x3E, 0x31, 0x3F]
        self.assemble_and_compare(asm_code, expected)
    
    def test_comments(self):
        asm_code = """
                    #  Comment to
                    nop # comments uli to
                        inc # isa pang comment
                        # putangina daming comments
                        dec
                    """
        expected = [0x3E, 0x31, 0x3F]
        self.assemble_and_compare(asm_code, expected)
    
    def test_case_insensitivity(self):
        asm_code = """
                    NOP
                    NoP
                    nOp
                    INC
                    DEC
                    to-Ra
                    TO-ra
                    """
        expected = [0x3E, 0x3E, 0x3E, 0x31, 0x3F, 0x20, 0x20]
        self.assemble_and_compare(asm_code, expected)
    
    def test_hex_output_format(self):
        asm_code = """
                    nop
                    inc
                    dec
                    """
        self.assemble_and_compare(asm_code, [0x3E, 0x31, 0x3F], format='hex')
    
    def test_hex_output_16_byte_lines(self):
        # create tayo 20 nop instructions
        asm_code = '\n'.join(['nop'] * 20)
        expected = [0x3E] * 20
        self.assemble_and_compare(asm_code, expected, format='hex')
    
    # Error testing
    def test_invalid_output_format(self):
        test_file = self.create_test_file('nop')
        with pytest.raises(InvalidOutputFormatError) as exc_info:
            self.assembler.assemble_code(test_file, 'txt')
    
    def test_unknown_instruction_error(self):
        test_file = self.create_test_file('invalid-instruction')
        with pytest.raises(UnknownInstructionError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
    
    def test_empty_label_error(self):
        test_file = self.create_test_file(':')
        with pytest.raises(EmptyLabelError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
    
    def test_duplicate_label_error(self):
        """Test duplicate label error"""
        asm_code = """
                    loop:
                        nop
                    loop:
                        inc
                    """
        test_file = self.create_test_file(asm_code)
        with pytest.raises(DuplicateLabelError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
    
    def test_invalid_label_name_error(self):
        test_file = self.create_test_file('123invalid:')
        with pytest.raises(InvalidLabelNameError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
    
    def test_invalid_register_error(self):
        test_file = self.create_test_file('inc*-rf')
        with pytest.raises(InvalidRegisterError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('dec*-rf')
        with pytest.raises(InvalidRegisterError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('inc*-ab')
        with pytest.raises(InvalidRegisterError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
        
        test_file = self.create_test_file('to-rf')
        with pytest.raises(InvalidRegisterError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
        
        test_file = self.create_test_file('from-rf')
        with pytest.raises(InvalidRegisterError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
    
    def test_missing_operand_error(self):
        test_file = self.create_test_file('add')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('sub')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('or')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('xor')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('or')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
        
        test_file = self.create_test_file('r4')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
        
        test_file = self.create_test_file('timer')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('add 10 10')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('sub 10 10')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('or 10 10')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('xor 10 10')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('or 10 10')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
        
        test_file = self.create_test_file('r4 10 10')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
        
        test_file = self.create_test_file('timer 10 10')
        with pytest.raises(MissingOperandError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
    
    def test_immediate_overflow_4bit(self):
        test_file = self.create_test_file('add 16')
        with pytest.raises(ImmediateOverflowError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('sub 16')
        with pytest.raises(ImmediateOverflowError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('or 16')
        with pytest.raises(ImmediateOverflowError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

        test_file = self.create_test_file('xor 16')
        with pytest.raises(ImmediateOverflowError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
        
        test_file = self.create_test_file('r4 16')
        with pytest.raises(ImmediateOverflowError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
        
        test_file = self.create_test_file('timer 16')
        with pytest.raises(ImmediateOverflowError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')

    
    def test_byte_value_error(self):
        test_file = self.create_test_file('.byte 0x100')
        with pytest.raises(ByteValueError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
        assert "Byte value 256 must be between 0x00 and 0xFF" in str(exc_info.value)
    
    def test_invalid_bit_position_error(self):
        test_file = self.create_test_file('b-bit 4 target')
        with pytest.raises(InvalidBitPositionError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
    
    
    def test_invalid_directive_error(self):
        test_file = self.create_test_file('.text')
        with pytest.raises(InvalidDirectiveError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
    
    def test_address_out_of_range_error(self):
        test_file = self.create_test_file('b 0x1000')
        with pytest.raises(AddressOutOfRangeError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
    
    def test_input_file_not_found(self):
        with pytest.raises(InputFileError) as exc_info:
            self.assembler.assemble_code('nonexistent.s', 'bin')
    
    # edge cases and comprehensive tests
    def test_empty_file(self):
        self.assemble_and_compare('', [])
    
    def test_only_comments_and_whitespace(self):
        asm_code = """
                # Just comments
                    # More comments
                        
                # And whitespace
                """
        self.assemble_and_compare(asm_code, [])
    
    def test_all_number_formats(self):
        asm_code = """
                        add 10      # decimal
                        add 0xA     # hex lowercase
                        add 0XA     # hex uppercase
                        add 0b1010  # binary
                    """
        expected = [0x40, 0x0A, 0x40, 0x0A, 0x40, 0x0A, 0x40, 0x0A]
        self.assemble_and_compare(asm_code, expected)
    
    def test_label_forward_reference(self):
        asm_code = """
                    b end
                    nop
                    nop
                end:
                    inc
                """
        expected = [0xE0, 0x04, 0x3E, 0x3E, 0x31]
        self.assemble_and_compare(asm_code, expected)
    
    def test_complex_program(self):
        asm_code = """
main:
    acc 0           # Initialize accumulator
    to-ra           # Store in RA
loop:
    from-ra         # Load from RA
    inc             # Increment
    to-ra           # Store back
    sub 10          # Compare with 10
    bnez loop       # Loop if not zero
    shutdown        # End program
"""
        expected = [
            0x70,
            0x20,
            0x21,
            0x31,
            0x20,
            0x41, 0x0A,
            0xB8, 0x02,
            0x37, 0x3E
        ]
        self.assemble_and_compare(asm_code, expected)
    
    
    def test_label_as_immediate(self):
        asm_code = """
                    nop
                    nop
                target:
                    b-bit 0 target
                    bnz-a target
                    b target
                    call target
                """

        expected = [
            0x3E,
            0x3E,
            0x80, 0x02,
            0xA0, 0x02,
            0xE0, 0x02,
            0xF0, 0x02
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_maximum_address_values(self):
        # For 11-bit addresses (branch instructions)
        asm_code = """
                    bnz-a 0x7FF
                    beqz 2047
                """
        expected = [
            0xA7, 0xFF,
            0xB7, 0xFF
        ]
        self.assemble_and_compare(asm_code, expected)
        
        # For 12-bit addresses (b and call)
        asm_code = """
                        b 0xFFF
                        call 4095
                    """
        expected = [
            0xEF, 0xFF,
            0xFF, 0xFF
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_inline_label_with_byte_directive(self):
        asm_code = """
                    data: .byte 0x42
                        .byte 0xFF
                    end: nop
                    """
        expected = [0x42, 0xFF, 0x3E]
        self.assemble_and_compare(asm_code, expected)
    
    def test_all_registers_in_different_instructions(self):

        asm_code = """
                    to-ra
                    to-rb
                    to-rc
                    to-rd
                    to-re
                    from-ra
                    from-rb
                    from-rc
                    from-rd
                    from-re
                    inc*-ra
                    inc*-rb
                    inc*-rc
                    inc*-rd
                    inc*-re
                    dec*-ra
                    dec*-rb
                    dec*-rc
                    dec*-rd
                    dec*-re
                """
        expected = [
            0x20, 0x22, 0x24, 0x26, 0x28,  # to-reg
            0x21, 0x23, 0x25, 0x27, 0x29,  # from-reg
            0x10, 0x12, 0x14, 0x16, 0x18,  # inc*-reg
            0x11, 0x13, 0x15, 0x17, 0x19   # dec*-reg
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_whitespace_variations(self):
        asm_code = """
                    nop
                        nop
                            nop
                    nop	# tab before comment
                        inc	# tab at start
                            dec		# multiple tabs
                    """
        expected = [0x3E, 0x3E, 0x3E, 0x3E, 0x31, 0x3F]
        self.assemble_and_compare(asm_code, expected)
    
    def test_edge_case_immediate_values(self):
        asm_code = """
                    add 0
                    add 15
                    sub 0
                    sub 15
                    timer 0
                    acc 0
                    acc 15
                    rarb 0
                    rarb 255
                    rcrd 0
                    rcrd 255
                """
        expected = [
            0x40, 0x00,
            0x40, 0x0F,
            0x41, 0x00,
            0x41, 0x0F,
            0x47, 0x00,
            0x70,
            0x7F,
            0x50, 0x00,
            0x5F, 0x0F,
            0x60, 0x00,
            0x6F, 0x0F
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_consecutive_labels(self):
        asm_code = """
                label1:
                label2:
                label3:
                    nop
                    b label1
                    b label2
                    b label3
                """
        expected = [
            0x3E,
            0xE0, 0x00,
            0xE0, 0x00,
            0xE0, 0x00
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_label_with_underscore_and_numbers(self):
        asm_code = """
                    _start:
                        nop
                    loop_1:
                        nop
                    test_123_end:
                        nop
                        b _start
                        b loop_1
                        b test_123_end
                    """
        expected = [
            0x3E,
            0x3E,
            0x3E,
            0xE0, 0x00,
            0xE0, 0x01,
            0xE0, 0x02
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_byte_directive_with_all_formats(self):
        asm_code = """
                    .byte 42
                    .byte 0x2A
                    .byte 0X2a
                    .byte 0b00101010
                """
        expected = [42, 42, 42, 42]
        self.assemble_and_compare(asm_code, expected)
    
    def test_program_near_address_limit(self):

        nop_count = 65530
        asm_code = '\n'.join(['nop'] * nop_count)
        expected = [0x3E] * nop_count
        self.assemble_and_compare(asm_code, expected)

    
    def test_special_two_byte_combinations(self):
        asm_code = """
                    # Immediate arithmetic
                    add 0b1111
                    sub 0xF
                    and 15
                    xor 0b0101
                    or 0xa
                    
                    # Special cases
                    r4 7
                    
                    # rarb/rcrd patterns
                    rarb 0b10100101
                    rcrd 0x3C
                """
        expected = [
            0x40, 0x0F,
            0x41, 0x0F,
            0x42, 0x0F,
            0x43, 0x05,
            0x44, 0x0A,
            0x46, 0x07,
            0x55, 0x0A,
            0x6C, 0x03
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_error_line_numbers(self):
        asm_code = """
                    nop
                    # Comment line
                    
                    invalid_instruction
                """
        test_file = self.create_test_file(asm_code)
        with pytest.raises(UnknownInstructionError) as exc_info:
            self.assembler.assemble_code(test_file, 'bin')
        assert "Line 5" in str(exc_info.value)
    
    def test_mixed_directives_and_instructions(self):
        asm_code = """
                    start:
                        .byte 0x00
                        nop
                        .byte 0xFF
                        inc
                    data:
                        .byte 0x12
                        .byte 0x34
                        .byte 0x56
                        .byte 0x78
                    end:
                        dec
                    """
        expected = [0x00, 0x3E, 0xFF, 0x31, 0x12, 0x34, 0x56, 0x78, 0x3F]
        self.assemble_and_compare(asm_code, expected)
    
    def test_write_output_method(self):
        test_file = self.create_test_file('nop')
        
        # Test bin output
        bin_data = self.assembler.assemble_code(test_file, 'bin')
        self.assembler.write_output(bin_data, test_file, 'bin')
        output_file = test_file.rsplit('.', 1)[0] + '.bin'
        assert os.path.exists(output_file)
        with open(output_file, 'rb') as f:
            assert f.read() == b'\x3e'
        
        # Test hex output
        hex_data = self.assembler.assemble_code(test_file, 'hex')
        self.assembler.write_output(hex_data, test_file, 'hex')
        output_file = test_file.rsplit('.', 1)[0] + '.hex'
        assert os.path.exists(output_file)
        with open(output_file, 'rb') as f:
            assert f.read() == b'3e'

    
    def test_timer_related_instructions(self):
        asm_code = """
                    timer 10
                    timer-start
                    from-timerl
                    from-timerh
                    to-timerl
                    to-timerh
                    b-timer running
                    timer-end
                running:
                    nop
                """
        expected = [
            0x47, 0x0A,
            0x38,
            0x3A,
            0x3B,
            0x3C,
            0x3D,
            0xD0, 0x0A,
            0x39,
            0x3E
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_io_instructions(self):
        asm_code = """
                    acc 5
                    to-ioa
                    acc 10
                    to-iob
                    acc 15
                    to-ioc
                    from-pa
                """
        expected = [
            0x75,
            0x32,
            0x7A,
            0x33,
            0x7F,
            0x34,
            0x30
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_arithmetic_operations(self):
        asm_code = """
                # Addition operations
                add-mba
                addc-mba
                add 5
                inc
                inc*-mba
                inc*-mdc
                inc*-ra
                
                # Subtraction operations
                sub-mba
                subc-mba
                sub 7
                dec
                dec*-mba
                dec*-mdc
                dec*-rb
                
                # BCD operation
                bcd
            """
        expected = [
            0x09,
            0x08,
            0x40, 0x05,
            0x31,
            0x0C,
            0x0E,
            0x10,
            0x0B,
            0x0A,
            0x41, 0x07,
            0x3F,
            0x0D,
            0x0F,
            0x13,
            0x36
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_logical_operations(self):
        asm_code = """
                    # AND operations
                    and-ba
                    and*-mba
                    and 0b1010
                    
                    # XOR operations
                    xor-ba
                    xor*-mba
                    xor 0x5
                    
                    # OR operations
                    or-ba
                    or*-mba
                    or 12
                """
        expected = [
            0x1A,
            0x1D,
            0x42, 0x0A,
            0x1B,
            0x1E,
            0x43, 0x05,
            0x1C,
            0x1F,
            0x44, 0x0C
        ]
        self.assemble_and_compare(asm_code, expected)
    
    def test_rotation_operations(self):
        """Test all rotation operations"""
        asm_code = """
                    rot-r
                    rot-l
                    rot-rc
                    rot-lc
                """
        expected = [0x00, 0x01, 0x02, 0x03]
        self.assemble_and_compare(asm_code, expected)
    
    def test_memory_operations(self):
        asm_code = """
                from-mba
                to-mba
                from-mdc
                to-mdc
            """
        expected = [0x04, 0x05, 0x06, 0x07]
        self.assemble_and_compare(asm_code, expected)
    
    def test_control_flow_operations(self):
        asm_code = """
                    ret
                    retc
                    set-ei
                    clr-ei
                    set-cf
                    clr-cf
                """
        expected = [0x2E, 0x2F, 0x2C, 0x2D, 0x2B, 0x2A]
        self.assemble_and_compare(asm_code, expected)
    
    def test_branch_conditions_comprehensive(self):
        asm_code = """
                start:
                    # Test each branch type
                    bnz-a near
                    bnz-b near
                    beqz near
                    bnez near
                near:
                    beqz-cf far
                    bnez-cf far
                    b-timer far
                    bnz-d far
                far:
                    b-bit 0 start
                    b-bit 1 near
                    b-bit 2 far
                    b-bit 3 end
                end:
                    b start
                    call near
                """
        test_file = self.create_test_file(asm_code)
        result = self.assembler.assemble_code(test_file, 'bin')
        assert len(result) == 28  # 14 instructions, most 2 bytes each
    
    def test_hex_format_multiple_lines(self):
        # Generate 50 bytes of data
        asm_code = '\n'.join(['.byte 0x{:02x}'.format(i) for i in range(50)])
        test_file = self.create_test_file(asm_code)
        result = self.assembler.assemble_code(test_file, 'hex')
        
        lines = result.decode('ascii').split('\n')
        assert len(lines) == 4  # 16 + 16 + 16 + 2 bytes
        
        # Check first line has 16 bytes
        assert len(lines[0].split()) == 16
        # Check last line has 2 bytes
        assert len(lines[3].split()) == 2
    
    def test_extreme_forward_reference(self):
        nop_count = 1000
        asm_code = 'b end\n' + '\n'.join(['nop'] * nop_count) + '\nend: shutdown'
        test_file = self.create_test_file(asm_code)
        result = self.assembler.assemble_code(test_file, 'bin')
        
        assert result[0] == 0xE3  # b instruction with high bits
        assert result[1] == 0xEA  # low bits of address (1002)
    
    def test_no_trailing_newline(self):
        test_file = self.create_test_file('nop')
        with open(test_file, 'rb') as f:
            content = f.read()
        content = content.rstrip()
        with open(test_file, 'wb') as f:
            f.write(content)
        
        result = self.assembler.assemble_code(test_file, 'bin')
        assert result == bytes([0x3E])
    
    def test_too_many_operands(self):
        test_file = self.create_test_file('add 5 10')
        with pytest.raises(MissingOperandError):
            self.assembler.assemble_code(test_file, 'bin')
    
    def test_final_integration(self):
        asm_code = """
                # Memory-mapped LED test program
                start:
                    acc 0
                    to-ra               # Initialize counter
                    
                main_loop:
                    from-ra             # Get counter
                    to-mba              # Store pattern to LED memory
                    
                    inc                 # Increment pattern
                    to-ra               # Save counter
                    
                    # Delay
                    acc 15
                delay_loop:
                    dec
                    bnez delay_loop
                    
                    # Check if we've done all patterns
                    from-ra
                    sub 15
                    bnez main_loop
                    
                    shutdown
                """

        expected = [
            0x70,
            0x20,
            0x21,
            0x05,
            0x31,
            0x20,
            0x7F,
            0x3F,
            0xB8, 0x07,
            0x21,
            0x41, 0x0F,
            0xB8, 0x02,
            0x37, 0x3E
        ]
        self.assemble_and_compare(asm_code, expected)
