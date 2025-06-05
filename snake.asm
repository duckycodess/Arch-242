# WE'RE LIMITED TO MEMORY FROM 0 to 255

# this is our 8 by 8 game grid now
# 197 (bit 0-3), 198 (bit 0-3)
# 202 (bit 0-3), 203 (bit 0-3)
# 207 (bit 0-3), 208 (bit 0-3)
# 212 (bit 0-3), 213 (bit 0-3)
# 217 (bit 0-3), 218 (bit 0-3)
# 222 (bit 0-3), 223 (bit 0-3)
# 227 (bit 0-3), 228 (bit 0-3)
# 232 (bit 0-3), 233 (bit 0-3)
# TODO: we need to update our translation method to LED matrix in every function
#  - check_if_self_collision = head_row, head_col in 0xAA, 0xAB. don't forget to put translated to 0xAC, 0xAD
#  - grow_the_snake = head_row, head_col from check_if_self_collision in 0xAA, 0xAB
#  - retain_snake_length = tail_row, tail_col

# Memory Mappings
# snake body [0 to 127] or [0x00 to 0x7F], implemented queue, we can still reuse this
# we split this into rows[] and cols[] arrays so
# rows [0x00 to 0x3F]
# cols [0x40 to 0x7F]

# direction [128] or [0x80], 0=up, 1=right, 2=down, 3=left
# head index [129, 130] or [0x81, 0x82], two alloted for [row, col]
# tail index [131, 132] or [0x83, 0x84], two alloted for [row, col]
# food index [133, 134] or [0x85, 0x86], two alloted for [row, col]
# delay [135] or [0x87], delay for each frame
# score [136, 137] or [0x88, 0x89], two alloted since max score is 61, most significant ung 0x88, pero required lang naman is max score to support is 15, so we'll just read from 0x89

# precomputed coordinates para madali magtranslate ng row, col coords into LED matrix coordinates
# high nibble [144 to 151] or [0x90 to 0x97]
# low nibble [160 to 167] or [0xA0 to 0xA7]

# precomputed table
# 0x90:  0xC  # high4(0xC0) 
# 0x91:  0xC  # high4(0xC8) 
# 0x92:  0xD  # high4(0xD0) 
# 0x93:  0xD  # high4(0xD8) 
# 0x94:  0xE  # high4(0xE0) 
# 0x95:  0xE  # high4(0xE8) 
# 0x96:  0xF  # high4(0xF0) 
# 0x97:  0xF  # high4(0xF8) 

# 0xA0:  0x0  # low4(0xC0)
# 0xA1:  0x8  # low4(0xC8)
# 0xA2:  0x0  # low4(0xD0)
# 0xA3:  0x8  # low4(0xD8)
# 0xA4:  0x0  # low4(0xE0)
# 0xA5:  0x8  # low4(0xE8)
# 0xA6:  0x0  # low4(0xF0)
# 0xA7:  0x8  # low4(0xF8)

# this is where the emulator puts the info about which keys are pressed
# ioa [176] or [0xB0], 0001=up, 0010=right, 0100=down, 1000=left 

# two nibbles are alloted for each pointer since 0..63 requires 6 bits
# queue head_ptr [179, 180] or [0xB3, 0xB4]
# queue tail_ptr [181, 182] or [0xB5, 0xB6]

# led matrix/grid [192 to 255] or [0xC0 to 0xFF]

# ========== precomputed table ==========
acc 0xC
rcrd 0x90
to-mdc
rcrd 0x91
to-mdc

acc 0xD
rcrd 0x92
to-mdc
rcrd 0x93
to-mdc

acc 0xE
rcrd 0x94
to-mdc
rcrd 0x95
to-mdc

acc 0xF
rcrd 0x96
to-mdc
rcrd 0x97
to-mdc


acc 0x0
rcrd 0xA0
to-mdc
rcrd 0xA2
to-mdc
rcrd 0xA4
to-mdc
rcrd 0xA6
to-mdc

acc 0x8
rcrd 0xA1
to-mdc
rcrd 0xA3
to-mdc
rcrd 0xA5
to-mdc
rcrd 0xA7
to-mdc
# /========== precomputed table ==========/ 

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


    # 4. place snake body in center LED = [0xD9, 0xDA, 0xDB]
    # 4.1 put head coords (3,3) to MEM[0x81] and MEM[0x82] respectively
    acc 0x3
    rarb 0x81
    to-mba
    rarb 0x82
    to-mba

    # 4.2 put tail coords (3,1) to MEM[0x83] and MEM[0x84] respectively
    acc 0x3
    rarb 0x83
    to-mba
    acc 0x1
    rarb 0x84
    to-mba

    # 4.3 light up the snake in the led matrix
    acc 0x1
    rarb 0xD9
    to-mba
    rarb 0xDA
    to-mba
    rarb 0xDB
    to-mba


    # 5. enqueue each body parts in the queue
    # 5.1 enqueue (3,1) at body[0]
    # set MEM[0x00] = 0x3 (row[0] = 0x1)
    # set MEM[0x40] = 0x1 (col[0] = 0x3)
    acc 0x3
    rarb 0x00
    to-mba # MEM[0x00] = 0x3

    acc 0x1
    rarb 0x40
    to-mba # MEM[0x40] = 0x1

    # 5.2 enqueue (3,2) at body[1]
    # set MEM[0x01] = 0x3 (row[1] = 0x2)
    # set MEM[0x41] = 0x2 (col[1] = 0x3)
    acc 0x3
    rarb 0x01
    to-mba # MEM[0x01] = 0x3
    
    acc 0x2
    rarb 0x41
    to-mba # MEM[0x41] = 0x2

    # 5.3 enqueue (3,3) at body[2]
    # set MEM[0x02] = 0x3 (row[2] = 0x3)
    # set MEM[0x42] = 0x3 (col[2] = 0x3)
    acc 0x3
    rarb 0x02
    to-mba # MEM[0x02] = 0x3

    acc 0x3
    rarb 0x42
    to-mba # MEM[0x42] = 0x3

    # 5.4 set head_ptr to body[2]
    # set MEM[0xB3] = 0x0 
    # set MEM[0xB4] = 0x2 
    acc 0x0
    rarb 0xB3
    to-mba # MEM[0xB3] = 0x0

    acc 0x2
    rarb 0xB4
    to-mba # MEM[0xB4] = 0x2

    # 5.5 set tail_ptr to body[0]
    # set MEM[0xB5] = 0x0 
    # set MEM[0xB6] = 0x0 
    acc 0x0
    rarb 0xB5
    to-mba # MEM[0xB4] = 0x0

    rarb 0xB6
    to-mba # MEM[0xB6] = 0x0

    # visually, it looks like
    # tail              head
    # (1,3) -> (2,3) -> (3,3)


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

    
    # 7. read from IOA
    from-ioa # ACC = IOA
    rcrd 0xB0 
    to-mdc # MEM[0xB0] = ACC

    b game_loop
# /========== start ==========/ 


# ========== main game loop ========== 
game_loop:
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
    # - update queue
    # - update score when eating
    # - detecting game over
    b move_snake

after_move:
    # TODO: pseudo random spawning of food, depende na lang sa position ng head or tail
    b game_loop
# /========== main game loop ==========/ 



# ========== write_led ========== 
write_led:
    # this is not important, kinopya ko lang format ng game loop sa lab07
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
    xor-ba # ACC = 0b0001 ^ MEM[IOA]
    bnez check_right # if ACC is not 0, it must be other direction
    
    # else, set direction to up
    acc 0x0 
    rarb 0x80 
    to-mba # set MEM[0x80] = 0x0
    b done_read

check_right: # if IOA=0010, set direction variable to down
    rarb 0xB0 # IOA
    acc 0x2
    xor-ba # ACC = 0b0010 ^ MEM[IOA]
    bnez check_down # if ACC is not 0, it must be other direction

    # else, set direction to down
    acc 0x2
    rarb 0x80
    to-mba # set MEM[0x80] = 0x2
    b done_read

check_down: # if IOA=0100, set direction variable to left
    rarb 0xB0 # IOA
    acc 0x4
    xor-ba # ACC = 0b0100 ^ MEM[IOA]
    bnez check_left # if ACC is not 0, it must other direction

    # else, set direction to left
    acc 0x3
    rarb 0x80
    to-mba # set MEM[0x80] = 0x3
    b done_read

check_left: # if IOA=1000, set direction variable to right
    rarb 0xB0 # IOA
    acc 0x8
    xor-ba # ACC = 0b1000 ^ MEM[IOA]
    bnez check_up_right # we've exhausted all single directions, this must be a diagonal

    # else, set direction to right
    acc 0x1
    rarb 0x80
    to-mba # set MEM[0x80] = 0x1
    b done_read

check_up_right: # if IOA=1001, set direction variable to up
    rarb 0xB0 # IOA
    acc 0x9
    xor-ba # ACC = 0b1001 ^ MEM[IOA]
    bnez check_up_left # check other diagonals

    # else, set direction to up
    acc 0x0
    rarb 0x80
    to-mba # set MEM[0x80] = 0x0
    b done_read

check_up_left: # if IOA=0101, set direction variable to up
    rarb 0xB0 # IOA
    acc 0x5
    xor-ba # ACC = 0b0101 ^ MEM[IOA]
    bnez check_down_right # check other diagonals

    # else, set direction to up
    acc 0x0
    rarb 0x80
    to-mba # set MEM[0x80] = 0x0
    b done_read

check_down_right: # if IOA=1010, set direction variable to down
    rarb 0xB0 # IOA
    acc 0xA
    xor-ba # ACC = 0b1010 ^ MEM[IOA]
    bnez check_down_left # check other diagonals

    # else, set direction to down
    acc 0x2
    rarb 0x80
    to-mba # set MEM[0x80] = 0x2
    b done_read

check_down_left: # if IOA=0110, set direction variable to down
    rarb 0xB0 # IOA
    acc 0x6
    xor-ba # ACC = 0b0110 ^ MEM[IOA]
    bnez no_keypad # for more than or equal to 3 inputs or 180 deg input, disregard as no input

    # else, set direction to down
    acc 0x2
    rarb 0x80
    to-mba # set MEM[0x80] = 0x2
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
    b game_over # pandebug nalang

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
    # here we check if new_head_row (RA) and new_head_col (RB) collides with snake body 

    # PSEUDOCODE
    # a smart implementation would be 
    # 1. store RA in temp MEM[0xAA] and RB in temp MEM[0xAB] to retain RA, RB information
    #
    # 2. translate(RA, RB)
    # translatedRB = MEM[0x90 + RA] = MEM[0x9:RA]
    # translatedRA = MEM[0xA0 + RA] + RB = MEM[0xA:RA] + RB

    # if MEM[translatedRB:translatedRA] = 0x1:
    #     if RA == food_row, check food_col
    #     else: b collision
    #     check food_col:   
    #         if RB == food_col: b check_if_food
    #         else: b collisiion
    # else:
    #     b check_if_food

    # IMPLEMENTATION
    # 1.1 store RA temporarily in MEM[0xAA]
    from-ra # ACC = REG[RA] = new_head_row
    rcrd 0xAA
    to-mdc # MEM[0xAA] = new_head_row

    # 1.2 store RB temporarily in MEM[0xAB]
    from-rb # ACC = REG[RB] = new_head_col
    rcrd 0xAB
    to-mdc # MEM[0xAB] = new_head_col


    # 2.1 translate RB into LED matrix index
    acc 0x9
    to-rb # REG[RB] = 0x9
    
    rcrd 0xAA
    from-mdc # ACC = REG[RA]
    to-ra # REG[RA] = 0xRA

    from-mba # ACC = MEM[0x9:RA]
    rcrd 0xAC
    to-mdc # store translatedRB temporarily in MEM[0xAC], MEM[0xAC] = MEM[0x9:RA]

    # 2.2 translate RA into LED matrix index
    acc 0xA
    to-rb # REG[RB] = 0xA

    rcrd 0xAA
    from-mdc # ACC = REG[RA]
    to-ra # REG[RA] = 0xRA

    from-mba # ACC = MEM[0xA:RA]
    rcrd 0xAD # 
    to-mdc # store partially_translatedRA to MEM[0xAD], MEM[0xAD] = MEM[0xA:RA]

    rcrd 0xAB
    from-mdc # ACC = REG[RB]
    
    rarb 0xAD
    add-mba # ACC = ACC + MEM[0xAD] = REG[RB] + MEM[0xA:RA]
    to-ra # REG[translatedRA] = ACC = REG[RB] + MEM[0xA:RA]
    to-mba # MEM[0xAD] = REG[RB] + MEM[0xA:RA], just in case

    # fetch translatedRB again
    rcrd 0xAC
    from-mdc 
    to-rb

    # summary:
    # 0xAA = RA (new_head_row)
    # 0xAB = RB (new_head_col)
    # 0xAC = translatedRB (translated new_head_col)
    # 0xAD = translatedRA (translated new_head_row)
    # currently here, we use translatedRA and translatedRB

    # 3. check if translatedRA and translatedRB is on
    acc 0x1
    and-ba # ACC = 0x1 & MEM[RB:RA]
    bnez check_if_food_or_body # if LED is turned on, it must be a food or body

    # else, go to check_if_food to know whether if the snake would grow or retain

    # turn back RA
    rcrd 0xAA
    from-mdc # ACC = MEM[0xAA] = RA
    to-ra # REG[RA] = ACC

    # turn back RB
    rcrd 0xAB
    from-mdc # ACC = MEM[0xAB] = RB
    to-rb # REG[RB] = ACC

    b check_if_food

check_if_food_or_body:
    # turn back RA
    rcrd 0xAA
    from-mdc # ACC = MEM[0xAA] = RA
    to-ra # REG[RA] = ACC

    # turn back RB
    rcrd 0xAB
    from-mdc # ACC = MEM[0xAB] = RB
    to-rb # REG[RB] = ACC

    b check_same_food_row_col

check_same_food_row_col:
    # store RA temporarily in MEM[0xAA]
    from-ra # ACC = REG[RA]
    rcrd 0xAA
    to-mdc # MEM[0xAA] = REG[RA]

    # store RB temporarily in MEM[0xAB]
    from-rb # ACC = REG[RB]
    rcrd 0xAB
    to-mdc # MEM[0xAB] = REG[RB]

    # compare RA and food_row
    rcrd 0xAA
    from-mdc # ACC = REG[RA]
    rarb 0x85
    xor-ba # ACC = ACC ^ MEM[0x85] = REG[RA] ^ food_row
    bnez collision # if new_head_row != food_row, then there's a collision since it must be the body

    # else, another check pa
    # compare RB and food_col
    rcrd 0xAB
    from-mdc # ACC = REG[RB]
    rarb 0x86
    xor-ba # ACC = ACC ^ MEM[0x86] = REG[RB] ^ food_col
    bnez collision # if new_head_col != food_col, then there's a collision since it must be the body
   
    # at this point, it's just the food! go to check_if_food to know whether the snake would grow or retain
    b check_if_food

check_if_food:
    # here we check if new_head_row (RA) and new_head_col (RB) collides with a food

    # PSEUDOCODE
    # if (food_row, food_col) == (RA, RB):
    #     b grow_the_snake
    # else:
    #     b retain_snake_length

    # store RA temporarily in MEM[0xAA]
    from-ra # ACC = REG[RA]
    rcrd 0xAA
    to-mdc # MEM[0xAA] = REG[RA]

    # store RB temporarily in MEM[0xAB]
    from-rb # ACC = REG[RB]
    rcrd 0xAB
    to-mdc # MEM[0xAB] = REG[RB]

    # compare RA and food_row
    rcrd 0xAA
    from-mdc # ACC = REG[RA]
    rarb 0x85
    xor-ba # ACC = ACC ^ MEM[0x85] = REG[RA] ^ food_row
    bnez retain_snake_length # if new_head_row != food_row, then no food collision

    # else, another check pa
    # compare RB and food_col
    rcrd 0xAB
    from-mdc # ACC = REG[RB]
    rarb 0x86
    xor-ba # ACC = ACC ^ MEM[0x86] = REG[RB] ^ food_col
    bnez retain_snake_length # if new_head_row != food_row, then no food collision

    # else, at this point, (food_row, food_col) == (RA, RB), so kumain!
    b grow_the_snake

grow_the_snake:
    # grow by just turning on the new_head_index in the LED matrix
    # update the head_ptr too, and row and col arrays

    # PSEUDOCODE
    # MEM[translatedRB:translatedRA] = 0x1
    # MEM[0x88], MEM[0x89]++ # update score, careful with carry bit
    # enqueue head

    # IMPLEMENTATION
    # takeout translated RA from 0xAD
    rcrd 0xAD
    from-mdc # ACC = MEM[0xAD] = translatedRA
    to-ra # REG[RA] = translatedRA

    # takeout translated RB from 0xAC
    rcrd 0xAC
    from-mdc # ACC = MEM[0xAC] = translatedRB
    to-rb # REG[RB] = translatedRB

    # turn on new_head in LED matrix
    acc 0x1
    to-mba # MEM[translatedRB:translatedRA] = 0x1

update_score:
    # update score at MEM[0x88] and MEM[0x89], just add 1
    acc 0x1
    rarb 0x89
    add-mba # ACC = ACC + MEM[0x89] = 0x1 + MEM[0x89]
    to-mba # MEM[0x89] = ACC
    
    # transfer carry bit to more significant nibble
    acc 0x0
    rarb 0x88
    addc-mba # ACC = ACC + MEM[0x88] + CF = 0x0 + MEM[0x88] + CF
    to-mba # MEM[0x89] = ACC


    # update head_index at MEM[0x81] and MEM[0x82]
    # turn back RA from 0xAA
    rcrd 0xAA
    from-mdc # ACC = MEM[0xAA] = RA
    rcrd 0x81 
    to-mdc # MEM[0x81] = ACC = RA

    # turn back RB from 0xAB
    rcrd 0xAB
    from-mdc # ACC = MEM[0xAB] = RB
    rcrd 0x82
    to-mdc # MEM[0x82] = ACC = RB

enqueue_head:
    # enqueue this head at the queue
    # PSEUDOCODE
    # 1. head_ptr++
    # 2. put (RA, RB) in body[head_ptr] for both row and col

    # 1. head_ptr++
    # we can do this by adding one to head_ptr_low (MEM[0xB4]) then add the CF to head_ptr_high (MEM[0xB3])
    acc 0x1
    rarb 0xB4
    add-mba # ACC = ACC + MEM[0xB4] = 0x1 + head_ptr_row
    to-mba # MEM[0xB4] = ACC

    # transfer carry bit to more significant nibble
    acc 0x0
    rarb 0xB3
    addc-mba # ACC = ACC + MEM[0xB3] + CF = 0x0 + MEM[0xB3] + CF
    to-mba = # MEM[0xB3] = ACC

    # note that head_ptr here can reach 0x40, so if it reaches 0x40, let's make head_ptr 0x00 again (circular queue)

    # PSEUDOCODE
    # if MEM[0xB3] == 4:
    #     if MEM[0xB4] == 0:
    #         MEM[0xB3] = MEM[0xB4] = 0x0
    #     else:
    #         # set_mem_head_ptr
    # else:
    #     # set_mem_head_ptr

    acc 0x4
    rarb 0xB3
    xor-ba # ACC = 0x4 ^ MEM[0xB3]
    bnez set_mem_head_ptr # if not equal

    # else, another check
    acc 0x0
    rarb 0xB4
    xor-ba # ACC = 0x0 ^ MEM[0xB4]
    bnez set_mem_head_ptr # if not equal, but this is impossible

    # else, sumobra head_ptr natin, we need it to be circular
    # set MEM[0xB3] = MEM[0xB4] = 0x0
    acc 0x0
    rarb 0xB3
    to-mba
    rarb 0xB4
    to-mba

set_mem_head_ptr:
    # 2. put (RA, RB) in body[head_ptr] for both row and col
    # now the values of head_ptr here would just range from 0x00..0x3F

    # PSEUDOCODE
    # set row[head_ptr_high:head_ptr_low] = RA (new_head_row)
    # set col[translated(head_ptr_high:head_ptr_low)] = RB (new_head_col), just add 0x40 to (head_ptr_high, head_ptr_low)

    # set RB = head_ptr_high
    rcrd 0xB3
    from-mdc # ACC = MEM[0xB3]
    to-rb # REG[RB] = head_ptr_high
    
    # set RA = head_ptr_low
    rcrd 0xB4
    from-mdc # ACC = MEM[0xB4]
    to-ra # REG[RA] = head_ptr_low

    # set row[head_ptr_high:head_ptr_low] = RA
    rcrd 0xAA # load new_head_row
    from-mdc # ACC = MEM[0xAA] = new_head_row
    to-mba # MEM[head_ptr_high:head_ptr_low] = ACC = new_head_row

    # set col[translated(head_ptr_high:head_ptr_low)] = RB
    # 1. add 0x4 to head_ptr_high
    acc 0x4
    rarb 0xB3
    add-mba # ACC = 0x4 + MEM[0xB3] = 0x4 + head_ptr_high = translated(head_ptr_high)
    to-rb # REG[RB] = ACC = translated(head_ptr_high)

    # 2. add 0x0 to head_ptr_low, but that's just unnecessary
    # we'll just direct to loading it to RA
    rcrd 0xB4
    from-mdc # ACC = MEM[0xB4] = head_ptr_low
    to-ra # REG[RA] = ACC = translated(head_ptr_low) = head_ptr_low
    
    # 3. finally, we can col[translated(head_ptr_high:head_ptr_low)] = RB
    rcrd 0xAB
    from-mdc # ACC = MEM[0xAB] = new_head_col
    to-mba # MEM[translated(head_ptr_high:head_ptr_low)] = ACC = new_head_col
    
    b after_move

retain_snake_length:
    # just move 
    # update queue here
    # illusion lang siya, pero in reality, it's just turning off tail index and turning on head index in the LED matrix

    # PSEUDOCODE
    # 1. translated(tail_row, tail_col) = 0x0
    # 2. translated(new_head_row, new_head_col) = 0x1
    # 3. update head index
    # 4. point tail_ptr to the next tail (make sure circular queue)
    #  - deque old tail by setting both to 0x0
    #  - update tail index
    # 5. enqueue head (make sure circular queue)

    # IMPLEMENTATION
    # 1. translated(tail_row, tail_col) = 0x0, let's set RA = tail_row, RB = tail_col 
    # translatedRB = MEM[0x90 + RA] = MEM[0x9:RA]
    # translatedRA = MEM[0xA0 + RA] + RB = MEM[0xA:RA] + RB
    # 1.1 translate tail_col into LED matrix index
    acc 0x9
    to-rb # REG[RB] = 0x9

    rcrd 0x83
    from-mdc # ACC = MEM[0x83] = tail_row
    to-ra # REG[RA] = tail_row

    from-mba # ACC = MEM[0x9:tail_row]
    rcrd 0xAE
    to-mdc # store translated_tail_col temporarily in MEM[0xAE]

    # 1.2 translate tail_row into LED matrix index
    acc 0xA
    to-rb # REG[RB] = 0xA

    rcrd 0x83
    from-mdc # ACC = MEM[0x83] = tail_row
    to-ra # REG[RA] = tail_row

    from-mba # ACC = MEM[0xA:tail_row]
    rcrd 0xAF 
    to-mdc # store partially_translated_tail_row to MEM[0xAF]

    rcrd 0x84
    from-mdc # ACC = tail_col

    rarb 0xAF
    add-mba # ACC = ACC + MEM[0xAF] = tail_col + MEM[0xA:tail_row]
    to-ra # REG[translated_tail_row] = ACC = tail_col + MEM[0xA:tail_row]
    to-mba # MEM[0xAF] = tail_col + MEM[0xA:tail_row], just in case

    # fetch translated_tail_row again
    rcrd 0xAE
    from-mdc
    to-rb 

    # at this point, RB = translated_tail_row, RA = translated_tail_col, so we can safely MEM[translated_tail_row:translated_tail_col] = 0x0, and turn off the old tail in the LED!
    acc 0x0
    to-mba # MEM[RB:RA] = 0x0


    # 2. translated(new_head_row, new_head_col)
    # this is easy since we already calculated this earlier
    # 2.1 fetch from MEM[0xAC] = translatedRB
    rcrd 0xAC
    from-mdc # ACC = translatedRB
    to-rb # REG[RB] = translatedRB

    # 2.2 fetch from MEM[0xAD] = translatedRA
    rcrd 0xAD
    from-mdc # ACC = translatedRA
    to-ra # REG[RA] = translatedRA

    # 2.3 then we can safely dom MEM[RB:RA] = 0x1, and turn on the new head in the LED!
    acc 0x1
    to-mba # MEM[RB:RA] = 0x1


    # 3. update head index
    # 3.1 fetch from MEM[0xAA] the new_head_row
    rcrd 0xAA
    from-mdc # ACC = MEM[0xAA] = new_head_row
    # 3.2 put new_head_row to MEM[0x81]
    rcrd 0x81
    to-mdc # MEM[0x81] = ACC = new_head_row
    # 3.3 fetch from MEM[0xAB] the new_head_col
    rcrd 0xAB
    from-mdc # ACC = MEM[0xAB] = new_head_col
    # 3.4 put new_head_col to MEM[0x82]
    rcrd 0x82
    to-mdc # MEM[0x82] = ACC = new_head_col

deque_tail:
    # 4. point tail_ptr to the next tail (make sure circular queue)
    # 4.1 make old tail be (0, 0) in row, col arrays
    # 4.1.1 set row[tail_ptr_high:tail_ptr_low] = 0x0
    # set RB = tail_ptr_high
    rcrd 0xB5
    from-mdc # ACC = MEM[0xB5]
    to-rb # REG[RB] = tail_ptr_high

    # set RA = tail_ptr_low
    rcrd 0xB6
    from-mdc # ACC = MEM[0xB6]
    to-ra # REG[RA] = tail_ptr_low

    # set row[tail_ptr_high:tail_ptr_low] = 0x0
    acc 0x0
    to-mba # MEM[tail_ptr_high:tail_ptr_low] = ACC = 0x0

    # 4.1.2 set col[translated(tail_ptr_high:tail_ptr_low)] = 0x0
    # add 0x4 to tail_ptr_high
    acc 0x4
    rarb 0xB5
    add-mba # ACC = 0x4 + MEM[0xB5] = 0x4 + tail_ptr_high = translated(tail_ptr_high)
    to-rb # REG[RB] = ACC = translated(tail_ptr_high)

    # add 0x0 to tail_ptr_low, but that's just unnecessary
    # we'll just direct to loading it to RA
    rcrd 0xB6
    from-mdc # ACC = MEM[0xB6] = tail_ptr_low
    to-ra # REG[RA] = ACC = translated(tail_ptr_low) = tail_ptr_low

    # finally, we can col[translated(tail_ptr_high:tail_ptr_low)] = 0x0
    acc 0x0
    to-mba # MEM[translated(tail_ptr_high:tail_ptr_low)] = 0x0
    

    # 4.2 tail_ptr++ (make sure circular queue)
    # 4.2.1 add 1 to tail_ptr_low (MEM[0xB6]) first then add CF to head_ptr_high (MEM[0xB5])
    acc 0x1
    rarb 0xB6
    add-mba # ACC = ACC + MEM[0xB6] = 0x1 + head_ptr_low
    to-mba # MEM[0xB6] = ACC
    # 4.2.2 transfer carry bit to more significant nibble
    acc 0x0
    rarb 0xB5
    addc-mba # ACC = ACC + MEM[0xB5] + CF = 0x0 + MEM[0xB5] + CF
    to-mba # MEM[0xB5] = ACC
    # 4.2.3 check if magooverflow sa queue yung tail_ptr bounds
    
    # PSEUDOCODE
    # if MEM[0xB5] == 4:
    #     if MEM[0xB6] == 0:
    #         MEM[0xB5] = MEM[0xB6] = 0x0
    #     else:
    #         # set_mem_tail_ptr
    # else:
    #     # set_mem_tail_ptr

    acc 0x4
    rarb 0xB5
    xor-ba # ACC = 0x4 ^ MEM[0xB5]
    bnez set_mem_tail_ptr # if not equal

    # else, another check
    acc 0x0
    rarb 0xB6
    xor-ba # ACC = 0x0 ^ MEM[0xB6]
    bnez set_mem_tail_ptr # if not equal, but this is impossible

    # else, sumobra head_ptr natin, we need it to be circular
    # set MEM[0xB5] = MEM[0xB6] = 0x0
    acc 0x0
    rarb 0xB5
    to-mba
    rarb 0xB6
    to-mba

set_mem_tail_ptr:
    # 4.3 fetch MEM[tail_ptr_high:tail_ptr_low] = (row, col) then put it to new_tail_index, this is basically the next tail
    # 4.3.1 set RB = tail_ptr_high
    rcrd 0xB5
    from-mdc # ACC = MEM[0xB5]
    to-rb

    # 4.3.2 set RA = tail_ptr_low
    rcrd 0xB6
    from-mdc # ACC = MEM[0xB6]
    to-ra # REG[RA] = tail_ptr_low

    # 4.3.3 set tail_row to next_tail_row
    from-mba # ACC = MEM[tail_ptr_high:tail_ptr_low]
    rcrd 0x83
    to-mdc # MEM[0x83] = ACC = MEM[tail_ptr_high:tail_ptr_low]

    # 4.3.4 set tail_col to next_tail_col
    # translate tail_ptr_high and tail_ptr_low
    # add 0x4 to tail_ptr_high
    acc 0x4
    rarb 0xB5
    add-mba # ACC = 0x4 + MEM[0xB5] = 0x4 + tail_ptr_high = translated(tail_ptr_high)
    to-rb # REG[RB] = ACC = translated(tail_ptr_high)

    # add 0x0 to tail_ptr_low, but that's just unnecessary
    # we'll just direct to loading it to RA
    rcrd 0xB6
    from-mdc # ACC = MEM[0xB6] = tail_ptr_low
    to-ra # REG[RA] = ACC = translated(tail_ptr_low) = tail_ptr_low

    from-mba # ACC = MEM[translated(tail_ptr_high:tail_ptr_low)]
    rcrd 0x84
    to-mdc # MEM[0x84] = ACC = MEM[translated(tail_ptr_high:tail_ptr_low)]


    # 5. enqueue head, or just copy paste ung code sa `set_mem_head_ptr`
    # 5.1 head_ptr++
    # 5.2 set row[head_ptr_high:head_ptr_low] = RA
    # 5.3 set col[translated(head_ptr_high:head_ptr_low)] = RB
    b enqueue_head # above is just duplicated of this 
# /========== move_snake ==========/



# ========== game over ========== 
collision:
    b game_over

game_over:
    # OPTIONAL? some indication to know it's game over
    shutdown
# /========== game over ==========/
