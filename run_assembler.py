from assembler import Arch242Assembler
import sys

def run_assembler():
    if len(sys.argv) != 3:
        print("Format: python run_assembler.py <input_file> <bin | hex>")
        exit()
    
    input_file = sys.argv[1]
    format = sys.argv[2]

    if format not in ['bin', 'hex']:
        exit()
    
    assembler = Arch242Assembler()

    try:
        output_data = assembler.assemble_code(input_file, format)
        assembler.write_output(output_data, input_file, format)
    except Exception as e:
        print(e)
        exit()
run_assembler()