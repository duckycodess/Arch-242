import re
from exception_handler_assembler import *

class Arch242Assembler:
    def __init__(self):
        self.single_byte_instructions = {
            'rot-r': 0x00,
            'rot-l': 0x01,
            'rot-rc': 0x02,
            'rot-lc': 0x03,
            'from-mba': 0x04,
            'to-mba': 0x05,
            'from-mdc': 0x06,
            'to-mdc': 0x07,
            'addc-mba': 0x08,
            'add-mba': 0x09,
            'subc-mba': 0x0A,
            'sub-mba': 0x0B,
            'inc*-mba': 0x0C,
            'dec*-mba': 0x0D,
            'inc*-mdc': 0x0E,
            'dec*-mdc': 0x0F,
            'and-ba': 0x1A,
            'xor-ba': 0x1B,
            'or-ba': 0x1C,
            'and*-mba': 0x1D,
            'xor*-mba': 0x1E,
            'or*-mba': 0x1F,
            'clr-cf': 0x2A,
            'set-cf': 0x2B,
            'set-ei': 0x2C,
            'clr-ei': 0x2D,
            'ret': 0x2E,
            'from-ioa': 0x30,
            'inc': 0x31,
            'bcd': 0x36,
            'nop': 0x3E,
            'dec': 0x3F,
        }
        
        self.branch_instructions = {
            'bnz-a': 0xA0,
            'bnz-b': 0xA8,
            'beqz': 0xB0,
            'bnez': 0xB8,
            'beqz-cf': 0xC0,
            'bnez-cf': 0xC8,
            'bnz-d': 0xD8
        }
        
        self.registers = {
            'ra': 0,
            'rb': 1,
            'rc': 2,
            'rd': 3,
            're': 4,
        }
        
        self.current_address = 0
        self.labels: dict[str, int] = {}
        self.label_definitions: dict[str, int] = {}  # dito lang stored yung labels
        self.output: list[str] = []
        self.current_line_number = 0
        self.current_line_content = ""
        
    def parse_immediate_values(self, value: str) -> int:
        value = value.strip()
        
        try:
            if value.startswith('0x') or value.startswith('0X'):
                return int(value, 16)
            elif value.startswith('0b'):
                return int(value, 2)
            else:
                return int(value)
        except ValueError as e:
            raise InvalidNumberFormatError(
                value, 
                "Invalid number format",
                self.current_line_number,
                self.current_line_content
            )
    
    def parse_line(self, line: str):
        original_line = line
    
        comment_position = line.find('#')
        if comment_position >= 0:
            line = line[:comment_position]

        line = line.strip()

        if not line:
            return None
        
        # labels! complete na (same with RISC-V implementation)
        if ':' in line:
            label_pos = line.find(':')
            label = line[:label_pos].strip()
            rest = line[label_pos + 1:].strip()
            
            if not label:
                raise EmptyLabelError(
                    self.current_line_number,
                    original_line
                )
            
            # validate label name
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', label):
                raise InvalidLabelNameError(
                    label,
                    "Labels can only start with letter or underscore and contain only letters, numbers, and underscores",
                    self.current_line_number,
                    original_line
                )
            
            if rest:
                return ('inline_label', (label, rest))
            else:
                return ('label', label)

        byte_match = re.match(r'\.byte\s+(.+)', line, re.IGNORECASE)
        if byte_match:
            try:
                val = self.parse_immediate_values(byte_match.group(1))
                if val > 0xFF:
                    raise ByteValueError(
                        val,
                        self.current_line_number,
                        original_line
                    )
                return ('byte', val)
            except InvalidNumberFormatError:
                raise
            except ByteValueError:
                raise
            except Exception:
                raise InvalidDirectiveError(
                    line,
                    self.current_line_number,
                    original_line
                )

        if line.startswith('.'):
            directive = line.split()[0]
            raise InvalidDirectiveError(
                directive,
                self.current_line_number,
                original_line
            )

        parts = line.split()
        if parts:
            return ('instruction', parts)
        
        return None
    
    def decode_address(self, operand: str):
        operand = operand.strip()

        if operand in self.labels:
            return self.labels[operand]

        try:
            return self.parse_immediate_values(operand)
        except InvalidNumberFormatError:
            # pag di valid number, it might be an undefined label (?) not sure if tama ba pagraise ko dito
            raise UndefinedLabelError(
                operand,
                self.current_line_number,
                self.current_line_content
            )
    
    def encode_instruction(self, parts: list[str], iteration: int) -> list[int]:
        if not parts:
            return []
        
        instruction = parts[0].lower()

        if instruction in self.single_byte_instructions:
            return [self.single_byte_instructions[instruction]]
        
        def register_encoded_values(instruction_number: int, register: str) -> list[int]:
            if register.lower() not in self.registers:
                raise InvalidRegisterError(
                    register,
                    list(self.registers.keys()),
                    self.current_line_number,
                    self.current_line_content
                )
            
            register_index = self.registers[register]
            return [instruction_number + (register_index << 1)]
        
        find_dash = instruction.find('-')
        if find_dash != -1:
            immediate_instruction = instruction[:find_dash]
            regis = instruction[find_dash+1:]
            
            match immediate_instruction:
                case 'inc*':
                    return register_encoded_values(16, regis)
                case 'dec*':
                    return register_encoded_values(17, regis)
                case 'to':
                    return register_encoded_values(32, regis)
                case 'from':
                    return register_encoded_values(33, regis)

        if instruction == 'shutdown':
            return [0x37, 0x3E]
        
        known_two_byte_instructions = ['add', 'sub', 'and', 'xor', 'or', 'r4',
        'acc', 'rarb', 'rcrd', 'b', 'call', 'b-bit'] + list(self.branch_instructions.keys())
        if instruction not in known_two_byte_instructions:
            # tangina anong instruction nilagay mo pag umabot dito HAHAHAHAHAHAAHAHAHA
            raise UnknownInstructionError(
                instruction,
                self.current_line_number,
                self.current_line_content
            )

        if instruction not in ['b', 'call', 'b-bit'] and instruction not in self.branch_instructions:
            if len(parts) < 2 or len(parts) > 2:
                raise MissingOperandError(
                    instruction,
                    1,
                    self.current_line_number,
                    self.current_line_content
                )
            
            try:
                immediate_value = self.parse_immediate_values(parts[1])
            except InvalidNumberFormatError:
                raise
            
            match instruction:
                case 'add' | 'sub' | 'and' | 'xor' | 'or' | 'r4':
                    if immediate_value > 0x0F:
                        raise ImmediateOverflowError(
                            immediate_value,
                            4,
                            15,
                            self.current_line_number,
                            self.current_line_content
                        )
                    
                    opcode_map = {
                        'add': 0x40,
                        'sub': 0x41,
                        'and': 0x42,
                        'xor': 0x43,
                        'or': 0x44,
                        'r4': 0x46
                    }
                    return [opcode_map[instruction], immediate_value & 0x0F]
                
                case 'acc':
                    if immediate_value > 0x0F:
                        raise ImmediateOverflowError(
                            immediate_value,
                            4,
                            15,
                            self.current_line_number,
                            self.current_line_content
                        )
                    return [0x70 | (immediate_value & 0x0F)]
                
                case 'rarb' | 'rcrd':
                    if immediate_value > 0xFF:
                        raise ImmediateOverflowError(
                            immediate_value,
                            8,
                            255,
                            self.current_line_number,
                            self.current_line_content
                        )
                    
                    yyyy = (immediate_value >> 4) & 0x0F
                    xxxx = immediate_value & 0x0F
                    base = 0x50 if instruction == 'rarb' else 0x60
                    return [base | xxxx, yyyy]
        
        # b-bit instruction
        if instruction == 'b-bit':
            if len(parts) < 3:
                raise MissingOperandError(
                    instruction,
                    2,
                    self.current_line_number,
                    self.current_line_content
                )
            
            try:
                kk = self.parse_immediate_values(parts[1])
            except InvalidNumberFormatError:
                raise
            
            if kk > 3:
                raise InvalidBitPositionError(
                    kk,
                    3,
                    self.current_line_number,
                    self.current_line_content
                )
            
            if iteration == 2:
                try:
                    target_address = self.decode_address(parts[2])
                except (InvalidNumberFormatError, UndefinedLabelError):
                    raise
                
                if target_address > 0x7FF:
                    raise AddressOutOfRangeError(
                        target_address,
                        0x7FF,
                        self.current_line_number,
                        self.current_line_content
                    )
                
                new_address = target_address & 0x7FF
                first_byte = 0x80 | (kk << 3) | ((new_address >> 8) & 0x07)
                second_byte = new_address & 0xFF
                return [first_byte, second_byte]
            else:
                return [0, 0]
        
        # Branch instructions
        if instruction in self.branch_instructions:
            if len(parts) < 2:
                raise MissingOperandError(
                    instruction,
                    1,
                    self.current_line_number,
                    self.current_line_content
                )
            
            if iteration == 2:
                try:
                    target_address = self.decode_address(parts[1])
                except (InvalidNumberFormatError, UndefinedLabelError):
                    raise
                
                if target_address > 0x7FF:
                    raise AddressOutOfRangeError(
                        target_address,
                        0x7FF,
                        self.current_line_number,
                        self.current_line_content
                    )
                
                new_address = target_address & 0x7FF
                first_byte = self.branch_instructions[instruction] | ((new_address >> 8) & 0x07)
                second_byte = new_address & 0xFF
                return [first_byte, second_byte]
            else:
                return [0, 0]
        
        # b instruction
        if instruction == 'b':
            if len(parts) < 2:
                raise MissingOperandError(
                    instruction,
                    1,
                    self.current_line_number,
                    self.current_line_content
                )
            
            if iteration == 2:
                try:
                    target_address = self.decode_address(parts[1])
                except (InvalidNumberFormatError, UndefinedLabelError):
                    raise
                
                if target_address > 0xFFF:
                    raise AddressOutOfRangeError(
                                                target_address,
                        0xFFF,
                        self.current_line_number,
                        self.current_line_content
                    )
                
                new_address = target_address & 0xFFF
                first_byte = 0xE0 | ((new_address >> 8) & 0x0F)
                second_byte = new_address & 0xFF
                return [first_byte, second_byte]
            else:
                return [0, 0]
        
        # call instruction
        if instruction == 'call':
            if len(parts) < 2:
                raise MissingOperandError(
                    instruction,
                    1,
                    self.current_line_number,
                    self.current_line_content
                )
            
            if iteration == 2:
                try:
                    target_address = self.decode_address(parts[1])
                except (InvalidNumberFormatError, UndefinedLabelError):
                    raise
                
                if target_address > 0xFFF:
                    raise AddressOutOfRangeError(
                        target_address,
                        0xFFF,
                        self.current_line_number,
                        self.current_line_content
                    )
                
                new_address = target_address & 0xFFF
                first_byte = 0xF0 | ((new_address >> 8) & 0x0F)
                second_byte = new_address & 0xFF
                return [first_byte, second_byte]
            else:
                return [0, 0]
        

    def convert_to_hex_format(self):
        hexadecimal_output: list[str] = []
        
        for byte in self.output:
            hexadecimal_output.append(f'{byte:02x}')
        
        return '\n'.join(hexadecimal_output).encode('ascii')

    def convert_to_bin_format(self):
        binary_output: list[str] = []
        
        for byte in self.output:
            binary_output.append(f'{byte:08b}')
        
        return '\n'.join(binary_output).encode('ascii')

    def assemble_code(self, input_file: str, output_format: str) -> bytes:
        # sana naman di ka na-mistype
        if output_format not in ['bin', 'hex']:
            raise InvalidOutputFormatError(
                output_format,
                ['bin', 'hex']
            )
        
        try:
            with open(input_file, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise InputFileError(input_file, "File not found")
        except IOError as e:
            raise InputFileError(input_file, str(e))

        # unang pass, so just calculate mga addresses na tatalunan natin if ever!
        self.current_address = 0
        self.labels = {}
        self.label_definitions = {}

        for line_number, line in enumerate(lines, 1):
            self.current_line_number = line_number
            self.current_line_content = line
            
            try:
                parsed = self.parse_line(line)
                if not parsed:
                    continue

                command_type, data = parsed

                if command_type == 'label':
                    if data in self.labels:
                        raise DuplicateLabelError(
                            data,
                            self.label_definitions.get(data),
                            line_number,
                            line
                        )
                    self.labels[data] = self.current_address
                    self.label_definitions[data] = line_number
                    
                elif command_type == 'inline_label':
                    label, instruction_data = data
                    if label in self.labels:
                        raise DuplicateLabelError(
                            label,
                            self.label_definitions.get(label),
                            line_number,
                            line
                        )
                    self.labels[label] = self.current_address
                    self.label_definitions[label] = line_number

                    parsed_instruction = self.parse_line(instruction_data)
                    if parsed_instruction:
                        _, instruction_information = parsed_instruction
                        if parsed_instruction[0] == 'byte':
                            self.current_address += 1
                        elif parsed_instruction[0] == 'instruction':
                            encoded = self.encode_instruction(instruction_information, 1)
                            self.current_address += len(encoded)

                elif command_type == 'byte':
                    self.current_address += 1
                    
                elif command_type == 'instruction':
                    instruction_encoded = self.encode_instruction(data, 1)
                    self.current_address += len(instruction_encoded)

            except AssemblerError:
                raise
            except Exception as e:
                raise AssemblerError(
                    f"Unexpected error: {str(e)}",
                    line_number,
                    line
                )

        # dito, encode na natin fr
        self.current_address = 0
        self.output: list[int] = []

        for line_number, line in enumerate(lines, 1):
            self.current_line_number = line_number
            self.current_line_content = line
            
            try:
                parsed = self.parse_line(line)
                if not parsed:
                    continue

                command_type, data = parsed

                if command_type == 'label':
                    continue
                    
                elif command_type == 'inline_label':
                    label, instruction_data = data
                    parsed_instruction = self.parse_line(instruction_data)
                    if parsed_instruction:
                        _, instruction_information = parsed_instruction
                        if parsed_instruction[0] == 'byte':
                            self.current_address += 1
                            self.output.append(instruction_information)
                        elif parsed_instruction[0] == 'instruction':
                            encoded = self.encode_instruction(instruction_information, 2)
                            self.output.extend(encoded)
                            self.current_address += len(encoded)
                            
                elif command_type == 'byte':
                    self.output.append(data)
                    self.current_address += 1
                    
                elif command_type == 'instruction':
                    instruction_encoded = self.encode_instruction(data, 2)
                    self.output.extend(instruction_encoded)
                    self.current_address += len(instruction_encoded)

            except AssemblerError:
                raise
            except Exception as e:
                raise AssemblerError(
                    f"Assembling error: {str(e)}",
                    line_number,
                    line
                )

        # check lang if nagexceed ng address space
        if self.current_address > 0xFFFF:
            raise AddressOutOfRangeError(
                self.current_address,
                0xFFFF,
                None,
                "Program exceeds 16-bit instruction address space"
            )

        # generate na natin output mwehehe
        if output_format == 'bin':
            return bytes(self.output) # can use self.convert_to_bin_format()
        elif output_format == 'hex':
            return self.convert_to_hex_format()

    def write_output(self, output_data: bytes, input_name: str, output_format: str):
        file_name = input_name.rsplit('.', 1)[0]
        if output_format == 'bin':
            output_file_name = file_name + '.bin'
        else:
            output_file_name = file_name + '.hex'

        try:
            with open(output_file_name, 'wb') as f:
                f.write(output_data)
        except IOError as e:
            raise OutputFileError(output_file_name, str(e))
        
        print(f"Assembled to {output_file_name}")