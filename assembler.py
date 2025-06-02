import re
import sys

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
        # inc*-reg and dec*-reg (0x10 - 0x19)
        'and-ba': 0x1A,
        'xor-ba': 0x1B,
        'or-ba': 0x1C,
        'and*-mba': 0x1D,
        'xor*-mba': 0x1E,
        'or*-mba': 0x1F,
        # to-reg and from-reg  (0x20–0x29)
        'clr-cf': 0x2A,
        'set-cf': 0x2B,
        'set-ei': 0x2C,
        'clr-ei': 0x2D,
        'ret': 0x2E,
        'retc': 0x2F,
        'from-pa': 0x30,
        'inc': 0x31,
        'to-ioa': 0x32,
        'to-iob': 0x33,
        'to-ioc': 0x34,
        # 0x35 ala pa
        'bcd': 0x36,
        # 0x37 ala pa
        'timer-start': 0x38,
        'timer-end': 0x39,
        'from-timerl': 0x3A,
        'from-timerh': 0x3B,
        'to-timerl': 0x3C,
        'to-timerh': 0x3D,
        'nop': 0x3E,
        'dec': 0x3F,
    }
        
        # btw placeholder lang for bit manipulation e2
        self.branch_instructions = {
            'bnz-a': 0xA0,
            'bnz-b': 0xA8,
            'beqz': 0xB0,
            'bnez': 0xB8,
            'beqz-cf': 0xC0,
            'bnez-cf': 0xC8,
            'b-timer': 0xD0,
            'bnz-d': 0xD8
    }
        
        self.registers = {
            'ra': 0,
            'rb': 1,
            'rc': 2,
            'rd': 3,
            're': 4,
            #'RF': 5,
    }
        self.current_address = 0
        self.labels: dict[str, int] = {}
        self.output: list[str] = []
        
    def parse_immediate_values(self, value: str) -> int:
        value = value.strip()
        if value.startswith('0x') or value.startswith('0X'):
            return int(value, 16)
        elif value.startswith('0b'):
            return int(value, 2)
        else:
            return int(value)
    
    def parse_line(self, line: str):
        # for comments in code
        comment_position = line.find('#')
        if comment_position >= 0:
            line = line[:comment_position]
        
        # linisin yung line
        line = line.strip()

        # walang line
        if not line:
            return None
        
        # labels TODO (if kaya)
        if ':' in line:
            label_pos = line.find(':')
            label = line[:label_pos].strip()
            rest = line[label_pos + 1:].strip()
            
            if not label:
                raise ValueError("Empty label")
            
            if rest:
                return ('inline_label', (label, rest))
            else:
                return ('label', label)

        # .byte
        # format nito ay .byte (check kung anong value 0x)
        byte_match = re.match(r'\.byte\s+(0x[0-9a-fA-F]{1,2})', line, re.IGNORECASE)
        if byte_match:

            # parse the immediate value
            val = self.parse_immediate_values(byte_match.group(1))
            
            # just in case? if overflow
            if val > 0xFF:
                print("not valid byte")
                raise ValueError(f"Value of the byte is not valid")
            return ('byte', val)

        parts = line.split()
        if parts:
            return ('instruction', parts)
        
        return None
    
    def decode_address(self, operand: str):
        operand = operand.strip()
        if label_pos := operand.find(':'):
            operand = operand[label_pos:]

        if operand in self.labels:
            return self.labels[operand]
        else:
            return self.parse_immediate_values(operand)
    
    def encode_instruction(self, parts: list[str], iteration: int)-> list[int]:
        if not parts:
            return []
        
        instruction = parts[0].lower()

        if instruction in self.single_byte_instructions:
            return [self.single_byte_instructions[instruction]]
        
        def register_encoded_values(instruction_number: int, register: str) -> list[int]:
            if register.lower() not in self.registers:
                print("Wala yung register")
                raise ValueError
            
            register_index = self.registers[register]
            return [instruction_number + (register_index << 1)]
        
        # mga kelangan ng register
        find_dash = instruction.find('-')
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
        
        # for immediate instructions
        if len(parts) > 1 and parts[0] not in ['b', 'call']:
            # TODO fix if overflow
            immediate_two_bit = self.parse_immediate_values(parts[1])
            immediate_two_bit = self.parse_immediate_values(parts[1]) & 0xFF
            
            immediate = self.parse_immediate_values(parts[1])
            immediate = immediate & 0x0F

            match instruction:
                case 'add':
                    return [0x40, immediate]
                case 'sub':
                    return [0x41, immediate]
                case 'and':
                    return [0x42, immediate]
                case 'xor':
                    return [0x43, immediate]
                case 'or':
                    return [0x44, immediate]
                case 'r4':
                    return [0x46, immediate]
                case 'timer':
                    return [0x47, immediate]
                case 'acc':
                    return [0x70 | immediate]
                case 'rarb':
                    yyyy = (immediate_two_bit >> 4) & 0x0F
                    xxxx = immediate_two_bit & 0x0F
                    return [0x50 | xxxx, 0x00 | yyyy]
                case 'rcrd':
                    yyyy = (immediate_two_bit >> 4) & 0x0F
                    xxxx = immediate_two_bit & 0x0F
                    return [0x60 | xxxx, 0x00 | yyyy]
        
        if instruction == 'b-bit':
            kk = self.parse_immediate_values(parts[1])
            if kk > 3:
                print("2 bits nga lang stupid")
                raise ValueError
            kk = kk & 0x03
            if iteration == 2:
                target_address = self.decode_address(parts[2])
                new_address = target_address & 0x7FF
                first_byte = 0x80 | (kk << 3) | ((new_address >> 8) & 0x07)
                second_byte = new_address & 0xFF
                return [first_byte, second_byte]
            else:
                return [0, 0]
            
        # branch instructions
        if instruction in self.branch_instructions and len(parts) > 1:
            if iteration == 2:
                target_address = self.decode_address(parts[1])
                new_address = target_address & 0x7FF
                first_byte = self.branch_instructions[instruction] | ((new_address >> 8) & 0x07)
                second_byte = new_address & 0xFF
                return [first_byte, second_byte]
            else:
                return [0, 0]
        
        # b instructions or jump ata to
        if instruction == 'b' and len(parts) > 1:
            if iteration == 2:
                target_address = self.decode_address(parts[1])
                new_address = target_address & 0xFFF
                first_byte = 0xE0 | ((new_address >> 8) & 0x0F)
                second_byte = new_address & 0xFF
                return [first_byte, second_byte]
            else:
                return [0, 0]
        
        if instruction == 'call' and len(parts) > 1:
            if iteration == 2:
                target_address = self.decode_address(parts[1])
                new_address = target_address & 0xFFF
                first_byte = 0xF0 | ((new_address >> 8) & 0x0F)
                second_byte = new_address & 0xFF
                return [first_byte, second_byte]
            else:
                return [0, 0]
        print(f"invalid instruction {parts}")
        raise ValueError
        

    def convert_to_hex_format(self):
        hexadecimal_output: list[str] = []

        for i in range(0, len(self.output), 16):
            chunk = self.output[i:i+16]
            hexadecimal = ' '.join(f'{b:02x}' for b in chunk)
            hexadecimal_output.append(hexadecimal)
        
        return '\n'.join(hexadecimal_output).encode('ascii')

    def assemble_code(self, input_file: str, output_format: str) -> bytes:

        with open(input_file, 'r') as f:
            lines = f.readlines()

        # TODO (if kaya) labels 
        # idea! 2 iterations to calculate yung address nung labels so we know where to jump tas store the address na lang
        self.current_address = 0

        for line_number, line in enumerate(lines, 1):
            try:
                parsed = self.parse_line(line)
                if not parsed:
                    continue

                command_type, data = parsed

                if command_type == 'label':
                    if data in self.labels:
                        print("nagamit na")
                        raise ValueError
                    self.labels[data] = self.current_address
                elif command_type == 'inline_label':
                    label, instruction_data = data
                    if label in self.labels:
                        print("nagamit na")
                        raise ValueError
                    self.labels[label] = self.current_address

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

            except Exception as e:
                print(f"error on first pass, {line}")
                raise ValueError(f"Error on line {line_number}, with error {str(e)}")


        self.current_address = 0
        self.output: list[int] = []

        for line_number, line in enumerate(lines, 1):
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

            except Exception as e:
                print("bobo ka tanga tanga ka")
                raise ValueError(f"Error on line {line_number}, with error {str(e)}")


        # output check
        if output_format == 'bin':
            return bytes(self.output)
        elif output_format == 'hex':
            return self.convert_to_hex_format()
        else:
            print("Unknown format, bobo ka ba?")
            raise ValueError(f"Unknown format, bobo ka ba?")

    def write_output(self, output_data: bytes, input_name: str, output_format: str):
        file_name = input_name.rsplit('.', 1)[0]
        if output_format == 'bin':
            output_file_name = file_name + '.bin'
        else:
            output_file_name = file_name + '.hex'

        with open(output_file_name, 'wb') as f:
            f.write(output_data)
        print(self.labels)
        print("Assembled fuck you")
                            
    
        

