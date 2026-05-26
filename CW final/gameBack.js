const express = require("express");
const router = express.Router(); //creating a router for server.js
const db = require("./db"); // imports the live connected object to the SQLite DB

router.use(express.json());

const board = [
	[0, 0, 0, 0, 0, 0, 0], // row 0 (top)
	[0, 0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0, 0],
	[0, 0, 0, 0, 0, 0, 0], // row 5 (bottom)
];

let turn = "p1";
let p1Moves = 0; // scores tracked in backend so users cant cheat
let p2Moves = 0;

//player = turn is used to make it so if no param is inputted, its default is turn
function dropPiece(col, player = turn) {
	// Going down the rows in the column to find a free space
	var row; // so it can be accessed out of the scope of the for loop.
	for (row = 5; row >= 0; row--) {
		// Decrements because of gravity, first one should be placed at the bottom.
		if (board[row][col] == 0) {
			board[row][col] = player;
			break;
		}
	}

	if (row < 0) {
		return null;
	} // If column is full return null.

	if (player === "p1") p1Moves++;
	else p2Moves++; //counting moves

	return row;
}

function checkWin(board) {
	const rows = board.length;
	const cols = board[0].length;

	// Direction vectors: right, down, diagonal \, diagonal /
	const directions = [
		[0, 1], // horizontal -
		[1, 0], // vertical ^
		[1, 1], // diagonal \
		[1, -1], // diagonal /
	];

	let topRowFull = true;

	for (let row = 0; row < rows; row++) {
		for (let col = 0; col < cols; col++) {
			if (row === 0 && board[row][col] === 0) topRowFull = false;

			if (board[row][col] === 0) {
				continue; //Skip if nothing has been placed in that coordinate
			}
			const player = board[row][col];
			// try each direction from this cell
			for (const [dr, dc] of directions) {
				let count = 1;

				//walk up 3 steps on all directions and check if 4 are the same
				for (let j = 1; j < 4; j++) {
					const r = row + dr * j; // next row in current direction
					const c = col + dc * j; // next col in current direction

					// this is so it doesnt fall off the grid
					if (board[r] === undefined) break; //r needs to be checked alone first or else it will return an error and wont check board[r][c]
					if (board[r][c] === undefined) break;
					// if the player is different so x | x | x | y
					if (board[r][c] !== player) break;

					count++;
				}

				// Saving winning cells to highligh them later
				if (count === 4) {
					const winCells = [];
					for (let j = 0; j < 4; j++) {
						winCells.push([row + dr * j, col + dc * j]);
					}
					return [true, player, winCells];
				}
			}
		}
	}
	// Dealing with draws by checking if the top row is full
	if (topRowFull) {
		console.log("Draw");
		return [true, "Draw", null];
	}

	return [null, false, null];
}

// Tries to find a random non full column.
function randomAI() {
	while (true) {
		let full = true;
		var col = Math.floor(Math.random() * 7);
		for (let row = 0; row < board.length; row++) {
			if (board[row][col] === 0) full = false;
			break;
		}
		if (!full) return col;
	} //TODO need to manage a tie.
}

function intermediateAI(board) {
	//attempts to win or block player stragteigically only on winning moves.
	const rows = board.length;
	const cols = board[0].length;

	// Direction vectors: right, down, diagonal \, diagonal /
	const directions = [
		[0, 1], // horizontal -
		[1, 0], // vertical ^
		[1, 1], // diagonal \
		[1, -1], // diagonal /
	];

	for (let row = 0; row < rows; row++) {
		for (let col = 0; col < cols; col++) {
			if (board[row][col] === 0) {
				continue; //Skip if nothing has been placed in that coordinate
			}
			const player = board[row][col];
			// try each direction from this cell
			for (const [dr, dc] of directions) {
				// entries is js' version of enumerate, it allows for both an index and value to be returned
				let count = 1;

				//walk up 3 steps on all directions and check if 4 are the same
				// count starts at 1 because it already counts the chip at (row, col) the start cell.
				for (let j = 1; j < 3; j++) {
					const r = row + dr * j; // next row in current direction
					const c = col + dc * j; // next col in current direction

					// this is so it doesnt fall off the grid
					if (board[r] === undefined) break; //r needs to be checked alone first or else it will return an error and wont check board[r][c]
					if (board[r][c] === undefined) break;
					// if the player is different so x | x | x | y
					if (board[r][c] !== player) break;

					count++;
				}

				if (count === 3) {
					// Check if connect 4 gravity allows for the winning/blocking play to occur, if so, then return column.

					// checking the tail of the 3-run X X X . (in all directions)
					const endR = row + dr * 3;
					const endC = col + dc * 3; // to get the space after the third chip

					// check head, which is dr, dc before the current coordinate
					const startR = row - dr;
					const startC = col - dc;

					// if not out of bounds, check if the location is empty.
					// (_XXX)
					if (
						startR >= 0 &&
						startR < rows &&
						startC >= 0 &&
						startC < cols
					) {
						// check if space below has a chip in it (connect 4 has gravity so it needs a chip to "stand" there)
						if (
							// if start R === rows - 1 is if the startR and StarC is on the bottom row
							startR === rows - 1 ||
							board[startR + 1][startC] !== 0
						)
							if (board[startR][startC] === 0) return startC;
						// then if there is no chip in the spot, return the column.
					}

					// (XXX_)
					if (endR >= 0 && endR < rows && endC >= 0 && endC < cols) {
						if (endR === rows - 1 || board[endR + 1][endC] !== 0)
							if (board[endR][endC] === 0) return endC;
					}
				}
			}
		}
	}

	return randomAI(); // return a random move if no winning or blocking move is found.
}

function getValidColumns(board) {
	const valid = [];
	for (let col = 0; col < 7; col++) {
		// Looks at the top row if the column isnt full valid move then Returns an array of all playable column numbers.
		if (board[0][col] === 0) valid.push(col);
	}
	return valid;
}

function simulateDrop(board, col, player) {
	const newBoard = board.map((row) => [...row]); // Simulates moves with a copy of board so that the actual board isnt affected to explore hypothetical moves
	for (let row = 5; row >= 0; row--) {
		if (newBoard[row][col] === 0) {
			newBoard[row][col] = player;
			break;
		}
	}
	return newBoard;
}

function minimax(board, isMaximising, depth = 5) {
	const [isOver, winner] = checkWin(board); // check if game is over

	// Base case is if game is over
	if (isOver || depth === 0) {
		if (winner === "ai") return 1;
		if (winner === "p1") return -1;
		return 0; // draw
	}

	const validCols = getValidColumns(board);

	// AI turn wants to pick best move so maximising
	if (isMaximising) {
		let best = -Infinity;
		for (const col of validCols) {
			//loops through every valid column, simulates dropping a piece ther then calls itself on the new board
			const newBoard = simulateDrop(board, col, "ai");
			best = Math.max(best, minimax(newBoard, false, depth - 1));
		}
		return best;
		// when player turn ai wants to pick worst move so minimizing
	} else {
		let best = +Infinity;
		for (const col of validCols) {
			const newBoard = simulateDrop(board, col, "p1");
			best = Math.min(best, minimax(newBoard, true, depth - 1));
		}
		return best;
	}
}

function advancedAI(board) {
	const validCols = getValidColumns(board);
	let bestScore = -Infinity;
	let bestCol = validCols[0];

	for (const col of validCols) {
		const newBoard = simulateDrop(board, col, "ai");
		const score = minimax(newBoard, false, 5); // false because AI just moved, now minimising player's turn
		if (score > bestScore) {
			bestScore = score;
			bestCol = col;
		}
	}
	return bestCol;
}

//ENDPOINTS --------------------------------------------------------------

//PVP endpoint
router.post("/api/gameBack/pVp", (req, res) => {
	try {
		console.log("Body received:", req.body);
		const { col, claimedTurn } = req.body; //destructuring body

		if (claimedTurn !== turn)
			return res.json({ valid: false, reason: "Wrong Turn" });
		// This is to check for cheating

		let row = dropPiece(Number(col)); //this is just to show that move was made, or if it was full/error
		if (row === null)
			return res.json({ valid: false, reason: "Column Full" });

		const [check, winner, winningCells] = checkWin(board); // checking if someone has won, and if so who the winner is.

		if (!check) turn = turn === "p1" ? "p2" : "p1"; // only switch turn if game isn't over

		res.status(202).json({
			valid: true,
			row,
			nextTurn: turn,
			check,
			winner,
			winningCells,
		}); //returns created status code (accepted) and returns body
	} catch (err) {
		console.log(`Something Went wrong: ${err}`);
		res.status(500).json({ error: "Server error" });
	}
});

//PVAI endpoint
router.post("/api/gameBack/pVai", (req, res) => {
	try {
		console.log("Body received:", req.body);
		const { col, difficulty } = req.body; //destructuring body

		// Dropping player piece
		let row = dropPiece(Number(col)); //this is just to show that move was made, or if it was full/error
		if (row === null)
			return res.json({ valid: false, reason: "Column Full" });

		let aiMove;
		//getting the aiMove based on the difficulty.
		if (difficulty === "pVai_R") {
			aiMove = randomAI();
		} else if (difficulty === "pVai_I") {
			aiMove = intermediateAI(board);
		} else if (difficulty === "pVai_A") {
			aiMove = advancedAI(board);
		} else {
			return res.json({ valid: false, reason: "Invalid Difficulty" });
		}

		let aiRow = dropPiece(Number(aiMove), "ai"); //AI will never choose a full column.
		//ai param is passed so that dropPiece drops AI (since turn isnt changed in AI).

		const [check, winner, winningCells] = checkWin(board); // checking if someone has won, and if so who the winner is.

		res.status(202).json({
			valid: true,
			row,
			aiRow,
			aiMove,
			check,
			winner,
			winningCells,
		}); //returns created status code (accepted) and returns body
	} catch (err) {
		console.log(`Something Went wrong: ${err}`);
		res.status(500).json({ error: "Server error" });
	}
});

function handlePvNPmove(col, player) {
	if (turn !== player) return { valid: false, reason: "Not your turn" }; // check if turn is correct

	const row = dropPiece(col, player);
	if (row === null) return { valid: false, reason: "Column Full" };

	const [check, winner, winningCells] = checkWin(board);
	if (!check) turn = turn === "p1" ? "p2" : "p1"; // switch turn

	return {
		valid: true,
		row,
		nextTurn: turn,
		check: check || null,
		winner: winner || null,
		winningCells: winningCells || null,
	};
}

//RESET endpoint
router.post("/api/gameBack/reset", (req, res) => {
	try {
		const { reset } = req.body;

		if (reset) {
			for (let row = 0; row < board.length; row++) {
				//Resetting board.
				for (let col = 0; col < board[0].length; col++) {
					board[row][col] = 0;
				}
			}

			turn = "p1";
			p1Moves = 0; // resetting other variables
			p2Moves = 0;
			res.status(200).json({ message: "Game was reset" });
		} else res.status(200).json({ message: "Reset was not allowed" });
	} catch (err) {
		console.log(`Something went wrong while trying to reset game: ${err}`);
		res.status(500).json({ error: "Server error" });
	}
});

// Highscore Endpoint
router.post("/api/users/highscore", (req, res) => {
	try {
		const { winner, username, mode } = req.body;

		let highscore;

		if (mode === "pVp") {
			if (winner === "p1") highscore = p1Moves;
			else highscore = p2Moves;

			db.get(
				"SELECT highScorePvP FROM users WHERE username = ?",
				[username],
				(err, row) => {
					if (err) {
						console.error(`Error in fetchin user data: ${err}`);
						return res
							.status(500)
							.json({ error: "failed to get user data" });
					}
					const currentHighScore = row.highScorePvP;
					// only save highscore if it is larger than currently stored highscore (which is defaulted to 0)
					if (currentHighScore > highscore || currentHighScore == 0) {
						db.run(
							"UPDATE users SET highScorePvP = ? WHERE username = ?",
							[highscore, username],
							(err) => {
								if (err) {
									console.error(
										`An Error occured while updating ${username} highscore: ${err}`,
									);
									return res.status(500).json({
										error: "Failed to update user",
									}); //returns server error status code
								}
								res.status(200).json({
									message: "Highscore succesfully updated",
								});
							},
						);
					} else {
						// this is what happens if no response is made, meaning that high score wasnt updated.
						res.status(200).json({
							message:
								"High Score smaller or equal to than of currently stored",
						});
					}
				},
			);
		}

		if (mode === "pVai") {
			if (winner === "p1") {
				// highscore should only be saved if its a player.
				highscore = p1Moves;
				db.get(
					"SELECT highScoreAI FROM users WHERE username = ?",
					[username],
					(err, row) => {
						if (err) {
							console.error(`Error in fetchin user data: ${err}`);
							return res
								.status(500)
								.json({ error: "failed to get user data" });
						}
						const currentHighScore = row.highScoreAI;

						if (
							currentHighScore > highscore ||
							currentHighScore == 0
						) {
							db.run(
								"UPDATE users SET highScoreAI = ? WHERE username = ?",
								[highscore, username],
								(err) => {
									if (err) {
										console.error(
											`An Error occured while updating ${username} highscore: ${err}`,
										);
										return res.status(500).json({
											error: "Failed to update user",
										}); //returns server error status code
									}
									res.status(200).json({
										message:
											"Highscore succesfully updated",
									});
								},
							);
						} else {
							// this is what happens if no response is made, meaning that high score wasnt updated.
							res.status(200).json({
								message:
									"High Score smaller or equal to than of currently stored",
							});
						}
					},
				);
			}
		}

		if (mode === "pVnp") {
			//TODO comment
			if (winner === "p1") highscore = p1Moves;
			else highscore = p2Moves;

			db.get(
				"SELECT highScoreNP FROM users WHERE username = ?",
				[username],
				(err, row) => {
					if (err) {
						console.error(`Error fetching user data: ${err}`);
						return res
							.status(500)
							.json({ error: "failed to get user data" });
					}
					const currentHighScore = row ? row.highScoreNP : 0;

					if (
						currentHighScore > highscore ||
						currentHighScore === 0
					) {
						db.run(
							"UPDATE users SET highScoreNP = ? WHERE username = ?",
							[highscore, username],
							(err) => {
								if (err) {
									console.error(
										`An Error occured while updating ${username} highscore: ${err}`,
									);
									return res.status(500).json({
										error: "Failed to update user",
									});
								}
								res.status(200).json({
									message: "Highscore succesfully updated",
								});
							},
						);
					} else {
						res.status(200).json({
							message:
								"High Score smaller or equal to than of currently stored",
						});
					}
				},
			);
		}
	} catch (err) {
		console.log(
			`Something went wrong while trying to update highscores: ${err}`,
		);
		res.status(500).json({ error: "Server error" });
	}
});

// Game state request
router.post("/api/gameBack/state", (req, res) => {
	try {
		const { fetchState } = req.body;
		if (fetchState) {
			let [check, winner, winningCells] = checkWin(board);
			let currentTurn = turn;
			res.status(200).json({
				board,
				currentTurn,
				check,
				winner,
				winningCells,
			}); // returning the current board and turn
		} else {
			console.log("fetch state was not valid.");
			res.status(200).json({ message: "fetch not accepted" });
		}
	} catch (err) {
		console.log(`An error occured while fetching game State: ${err}`);
		res.status(500).json({ error: "Server Error" });
	}
});

// Specific for PvNP gamemode
function resetBoardState() {
	for (let row = 0; row < board.length; row++) {
		for (let col = 0; col < board[0].length; col++) {
			board[row][col] = 0;
		}
	}
	turn = "p1";
	p1Moves = 0;
	p2Moves = 0;
}

module.exports = router;
module.exports.handlePvNPmove = handlePvNPmove;
module.exports.resetBoardState = resetBoardState;
