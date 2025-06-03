class AssemblerError(Exception):
    def __init__(self, message, line_number=None, line_content=None):
        self.line_number = line_number
        self.line_content = line_content
        
        if line_number is not None:
            message = f"Line {line_number}: {message}"
            if line_content:
                message += f"\n    {line_content.strip()}"
        
        super().__init__(message)

class SyntaxError(AssemblerError):
    # dito maiinherit yung mga basta syntax error
    pass


class EncodingError(AssemblerError):
    # so dito naman yung mga invalid registers, invalid instructions, and other illegal stuff
    pass


class LabelError(AssemblerError):
    # label related, paghandle lang para di buggy
    pass


class ValueError(AssemblerError):
    # so for value related like overflow and shit
    pass


# MGA SYNTAX ERRORS
class EmptyLabelError(SyntaxError):
    def __init__(self, line_number=None, line_content=None) -> None:
        super().__init__(
            "Empty label", 
            line_number, 
            line_content
        ) # technically ang case lang nito is mga labels named yung colon lang


class InvalidDirectiveError(SyntaxError):
    def __init__(self, directive, line_number=None, line_content=None) -> None:
        super().__init__(
            f"Invalid directive '{directive}'", 
            line_number, 
            line_content
        ) # so technically .byte lang meron tayo so dapat mahandle to such that di mamisuse yung .text and shi from ripes

class UnknownInstructionError(EncodingError):
    def __init__(self, instruction, line_number=None, line_content=None):
        super().__init__(
            f"Unknown instruction '{instruction}'", 
            line_number, 
            line_content
        ) # basta this is just instructions na like invalid or doesn't exist


class InvalidRegisterError(EncodingError):
    def __init__(self, register, valid_registers=None, line_number=None, line_content=None):
        message = f"Invalid register '{register}'"
        if valid_registers:
            message += f". Valid registers are: {', '.join(valid_registers)}"
        super().__init__(message, line_number, line_content) # self-explanatory, invalid index ng register


class MissingOperandError(EncodingError):
    def __init__(self, instruction, number, line_number=None, line_content=None):
        super().__init__(
            f"Instruction '{instruction}' requires {number} more argument(s), you may have forgotten the immediate value", 
            line_number, 
            line_content
        ) # handle natin yung mga instructions na kulang ng arguments


# Specific label errors
class DuplicateLabelError(LabelError):
    def __init__(self, label, first_definition_line=None, line_number=None, line_content=None):
        message = f"Label '{label}' is already defined"
        if first_definition_line:
            message += f" (first defined at line {first_definition_line})"
        super().__init__(message, line_number, line_content) # self-explanatory din


class UndefinedLabelError(LabelError):
    def __init__(self, label, line_number=None, line_content=None):
        super().__init__(
            f"Undefined label '{label}'", 
            line_number, 
            line_content
        ) # eh di naman nag-eexist yung label parang yung sainyo HAWHDAHJKWDHJSAHFYADs


class InvalidLabelNameError(LabelError):
    def __init__(self, label, reason, line_number=None, line_content=None):
        super().__init__(
            f"Invalid label name '{label}': {reason}", 
            line_number, 
            line_content
        ) # err basta yung label may illegal characters


class ImmediateOverflowError(ValueError):
    def __init__(self, value, max_bits, max_value, line_number=None, line_content=None):
        super().__init__(
            f"Immediate value {value} exceeds {max_bits}-bit limit (max: {max_value})", 
            line_number, 
            line_content
        ) # basta nagexceed yung allowed bits


class ByteValueError(ValueError):
    def __init__(self, value, line_number=None, line_content=None):
        super().__init__(
            f"Byte value {value} must be between 0x00 and 0xFF or in decimal, 0 and 255", 
            line_number, 
            line_content
        ) # medyo malaki na yung byte value

class InvalidBitPositionError(ValueError):
    def __init__(self, bit_position, max_position, line_number=None, line_content=None):
        super().__init__(
            f"Bit position {bit_position} is invalid (must be 0-{max_position})", 
            line_number, 
            line_content
        ) # bit position is out of range


class InvalidNumberFormatError(ValueError):
    def __init__(self, value, reason, line_number=None, line_content=None):
        super().__init__(
            f"Invalid number format '{value}': {reason}", 
            line_number, 
            line_content
        ) # bro is making up numbers


class FileError(AssemblerError):
    # Category na naghahandle ng File and I/O errors
    pass


class InputFileError(FileError):
    def __init__(self, filename, reason):
        super().__init__(f"Cannot read input file '{filename}': {reason}") # may problema siguro sa input file


class OutputFileError(FileError):
    def __init__(self, filename, reason):
        super().__init__(f"Cannot write output file '{filename}': {reason}") # may problema siguro sa output file


class InvalidOutputFormatError(FileError):
    def __init__(self, format_type, valid_formats=None):
        message = f"Invalid output format '{format_type}'"
        if valid_formats:
            message += f". Valid formats are: {', '.join(valid_formats)}"
        super().__init__(message) # what kind of output format is bro using


class AddressError(AssemblerError):
    # ig self-explanatory pero basta related with address
    pass

class AddressOutOfRangeError(AddressError):
    def __init__(self, address, max_address, line_number=None, line_content=None):
        super().__init__(
            f"Address {address} exceeds maximum address {max_address}", 
            line_number, 
            line_content
        ) # so basta nagexceed ka sa valid range of addresses nararaise to


class InvalidAddressError(AddressError):
    def __init__(self, address, reason, line_number=None, line_content=None):
        super().__init__(
            f"Invalid address '{address}': {reason}", 
            line_number, 
            line_content
        ) # what kind of address format is bro using