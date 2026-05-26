.data
#   -   PLAYER CLASS 	- 
	#position:
	pY: .word 4		# grid[3][3] STARTS AT MIDDLE #
	pX: .word 3	
	
#   -   REWARD CLASS 	- 
	
	#position:
	rX: .word  0 #NULL
	rY: .word  0 #NULL
 
 #   -   WALL CLASS  	- 
 
#here i am creating a 2d array of chars so i can access its indexes later for movement of the player
		
	#                  x
	#	 0   1   2   3   4   5   6   7

grid: .byte 'S','c','o','r','e',':','0',' '   #0
		'#','#','#','#','#','#','#','#'   #1					
		'#',' ',' ',' ',' ',' ',' ','#'   #2						
		'#',' ',' ',' ',' ',' ',' ','#'   #3						
		'#',' ',' ','P',' ',' ',' ','#'   #4   y					
		'#',' ',' ',' ',' ',' ',' ','#'   #5							
		'#',' ',' ',' ',' ',' ',' ','#'   #6					
		'#','#','#','#','#','#','#','#'   #7
	

 #   -   GAME CLASS 	- 
 
 pScore:  .word 0
 GOreason: .asciiz "GAME OVERScore: "
 
 
 
 #   -   DISPLAY CLASS 	-
 
 clear: .word 12
  
 # ------------------------ program below --------------------------#
 
.text

j main

main:

	j loadReward
	
		loadReward: 
			
			create_index:
				# rX index creation
				li $a1, 7		#upper bound
				li $v0, 42 		#syscall for random number in range
				syscall
				
				beq $a0, 0,adD			#if random num is 0, then add 1 for it not to be 0 (would be outside of wall), else continue
				j con
				adD:
					addi $a0,$a0,1
				con:
				
				sw $a0, rX
				
				# rY index creation
				li $a1, 7		#upper bound
				li $v0, 42 		#syscall for random number in range
				syscall
				
				beq $a0, 0,add2
				beq $a0, 1,addd
				j cont			#if random num is 0 add 2, and if 1 add 1, since 0 and 1 are off bounds (outside of wall), else continue.
				addd:
					addi $a0,$a0,1
				add2:
					addi $a0,$a0,2
				cont:
				
				sw $a0, rY
			
			lw $t1, pY
			lw $t2, pX			#loading coordinates of player and reward
			lw $t3, rX
			lw $t4, rY
			
			#preventing reward spawning on player
			beq $t1,$t3,and
			j skip		
							#if player index and reward index the same, create another reward index, if not then skip
				and:
					beq $t2,$t4,create_index
			
			skip:	
				#storing reward in the grid
				la $t0, grid            # Load grid base address
				lw $t1, rY
				lw $t2, rX
				
				#calculating grid index (reused code from move function
				
				mul  $s0, $t1, 8
    				add  $s0, $s0, $t2
    				add  $s0, $t0, $s0
    				
    				li   $t3, 'R'             # ASCCII R 
    				sb   $t3, 0($s0)          # storing R in in its index

		loadScore:
			lw $t9,pScore
			bgt $t9,9,twoDigit		#if score is bigger than 9 (AKA a two digit number, then go to two digit function)
			j oneDigit
	
			twoDigit:
				#first digit
				divu $t9,$t9,10	#integer division
				mflo $t8		# LO register stores quotient.
				mfhi $t7		# HI register stores remainder, moving remainder into t7
		
				#convert to asccii
				addi $t8,$t8,48
				addi $t7,$t7,48
		
				la $t0, grid		#loading grid
		
				#calculating index grid[6][0]
				li $t1, 0
				li $t2, 6		
		
				mul  $s0, $t1, 8
    				add  $s0, $s0, $t2		#reused code from move function
    				add  $s0, $t0, $s0
    				
    				sb   $t8, 0($s0)          # storing first digit in score: _
    				
    				#calculating index grid[6][0]
				li $t2, 7		
		
				mul  $s0, $t1, 8
    				add  $s0, $s0, $t2		#reused code from move function
    				add  $s0, $t0, $s0
    				
    				sb   $t7, 0($s0)          # storing second digit in score: _x
		
				jal LoadDisplay		#reload display then go back to game function
				j gameFunction
	
			oneDigit:
				addi $t9, $t9,48	#converting to ascii
				la $t0, grid	#loading grid
				#calculating index grid[6][0]
				li $t1, 0
				li $t2, 6		
		
				mul  $s0, $t1, 8
    				add  $s0, $s0, $t2		#reused from move function
    				add  $s0, $t0, $s0
    				
    				
    				sb   $t9, 0($s0)          # storing first digit in score: x_
    				
    				jal LoadDisplay
    				j gameFunction

		LoadDisplay:
			
			la $t0, grid			#loading address of grid that will point to the byte at which the grid is at, so will start with first '#'
			li $t1, 0				#counter for the current row
			li $t2, 0				#counter for the current column
			li $t3, 0xFFFF0008		#loading the MMIO control address
			li $t4, 0xFFFF000C		#loading the MMIO transmitter data address
			
			#function to clear display before loading it #
			
					#loading asciiz 12
			lw $t9, clear
			
			waitLoopClear:					#loop inspiration from: https://wilkinsonj.people.charleston.edu/mmio.html
				lw $t6, 0($t3)
				andi $t6, $t6, 1
				beq $t6, $zero, waitLoopClear
			
			sb $t9, 0($t4)					#store it in the MMIO transmitter data register
					
			outerLoop:
				beq $t1, 8, exitOuter		#if the 7 columns are printed exit
				
				li $t2, 0				#reseting column counter for each row
															#this is a nested for loop to print the grid
					innerLoop:
						beq $t2, 8, exitInner		#if the 7 rows are printed exit
						
						mul $s0, $t1, 8 			#calculating index
						add $s0, $s0, $t2 		#doing the index = (row * width) + column	
						add $s0, $t0, $s0			#adding the address of the grid in that position
						
						lb $t5, 0($s0)			#loading the byte at the current index of the grid		
						
						waitLoop:					#loop inspiration from: https://wilkinsonj.people.charleston.edu/mmio.html
							lw $t6, 0($t3)
							andi $t6, $t6, 1
							beq $t6, $zero, waitLoop
						
						sb $t5, 0($t4) #copying to data register
											
						
						addi $t2, $t2, 1			 #incrementing row counter
						j innerLoop
						
						exitInner:
						
							li $t5, 10 #loading ASCII 10 which is \n to print a new line after a row is completed
							
							waitLoop2:
								lw $t6, 0($t3)
								andi $t6, $t6, 1			#reused from other waitloops
								beq $t6, $zero, waitLoop2
								
							sb $t5, 0($t4) #copying \n to data register
							
						
						addi $t1, $t1, 1			#incrementing column counter
						j outerLoop
				
				exitOuter:
				jr $ra
				#load return address


		gameFunction:	
			lw $t0, pScore				# current score
			beq $t0, 100, gameOver			# while player point not equal to 40, continue, if so jump to gameover
		
				
			ifCollision:
    				lw   $t1, pY              # Load current player X
    				lw   $t2, pX              # Load current player Y
    				
    				beq $t1, 1, gameOver
    				beq $t1, 7, gameOver
    				beq $t2, 0, gameOver		#checking if px and py are in the range of the borders #, using their indexes.
    				beq $t2, 7, gameOver
			
			ifReward:
			
				lw $t3, pY
				lw $t4, pX			
				lw $t5, rY				#loading player and reward coordinates
				lw $t6, rX
   				 
   				bne $t5, $t3, skipReward
   				bne $t6, $t4, skipReward		#if player coordinates are not on TOP of (equal to) reward coordinates skip.
   				
   				yesReward:
   					lw $t9,pScore
   					addi $t9,$t9,5			#if they are, then add 5 points to score and spawn a new reward.
   					sw $t9,pScore
					j loadReward
   				
   				skipReward:
			
			 waitForKey:
    				li $t0, 0xFFFF0000       # Receiver Control Register
    				lw $t1, 0($t0)           # Load control register
    				andi $t1, $t1, 1         # Check Ready bit (bit 0)
    				beq $zero, $t1, waitForKey     # If not ready, wait

    				# Read key from MMIO keyboard data register
    				li $t0, 0xFFFF0004
    				lw $t1, 0($t0)           # Load pressed key
    				
    
 			li   $t3, 'w'
			beq  $t1, $t3, move_up
			li   $t3, 's'
			beq  $t1, $t3, move_down			#loading wasd into temp registers to be compared to jump into their associated functions
			li   $t3, 'a'
			beq  $t1, $t3, move_left
			li   $t3, 'd'
			beq  $t1, $t3, move_right 	
 	
			j gameFunction 							# all done, return 
    	
    	
			move_up:
			
   		 		lw   $t1, pY              # Load current player Y
    				lw   $t2, pX              # Load current player X
    				la   $t0, grid            # Load grid base address

   				# Calculate current grid index (player position)
    				mul  $s0, $t1, 8          # row * width
    				add  $s0, $s0, $t2        # (row * width) + column
    				add  $s0, $t0, $s0        # Get grid address
    				li   $t3, ' '             # ASCII space (empty cell)
    				sb   $t3, 0($s0)          # Clear old position

    				# Update Y coordinate (move up)
    				subi $t1, $t1, 1
    				sw   $t1, pY

    				# Calculate new grid index (player new position)
    				mul  $s0, $t1, 8
    				add  $s0, $s0, $t2
    				add  $s0, $t0, $s0
    				li   $t3, 'P'             # ASCII 'P' (player)
    				sb   $t3, 0($s0)          # Store new position

    				jal  LoadDisplay       # Refresh only changed cells
    				j    gameFunction
    				
    			move_down:
			
   		 		lw   $t1, pY              # Load current player X
    				lw   $t2, pX              # Load current player Y
    				la   $t0, grid            # Load grid base address

   				# Calculate current grid index (player position)
    				mul  $s0, $t1, 8          # row * width
    				add  $s0, $s0, $t2        # (row * width) + column
    				add  $s0, $t0, $s0        # Get grid address
    				li   $t3, ' '             # ASCII space (empty cell)
    				sb   $t3, 0($s0)          # Clear old position

    				# Update Y coordinate (move up)
    				addi $t1, $t1, 1
    				sw   $t1, pY

    				# Calculate new grid index (player new position)
    				mul  $s0, $t1, 8
    				add  $s0, $s0, $t2
    				add  $s0, $t0, $s0
    				li   $t3, 'P'             # ASCII 'P' (player)
    				sb   $t3, 0($s0)          # Store new position

    				jal  LoadDisplay       # Refresh only changed cells
    				j    gameFunction
			
			move_left:
			
   		 		lw   $t1, pY              # Load current player X
    				lw   $t2, pX              # Load current player Y
    				la   $t0, grid            # Load grid base address

   				# Calculate current grid index (player position)
    				mul  $s0, $t1, 8          # row * width
    				add  $s0, $s0, $t2        # (row * width) + column
    				add  $s0, $t0, $s0        # Get grid address
    				li   $t3, ' '             # ASCII space (empty cell)
    				sb   $t3, 0($s0)          # Clear old position

    				# Update X coordinate (move left)
    				subi $t2, $t2, 1
    				sw   $t2, pX

    				# Calculate new grid index (player new position)
    				mul  $s0, $t1, 8
    				add  $s0, $s0, $t2
    				add  $s0, $t0, $s0
    				li   $t3, 'P'             # ASCII 'P' (player)
    				sb   $t3, 0($s0)          # Store new position

    				jal  LoadDisplay       # Refresh only changed cells
    				j    gameFunction
				#input the movements here, the only thing that should be in the other file is the interrupt stuff				
			
			move_right:
			
   		 		lw   $t1, pY              # Load current player X
    				lw   $t2, pX              # Load current player Y
    				la   $t0, grid            # Load grid base address

   				# Calculate current grid index (player position)
    				mul  $s0, $t1, 8          # row * width
    				add  $s0, $s0, $t2        # (row * width) + column
    				add  $s0, $t0, $s0        # Get grid address
    				li   $t3, ' '             # ASCII space (empty cell)
    				sb   $t3, 0($s0)          # Clear old position

    				# Update Y coordinate (move right)
    				addi $t2, $t2, 1
    				sw   $t2, pX

    				# Calculate new grid index (player new position)
    				mul  $s0, $t1, 8
    				add  $s0, $s0, $t2
    				add  $s0, $t0, $s0
    				li   $t3, 'P'             # ASCII 'P' (player)
    				sb   $t3, 0($s0)          # Store new position

    				jal  LoadDisplay       # Refresh only changed cells
    				j    gameFunction

		
			gameOver:
				li $t8, 0				#counter to print new line
				la $t1, GOreason			#loading the game over reason
				lw $t9, clear			#clear ascii 12
				li $t4, 0xFFFF000C		#loading the MMIO transmitter data address
				li $t2, 0xFFFF0008		#loading control register
			
				#clearing screen
				waitLoopClear2:					#loop inspiration from: https://wilkinsonj.people.charleston.edu/mmio.html
					lw $t6, 0($t2)
					andi $t6, $t6, 1
					beq $t6, $zero, waitLoopClear2
			
				sb $t9, 0($t4)					#store it in the MMIO transmitter data register
		
			#printing out Game over message
			#this loop was made by using the same logic of the grid though without .byte and with a string
				printLoop:
					lb $t7, 0($t1)			#loading first character from string
					beq $zero, $t7, printScore		#while index not at null terminator
					
					waitLoopPrint:					#loop inspiration from: https://wilkinsonj.people.charleston.edu/mmio.html
						lw $t6, 0($t2)
						andi $t6, $t6, 1
						beq $t6, $zero, waitLoopPrint
						
					sb $t7, 0($t4) #copying to data register
					addi $t1, $t1, 1	# i++ index to get next character
					
					addi $t8, $t8, 1	# incrementing gameover counter
					#if counter == 9 because GAME OVER has 9 characters
					#print new line, if not then just continue looping. after print new line is done, go back to loop.
					beq $t8, 9, newL
					
					j printLoop
					
					newL:
						li $t5, 10 #loading ASCII 10 which is \n to print a new line after a row is completed
							
							waitLoopNewL:
									lw $t6, 0($t2)				#reused waitLoop
									andi $t6, $t6, 1
									beq $t6, $zero, waitLoopNewL
								
							sb $t5, 0($t4) #copying \n to data register
							j printLoop
				
				printScore:					#almost the same logic as loadScore, though without the need of grid index calculations
					lw $t9,pScore
					beq $t9,100,maxScore		#checking if score is 100 to go to max score function
					bgt $t9,9,secondDigit		#checking if pScore is a single or double digit number (up until 10 is 1 digit)
					j firstDigit
	
					secondDigit:
						#first digit
						divu $t9,$t9,10	#integer division
						mflo $t8		# LO register stores quotient.
						mfhi $t7		# HI register stores remainder, moving remainder into t7
		
						#convert to asccii
						addi $t8,$t8,48
						addi $t7,$t7,48
			
						#printing first digit:
						waitLoopDigitOne:
							lw $t6, 0($t2)
							andi $t6, $t6, 1				#reused waitloop
							beq $t6, $zero, waitLoopDigitOne
						
						sb $t8, 0($t4) #copying to data register
				
						#printing second digit
						waitLoopDigitTwo:
							lw $t6, 0($t2)
							andi $t6, $t6, 1					#reused waitloop
							beq $t6, $zero, waitLoopDigitTwo
						
						sb $t7, 0($t4) #copying to data register
				
						j exit
	
					firstDigit:
						addi $t9, $t9,48	#converting to ascii
				
    						#printing single digit
						waitLoopDigitThree:
							lw $t6, 0($t2)					#reused Waitloop
							andi $t6, $t6, 1
							beq $t6, $zero, waitLoopDigitThree
						
						sb $t9, 0($t4) #copying to data register
    				
    						j exit
					
					maxScore:
						li $t9, 49		#loading 1 in ascii
						li $t8, 48		#loading 0 in ascii
						li $t7, 48		#loading 0 in ascii
						
						#printing first digit:
						waitLoopDigitMax1:
							lw $t6, 0($t2)
							andi $t6, $t6, 1				#reused waitloop
							beq $t6, $zero, waitLoopDigitMax1
						
						sb $t9, 0($t4) #copying to data register
				
						#printing second digit
						waitLoopDigitMax2:
							lw $t6, 0($t2)
							andi $t6, $t6, 1					#reused waitloop
							beq $t6, $zero, waitLoopDigitMax2
						
						sb $t8, 0($t4) #copying to data register
						
						#printing third digit
						waitLoopDigitMax3:
							lw $t6, 0($t2)
							andi $t6, $t6, 1					#reused waitloop
							beq $t6, $zero, waitLoopDigitMax3
						
						sb $t7, 0($t4) #copying to data register
				
						j exit
						
					
			exit:
				waitLoopExit:
							lw $t6, 0($t2)		#using a reUsed waitloop so the last digit can be printed before exiting program
							andi $t6, $t6, 1
							beq $t6, $zero, waitLoopExit
				li $v0, 10
				syscall
				#exit syscall
	
		
