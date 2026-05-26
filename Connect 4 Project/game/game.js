// This here is done so that if the user has their mouse on a column in the table, a chip appears above it
document.querySelectorAll(".cell").forEach((cell) => {
	cell.addEventListener("mouseenter", () => {
		const col = cell.dataset.col;
		document.getElementById(`${col}`).style.visibility = "visible";
	});

	// if the user leaves from that column, that chip is hidden.

	cell.addEventListener("mouseleave", () => {
		const col = cell.dataset.col;
		document.getElementById(`${col}`).style.visibility = "hidden";
	});
});

document.getElementById("resetGame").addEventListener("click", () => {
	const alertEl = document.getElementById("Alert");
	alertEl.style.display = "flex";
	alertEl.setAttribute("aria-hidden", "false");
	gameOver = true; //temporarily blocking the game
	// Shows the alert to check if user really wants to reset game
	document.getElementById("alertMessage").textContent =
		"Are you sure you want to Reset the Game?";

	// if yes, check if other user wants to reset too. if not network game just reset.
	document.getElementById("Confirm").addEventListener(
		"click",
		async () => {
			await axios.post("http://localhost:4004/api/gameBack/reset", {
				reset: true,
			});

			// Reset frontend state
			document.querySelectorAll(".cell").forEach((cell) => {
				cell.style.background = "";
			});
			turn = "p1";
			gameOver = false;
			document.querySelector("h3").textContent = "Current player: ";
			const alertElReset = document.getElementById("Alert");
			alertElReset.style.display = "none";
			alertElReset.setAttribute("aria-hidden", "true");
			updatePlayer();
			document.getElementById("playerChip").style.visibility = "none";
			location.reload();
		},
		{ once: true },
	); // once true makes it so the browser removes the listenter after it is fired once, so that only one listener is active per time.

	document // If reset is cancelled just hide the alert.
		.getElementById("Cancel")
		.addEventListener(
			"click",
			async () => {
				const alertElCancel = document.getElementById("Alert");
				alertElCancel.style.display = "none";
				alertElCancel.setAttribute("aria-hidden", "true");
				gameOver = false; // Unblocking the game
			},
			{ once: true },
		);
});

document.getElementById("home").addEventListener("click", async () => {
	const alertElHome = document.getElementById("Alert");
	alertElHome.style.display = "flex";
	alertElHome.setAttribute("aria-hidden", "false");
	gameOver = true; //temporarily blocking the game
	document.getElementById("alertMessage").textContent =
		"Are you sure you want to return to the home page?";
	document.getElementById("Confirm").addEventListener(
		"click",
		async () => {
			if (mode === "pVnp" && ws?.readyState === WebSocket.OPEN) {
				ws.send(JSON.stringify({ type: "leave" }));
				window.location.href = `../openPage/page.html`;
			} else {
				// Calling for a game reset
				await axios.post("http://localhost:4004/api/gameBack/reset", {
					reset: true,
				});
				window.location.href = `../openPage/page.html`;
			}
		},
		{ once: true },
	);

	document.getElementById("Cancel").addEventListener(
		"click",
		async () => {
			gameOver = false;
			const alertElHomeCancel = document.getElementById("Alert");
			alertElHomeCancel.style.display = "none";
			alertElHomeCancel.setAttribute("aria-hidden", "true");
		},
		{ once: true },
	);
});

let gameOver = false;
let ws = null;
//Getting the mode from the URL
const params = new URLSearchParams(window.location.search);
const mode = params.get("mode");

// Fetching state so that if the page is reloaded, the game doesn't restart.
let turn;
document.getElementById("playerChip").style.visibility = "none";

// pVnp manages its own state via WebSocket, so skip the HTTP state fetch
if (mode !== "pVnp") {
	(async () => {
		const {
			data: { board, currentTurn, check, winner, winningCells },
		} = await axios.post("http://localhost:4004/api/gameBack/state", {
			fetchState: true,
		});
		turn = currentTurn;

		// Render existing pieces from saved board state
		board.forEach((row, rowIndex) => {
			row.forEach((cell, colIndex) => {
				if (cell) dropPiece(rowIndex, colIndex, cell);
			});
		});

		if (check) {
			endGame(winner, winningCells);
		} else {
			updatePlayer();
		}
		//checking if game is over already
		// Putting the correct player chip only if game isn't over
	})();
}

//This function checks what cell was clicked, and who's turn it is, and drop the piece into the board, while checking if anyone has one.
if (mode === "pVp") {
	document.querySelectorAll(".cell").forEach((cell) => {
		cell.addEventListener("click", async function (e) {
			if (gameOver) return; //if the gameover is true, do not allow any moves.

			let col = e.target.getAttribute("data-col");
			let claimedTurn = turn;
			const {
				data: {
					valid,
					reason,
					row,
					nextTurn,
					check,
					winner,
					winningCells,
				},
			} = await axios.post("http://localhost:4004/api/gameBack/pVp", {
				col,
				claimedTurn,
			}); // Creating a post request to the db, sending the column and turn so that the move is managed by the server.
			// destructuring response
			if (!valid) {
				console.log(reason);
				return; //if not valid, tell why and then do nothing.
			}

			dropPiece(row, col); //change UI — called before turn update so colour is correct
			turn = nextTurn; //change turn

			if (check) {
				endGame(winner, winningCells); //Ending the game with the winner being displayed
				return;
			}
			updatePlayer(); //updating the player chip.
		});
	});
}

//Same as the block above, but this time the AI move is handeled by the backend.
if (mode === "pVai") {
	document.querySelectorAll(".cell").forEach((cell) => {
		cell.addEventListener("click", async function (e) {
			if (gameOver) return;
			if (turn !== "p1") return; // ignore clicks during AI turn

			const params = new URLSearchParams(window.location.search);
			const difficulty = params.get("difficulty"); //getting the difficulty from url

			let col = e.target.getAttribute("data-col");

			const {
				data: {
					valid,
					reason,
					row,
					aiRow,
					check,
					winner,
					aiMove,
					winningCells,
				},
			} = await axios.post("http://localhost:4004/api/gameBack/pVai", {
				col,
				difficulty,
			}); // Creating a post request to the db, sending the column and turn so that the move is managed by the server.

			if (!valid) {
				console.log(reason);
				return; //if not valid, tell why and then do nothing.
			}

			dropPiece(row, col, "p1"); //render player piece
			dropPiece(aiRow, aiMove, "ai"); //render AI piece
			// Since it techincally its ALWAYS p1s turn, no turn is needed to change, and a further parameter is passed onto droppiece,
			// only so the function knows which one is the player and the ai. Also update player is not needed for the same reason.

			if (check) {
				endGame(winner, winningCells); //Ending the game with the winner being displayed
				return;
			}

			updatePlayer(); //updating the player chip.
		});
	});
}

if (mode === "pVnp") {
	const username = params.get("username"); // username from the URL
	let myRole = null; // "p1" or "p2" assigned by server when matched
	let opponentUsername = null;
	let gameStarted = false; // true once the first move is made

	// Hide reset button since pVnp has no reset
	document.getElementById("resetGame").style.display = "none";

	// Open a WebSocket connection to the server
	ws = new WebSocket("ws://localhost:4004");

	let wsConnected = false;

	// announce and match with opp and open connection
	ws.addEventListener("open", () => {
		wsConnected = true;
		ws.send(JSON.stringify({ type: "join", username }));
	});

	// If the connection stp[s] unexpectedly (before game over) reload so the
	// player automatically reenters the queue. gameOver proctects against reloading
	// on an intentional leave or after a game finishes normally
	ws.addEventListener("close", () => {
		if (wsConnected && !gameOver) location.reload();
	});

	// Handle all incoming messages from the server
	ws.addEventListener("message", async (event) => {
		const msg = JSON.parse(event.data);

		if (msg.type === "waiting") {
			// Still waiting for an opponent
			const npWaitingEl = document.getElementById("npWaiting");
			npWaitingEl.style.display = "flex"; // show np waiting
			npWaitingEl.setAttribute("aria-hidden", "false");
			console.log("Waiting for opponent...");
		}

		if (msg.type === "matched") {
			// Opponent found server tells the user their role (p1 or p2)
			myRole = msg.role;
			opponentUsername = msg.opponentUsername;
			turn = "p1"; // p1 always goes first
			const npWaitingElHide = document.getElementById("npWaiting");
			npWaitingElHide.style.display = "none";
			npWaitingElHide.setAttribute("aria-hidden", "true");
			updatePlayer();
		}

		if (msg.type === "update") {
			// A move was made either by player or opponent, render the chip
			gameStarted = true;
			dropPiece(msg.row, msg.col, msg.player);
			turn = msg.nextTurn;

			if (msg.check) {
				//managing gameOver here because msg is needed.
				gameOver = true;
				document.getElementById("playerChip").style.visibility =
					"hidden";

				if (msg.winner === "Draw") {
					document.querySelector("h3").textContent = "It's a Draw!";
				} else {
					const winnerName =
						msg.winner === myRole ? username : opponentUsername; // if msg.winner is myRole, then return my username, else return opponents
					document.querySelector("h3").textContent =
						`${winnerName} Won!`;

					if (msg.winningCells) {
						msg.winningCells.forEach(([row, col]) => {
							const cell = document.querySelector(
								`[data-row="${row}"][data-col="${col}"]`,
							);
							if (cell) cell.classList.add("winning-cell");
						});
					}

					// Only the winning player submits the highscore
					if (msg.winner === myRole) {
						await axios.post(
							"http://localhost:4004/api/users/highscore",
							{ winner: myRole, username, mode: "pVnp" },
						);
					}
				}
				return;
			}
			updatePlayer();
		}

		if (msg.type === "opponentLeft") {
			if (!gameStarted) {
				// Opponent left before any move was played, so rejoin so
				// the queue on the same connection so P2 doesnt need to refresh.
				myRole = null;
				opponentUsername = null;
				const npWaitingEl = document.getElementById("npWaiting");
				npWaitingEl.style.display = "flex";
				npWaitingEl.setAttribute("aria-hidden", "false");
				ws.send(JSON.stringify({ type: "join", username }));
			} else {
				gameOver = true;
				document.querySelector("h3").textContent =
					`${opponentUsername} disconnected!`;
				document.getElementById("playerChip").style.visibility =
					"hidden";
			}
		}
	});

	// Cell click — send move to server (only on your turn)
	document.querySelectorAll(".cell").forEach((cell) => {
		cell.addEventListener("click", function (e) {
			if (gameOver || !myRole) return;
			if (turn !== myRole) {
				const wrongTurnEl = document.getElementById("wrongTurn");
				wrongTurnEl.style.display = "flex";
				wrongTurnEl.setAttribute("aria-hidden", "false");
				document
					.getElementById("okButton")
					.addEventListener("click", () => {
						wrongTurnEl.style.display = "none";
						wrongTurnEl.setAttribute("aria-hidden", "true");
						return;
					});
			}
			const col = e.target.getAttribute("data-col");
			ws.send(JSON.stringify({ type: "move", col }));
		});
	});
}
// player = turn makes it so IF player parameter is not inputted, it falls back to turn as default value.
function dropPiece(row, col, player = turn) {
	let colour;
	let playerName;
	if (player === "p1") {
		colour = "rgb(168, 19, 19)"; //p1 is red, p2/ai/np is yellow.
		playerName = "Player 1";
	} else if (player === "ai") {
		colour = "rgb(229, 202, 26)";
		playerName = "AI";
	} else {
		colour = "rgb(229, 202, 26)";
		playerName = "Player 2";
	}
	const cell = document.querySelector(
		`[data-row="${row}"][data-col="${col}"]`,
	);
	cell.style.background = colour; // This fills in the hole in the game board
	cell.setAttribute(
		"aria-label",
		`Column ${Number(col) + 1}, Row ${Number(row) + 1}: ${playerName}`,
	);
	cell.setAttribute("aria-disabled", "true");
}

function updatePlayer() {
	if (turn === "p1") {
		// Displays the current players chip color depending on the turn. and changes hover chip color
		document.getElementById("playerChip").style.background =
			"rgb(168, 19, 19)";
		document.querySelectorAll(".hoverChip").forEach((chip) => {
			chip.style.background = "rgb(168, 19, 19)";
		});
	} else {
		document.getElementById("playerChip").style.background =
			"rgb(229, 202, 26)";
		document.querySelectorAll(".hoverChip").forEach((chip) => {
			chip.style.background = "rgb(229, 202, 26)";
		});
	}
}

// End game is resetting the DOM for some reason.

async function endGame(winner, winningCells) {
	gameOver = true; //Block game
	var winName;

	// Determine winner name first
	if (mode === "pVp") {
		if (winner === "p1") winName = params.get("p1Username");
		else if (winner === "p2") winName = params.get("p2Username");
	}
	if (mode == "pVai") {
		const username = params.get("username");
		if (winner === "p1") winName = username;
		else if (winner === "ai") winName = "ai";
	}

	// Update UI immediately before any async calls
	document.querySelector("h3").textContent =
		winner === "Draw" ? "It's a Draw!" : `${winName} Won!`;
	document.getElementById("playerChip").style.visibility = "hidden";

	if (winningCells) {
		winningCells.forEach(([row, col]) => {
			const cell = document.querySelector(
				`[data-row="${row}"][data-col="${col}"]`,
			);
			if (cell) cell.classList.add("winning-cell");
		});
	}

	// Async calls after UI is already updated
	if (mode === "pVp" && winner !== "Draw") {
		await axios.post("http://localhost:4004/api/users/highscore", {
			winner,
			username: winName,
			mode,
		});
	}
	if (mode == "pVai" && winner !== "ai" && winner !== "Draw") {
		const username = params.get("username");
		await axios.post("http://localhost:4004/api/users/highscore", {
			winner,
			username,
			mode,
		});
	}

	if (winner === "Draw") {
		await axios.post("http://localhost:4004/api/gameBack/reset", {
			reset: true,
		});
	}
	// Have no clue why winner chip is always wrong.
	//TODO Work around reset bug
}
