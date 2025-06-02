# WE'RE LIMITED TO MEMORY FROM 0 to 255

# Memory Mappings
# snake's body [0 to 63] or [0x00 to 0x3F], so we can separate snake state and output state, also this is 0-indexed unlike the LED matrix addresses where you still need to convert
# snake's current length [64] or [0x40]
# direction [65] or [0x41]
# head index [66] or [0x42], values ranges from 0 to 63 
# food index [67] or [0x43], values ranges from 0 to 63 
# delay [68] or [0x44]
# score [69] or [0x45]

# iniisip ko sana if merong precalculated index for the new updated pos of snake for N,S,W,E pero memory expensive pala

# this is where the emulator puts the info about which keys are pressed
# ioa [176] or [0xB0]
# iob [177] or [0xB1]
# ioc [178] or [0xB2]

# led matrix/grid [192 to 255] or [0xC0 to 0xFF]

# ========== start ========== 
start:
    # clear everything
    acc 0x0
    rarb 0x0C # set RB to 0xC and RA to 0x0, which is the start address of LED matrix

clear_leds:
    to-mba # MEM[RBRA] to 0, LED off
    inc*-ra # RA++, inner loop from 0->...->F->0
    bnz-a next_row # if tapos na matraverse ng RA buong column sa isang row (that is 0xF->0x0), next row naman
    b clear_leds # else, keep traversing the whole column of this row

next_row:
    inc*-rb # RB++, outer loop from 0->...->F->0
    bnz-b clear_leds # if hindi pa rin tapos magtraverse RB (that is hindi pa 0xF->0x0), keep clearing other columns pa

    # at this point, 0xC0 and 0xFF are all cleared
    b initialize_states

initialize_states:
    # 1. initialize state length in mem
    acc 0x3
    rarb 0x04
    to-mba # MEM[0x40] = 0x3


    # 2. initialize direction (right) in mem
    acc 0x1
    rarb 0x14
    to-mba # MEM[0x41] = 0x1


    # 3. initialize delay in mem
    acc 0x5
    rarb 0x44
    to-mba # MEM[0x44] = 0x5


    # 4. initialize score in mem
    acc 0x0
    rarb 0x54
    to-mba # MEM[#45] = 0x0

    # MALI PA TONG PART BECOZ ACC SKILL ISSUE
    # 5. place snake body in center LED = (0xD9, 0xDA, 0xDB), SNAKEBODY = (25, 26, 27)
    # 5.1 place head index first
    acc 0xB1
    rarb 0x24
    to-mba # MEM[0x42] = 0xB1 (reverse because of how to-mba works, will be helpful for future reads)

    # 5.2 reflect the grid index of each body position in snake's body array
    # body[0] = 0xD9 (tail)
    acc 0x9D
    rarb 0x00
    to-mba # MEM[0x00] = 0x9D

    # body[1] = 0xDA (chest)
    acc 0xAD
    rarb 0x01
    to-mba # MEM[0x01] = 0xAD

    # body[2] = 0xDB (head)
    acc 0xBD
    rarb 0x02
    to-mba # MEM[0x02] = 0xBD


    # 6. light snake in the led matrix (light up 0xD9, 0xDA, 0xDB)


    # 7. spawn initial food randomly (generate a random index to be reflected in led matrix)

    # 8. actually light up the food led

    # 9. finish! proceed to game loop

# ========== main game loop ========== 





# ========== game over ========== 


