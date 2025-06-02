from assembler_module import Arch242Assembler
from assembler_exceptions import *
import sys

def print_error(error):
    print(f"\nAssembling Error: {error}", file=sys.stderr)

def run_assembler():
    if len(sys.argv) != 3:
        print("Usage: python run_assembler.py <input_file> <bin|hex>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_format = sys.argv[2]

    assembler = Arch242Assembler()

    try:
        output_data = assembler.assemble_code(input_file, output_format)
        assembler.write_output(output_data, input_file, output_format)
    except InputFileError as e:
        print_error(e)
        sys.exit(2)
    except InvalidOutputFormatError as e:
        print_error(e)
        sys.exit(3)
    except SyntaxError as e:
        print_error(e)
        sys.exit(4)
    except LabelError as e:
        print_error(e)
        sys.exit(5)
    except ValueError as e:
        print_error(e)
        sys.exit(6)
    except OutputFileError as e:
        print_error(e)
        sys.exit(7)
    except AssemblerError as e:
        print_error(e)
        sys.exit(8)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(9)

if __name__ == "__main__":
    run_assembler()