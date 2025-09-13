# Arch-242 (CS 21.242 Project)


## How to Use

- **Assembler**: run `python assembler/assembler.py 
<.asm FILE> <hex/bin>` 

- **Emulator**: run `python arch242_emulator.py 
<.asm FILE/ .bin FILE>`

- **Logisim**: Open `arch_242_Logisim.circ` on Logisim Evolution v3.9 and above. Further instructions can be found inside.

- **Snake**: Run the `snake.asm` file on either the emulator or the logisim circuit (already preset). Note that `snake.asm` uses additional features provided by the assembler.

## Additional Features

To make writing in assembler smoother, certain features were added:
- **Comments**: Use `#` to start a line comment
- **Labels**: Any alphanumeric string followed by a colon will be interpreted as a label, and can be used by branching and jumping instructions instead of immediate
- **Binary/Hex Immediates**: aside from base 10 immediates, any instruction that takes in an immediate argument can parse binary (if it starts with `0b`) or hex (if it starts with `0x`).
- **Exceptions**: the assembler can detect invalid instructions, invalid arguments, invalid files et cetera. It also provides helpful errors for each exception.

To make debugging the snake game easier, certain emulator features were added:

- **Debug Panel**: The right hand side of the emulator contains the current state of the processor, along with useful information about the current instruction and specific memory addresses useful to `snake.asm`.

- **Color LEDs**: `snake.asm` utilizes different colors for specific parts of the game. This allows to differentiate the food from the snake, which is both aesthetically pleasing and useful for debugging. Running a binary or assembly file named `snake` will switch to the Color LEDs, otherwise, it will revert back to the original LED matrix.

## Demonstration
