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

# PSEUDOCODE for fetching translatedRA, translatedRB given RA, RB from the precomputed table
# translatedRB = MEM[0x90 + RA] = MEM[0x9:RA]
# translatedRA = MEM[0xA0 + RA] = MEM[0xA:RA]
# NOTE: this is partially pa rin, it needs to pass through another check if it should go to the next address to it (i.e. +1)

# PSEUDOCODE FOR TURNING ON AN LED GIVEN RA, RB (row, col) index
# store RA, RB temporarily in MEM[0xAA], MEM[0xAB]
# fetch translatedRA, translatedRB from the precomputed table, store it temporarily in MEM[0xAC], MEM[0xAD]
# 
# if RB >= 4, that is CF of RB - 4 != 0, b turn_on_led
# 
# else, we should add 1 to address and RB = RB - 4
#  - translatedRA = translatedRA + 1
#  - translatedRB = translatedRB + CF + 0
#  - normalizedRB = RB - 4
#
# turn_on_led:
#     # now we have normalized RB here
#     if normalizedRB == 0, MEM[translated(RB:RA)] |= 0b0001
#     if normalizedRB == 1, MEM[translated(RB:RA)] |= 0b0010
#     if normalizedRB == 2, MEM[translated(RB:RA)] |= 0b0100
#     if normalizedRB == 3, MEM[translated(RB:RA)] |= 0b1000
# NOTE: nakaOR ops para di natin matouch ung other 3 bits in that address

# PSEUDOCODE FOR TURNING OFF AN LED GIVEN RA, RB (row, col) index
# store RA, RB temporarily in MEM[0xAA], MEM[0xAB]
# fetch translatedRA, translatedRB from the precomputed table, store it temporarily in MEM[0xAC], MEM[0xAD]
# 
# if RB >= 4, that is CF of RB - 4 != 0, b turn_off_led
# 
# else, we should add 1 to address and RB = RB - 4
#  - translatedRA = translatedRA + 1
#  - translatedRB = translatedRB + CF + 0
#  - normalizedRB = RB - 4
#
# turn_off_led:
#     # now we have normalized RB here
#     if normalizedRB == 0, MEM[translated(RB:RA)] &= 0b1110
#     if normalizedRB == 1, MEM[translated(RB:RA)] &= 0b1101
#     if normalizedRB == 2, MEM[translated(RB:RA)] &= 0b1011
#     if normalizedRB == 3, MEM[translated(RB:RA)] &= 0b0111
# NOTE: AND bit masking just to turn on that specific bit, and not touch the other 3 bits

# PSEUDOCODE FOR CHECKING IF A GIVEN RA, RB (row, col) is turned on in the LED matrix
# store RA, RB temporarily in MEM[0xAA], MEM[0xAB]
# fetch translatedRA, translatedRB from the precomputed table, store it temporarily in MEM[0xAC], MEM[0xAD]
#
# if RB >= 4, that is CF of RB - 4 != 0, b check_if_turned_on
# 
# else, we should add 1 to address and RB = RB - 4
#  - translatedRA = translatedRA + 1
#  - translatedRB = translatedRB + CF + 0
#  - RB = RB - 4
# 
# check_if_turned_on:
#     if MEM[translated(RB:RA)] & 0x1 == 0x1:
#         if RB == 0x0:
#             # RA, RB is turned ON!
#         else: # no
#     if MEM[translated(RB:RA)] & 0x2 == 0x2:
#         if RB == 0x1:
#             # RA, RB is turned ON!
#         else: # no
#     if MEM[translated(RB:RA)] & 0x4 == 0x4:
#         if RB == 0x2:
#             # RA, RB is turned ON!
#         else: # no
#     if MEM[translated(RB:RA)] & 0x8 == 0x8:
#         if RB == 0x3:
#             # RA, RB is turned ON!
#         else: # no
# NOTE: we used AND ops to know if that specific bit is on, and not really care about the other 3 bits

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
# 0x90:  0xC  # high4(0xC5) 
# 0x91:  0xC  # high4(0xCA) 
# 0x92:  0xC  # high4(0xCF) 
# 0x93:  0xD  # high4(0xD4) 
# 0x94:  0xD  # high4(0xD9) 
# 0x95:  0xD  # high4(0xDE) 
# 0x96:  0xE  # high4(0xE3) 
# 0x97:  0xE  # high4(0xE8) 

# 0xA0:  0x5  # low4(0xC5)
# 0xA1:  0xA  # low4(0xCA)
# 0xA2:  0xF  # low4(0xCF)
# 0xA3:  0x4  # low4(0xD4)
# 0xA4:  0x9  # low4(0xD9)
# 0xA5:  0xE  # low4(0xDE)
# 0xA6:  0x3  # low4(0xE3)
# 0xA7:  0x8  # low4(0xE8)

# normalizedRB_head [0xA8] 
# normalizedRB_tail [0xA9]
# RA (row coords, 0..7) [0xAA]
# RB (col coords, 0..7) [0xAB]
# translatedRB address of head [0xAC]
# translatedRA address of head [0xAD]
# translatedRB address of tail [0xAE]
# translatedRA address of tail [0xAF]

# this is where the emulator puts the info about which keys are pressed
# ioa [176] or [0xB0], 0001=up, 0010=down, 0100=left, 1000=right

# two nibbles are alloted for each pointer since 0..63 requires 6 bits
# queue head_ptr [179, 180] or [0xB3, 0xB4], high and low nibble
# queue tail_ptr [181, 182] or [0xB5, 0xB6], high and low nibble

# led matrix/grid [192 to 255] or [0xC0 to 0xFF]

# ========== precomputed table ==========
acc 0xC
rcrd 0x90
to-mdc
rcrd 0x91
to-mdc
rcrd 0x92
to-mdc

acc 0xD
rcrd 0x93
to-mdc
rcrd 0x94
to-mdc
rcrd 0x95
to-mdc

acc 0xE
rcrd 0x96
to-mdc
rcrd 0x97
to-mdc



acc 0x5
rcrd 0xA0
to-mdc

acc 0xA
rcrd 0xA1
to-mdc

acc 0xF
rcrd 0xA2
to-mdc

acc 0x4
rcrd 0xA3
to-mdc

acc 0x9
rcrd 0xA4
to-mdc

acc 0xE
rcrd 0xA5
to-mdc

acc 0x3
rcrd 0xA6
to-mdc

acc 0x8
rcrd 0xA7
to-mdc
# /========== precomputed table ==========/ 



# ========== start ========== 
start:
    # clear everything from 0xC0 to 0xF1
    acc 0x0
    rarb 0xC0 # set RB to 0xC and RA to 0x0, which is the start address of LED matrix

clear_row_C:
    to-mba
    inc*-reg 0
    bnz-a clear_row_C # if RA != 0, keep turning off LEDs 0xC:RA

    # else, this means nakawrap around na ung pagclear from RA=0x0->0xF for RB=0xC

    acc 0x0
    rarb 0xD0 # start from here naman

clear_row_D:
    to-mba
    inc*-reg 0
    bnz-a clear_row_D # if RA != 0, keep turning off LEDs 0xD:RA

    # else, this means nakawrap around na ung pagclear from RA=0x0->0xF for RB=0xD

    acc 0x0
    rarb 0xE0 # start from here naman

clear_row_E:
    to-mba
    inc*-reg 0
    bnz-a clear_row_E # if RA != 0, keep turning off LEDs 0xD:RA

    # else, this means nakawrap around na ung pagclear from RA=0x0->0xF for RB=0xE

    # we just set this manually since awkward ung 241 na address
    acc 0x0
    rarb 0xF0
    to-mba

    acc 0x0
    rarb 0xF1
    to-mba

    # at this point, 0xC0 to 0xF1 are all cleared

    b initialize_states

initialize_states:
    # ========== border_leds ========== 
    acc 0xF

    # top border wall
    rcrd 0xC0
    to-mdc
    rcrd 0xC1
    to-mdc
    rcrd 0xC2
    to-mdc
    rcrd 0xC3
    to-mdc
    rcrd 0xC4
    to-mdc

    # middle border wall
    rcrd 0xC7
    to-mdc
    rcrd 0xCC
    to-mdc
    rcrd 0xD1
    to-mdc
    rcrd 0xD6
    to-mdc
    rcrd 0xDB
    to-mdc
    rcrd 0xE0
    to-mdc
    rcrd 0xE5
    to-mdc
    rcrd 0xEA
    to-mdc 

    # bottom border wall
    rcrd 0xED
    to-mdc
    rcrd 0xEE
    to-mdc
    rcrd 0xEF
    to-mdc
    rcrd 0xF0
    to-mdc
    rcrd 0xF1
    to-mdc
    # /========== border_leds ==========/ 


    # 1. initialize direction (right) in mem
    acc 0x1
    rarb 0x80
    to-mba # MEM[0x80] = 0x1


    # 2. initialize delay in mem (wala na pala timer, so this is useless)
    acc 0x5
    rarb 0x87
    to-mba # MEM[0x87] = 0x5


    # 3. initialize score in mem
    acc 0x0
    rarb 0x88
    to-mba # MEM[0x88] = 0x0
    rarb 0x89
    to-mba # MEM[0x89] = 0x0

    # ========== LED score to 0 ==========
    # tens digit
    acc 0x6
    rcrd 0xCD
    to-mdc
    rcrd 0xE6
    to-mdc

    acc 0x9
    rcrd 0xD2
    to-mdc
    rcrd 0xD7
    to-mdc
    rcrd 0xDC
    to-mdc
    rcrd 0xE1
    to-mdc

    # ones digit
    acc 0x6
    rcrd 0xCE
    to-mdc
    rcrd 0xE7
    to-mdc

    acc 0x9
    rcrd 0xD3
    to-mdc
    rcrd 0xD8
    to-mdc
    rcrd 0xDD
    to-mdc
    rcrd 0xE2
    to-mdc
    # /========== LED score to 0 ==========/ 

    # 4. place snake body in center
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
    acc 0xE
    rarb 0xD4
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

    # 5.4 set head_ptr to index 2 of body
    # set MEM[0xB3] = 0x0 
    # set MEM[0xB4] = 0x2 
    acc 0x0
    rarb 0xB3
    to-mba # MEM[0xB3] = 0x0

    acc 0x2
    rarb 0xB4
    to-mba # MEM[0xB4] = 0x2

    # 5.5 set tail_ptr to index 0 of body
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
    # 6.1 put food coords (3,6) to MEM[0x85] and MEM[0x86] respectively
    acc 0x3
    rarb 0x85
    to-mba
    
    acc 0x5
    rarb 0x86
    to-mba

    # 6.2 light up the food in the led matrix
    acc 0x2
    rarb 0xD5
    to-mba
    
    b game_loop
# /========== start ==========/ 


# ========== main game loop ========== 
game_loop:
    acc 0x1
    b read_from_ioa

after_read_from_ioa:
    # we update direction based from IOA value
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
    b update_score_display
    
after_update_score_display:
    b food_spawn

after_food_spawn:
    b game_loop
# /========== main game loop ==========/ 



# ========== read_from_ioa ========== 
read_from_ioa:
    from-ioa # ACC = IOA
    rcrd 0xB0 
    to-mdc # MEM[0xB0] = ACC

    b after_read_from_ioa
# /========== read_from_ioa ==========/



# ========== read_keypad ========== 
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
    bnez check_down # if ACC is not 0, it must be other direction
    
    # else, set direction to up
    acc 0x0 
    rarb 0x80 
    to-mba # set MEM[0x80] = 0x0
    b done_read

check_down: # if IOA=0010, set direction variable to down
    rarb 0xB0 # IOA
    acc 0x2
    xor-ba # ACC = 0b0010 ^ MEM[IOA]
    bnez check_left # if ACC is not 0, it must be other direction

    # else, set direction to down
    acc 0x2
    rarb 0x80
    to-mba # set MEM[0x80] = 0x2
    b done_read

check_left: # if IOA=0100, set direction variable to left
    rarb 0xB0 # IOA
    acc 0x4
    xor-ba # ACC = 0b0100 ^ MEM[IOA]
    bnez check_right # if ACC is not 0, it must other direction

    # else, set direction to left
    acc 0x3
    rarb 0x80
    to-mba # set MEM[0x80] = 0x3
    b done_read

check_right: # if IOA=1000, set direction variable to right
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
# /========== read_keypad ==========/



# ========== move_snake ==========
move_snake:
    # load head_row into RA
    rarb 0x81
    from-mba # ACC = MEM[0x81]
    to-reg 0 # REG[RA] = ACC

    # load head_col into RB
    rarb 0x82
    from-mba # ACC = MEM[0x82]
    to-reg 1 # REG[RB] = ACC

    # load direction into RC
    rarb 0x80
    from-mba # ACC = MEM[0x80]
    to-reg 2 # REC[RC] = ACC

    # calculate new_head_row, new_head_col (check walls -> collision)
    from-reg 2 # ACC = REG[RC]
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
    rcrd 0x81
    from-mdc # ACC = old_head_row
    beqz bounds_collision # if old_head_row = 0, umabot sa up bounds, so DEADS

    # else, update old_head_row 
    from-mdc
    sub 1 # this is valid now
    to-mdc # new_head_row = old_head_row - 1

    # we don't need to update old_head_col here
    # new_head_col = old_head_col
    b check_if_self_collision 

move_right:
    rcrd 0x82
    from-mdc # ACC = old_head_col
    sub 7
    beqz bounds_collision # if old_head_col - 7 = 0, umabot sa right bounds, so DEADS

    # else, update old_head_col
    from-mdc
    add 1
    to-mdc # new_head_col = old_head_col + 1

    # we don't need to update old_head_row here
    # new_head_row = old_head_row
    b check_if_self_collision

move_down:
    rcrd 0x81
    from-mdc # ACC = old_head_row
    sub 7
    beqz bounds_collision # if old_head_row - 7 = 0, umabot sa bot bounds, so DEADS

    # else, update old_head_row
    from-mdc
    add 1
    to-mdc # new_head_row = old_head_row + 1

    # we don't need to update old_head_col here
    # new_head_col = old_head_col
    b check_if_self_collision

move_left:
    rcrd 0x82
    from-mdc # ACC = old_head_col
    beqz bounds_collision # if old_head_row = 0, umabot sa left bounds, so DEADS

    # else, update old_head_col
    from-mdc
    sub 1
    to-mdc # new_head_col = old_head_col - 1

    # we don't need to update old_head_row here
    # new_head_row = old_head_row
    b check_if_self_collision
    
check_if_self_collision:
    # nagiiba RA tsaka RB here so I just extracted directly from 0x81 and 0x82

    rcrd 0x81
    from-mdc
    to-reg 0

    rcrd 0x82
    from-mdc
    to-reg 1

    # here we check if new_head_row (RA) and new_head_col (RB) collides with snake body 

    # PSEUDOCODE
    # a smart implementation would be 
    # 1. store RA in temp MEM[0xAA] and RB in temp MEM[0xAB] to retain RA, RB information

    # 2. translate(RA, RB)
    # PSEUDOCODE for fetching translatedRA, translatedRB given RA, RB from the precomputed table
    # 2.1 translatedRB = MEM[0x90 + RA] = MEM[0x9:RA]
    # 2.2 translatedRA = MEM[0xA0 + RA] = MEM[0xA:RA]
    # NOTE: this is partially pa rin, it needs to pass through another check if it should go to the next address to it (i.e. +1)
    
    # 2.3 we still need to check if we need to add 1 to translatedRB
    # 2.3.1 if RB >= 4, that is CF of RB - 4 != 0, b check_if_turned_on
    # 2.3.2 else, we should add 1 to address and RB = RB - 4
    #  - 2.3.2.1 translatedRA = translatedRA + 1, store in MEM[0xAD]
    #  - 2.3.2.2 translatedRB = translatedRB + CF + 0, store in MEM[0xAC]
    #  - 2.3.2.3 normalizedRB = RB - 4

    # PSEUDOCODE FOR CHECKING IF A GIVEN RA, RB (row, col) is turned on in the LED matrix
    # check_if_turned_on:
    #     if MEM[translated(RB:RA)] & 0x1 == 0x1:
    #         if normalizedRB == 0x0:
    #             # RA, RB is turned ON! so it either must be a food or body
    #             b check_if_food_or_body
    #     if MEM[translated(RB:RA)] & 0x2 == 0x2:
    #         if normalizedRB == 0x1:
    #             # RA, RB is turned ON! so it either must be a food or body
    #             b check_if_food_or_body
    #     if MEM[translated(RB:RA)] & 0x4 == 0x4:
    #         if normalizedRB == 0x2:
    #             # RA, RB is turned ON! so it either must be a food or body
    #             b check_if_food_or_body
    #     if MEM[translated(RB:RA)] & 0x8 == 0x8:
    #         if normalizedRB == 0x3:
    #             # RA, RB is turned ON! so it either must be a food or body
    #             b check_if_food_or_body
    #     else: b check_if_food
    # NOTE: we used AND ops to know if that specific bit is on, and not really care about the other 3 bits

    # IMPLEMENTATION
    # 1.1 store RA temporarily in MEM[0xAA]
    from-reg 0 # ACC = REG[RA] = new_head_row
    rcrd 0xAA
    to-mdc # MEM[0xAA] = new_head_row

    # 1.2 store RB temporarily in MEM[0xAB]
    from-reg 1 # ACC = REG[RB] = new_head_col
    rcrd 0xAB
    to-mdc # MEM[0xAB] = new_head_col

    # translatedRB = MEM[0x90 + RA] = MEM[0x9:RA]
    # translatedRA = MEM[0xA0 + RA] = MEM[0xA:RA]

    # 2.1 translate RB into LED matrix index
    acc 0x9
    to-reg 1 # REG[RB] = 0x9
    
    rcrd 0xAA
    from-mdc # ACC = REG[RA]
    to-reg 0 # REG[RA] = RA

    from-mba # ACC = MEM[0x9:RA]
    rcrd 0xAC
    to-mdc # store translatedRB in MEM[0xAC], MEM[0xAC] = MEM[0x9:RA]

    # 2.2 translate RA into LED matrix index
    acc 0xA
    to-reg 1 # REG[RB] = 0xA

    rcrd 0xAA
    from-mdc # ACC = REG[RA]
    to-reg 0 # REG[RA] = RA

    from-mba # ACC = MEM[0xA:RA]
    rcrd 0xAD 
    to-mdc # store translatedRA in MEM[0xAD], MEM[0xAD] = MEM[0xA:RA]

    # summary:
    # 0xAA = RA (new_head_row)
    # 0xAB = RB (new_head_col)
    # 0xAC = translatedRB (translated new_head_col)
    # 0xAD = translatedRA (translated new_head_row)

    # 2.3 we still need to check if we need to add 1 to translatedRB, translatedRA
    # 2.3.1 if RB >= 4, that is CF of RB - 4 != 0, b check_if_turned_on
    # 2.3.2 else, we should add 1 to address and normalizedRB = RB - 4
    #  - 2.3.2.1 translatedRA = translatedRA + 1, and update final translatedRA to MEM[0xAD]
    #  - 2.3.2.2 translatedRB = translatedRB + CF + 0, and update final translatedRB to MEM[0xAC]
    #  - 2.3.2.3 normalizedRB = RB - 4

    # 2.3.1 check if RB >= 4
    # store 0x4 temporarily to MEM[0xB1]
    acc 0x4
    rcrd 0xB1
    to-mdc # MEM[0xB1] = 0x4

    # store back RB from MEM[0xAB]
    rcrd 0xAB
    from-mdc # ACC = RB
    
    rcrd 0xA8
    to-mdc # MEM[0xA8] = RB

    # perform RB - 4
    rarb 0xB1
    sub-mba # ACC = ACC - MEM[0xB1] = RB - 0x4


    bnez-cf check_if_turned_on # if CF is not 0, we don't add 1 to the address na, we're on the right address

    # 2.3.2 else, add 1 to address to translatedRA and translatedRB
    # 2.3.2.1 fetch translatedRA again from MEM[0xAD] and + 1
    acc 0x1
    rarb 0xAD
    clr-cf # set CF = 0, just in case
    add-mba # ACC = ACC + MEM[RB:RA] = 0x1 + MEM[0xAD]
    to-mba # store final translatedRA to MEM[0xAD], MEM[0xAD] = ACC

    # 2.3.2.2 fetch translatedRB again from MEM[0xAC] and + CF from prev
    acc 0x0
    rarb 0xAC
    addc-mba # ACC = ACC + MEM[RB:RA] + CF = 0x0 + MEM[0xAC] + CF
    to-mba # store final translatedRB to MEM[0xAC], MEM[0xAC] = ACC

    # 2.3.2.3 normalizedRB_head = RB - 4
    # store 0x4 temporarily to MEM[0xB1]
    acc 0x4
    rcrd 0xB1
    to-mdc # MEM[0xB1] = 0x4

    # store back RB from MEM[0xAB]
    rcrd 0xAB
    from-mdc # ACC = RB

    # perform RB - 4
    rarb 0xB1
    sub-mba # ACC = ACC - MEM[0xB1] = RB - 0x4

    rcrd 0xA8
    to-mdc # MEM[0xA8] = ACC = RB - 0x4 = normalizedRB

check_if_turned_on:
    # at this point we have:
    #  - RA = normalizedRA
    #  - RA, RB at 0xAA, 0xAB
    #  - normalized RA, RB at 0xAA, 0xA8
    #  - correct address, translatedRA, translatedRB at 0xAD, 0xAC

    # PSEUDOCODE FOR CHECKING IF A GIVEN RA, RB (row, col) is turned on in the LED matrix
    # check_if_turned_on:
    #     if MEM[translated(RB:RA)] & 0x1 == 0x1:
    #         if normalizedRB == 0x0:
    #             # RA, RB is turned ON! so it either must be a food or body
    #             b check_if_food_or_body
    #     if MEM[translated(RB:RA)] & 0x2 == 0x2:
    #         if normalizedRB == 0x1:
    #             # RA, RB is turned ON! so it either must be a food or body
    #             b check_if_food_or_body
    #     if MEM[translated(RB:RA)] & 0x4 == 0x4:
    #         if normalizedRB == 0x2:
    #             # RA, RB is turned ON! so it either must be a food or body
    #             b check_if_food_or_body
    #     if MEM[translated(RB:RA)] & 0x8 == 0x8:
    #         if normalizedRB == 0x3:
    #             # RA, RB is turned ON! so it either must be a food or body
    #             b check_if_food_or_body
    #     else: b check_if_food  

    # 2. check each cases

is_bit_0_on:
    # 2.1 if MEM[translated(RB:RA)] & 0x1 == 0x1, b is_normalizedRB_0
    # fetch translatedRB

    # 1. fetch translatedRB, translatedRA from 0xAC, 0xAD
    # 1.1 translatedRB
    rcrd 0xAC
    from-mdc
    to-reg 1

    # 1.2 translatedRA
    rcrd 0xAD
    from-mdc
    to-reg 0

    acc 0x1
    and-ba # ACC = ACC & MEM[translated(RB:RA)] = 0x1 & MEM[translated(RB:RA)]
    rcrd 0xB1 
    to-mdc # store result temporarily in MEM[0xB1]

    # if MEM[translated(RB:RA)] & 0x1 == 0x1, b is_normalizedRB_0
    acc 0x1
    rarb 0xB1
    xor-ba # ACC = 0x1 ^ MEM[0xB1] = 0x1 ^ (0x1 & MEM[translated(RB:RA)])
    beqz is_normalizedRB_0

    # else:
    b is_bit_1_on

is_bit_1_on:
    # 2.2 else, if MEM[translated(RB:RA)] & 0x2 == 0x2, b is_normalizedRB_1

    # 1. fetch translatedRB, translatedRA from 0xAC, 0xAD
    # 1.1 translatedRB
    rcrd 0xAC
    from-mdc
    to-reg 1

    # 1.2 translatedRA
    rcrd 0xAD
    from-mdc
    to-reg 0

    acc 0x2
    and-ba # ACC = ACC & MEM[translated(RB:RA)] = 0x2 & MEM[translated(RB:RA)]
    rcrd 0xB1 
    to-mdc # store result temporarily in MEM[0xB1]

    # if MEM[translated(RB:RA)] & 0x2 == 0x2, b is_normalizedRB_1
    acc 0x2
    rarb 0xB1
    xor-ba # ACC = 0x2 ^ MEM[0xB1] = 0x2 ^ (0x2 & MEM[translated(RB:RA)])
    beqz is_normalizedRB_1
    
    # else:
    b is_bit_2_on

is_bit_2_on:
    # 2.3 else, if MEM[translated(RB:RA)] & 0x4 == 0x4, b is_normalizedRB_2

    # 1. fetch translatedRB, translatedRA from 0xAC, 0xAD
    # 1.1 translatedRB
    rcrd 0xAC
    from-mdc
    to-reg 1

    # 1.2 translatedRA
    rcrd 0xAD
    from-mdc
    to-reg 0

    acc 0x4
    and-ba # ACC = ACC & MEM[translated(RB:RA)] = 0x4 & MEM[translated(RB:RA)]
    rcrd 0xB1 
    to-mdc # store result temporarily in MEM[0xB1]

    # if MEM[translated(RB:RA)] & 0x4 == 0x4, b is_normalizedRB_2
    acc 0x4
    rarb 0xB1
    xor-ba # ACC = 0x4 ^ MEM[0xB1] = 0x4 ^ (0x4 & MEM[translated(RB:RA)])
    beqz is_normalizedRB_2
    
    # else:
    b is_bit_3_on

is_bit_3_on:
    # 2.4 else, if MEM[translated(RB:RA)] & 0x8 == 0x8, b is_normalizedRB_3

    # 1. fetch translatedRB, translatedRA from 0xAC, 0xAD
    # 1.1 translatedRB
    rcrd 0xAC
    from-mdc
    to-reg 1

    # 1.2 translatedRA
    rcrd 0xAD
    from-mdc
    to-reg 0

    acc 0x8
    and-ba # ACC = ACC & MEM[translated(RB:RA)] = 0x8 & MEM[translated(RB:RA)]
    rcrd 0xB1 
    to-mdc # store result temporarily in MEM[0xB1]

    # if MEM[translated(RB:RA)] & 0x8 == 0x8, b is_normalizedRB_3
    acc 0x8
    rarb 0xB1
    xor-ba # ACC = 0x8 ^ MEM[0xB1] = 0x8 ^ (0x8 & MEM[translated(RB:RA)])
    beqz is_normalizedRB_3

    # else:
    b led_is_turned_off

led_is_turned_off:
    # this means that buong 4 bits turned off, and we're safe
    # 2.5 else, b check_if_food to know if the snake would grow or retain
    b check_if_food

is_normalizedRB_0:
    # if normalizedRB == 0x0: b check_if_food_or_body
    acc 0x0
    rarb 0xA8
    xor-ba # ACC = 0x0 ^ MEM[0xA8]
    beqz check_if_food_or_body

    # else:
    b is_bit_1_on

is_normalizedRB_1:
    # if normalizedRB == 0x1: b check_if_food_or_body
    acc 0x1
    rarb 0xA8
    xor-ba # ACC = 0x1 ^ MEM[0xA8]
    beqz check_if_food_or_body

    # else:
    b is_bit_2_on

is_normalizedRB_2:
    # if normalizedRB == 0x2: b check_if_food_or_body
    acc 0x2
    rarb 0xA8
    xor-ba # ACC = 0x2 ^ MEM[0xA8]
    beqz check_if_food_or_body

    # else:
    b is_bit_3_on

is_normalizedRB_3:
    # if normalizedRB == 0x3: b check_if_food_or_body
    acc 0x3
    rarb 0xA8
    xor-ba # ACC = 0x3 ^ MEM[0xA8]
    beqz check_if_food_or_body

    # else:
    b led_is_turned_off

check_if_food_or_body:
    # basically, we can reuse our old code here
    # make sure to fetch correct RA, RB from 0xAA, 0xAB first!
    # RA, RB is turned ON here!

    # turn back RA
    rcrd 0xAA
    from-mdc # ACC = MEM[0xAA] = RA
    to-reg 0 # REG[RA] = ACC

    # turn back RB
    rcrd 0xAB
    from-mdc # ACC = MEM[0xAB] = RB
    to-reg 1 # REG[RB] = ACC

    b check_same_food_row_col

check_same_food_row_col:
    # PSEUDOCODE
    # if RA == food_row, check food_col
    # else: b collision
    # check food_col:   
    #     if RB == food_col: b check_if_food
    #         else: b collision

    # compare RA and food_row
    rcrd 0xAA
    from-mdc # ACC = REG[RA]
    rarb 0x85
    xor-ba # ACC = ACC ^ MEM[0x85] = REG[RA] ^ food_row
    bnez self_collision # if new_head_row != food_row, then there's a collision since it must be the body

    # else, another check pa
    # compare RB and food_col
    rcrd 0xAB
    from-mdc # ACC = REG[RB]
    rarb 0x86
    xor-ba # ACC = ACC ^ MEM[0x86] = REG[RB] ^ food_col
    bnez self_collision # if new_head_col != food_col, then there's a collision since it must be the body
   
    # at this point, it's just the food! go to check_if_food to know whether the snake would grow or retain
    b check_if_food

check_if_food:
    # here we check if new_head_row (RA) and new_head_col (RB) collides with a food

    # PSEUDOCODE
    # if (food_row, food_col) == (RA, RB):
    #     b grow_the_snake
    # else:
    #     b retain_snake_length

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
    # 1. MEM[0x88], MEM[0x89]++ # update score, careful with carry bit
    # 2. update food_index to be a non-valid index! this is to guarantee that we should update food_index in food_spawn
    # 3. b turn_on_head_led
    # 4. update head_index
    # 5. enqueue head

    b update_score

update_score:
    # 1. update score at MEM[0x88] and MEM[0x89], just add 1
    acc 0x1
    rarb 0x89
    clr-cf # set CF = 0, just in case
    add-mba # ACC = ACC + MEM[0x89] = 0x1 + MEM[0x89]
    to-mba # MEM[0x89] = ACC
    
    # transfer carry bit to more significant nibble
    acc 0x0
    rarb 0x88
    addc-mba # ACC = ACC + MEM[0x88] + CF = 0x0 + MEM[0x88] + CF
    to-mba # MEM[0x88] = ACC

update_food_index:
    # 2. update food_index to be a non-valid index!
    # this would be an edge case, if the tail catches on this again
    # kaya it's important to update this again in food_spawn

    acc 0xF
    rcrd 0x85
    to-mdc
    rcrd 0x86
    to-mdc

    # 3. b turn_on_head_led
    b turn_on_head_led

turn_on_head_led:
    # 3.1 turn on translated(new_head_row, new_head_col)

    # PSEUDOCODE
    # remember, we have normalizedRB_head in MEM[0xA8], calculated earlier
    # we also have translatedRB, and translatedRA in MEM[0xAC], and MEM[0xAD]
    # so we just do this
    # turn_on_head_led:
    #     if normalizedRB_head == 0, MEM[translated(RB:RA)] |= 0b0001
    #     if normalizedRB_head == 1, MEM[translated(RB:RA)] |= 0b0010
    #     if normalizedRB_head == 2, MEM[translated(RB:RA)] |= 0b0100
    #     if normalizedRB_head == 3, MEM[translated(RB:RA)] |= 0b1000

    b is_normalizedRB_head_0

is_normalizedRB_head_0:
    # if normalizedRB_head == 0, b turn_on_bit_0
    # fetch normalizedRB_head from MEM[0xA8] 
    acc 0x0
    rarb 0xA8
    xor-ba # ACC = ACC ^ MEM[0xA8] = 0x0 ^ normalizedRB_head
    beqz turn_on_bit_0

    # else:
    b is_normalizedRB_head_1

is_normalizedRB_head_1:
    # if normalizedRB_head == 1, b turn_on_bit_1
    # fetch normalizedRB_head from MEM[0xA8] 
    acc 0x1
    rarb 0xA8
    xor-ba # ACC = ACC ^ MEM[0xA8] = 0x1 ^ normalizedRB_head
    beqz turn_on_bit_1

    # else:
    b is_normalizedRB_head_2

is_normalizedRB_head_2:
    # if normalizedRB_head == 2, b turn_on_bit_2
    # fetch normalizedRB_head from MEM[0xA8] 
    acc 0x2
    rarb 0xA8
    xor-ba # ACC = ACC ^ MEM[0xA8] = 0x2 ^ normalizedRB_head
    beqz turn_on_bit_2

    # else:
    b is_normalizedRB_head_3

is_normalizedRB_head_3:
    # if normalizedRB_head == 3, b turn_on_bit_3
    # fetch normalizedRB_head from MEM[0xA8] 
    acc 0x3
    rarb 0xA8
    xor-ba # ACC = ACC ^ MEM[0xA8] = 0x3 ^ normalizedRB_head
    beqz turn_on_bit_3

    # else:
    b game_over # PANDEBUG LANG KUNG SAKALI DI TALAGA NANORMALIZE RB, BUT I TRUST IN GOD!

turn_on_bit_0:
    # MEM[translated(RB:RA)] |= 0b0001

    # fetch translatedRB from MEM[0xAC]
    rcrd 0xAC
    from-mdc
    to-reg 1 # REG[RB] = translatedRB

    # fetch translatedRA from MEM[0xAD]
    rcrd 0xAD
    from-mdc
    to-reg 0 # REG[RA] = translatedRA

    acc 0x1
    or*-mba # MEM[translated(RB:RA)] = 0b0001 | MEM[translated(RB:RA)]

    b update_head_index

turn_on_bit_1:
    # MEM[translated(RB:RA)] |= 0b0010

    # fetch translatedRB from MEM[0xAC]
    rcrd 0xAC
    from-mdc
    to-reg 1 # REG[RB] = translatedRB

    # fetch translatedRA from MEM[0xAD]
    rcrd 0xAD
    from-mdc
    to-reg 0 # REG[RA] = translatedRA

    acc 0x2
    or*-mba # MEM[translated(RB:RA)] = 0b0010 | MEM[translated(RB:RA)]

    b update_head_index

turn_on_bit_2:
    # MEM[translated(RB:RA)] |= 0b0100

    # fetch translatedRB from MEM[0xAC]
    rcrd 0xAC
    from-mdc
    to-reg 1 # REG[RB] = translatedRB

    # fetch translatedRA from MEM[0xAD]
    rcrd 0xAD
    from-mdc
    to-reg 0 # REG[RA] = translatedRA

    acc 0x4
    or*-mba # MEM[translated(RB:RA)] = 0b0100 | MEM[translated(RB:RA)]

    b update_head_index

turn_on_bit_3:
    # MEM[translated(RB:RA)] |= 0b1000

    # fetch translatedRB from MEM[0xAC]
    rcrd 0xAC
    from-mdc
    to-reg 1 # REG[RB] = translatedRB

    # fetch translatedRA from MEM[0xAD]
    rcrd 0xAD
    from-mdc
    to-reg 0 # REG[RA] = translatedRA

    acc 0x8
    or*-mba # MEM[translated(RB:RA)] = 0b1000 | MEM[translated(RB:RA)]

    b update_head_index

update_head_index:
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

    b enqueue_head

enqueue_head:
    # enqueue this head at the queue
    # PSEUDOCODE
    # 1. head_ptr++
    # 2. put (RA, RB) in body[head_ptr] for both row and col

    # 1. head_ptr++
    # we can do this by adding one to head_ptr_low (MEM[0xB4]) then add the CF to head_ptr_high (MEM[0xB3])
    acc 0x1
    rarb 0xB4
    clr-cf # set CF = 0, just in case
    add-mba # ACC = ACC + MEM[0xB4] = 0x1 + head_ptr_low
    to-mba # MEM[0xB4] = ACC

    # transfer carry bit to more significant nibble
    acc 0x0
    rarb 0xB3
    addc-mba # ACC = ACC + MEM[0xB3] + CF = 0x0 + head_ptr_high + CF
    to-mba = # MEM[0xB3] = ACC

    # note that head_ptr here can reach 0x40 (that means it reached the col array address when it's not supposed to), so if it reaches 0x40, let's make head_ptr 0x00 again (circular queue)

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
    bnez set_mem_head_ptr # if not equal, but this is impossible since prevented na sa una

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
    to-reg 1 # REG[RB] = head_ptr_high
    
    # set RA = head_ptr_low
    rcrd 0xB4
    from-mdc # ACC = MEM[0xB4]
    to-reg 0 # REG[RA] = head_ptr_low

    # set row[head_ptr_high:head_ptr_low] = RA
    rcrd 0xAA # load new_head_row
    from-mdc # ACC = MEM[0xAA] = new_head_row
    to-mba # MEM[head_ptr_high:head_ptr_low] = ACC = new_head_row

    # set col[translated(head_ptr_high:head_ptr_low)] = RB
    # 1. add 0x4 to head_ptr_high
    acc 0x4
    rarb 0xB3
    add-mba # ACC = 0x4 + MEM[0xB3] = 0x4 + head_ptr_high = translated(head_ptr_high)
    to-reg 1 # REG[RB] = ACC = translated(head_ptr_high)

    # 2. add 0x0 to head_ptr_low, but that's just unnecessary
    # we'll just direct to loading it to RA
    rcrd 0xB4
    from-mdc # ACC = MEM[0xB4] = head_ptr_low
    to-reg 0 # REG[RA] = ACC = translated(head_ptr_low) = head_ptr_low
    
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
    # 1. b turn_off_old_tail_led
    #  1.1 turn off translated(tail_row, tail_col)
    #  1.2 point tail_ptr to the next tail (make sure circular queue), deque old tail, update tail_index to next_tail_index
    # 2. b turn_on_head_led

    # 1. b turn_off_old_tail_led
    b turn_off_old_tail_led

turn_off_old_tail_led:
    # 1.1 turn off translated(tail_row, tail_col)

    # PSEUDOCODE FOR TURNING OFF AN LED GIVEN RA, RB (tail_row, tail_col) index
    # fetch and calculate translatedRB_tail, translatedRA_tail from the precomputed table, store it temporarily in MEM[0xAE], MEM[0xAF]
    # 
    # if RB >= 4, that is CF of RB - 4 != 0, b turn_off_led
    # 
    # else, we should add 1 to address and RB = RB - 4
    #  - translatedRA = translatedRA + 1
    #  - translatedRB = translatedRB + CF + 0
    #  - normalizedRB = RB - 4
    #
    # turn_off_led:
    #     # now we have normalized RB here
    #     if normalizedRB == 0, MEM[translated(RB:RA)] &= 0b1110
    #     if normalizedRB == 1, MEM[translated(RB:RA)] &= 0b1101
    #     if normalizedRB == 2, MEM[translated(RB:RA)] &= 0b1011
    #     if normalizedRB == 3, MEM[translated(RB:RA)] &= 0b0111
    # NOTE: AND bit masking just to turn on that specific bit, and not touch the other 3 bits

    # translatedRB = MEM[0x90 + RA] = MEM[0x9:RA]
    # translatedRA = MEM[0xA0 + RA] = MEM[0xA:RA]

    # 2.1 translate RB into LED matrix index
    acc 0x9
    to-reg 1 # REG[RB] = 0x9
    
    rcrd 0x83
    from-mdc # ACC = REG[RA]
    to-reg 0 # REG[RA] = RA

    from-mba # ACC = MEM[0x9:RA]
    rcrd 0xAE
    to-mdc # store translatedRB temporarily in MEM[0xAE], MEM[0xAE] = MEM[0x9:RA]

    # 2.2 translate RA into LED matrix index
    acc 0xA
    to-reg 1 # REG[RB] = 0xA

    rcrd 0x83
    from-mdc # ACC = REG[RA]
    to-reg 0 # REG[RA] = 0xRA

    from-mba # ACC = MEM[0xA:RA]
    rcrd 0xAF
    to-mdc # store translatedRA in MEM[0xAF], MEM[0xAF] = MEM[0xA:RA]

    # summary:
    # 0xAA = RA (new_head_row)
    # 0xAB = RB (new_head_col)
    # 0xAC = translatedRB (translated new_head_col)
    # 0xAD = translatedRA (translated new_head_row)
    # 0xAE = translatedRB (translated tail_col)
    # 0xAF = translatedRA (translated tail_row)

    # 2.3 we still need to check if we need to add 1 to translatedRB
    # 2.3.1 if RB >= 4, that is CF of RB - 4 != 0, b is_normalizedRB_tail_0
    # 2.3.2 else, we should add 1 to address and RB = RB - 4
    #  - 2.3.2.1 translatedRA = translatedRA + 1, and update final translatedRA to MEM[0xAD]
    #  - 2.3.2.2 translatedRB = translatedRB + CF + 0, and update final translatedRB to MEM[0xAC]
    #  - 2.3.2.3 normalizedRB = RB - 4

    # 2.3.1 check if RB >= 4
    # store 0x4 temporarily to MEM[0xB1]
    acc 0x4
    rcrd 0xB1
    to-mdc # MEM[0xB1] = 0x4

    # store back RB from MEM[0x84]
    rcrd 0x84
    from-mdc # ACC = RB

    # OOPSIE DAISY HERE LMAO! forgot to write here
    rcrd 0xA9
    to-mdc # MEM[0xA9] = RB

    # perform RB - 4
    rarb 0xB1
    sub-mba # ACC = ACC - MEM[0xB1] = RB - 0x4

    bnez-cf is_normalizedRB_tail_0 # if CF is not 0, we don't add 1 to the address na, we're on the right address

    # 2.3.2 else, add 1 to address to translatedRA and translatedRB
    # 2.3.2.1 fetch translatedRA again from MEM[0xAF] and + 1
    acc 0x1
    rarb 0xAF
    clr-cf # set CF = 0, just in case
    add-mba # ACC = ACC + MEM[RB:RA] = 0x1 + MEM[0xAF]
    to-mba # store final translatedRA to MEM[0xAF], MEM[0xAF] = ACC

    # 2.3.2.2 fetch translatedRB again from MEM[0xAE] and + CF from prev
    acc 0x0
    rarb 0xAE
    addc-mba # ACC = ACC + MEM[RB:RA] + CF = 0x0 + MEM[0xAE] + CF
    to-mba # store final translatedRB to MEM[0xAE], MEM[0xAE] = ACC

    # 2.3.2.3 normalizedRB_head = RB - 4
    # store 0x4 temporarily to MEM[0xB1]
    acc 0x4
    rcrd 0xB1
    to-mdc # MEM[0xB1] = 0x4

    # store back RB from MEM[0x84]
    rcrd 0x84
    from-mdc # ACC = RB

    # perform RB - 4
    rarb 0xB1
    sub-mba # ACC = ACC - MEM[0xB1] = RB - 0x4

    rcrd 0xA9
    to-mdc # MEM[0xA9] = ACC = RB - 0x4

    # summary:
    # 0xA8 = normalizedRB_head
    # 0xA9 = normalizedRB_tail
    # 0xAA = RA (new_head_row)
    # 0xAB = RB (new_head_col)
    # 0xAC = translatedRB (translated new_head_col)
    # 0xAD = translatedRA (translated new_head_row)
    # 0xAE = translatedRB (translated tail_col)
    # 0xAF = translatedRA (translated tail_row)

    # 3. start checks
    b is_normalizedRB_tail_0

is_normalizedRB_tail_0:
    # if normalizedRB_tail == 0, b turn_off_bit_0
    # fetch normalizedRB_tail from MEM[0xA9] 
    acc 0x0
    rarb 0xA9
    xor-ba # ACC = ACC ^ MEM[0xA9] = 0x0 ^ normalizedRB_tail
    beqz turn_off_bit_0

    # else:
    b is_normalizedRB_tail_1

is_normalizedRB_tail_1:
    # if normalizedRB_tail == 1, b turn_off_bit_1
    # fetch normalizedRB_tail from MEM[0xA9] 
    acc 0x1
    rarb 0xA9
    xor-ba # ACC = ACC ^ MEM[0xA9] = 0x1 ^ normalizedRB_tail
    beqz turn_off_bit_1

    # else:
    b is_normalizedRB_tail_2

is_normalizedRB_tail_2:
    # if normalizedRB_tail == 2, b turn_off_bit_2
    # fetch normalizedRB_tail from MEM[0xA9] 
    acc 0x2
    rarb 0xA9
    xor-ba # ACC = ACC ^ MEM[0xA9] = 0x2 ^ normalizedRB_tail
    beqz turn_off_bit_2

    # else:
    b is_normalizedRB_tail_3

is_normalizedRB_tail_3:
    # if normalizedRB_tail == 3, b turn_off_bit_3
    # fetch normalizedRB_tail from MEM[0xA9] 
    acc 0x3
    rarb 0xA9
    xor-ba # ACC = ACC ^ MEM[0xA9] = 0x3 ^ normalizedRB_tail
    beqz turn_off_bit_3

    # else:
    b game_over # PANDEBUG LANG KUNG SAKALI DI TALAGA NANORMALIZE RB, BUT I TRUST IN GOD!

turn_off_bit_0:
    # MEM[translated(RB:RA)] &= 0b1110

    # fetch translatedRB from MEM[0xAE]
    rcrd 0xAE
    from-mdc
    to-reg 1 # REG[RB] = translatedRB
    
    # fetch translatedRA from MEM[0xAF]
    rcrd 0xAF
    from-mdc
    to-reg 0 # REG[RA] = translatedRA

    acc 0xE
    and*-mba # MEM[translated(RB:RA)] = 0b1110 & MEM[translated(RB:RA)]

    b deque_tail

turn_off_bit_1:
    # MEM[translated(RB:RA)] &= 0b1101

    # fetch translatedRB from MEM[0xAE]
    rcrd 0xAE
    from-mdc
    to-reg 1 # REG[RB] = translatedRB
    
    # fetch translatedRA from MEM[0xAF]
    rcrd 0xAF
    from-mdc
    to-reg 0 # REG[RA] = translatedRA

    acc 0xD
    and*-mba # MEM[translated(RB:RA)] = 0b1101 & MEM[translated(RB:RA)]

    b deque_tail

turn_off_bit_2:
    # MEM[translated(RB:RA)] &= 0b1011

    # fetch translatedRB from MEM[0xAE]
    rcrd 0xAE
    from-mdc
    to-reg 1 # REG[RB] = translatedRB
    
    # fetch translatedRA from MEM[0xAF]
    rcrd 0xAF
    from-mdc
    to-reg 0 # REG[RA] = translatedRA

    acc 0xB
    and*-mba # MEM[translated(RB:RA)] = 0b1011 & MEM[translated(RB:RA)]

    b deque_tail

turn_off_bit_3:
    # MEM[translated(RB:RA)] &= 0b0111

    # fetch translatedRB from MEM[0xAE]
    rcrd 0xAE
    from-mdc
    to-reg 1 # REG[RB] = translatedRB
    
    # fetch translatedRA from MEM[0xAF]
    rcrd 0xAF
    from-mdc
    to-reg 0 # REG[RA] = translatedRA

    acc 0x7
    and*-mba # MEM[translated(RB:RA)] = 0b0111 & MEM[translated(RB:RA)]

    b deque_tail

deque_tail:
    # 1.2. point tail_ptr to the next tail (make sure circular queue)
    # 1.2.1 make old tail be (0, 0) in row, col arrays
    # 1.2.1.1 set row[tail_ptr_high:tail_ptr_low] = 0x0
    # set RB = tail_ptr_high
    rcrd 0xB5
    from-mdc # ACC = MEM[0xB5]
    to-reg 1 # REG[RB] = tail_ptr_high

    # set RA = tail_ptr_low
    rcrd 0xB6
    from-mdc # ACC = MEM[0xB6]
    to-reg 0 # REG[RA] = tail_ptr_low

    # set row[tail_ptr_high:tail_ptr_low] = 0x0
    acc 0x0
    to-mba # MEM[tail_ptr_high:tail_ptr_low] = ACC = 0x0

    # 1.2.1.2 set col[translated(tail_ptr_high:tail_ptr_low)] = 0x0
    # add 0x4 to tail_ptr_high
    acc 0x4
    rarb 0xB5
    add-mba # ACC = 0x4 + MEM[0xB5] = 0x4 + tail_ptr_high = translated(tail_ptr_high)
    to-reg 1 # REG[RB] = ACC = translated(tail_ptr_high)

    # add 0x0 to tail_ptr_low, but that's just unnecessary
    # we'll just direct to loading it to RA
    rcrd 0xB6
    from-mdc # ACC = MEM[0xB6] = tail_ptr_low
    to-reg 0 # REG[RA] = ACC = translated(tail_ptr_low) = tail_ptr_low

    # finally, we can col[translated(tail_ptr_high:tail_ptr_low)] = 0x0
    acc 0x0
    to-mba # MEM[translated(tail_ptr_high:tail_ptr_low)] = 0x0
    

    # 1.2.2 tail_ptr++ (make sure circular queue)
    # 1.2.2.1 add 1 to tail_ptr_low (MEM[0xB6]) first then add CF to head_ptr_high (MEM[0xB5])
    acc 0x1
    rarb 0xB6
    clr-cf # set CF = 0, just in case
    add-mba # ACC = ACC + MEM[0xB6] = 0x1 + head_ptr_low
    to-mba # MEM[0xB6] = ACC
    # 1.2.2.2 transfer carry bit to more significant nibble
    acc 0x0
    rarb 0xB5
    addc-mba # ACC = ACC + MEM[0xB5] + CF = 0x0 + MEM[0xB5] + CF
    to-mba # MEM[0xB5] = ACC
    # 1.2.2.3 check if magooverflow sa queue yung tail_ptr bounds
    
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
    bnez set_mem_tail_ptr # if not equal, but this is impossible since prevented na sa una

    # else, sumobra head_ptr natin, we need it to be circular
    # set MEM[0xB5] = MEM[0xB6] = 0x0
    acc 0x0
    rarb 0xB5
    to-mba
    rarb 0xB6
    to-mba

set_mem_tail_ptr:
    # 1.2.3 fetch MEM[tail_ptr_high:tail_ptr_low] = (row, col) then put it to new_tail_index, this is basically the next tail
    # 1.2.3.1 set RB = tail_ptr_high
    rcrd 0xB5
    from-mdc # ACC = MEM[0xB5]
    to-reg 1

    # 1.2.3.2 set RA = tail_ptr_low
    rcrd 0xB6
    from-mdc # ACC = MEM[0xB6]
    to-reg 0 # REG[RA] = tail_ptr_low

    # 1.2.3.3 set tail_row to next_tail_row
    from-mba # ACC = MEM[tail_ptr_high:tail_ptr_low]
    rcrd 0x83
    to-mdc # MEM[0x83] = ACC = MEM[tail_ptr_high:tail_ptr_low]

    # 1.2.3.4 set tail_col to next_tail_col
    # translate tail_ptr_high and tail_ptr_low
    # add 0x4 to tail_ptr_high
    acc 0x4
    rarb 0xB5
    clr-cf # set CF = 0, just in case
    add-mba # ACC = 0x4 + MEM[0xB5] = 0x4 + tail_ptr_high = translated(tail_ptr_high)
    to-reg 1 # REG[RB] = ACC = translated(tail_ptr_high)

    # add 0x0 to tail_ptr_low, but that's just unnecessary
    # we'll just direct to loading it to RA
    rcrd 0xB6
    from-mdc # ACC = MEM[0xB6] = tail_ptr_low
    to-reg 0 # REG[RA] = ACC = translated(tail_ptr_low) = tail_ptr_low

    from-mba # ACC = MEM[translated(tail_ptr_high:tail_ptr_low)]
    rcrd 0x84
    to-mdc # MEM[0x84] = ACC = MEM[translated(tail_ptr_high:tail_ptr_low)]


    # 2. b turn_on_head_led
    b turn_on_head_led
# /========== move_snake ==========/



# ========== food_spawn ========== 
food_spawn:
    # NOTE: we have the access to the following variables
    # normalizedRB_head [0xA8] 
    # normalizedRB_tail [0xA9]
    # RA (row coords, 0..7) [0xAA]
    # RB (col coords, 0..7) [0xAB]
    # translatedRB address of head [0xAC]
    # translatedRA address of head [0xAD]
    # translatedRB address of tail [0xAE]
    # translatedRA address of tail [0xAF]

    # IDEA: 
    # 1. Randomly generate a valid index in the grid, meaning dapat hindi currently turned on sa LED matrix
    # 2. Use the following pseudocode for detecting if a given (food_row, food_col) coords is ON in the LED matrix 

    # PSEUDOCODE FOR CHECKING IF A GIVEN RA, RB (row, col) is turned on in the LED matrix
    # fetch translatedRA_food, translatedRB_food from the precomputed table, store it temporarily in MEM[0xAC], MEM[0xAD]
    #
    # if RB >= 4, that is CF of RB - 4 != 0, b check_if_turned_on
    # 
    # else, we should add 1 to address and RB = RB - 4
    #  - translatedRA = translatedRA + 1
    #  - translatedRB = translatedRB + CF + 0
    #  - RB = RB - 4
    # 
    # check_if_turned_on:
    #     if MEM[translated(RB:RA)] & 0x1 == 0x1:
    #         if RB == 0x0:
    #             # RA, RB is turned ON!
    #         else: # no
    #     if MEM[translated(RB:RA)] & 0x2 == 0x2:
    #         if RB == 0x1:
    #             # RA, RB is turned ON!
    #         else: # no
    #     if MEM[translated(RB:RA)] & 0x4 == 0x4:
    #         if RB == 0x2:
    #             # RA, RB is turned ON!
    #         else: # no
    #     if MEM[translated(RB:RA)] & 0x8 == 0x8:
    #         if RB == 0x3:
    #             # RA, RB is turned ON!
    #         else: # no
    # NOTE: we used AND ops to know if that specific bit is on, and not really care about the other 3 bits

    # 3. If the newly generated index is turned-off in the LED matrix, it is valid to be a food! So, update food_row, food_col at MEM[0x85], MEM[0x86]. We're still using the eaten food at this point.
    # 4. Use the following pseudocode for turning on a food LED, given (food_row, food_col)

    # PSEUDOCODE FOR TURNING ON AN LED GIVEN RA, RB (food_row, food_col) index
    # fetch translatedRA_food, translatedRB_food as computed in #2
    #
    # turn_on_led:
    #     # now we have normalized RB here
    #     if normalizedRB == 0, MEM[translated(RB:RA)] |= 0b0001
    #     if normalizedRB == 1, MEM[translated(RB:RA)] |= 0b0010
    #     if normalizedRB == 2, MEM[translated(RB:RA)] |= 0b0100
    #     if normalizedRB == 3, MEM[translated(RB:RA)] |= 0b1000
    # NOTE: nakaOR ops para di natin matouch ung other 3 bits in that address

    # Check if we need to spawn food (food coords at 0xF means eaten)
    rcrd 0x85
    from-mdc
    sub 0xF
    bnez after_food_spawn  # if food_row != 0xF, food still exists
    
    # Generate pseudo-random food position
    b generate_food_position

generate_food_position:
    # Use a better pseudo-random algorithm that jumps around more
    # food_row = ((head_row * 3) + (tail_row * 5) + direction + score) & 0x7
    
    # 1. Get head_row * 3
    rcrd 0x81
    from-mdc
    rcrd 0xB1
    to-mdc  # Store head_row in 0xB1
    
    # Multiply by 3 (add to itself twice)
    from-mdc
    rarb 0xB1
    add-mba  # head_row * 2
    add-mba  # head_row * 3
    rcrd 0xB1
    to-mdc  # Store head_row * 3
    
    # 2. Get tail_row * 5
    rcrd 0x83
    from-mdc
    rcrd 0xB2
    to-mdc  # Store tail_row
    
    # Multiply by 5 (add to itself 4 times)
    from-mdc
    rarb 0xB2
    add-mba  # tail_row * 2
    add-mba  # tail_row * 3
    add-mba  # tail_row * 4
    add-mba  # tail_row * 5
    
    # 3. Add to head_row * 3
    rarb 0xB1
    add-mba
    
    # 4. Add direction
    rarb 0x80
    add-mba
    
    # 5. Add score
    rarb 0x89
    add-mba
    
    # 6. Mask to 0-7
    and 0x7
    rcrd 0xB1
    to-mdc  # Store candidate food_row
    
    # Generate food_col = ((head_col * 7) + (tail_col * 3) + CLOCK) & 0x7
    # We'll use a different multiplier pattern for better distribution
    
    # 1. Get head_col * 7
    rcrd 0x82
    from-mdc
    rcrd 0xB2
    to-mdc  # Store head_col
    
    # Multiply by 7
    from-mdc
    rarb 0xB2
    add-mba  # * 2
    add-mba  # * 3
    add-mba  # * 4
    add-mba  # * 5
    add-mba  # * 6
    add-mba  # * 7
    rcrd 0xB2
    to-mdc
    
    # 2. Get tail_col * 3
    rcrd 0x84
    from-mdc
    rcrd 0xB7
    to-mdc
    
    from-mdc
    rarb 0xB7
    add-mba  # * 2
    add-mba  # * 3
    
    # 3. Add to head_col * 7
    rarb 0xB2
    add-mba
    
    # 4. Add row to create more variation
    rarb 0xB1
    add-mba
    
    # 5. Add score for more randomness
    rarb 0x89
    add-mba
    
    # 6. Mask to 0-7
    and 0x7
    rcrd 0xB2
    to-mdc  # Store candidate food_col
    
    # Now check if this position is valid
    b check_food_position_valid

check_food_position_valid:
    # Load candidate position into RA, RB
    rcrd 0xB1
    from-mdc
    to-reg 0  # RA = candidate food_row
    
    rcrd 0xB2
    from-mdc
    to-reg 1  # RB = candidate food_col
    
    # Store in temp locations for LED checking
    from-reg 0
    rcrd 0xAA
    to-mdc  # MEM[0xAA] = food_row
    
    from-reg 1
    rcrd 0xAB
    to-mdc  # MEM[0xAB] = food_col
    
    # Translate to LED matrix coordinates
    # 1. Translate RB
    acc 0x9
    to-reg 1
    
    rcrd 0xAA
    from-mdc
    to-reg 0
    
    from-mba
    rcrd 0xAC
    to-mdc  # translatedRB in 0xAC
    
    # 2. Translate RA
    acc 0xA
    to-reg 1
    
    rcrd 0xAA
    from-mdc
    to-reg 0
    
    from-mba
    rcrd 0xAD
    to-mdc  # translatedRA in 0xAD
    
    # Check if we need to adjust for col >= 4
    acc 0x4
    rcrd 0xB7
    to-mdc
    
    rcrd 0xAB
    from-mdc
    rcrd 0xA8
    to-mdc  # Store RB for normalization
    
    rarb 0xB7
    sub-mba
    
    bnez-cf check_food_led_status
    
    # Adjust addresses if col >= 4
    acc 0x1
    rarb 0xAD
    clr-cf
    add-mba
    to-mba
    
    acc 0x0
    rarb 0xAC
    addc-mba
    to-mba
    
    # Normalize RB
    acc 0x4
    rcrd 0xB7
    to-mdc
    
    rcrd 0xAB
    from-mdc
    rarb 0xB7
    sub-mba
    rcrd 0xA8
    to-mdc

# WARNING VERY INEFFICIENT
check_food_led_status:
    # Compare with normalized RB to check if the led is turned off
    # if normalized RB == 0: 
    # if bit 0 of LED is on, then position is not free
    acc 0x0
    rarb 0xA8
    xor-ba
    bnez check_food_led_status_skip_0
    
    rcrd 0xAC
    from-mdc
    to-reg 1
    rcrd 0xAD
    from-mdc
    to-reg 0
    from-mba

    b-bit 0 adjust_food_position
    b food_position_is_free

check_food_led_status_skip_0:

    # if normalized RB == 1: 
    # if bit 1 of LED is on, then position is not free
    acc 0x1
    rarb 0xA8
    xor-ba
    bnez check_food_led_status_skip_1
    
    rcrd 0xAC
    from-mdc
    to-reg 1
    rcrd 0xAD
    from-mdc
    to-reg 0
    from-mba

    b-bit 1 adjust_food_position
    b food_position_is_free

check_food_led_status_skip_1:

    # if normalized RB == 2: 
    # if bit 2 of LED is on, then position is not free
    acc 0x2
    rarb 0xA8
    xor-ba
    bnez check_food_led_status_skip_2
    
    rcrd 0xAC
    from-mdc
    to-reg 1
    rcrd 0xAD
    from-mdc
    to-reg 0
    from-mba

    b-bit 2 adjust_food_position
    b food_position_is_free

check_food_led_status_skip_2:

    # assert normalized RB == 3
    acc 0x3
    rarb 0xA8
    xor-ba
    bnez game_over
    # if bit 3 of LED is on, then position is not free
    rcrd 0xAC
    from-mdc
    to-reg 1
    rcrd 0xAD
    from-mdc
    to-reg 0
    from-mba

    b-bit 3 adjust_food_position
    b food_position_is_free

adjust_food_position:
    # Simple adjustment: increment col, wrap around if needed
    rcrd 0xB2
    from-mdc
    add 0x1
    and 0x7  # Keep within 0-7
    rcrd 0xB2
    to-mdc
    
    # If we wrapped to 0, also increment row
    bnez check_food_position_valid
    
    # Increment row too
    rcrd 0xB1
    from-mdc
    add 0x1
    and 0x7
    rcrd 0xB1
    to-mdc
    
    b check_food_position_valid

food_position_is_free:
    # Update food position in memory
    rcrd 0xB1
    from-mdc
    rcrd 0x85
    to-mdc  # MEM[0x85] = food_row
    
    rcrd 0xB2
    from-mdc
    rcrd 0x86
    to-mdc  # MEM[0x86] = food_col
    
    # Turn on food LED
    b turn_on_food_led

turn_on_food_led:
    # We already have normalized RB in 0xA8
    # Check which bit to turn on
    
    # Check if normalizedRB == 0
    acc 0x0
    rarb 0xA8
    xor-ba
    beqz turn_on_food_bit_0
    
    # Check if normalizedRB == 1
    acc 0x1
    rarb 0xA8
    xor-ba
    beqz turn_on_food_bit_1
    
    # Check if normalizedRB == 2
    acc 0x2
    rarb 0xA8
    xor-ba
    beqz turn_on_food_bit_2
    
    # Must be 3
    b turn_on_food_bit_3

turn_on_food_bit_0:
    rcrd 0xAC
    from-mdc
    to-reg 1
    
    rcrd 0xAD
    from-mdc
    to-reg 0
    
    acc 0x1
    or*-mba
    
    b after_food_spawn

turn_on_food_bit_1:
    rcrd 0xAC
    from-mdc
    to-reg 1
    
    rcrd 0xAD
    from-mdc
    to-reg 0
    
    acc 0x2
    or*-mba
    
    b after_food_spawn

turn_on_food_bit_2:
    rcrd 0xAC
    from-mdc
    to-reg 1
    
    rcrd 0xAD
    from-mdc
    to-reg 0
    
    acc 0x4
    or*-mba
    
    b after_food_spawn

turn_on_food_bit_3:
    rcrd 0xAC
    from-mdc
    to-reg 1
    
    rcrd 0xAD
    from-mdc
    to-reg 0
    
    acc 0x8
    or*-mba
    
    b after_food_spawn

# /========== food_spawn ==========/ 



# ========== update_score_display ==========
update_score_display:
    # NOTE: I actually set score to have two nibbles so it can support up to max score of 255, but since required lang is at most 15, it's okay if we read from MEM[0x89]

    # PSEUDOCODE
    # hardcode ifs from score 0 to 15
    # if MEM[0x89] == 0: show_0
    # if MEM[0x89] == 1: show_1
    # ...
    # if MEM[0x89] == 15: show_15

    # if MEM[0x88] == 1, that means naging 15 na ung score and we have to game over na
    acc 0x1
    rarb 0x88
    xor-ba # ACC = 0x1 ^ MEM[0x88]
    beqz game_over

    acc 0x0
    rarb 0x89
    xor-ba # ACC = 0x0 ^ MEM[0x89]
    beqz show_0

    acc 0x1
    rarb 0x89
    xor-ba # ACC = 0x1 ^ MEM[0x89]
    beqz show_1

    acc 0x2
    rarb 0x89
    xor-ba # ACC = 0x2 ^ MEM[0x89]
    beqz show_2

    acc 0x3
    rarb 0x89
    xor-ba # ACC = 0x3 ^ MEM[0x89]
    beqz show_3

    acc 0x4
    rarb 0x89
    xor-ba # ACC = 0x4 ^ MEM[0x89]
    beqz show_4

    acc 0x5
    rarb 0x89
    xor-ba # ACC = 0x5 ^ MEM[0x89]
    beqz show_5

    acc 0x6
    rarb 0x89
    xor-ba # ACC = 0x6 ^ MEM[0x89]
    beqz show_6

    acc 0x7
    rarb 0x89
    xor-ba # ACC = 0x7 ^ MEM[0x89]
    beqz show_7

    acc 0x8
    rarb 0x89
    xor-ba # ACC = 0x8 ^ MEM[0x89]
    beqz show_8

    acc 0x9
    rarb 0x89
    xor-ba # ACC = 0x9 ^ MEM[0x89]
    beqz show_9

    acc 0xA
    rarb 0x89
    xor-ba # ACC = 0xA ^ MEM[0x89]
    beqz show_10

    acc 0xB
    rarb 0x89
    xor-ba # ACC = 0xB ^ MEM[0x89]
    beqz show_11

    acc 0xC
    rarb 0x89
    xor-ba # ACC = 0xC ^ MEM[0x89]
    beqz show_12

    acc 0xD
    rarb 0x89
    xor-ba # ACC = 0xD ^ MEM[0x89]
    beqz show_13

    acc 0xE
    rarb 0x89
    xor-ba # ACC = 0xE ^ MEM[0x89]
    beqz show_14

    acc 0xF
    rarb 0x89
    xor-ba # ACC = 0xF ^ MEM[0x89]
    beqz show_15

    # if score is greater than 15, just go back to the loop, don't update score display!
    b after_update_score_display
# /========== update_score_display ==========/



# ========== hardcoded-mappings ==========
show_0:

    # tens digit
    acc 0x6
    rcrd 0xCD
    to-mdc
    rcrd 0xE6
    to-mdc

    acc 0x9
    rcrd 0xD2
    to-mdc
    rcrd 0xD7
    to-mdc
    rcrd 0xDC
    to-mdc
    rcrd 0xE1
    to-mdc

    # ones digit
    acc 0x6
    rcrd 0xCE
    to-mdc
    rcrd 0xE7
    to-mdc

    acc 0x9
    rcrd 0xD3
    to-mdc
    rcrd 0xD8
    to-mdc
    rcrd 0xDD
    to-mdc
    rcrd 0xE2
    to-mdc

    b after_update_score_display

show_1:
    # tens digit
    # same as prev

    # ones digit
    acc 0x4
    rcrd 0xCE
    to-mdc

    acc 0x6
    rcrd 0xD3
    to-mdc

    acc 0x5
    rcrd 0xD8
    to-mdc

    acc 0x4
    rcrd 0xDD
    to-mdc
    rcrd 0xE2
    to-mdc

    acc 0xF
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_2:

    # tens digit
    # same as prev

    # ones digit
    acc 0x6
    rcrd 0xCE
    to-mdc

    acc 0x9
    rcrd 0xD3
    to-mdc

    acc 0x8
    rcrd 0xD8
    to-mdc

    acc 0x4
    rcrd 0xDD
    to-mdc

    acc 0x2
    rcrd 0xE2
    to-mdc

    acc 0xF
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_3:

    # tens digit
    # same as prev

    # ones digit
    acc 0x6
    rcrd 0xCE
    to-mdc

    acc 0x9
    rcrd 0xD3
    to-mdc

    acc 0x4
    rcrd 0xD8
    to-mdc

    acc 0x8
    rcrd 0xDD
    to-mdc

    acc 0x9
    rcrd 0xE2
    to-mdc

    acc 0x6
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_4:

    # tens digit
    # same as prev

    # ones digit
    acc 0x9
    rcrd 0xCE
    to-mdc

    acc 0x9
    rcrd 0xD3
    to-mdc

    acc 0xF
    rcrd 0xD8
    to-mdc

    acc 0x8
    rcrd 0xDD
    to-mdc
    rcrd 0xE2
    to-mdc
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_5:

    # tens digit
    # same as prev

    # ones digit
    acc 0xF
    rcrd 0xCE
    to-mdc

    acc 0x1
    rcrd 0xD3
    to-mdc

    acc 0x7
    rcrd 0xD8
    to-mdc

    acc 0x8
    rcrd 0xDD
    to-mdc

    acc 0x9
    rcrd 0xE2
    to-mdc

    acc 0x6
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_6:

    # tens digit
    # same as prev

    # ones digit
    acc 0xF
    rcrd 0xCE
    to-mdc

    acc 0x1
    rcrd 0xD3
    to-mdc

    acc 0xF
    rcrd 0xD8
    to-mdc

    acc 0x9
    rcrd 0xDD
    to-mdc

    acc 0x9
    rcrd 0xE2
    to-mdc

    acc 0xF
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_7:

    # tens digit
    # same as prev

    # ones digit
    acc 0xF
    rcrd 0xCE
    to-mdc

    acc 0x8
    rcrd 0xD3
    to-mdc

    acc 0x4
    rcrd 0xD8
    to-mdc

    acc 0x2
    rcrd 0xDD
    to-mdc
    rcrd 0xE2
    to-mdc
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_8:

    # tens digit
    # same as prev

    # ones digit
    acc 0x6
    rcrd 0xCE
    to-mdc

    acc 0x9
    rcrd 0xD3
    to-mdc

    acc 0x6
    rcrd 0xD8
    to-mdc

    acc 0x9
    rcrd 0xDD
    to-mdc

    acc 0x9
    rcrd 0xE2
    to-mdc

    acc 0x6
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_9:

    # tens digit
    # same as prev

    # ones digit
    acc 0xE
    rcrd 0xCE
    to-mdc

    acc 0x9
    rcrd 0xD3
    to-mdc

    acc 0x9
    rcrd 0xD8
    to-mdc

    acc 0xE
    rcrd 0xDD
    to-mdc

    acc 0x8
    rcrd 0xE2
    to-mdc

    acc 0x8
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_10:

    # tens digit
    acc 0x4
    rcrd 0xCD
    to-mdc

    acc 0x6
    rcrd 0xD2
    to-mdc

    acc 0x5
    rcrd 0xD7
    to-mdc

    acc 0x4
    rcrd 0xDC
    to-mdc
    rcrd 0xE1
    to-mdc

    acc 0xF
    rcrd 0xE6
    to-mdc

    # ones digit
    acc 0x6
    rcrd 0xCE
    to-mdc
    rcrd 0xE7
    to-mdc

    acc 0x9
    rcrd 0xD3
    to-mdc
    rcrd 0xD8
    to-mdc
    rcrd 0xDD
    to-mdc
    rcrd 0xE2
    to-mdc

    b after_update_score_display

show_11:

    # tens digit
    # same as prev

    # ones digit
    acc 0x4
    rcrd 0xCE
    to-mdc

    acc 0x6
    rcrd 0xD3
    to-mdc

    acc 0x5
    rcrd 0xD8
    to-mdc

    acc 0x4
    rcrd 0xDD
    to-mdc
    rcrd 0xE2
    to-mdc

    acc 0xF
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_12:

    # tens digit
    # same as prev

    # ones digit
    acc 0x6
    rcrd 0xCE
    to-mdc

    acc 0x9
    rcrd 0xD3
    to-mdc

    acc 0x8
    rcrd 0xD8
    to-mdc

    acc 0x4
    rcrd 0xDD
    to-mdc

    acc 0x2
    rcrd 0xE2
    to-mdc

    acc 0xF
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_13:

    # tens digit
    # same as prev

    # ones digit
    acc 0x6
    rcrd 0xCE
    to-mdc

    acc 0x9
    rcrd 0xD3
    to-mdc

    acc 0x4
    rcrd 0xD8
    to-mdc

    acc 0x8
    rcrd 0xDD
    to-mdc

    acc 0x9
    rcrd 0xE2
    to-mdc

    acc 0x6
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_14:

    # tens digit
    # same as prev

    # ones digit
    acc 0x9
    rcrd 0xCE
    to-mdc

    acc 0x9
    rcrd 0xD3
    to-mdc

    acc 0xF
    rcrd 0xD8
    to-mdc

    acc 0x8
    rcrd 0xDD
    to-mdc
    rcrd 0xE2
    to-mdc
    rcrd 0xE7
    to-mdc

    b after_update_score_display

show_15:

    # tens digit
    # same as prev

    # ones digit
    acc 0xF
    rcrd 0xCE
    to-mdc

    acc 0x1
    rcrd 0xD3
    to-mdc

    acc 0x7
    rcrd 0xD8
    to-mdc

    acc 0x8
    rcrd 0xDD
    to-mdc

    acc 0x9
    rcrd 0xE2
    to-mdc

    acc 0x6
    rcrd 0xE7
    to-mdc

    b after_update_score_display
# /========== hardcoded-mappings ==========/


# ========== game over ==========
self_collision:
    b game_over

bounds_collision:
    b game_over

game_over:
    # OPTIONAL? some indication to know it's game over
    shutdown
# /========== game over ==========/
