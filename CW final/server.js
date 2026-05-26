const express = require("express");
const app = new express(); //creating backend application
const PORT = 4004;

const db = require("./db"); // imports the live connected object to the SQLite DB
const cors = require("cors"); // Cross origin resource sharing is needed to allow communication between back and frontend

const WebSocket = require("ws");

//Server configuration
// Create a WebSocket server
const wss = new WebSocket.Server({ noServer: true });

app.use(cors());
// This makes no validation required for any requests, which makes the server vulnerable for many things such as an sql injection but, this projectp does not require this so for ease of use i'll use this.

app.use(express.json()); // allows express to read JSON

const gameLogic = require("./gameBack");

app.use("/", gameLogic); //using the gameLogic routes.

// USERNAME INITIAL INPUT IN HOMEPAGE ENDPOINT
app.post("/api/users", (req, res) => {
	console.log("Body received:", req.body);

	const { username } = req.body; //destructuring body
	const sql = `INSERT INTO users(username) VALUES (?)`; // prepared sql statement which allows for values to be inputted dynamically. ? will be replaced with username.

	db.run(sql, [username], (err) => {
		// executes sql statement, modifying DB with the username input
		if (err) {
			console.error(
				`An Error occured while inserting ${username}: ${err}`,
			);
			return res.status(500).json({ error: "Failed to insert user" }); //returns server error status code
		}
		console.log(`Username: ${username} inputted correctly`);
		res.status(201).json({ message: "User created successfully" }); //returns created status code
	});
});

app.get("/api/users", (_, res) => {
	try {
		console.log("Get users request recieved");

		db.all(`SELECT * FROM users;`, (err, data) => {
			// getting all users from the db
			if (err) {
				console.error(`An error occured while fetching users: ${err}`);
				return res.status(500).json({ error: "Failed to fetch users" }); //returns server error with a message
			}
			res.status(200).json({ users: data });
		});
	} catch (err) {
		console.log(`Something went wrong in fetching users ${err}`);
		res.status(500).json({ error: "Server error" });
	}
});

app.express;

app.post("/api/closeConnection", (req, res) => {});

// pvnp session state which needs to be seperate from pvp/pvai
let npQueue = null; //first player waiting
let npGame = null; // npGame will be =  {board, turn, p1: {ws, username}, p2: {ws, username} when a game is happening.

function safeSend(ws, object) {
	//Only send stuff through TCP if the socket is open.
	if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(object));
}

function handleDisconnect(ws) {
	if (npQueue === ws) {
		npQueue = null; // if player disconnects while waiting for an opponent (which is in the queue), the clear is queued so that another person can join
		return;
	}
	if (npGame) {
		// If a npGame is occuring
		const other = npGame.p1.ws === ws ? npGame.p2.ws : npGame.p1.ws; // other points to whoever did NOT disconnect.
		safeSend(other, { type: "opponentLeft" }); // sending to other player that the opponent disconnected
		resetBoardState();
		npGame = null; // close game
	}
}

// getting function from gameback
const { handlePvNPmove, resetBoardState } = require("./gameBack");

// Handle new WebSocket connections
wss.on("connection", (ws) => {
	ws.on("message", (data) => {
		let msg;
		msg = JSON.parse(data);
		// client announces itself and wants to be matched
		if (msg.type === "join") {
			ws.npUsername = msg.username; // setting the websockets username from the msg recieved
			if (!npQueue || npQueue.readyState !== WebSocket.OPEN) {
				// First player joined (or stale queued connection), wait for someone else
				npQueue = ws;
				safeSend(ws, { type: "waiting" });
				console.log(`${msg.username} waiting for opponent...`);
			} else {
				// Second player joined, pair them up and game starts
				const p1ws = npQueue;
				npQueue = null;
				npGame = {
					turn: "p1",
					p1: { ws: p1ws, username: p1ws.npUsername },
					p2: { ws, username: ws.npUsername },
				};
				safeSend(p1ws, {
					type: "matched",
					role: "p1",
					opponentUsername: ws.npUsername,
				});
				safeSend(ws, {
					type: "matched",
					role: "p2",
					opponentUsername: p1ws.npUsername,
				});
				console.log(`Game: ${p1ws.npUsername} vs ${ws.npUsername}`);
			}
		}

		if (msg.type === "move") {
			if (!npGame) return;
			const role =
				npGame.p1.ws === ws ? "p1" : npGame.p2.ws === ws ? "p2" : null;
			if (!role) return;

			// All game logic stays in gameBack
			const result = handlePvNPmove(Number(msg.col), role);

			if (!result.valid) {
				safeSend(ws, { type: "invalid", reason: result.reason });
				return;
			}

			// Server just handles broadcasting to both players
			const update = {
				type: "update",
				col: Number(msg.col),
				row: result.row,
				player: role,
				nextTurn: result.nextTurn,
				check: result.check,
				winner: result.winner,
				winningCells: result.winningCells,
			};
			safeSend(npGame.p1.ws, update);
			safeSend(npGame.p2.ws, update);

			if (result.check) {
				resetBoardState();
				npGame = null;
			}
		}

		if (msg.type === "leave") handleDisconnect(ws);
	});

	ws.on("close", () => handleDisconnect(ws));
});

const server = app.listen(PORT, () => {
	//TODO Server listen to
	console.log(`Server has started on: http://localhost:${PORT}`);
});

// Establishes the handshake for TCP (This is aided with lab code)
server.on("upgrade", (req, socket, head) => {
	wss.handleUpgrade(req, socket, head, (ws) => {
		wss.emit("connection", ws, req);
	});
});
