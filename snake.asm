# WE'RE LIMITED TO MEMORY FROM 0 to 255

# Memory Mappings
# RAM [0 to 119] or [0x00 to 0x77], this is where we'll do some computations
# direction [128] or [0x80], 0=up, 1=right, 2=down, 3=left
# head index [129, 130] or [0x81, 0x82], two alloted for [row, col]
# tail index [131, 132] or [0x83, 0x84], two alloted for [row, col]
# food index [133, 134] or [0x85, 0x86], two alloted for [row, col]
# delay [135] or [0x87], delay for each frame
# score [136, 137] or [0x88, 0x89], two alloted since max score is 61

# precomputed coordinates to ng LED matrix so madali magtranslate ng row, col coords
# high nibble [138 to 145] or [0x8A to 0x91]
# low nibble [146 to 153] or [0x92 to 0x99]

# 0x8A:  0xC  # high4(0xC0) = 0xC
# 0x8B:  0xC  # high4(0xC8) = 0xC
# 0x8C:  0xD  # high4(0xD0) = 0xD
# 0x8D:  0xD  # high4(0xD8) = 0xD
# 0x8E:  0xE  # high4(0xE0) = 0xE
# 0x8F:  0xE  # high4(0xE8) = 0xE
# 0x90:  0xF  # high4(0xF0) = 0xF
# 0x91:  0xF  # high4(0xF8) = 0xF

# 0x92:  0x0  # low4(0xC0) = 0x0
# 0x93:  0x8  # low4(0xC8) = 0x8
# 0x94:  0x0  # low4(0xD0) = 0x0
# 0x95:  0x8  # low4(0xD8) = 0x8
# 0x96:  0x0  # low4(0xE0) = 0x0
# 0x97:  0x8  # low4(0xE8) = 0x8
# 0x98:  0x0  # low4(0xF0) = 0x0
# 0x99:  0x8  # low4(0xF8) = 0x8

# this is where the emulator puts the info about which keys are pressed
# ioa [176] or [0xB0], 0001=up, 0010=right, 0100=down, 1000=left 
# iob [177] or [0xB1] (unused so far)
# ioc [178] or [0xB2] (unused so far)

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

    # else, 0xC0 to 0xFF are all cleared
    b initialize_states

initialize_states:
    # 1. initialize direction (right) in mem
    acc 0x1
    rarb 0x80
    to-mba # MEM[0x80] = 0x1


    # 2. initialize delay in mem
    acc 0x5
    rarb 0x87
    to-mba # MEM[0x87] = 0x5


    # 3. initialize score in mem
    acc 0x0
    rarb 0x88
    to-mba # MEM[0x88] = 0x0
    rarb 0x89
    to-mba # MEM[0x89] = 0x0


    # 5. place snake body in center LED = [0xD9, 0xDA, 0xDB]
    # 5.1 put head coords (3,3) to MEM[0x81] and MEM[0x82] respectively
    acc 0x3
    rarb 0x81
    to-mba
    rarb 0x82
    to-mba

    # 5.2 put tail coords (1,3) to MEM[0x83] and MEM[0x84] respectively
    acc 0x1
    rarb 0x83
    to-mba
    acc 0x3
    rarb 0x84
    to-mba

    # 5.3 light up the snake in the led matrix
    acc 0x1
    rarb 0xD9
    to-mba
    rarb 0xDA
    to-mba
    rarb 0xDB
    to-mba


    # 6. spawn the first food initially beside the snake LED = [0xDE]
    # 6.1 put food coords (3,7) to MEM[0x85] and MEM[0x86] respectively
    acc 0x3
    rarb 0x85
    to-mba
    acc 0x7
    rarb 0x86
    to-mba

    # 6.2 light up the food in the led matrix
    acc 0x1
    rarb 0xDE
    to-mba


# ========== main game loop ========== 
game_loop:
    timer-start # begin counting (increments every 4 clock edges)

    acc 0x1
    b write_led

after_write_led:
    # we update direction here by reading from IOA
    b read_keypad

after_read_keypad:
    # here we do the following:
    # - compute new head/tail based from direction from IOA
    # - handle head to bounds or head to body collisions
    # - eating 
    # - detecting game over
    b move_snake

after_move:
    # TODO: put a delay here for the next frame
    b game_loop
# /========== main game loop ==========/ 



# ========== write_led ========== 
write_led:
    # idk what to do here
    b after_write_led
# /========== write_led ==========/


# ========== read_led ========== 
read_keypad:
    rarb 0xB0 # IOA
    from-mba # ACC = IOA nibble
    beqz no_keypad # if ACC is zero, no key is pressed and keep old direction

    # else, update direction variable MEM[0x80]
    # start detecting which direction IOA is telling
    b check_up

check_up: # if IOA=0001, set direction variable to up
    rarb 0xB0 # IOA
    acc 0x1
    and-ba # ACC = 0b0001 & MEM[IOA]
    beqz check_right # if ACC is not 1, it must be other direction
    
    # else, set direction to up
    acc 0x0 
    rarb 0x80 
    to-mba # set MEM[0x80] = 0x0
    b done_read

check_right: # if IOA=0010, set direction variable to right
    rarb 0xB0 # IOA
    acc 0x2
    and-ba # ACC = 0b0010 & MEM[IOA]
    beqz check_down # if ACC is not 1, it must be other direction

    # else, set direction to right
    acc 0x1
    rarb 0x80
    to-mba # set MEM[0x80] = 0x1
    b done_read

check_down: # if IOA=0100, set direction variable to down
    rarb 0xB0 # IOA
    acc 0x4
    and-ba # ACC = 0b0100 & MEM[IOA]
    beqz check_left # if ACC is not 1, it must other direction

    # else, set direction to down
    acc 0x2
    rarb 0x80
    to-mba # set MEM[0x80] = 0x2
    b done_read

check_left: # if IOA=1000, set direction variable to left
    rarb 0xB0 # IOA
    acc 0x8
    and-ba # ACC = 0b1000 & MEM[IOA]
    beqz no_keypad # we've exhausted all directions, so illegal key 'to

    # else, set direction to left
    acc 0x3
    rarb 0x80
    to-mba # set MEM[0x80] = 0x3
    b done_read

no_keypad:
    b after_read_keypad
done_read:
    b after_read_keypad
# /========== read_led ==========/



# ========== move_snake ==========
move_snake:
    # load head_row into RA
    rarb 0x81
    from-mba # ACC = MEM[0x81]
    to-ra # REG[RA] = ACC

    # load head_col into RB
    rarb 0x82
    from-mba # ACC = MEM[0x82]
    to-rb # REG[RB] = ACC

    # load direction into RC
    rarb 0x80
    from-mba # ACC = MEM[0x80]
    to-rc # REC[RC] = ACC

    # calculate new_head_row, new_head_col (check walls -> collision)
    from-rc # ACC = REG[RC]
    beqz move_up # if direction is 0x0, move up

    # else, try to move right
    sub 1
    beqz move_right # ACC - 1 = 0 would mean na right

    # else, try to move down
    sub 1
    beqz move_down # ACC - 2 = 0 would mean na down

    # else, try to move left
    sub 1
    beqz move_left # ACC - 3 = 0 would mean na left

    # pag nakarating pa dito what the fuck na lang

move_up:
    from-ra # ACC = old_head_row
    beqz collision # if old_head_row = 0, umabot sa up bounds, so DEADS

    # else, update old_head_row 
    from-ra
    sub 1 # this is valid now
    to-ra # new_head_row = old_head_row - 1

    # we don't need to update old_head_col here
    # new_head_col = old_head_col
    b check_if_self_collision 

move_right:
    from-rb # ACC = old_head_col
    sub 7
    beqz collision # if old_head_col - 7 = 0, umabot sa right bounds, so DEADS

    # else, update old_head_col
    from-rb
    add 1
    to-rb # new_head_col = old_head_col + 1

    # we don't need to update old_head_row here
    # new_head_row = old_head_row
    b check_if_self_collision

move_down:
    from-ra # ACC = old_head_row
    sub 7
    beqz collision # if old_head_row - 7 = 0, umabot sa bot bounds, so DEADS

    # else, update old_head_row
    from-ra
    add 1
    to-ra # new_head_row = old_head_row + 1

    # we don't need to update old_head_col here
    # new_head_col = old_head_col
    b check_if_self_collision

move_left:
    from-rb # ACC = old_head_col
    beqz collision # if old_head_row = 0, umabot sa left bounds, so DEADS

    # else, update old_head_col
    from-rb
    sub 1
    to-rb # new_head_col = old_head_col - 1

    # we don't need to update old_head_row here
    # new_head_row = old_head_row
    b check_if_self_collision
    
check_if_self_collision:
    # TODO: here we check if new_head_row (RA) and new_head_col (RB) collides with snake body 
    # - we do this by scanning the grid, checking if there are other indices except the head, and food that is the same with the head

    # PSEUDOCODE
    # for RC = 0x0..0x7:
    #     for RD = 0x0..0x7:
    #         if (RC, RD) == (food_row, food_col): 
    #             skip (don't treat food as a collision)
    #         else:
    #             if (RC, RD) == (RA, RB) # either this is the head itself or 
    #             the body
    #                 RE++
    # if RE == 2:
    #     # we have collided with the head coord itself, and the body itself
    #     b collision
    # else: 
    #     # no collision
    #     b check_if_food

check_if_food:
    # TODO: here we check if new_head_row (RA) and new_head_col (RB) collides with a food

    # PSEUDOCODE
    # if (food_row, food_col) == (RA, RB):
    #     b grow_the_snake
    # else:
    #     b retain_snake_length

    # 1. load the food_row from MEM[0x85]
    rcrd 0x85
    from-mdc # ACC = MEM[0x85] = food_row
    to-mba # MEM[RB:RA] = ACC = food_row (note this is safe since we've allocated memory for 0x00 to 0x77, also temporary lang)
    from-ra # ACC = new_head_row
    sub-mba # ACC = new_head_row - food_row
    bnez retain_snake_length # if new_head_row != food_row, then no food collision

    # else, another check pa
    # 2. load the food_col from MEM[0x86]
    rcrd 0x86 
    from-mdc # ACC = MEM[0x86] = food_col
    to-mba # MEM[RB:RA] = ACC = food_col
    from-rb # ACC = new_head_col
    sub-mba # ACC = new_head_col - food_col
    bnez retain_snake_length # if new_head_col != food_col, then no food collision

    # else, at this point, (food_row, food_col) == (RA, RB)
    b grow_the_snake

grow_the_snake:
    # TODO: grow by just turning on the new_head index in the LED matrix

    b after_move

retain_snake_length:
    # TODO: just move 
    # illusion lang siya, pero in reality, it's just turning off tail index and turning on head index in the LED matrix
    
    b after_move
# /========== move_snake ==========/



# ========== game over ========== 
collision:
    b game_over

game_over:
    b start
# /========== game over ==========/
