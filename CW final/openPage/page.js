// This is DOM methods are used to change the visibility of the AI difficulty options.
// This first one blocks the style display, making the options visible.

// This makes it so space or enter can be used to "click" on buttons
document.addEventListener("keydown", (e) => {
	if (e.key === "Enter" && e.target.type === "radio") {
		e.target.click();
	}
});
async function loadhighScores() {
	const { data } = await axios.get("http://localhost:4004/api/users");
	const users = data.users;

	// sort by best score across all modes
	users.sort((a, b) => {
		const bestA = Math.min(
			a.highScorePvP || Infinity,
			a.highScoreAI || Infinity,
			a.highScoreNP || Infinity,
		);
		const bestB = Math.min(
			b.highScorePvP || Infinity,
			b.highScoreAI || Infinity,
			b.highScoreNP || Infinity,
		);
		// or infinity is used so that if 0 (falsy) then it will be infinity, meaning that its always the largest possible number and it will never win as minimum so only the REAL minimum score wins, not 0.
		return bestA - bestB; // for ascending order
	});

	const table = document.getElementById("highScoreTable");
	table.innerHTML = ""; //resetting the html

	let rank = -1;
	users.forEach((user) => {
		// for each user, create a card, displaying their highscore in a ranked fashion
		if (
			// skipping users with all 0s
			user.highScorePvP === 0 &&
			user.highScoreAI === 0 &&
			user.highScoreNP === 0
		) {
			return;
		}

		rank++;

		const card = document.createElement("div");
		// creating aria label and role per card
		card.setAttribute(
			"aria-label",
			`Rank ${rank + 1}: ${user.username}, PvP: ${user.highScorePvP}, AI: ${user.highScoreAI}, NP: ${user.highScoreNP}`,
		);
		card.setAttribute("role", "article");
		card.innerHTML = `
			<div class="scoreCard">
				<div class="score-rank">#${rank + 1}</div>
				<div class="score-username">${user.username}</div>
				<div class="score-stats">
					<span>PvP: ${user.highScorePvP ?? 0}</span>
					<span>AI: ${user.highScoreAI ?? 0}</span>
					<span>NP: ${user.highScoreNP ?? 0}</span>
				</div>
			</div>
		`;
		table.appendChild(card);
	});

	document.getElementById("pVai").addEventListener("change", () => {
		const difficultyGroup = document.getElementById("difficultyGroup");
		// making it so the aria labels also are hidden along w the components
		difficultyGroup.style.display = "block";
		difficultyGroup.setAttribute("aria-hidden", "false");

		//This below makes it so the username input and heading turn invisible if any of the other options (except for pvp) are selected. (same logic as pVai)
		const p2Heading = document.getElementById("p2Heading");
		p2Heading.style.display = "none";
		p2Heading.setAttribute("aria-hidden", "true");

		const p2Username = document.getElementById("p2Username");
		p2Username.style.display = "none";
		p2Username.setAttribute("aria-hidden", "true");
	});
}

loadhighScores();

document.getElementById("pVp").addEventListener("change", () => {
	const difficultyGroup = document.getElementById("difficultyGroup");
	difficultyGroup.style.display = "none";
	difficultyGroup.setAttribute("aria-hidden", "true");

	//This below, makes the second username input and heading appear.
	const p2Heading = document.getElementById("p2Heading");
	p2Heading.style.display = "block";
	p2Heading.setAttribute("aria-hidden", "false");

	const p2Username = document.getElementById("p2Username");
	p2Username.style.display = "block";
	p2Username.setAttribute("aria-hidden", "false");
});

// These two DOM methods, above and below, then make it so the options are invisible again when any of them two are selected.

document.getElementById("pVnp").addEventListener("change", () => {
	const difficultyGroup = document.getElementById("difficultyGroup");
	difficultyGroup.style.display = "none";
	difficultyGroup.setAttribute("aria-hidden", "true");

	const p2Heading = document.getElementById("p2Heading");
	p2Heading.style.display = "none";
	p2Heading.setAttribute("aria-hidden", "true");

	const p2Username = document.getElementById("p2Username");
	p2Username.style.display = "none";
	p2Username.setAttribute("aria-hidden", "true");
});

//END of AI options methods

document.getElementById("startGame").addEventListener("click", async () => {
	let username1 = document.getElementById("Username");
	let username2 = document.getElementById("p2Username");

	let pVai = document.getElementById("pVai");
	let pVp = document.getElementById("pVp");
	let pVnp = document.getElementById("pVnp");
	let mode;
	let difficulty = // Storing the difficuly if ai is chosen, else its null.
		document.querySelector('input[name="difficulty"]:checked')?.value ??
		null;
	// ? at the end of queryselector allows for optional chaining which returns undefined if nothing is checked.

	// This makes it so if the input on username1 is empty, it requires the user to input it.
	if (!username1.value) {
		username1.placeholder = "Please input a Username!";
		username1.style.border = "1px solid #f05d5d";

		return;
	}

	//If an error occurs and no mode is chosen, nothing happens
	if (!pVai.checked && !pVp.checked && !pVnp.checked) {
		return;
	}

	// pVp is a local game so it does not matter.
	// Getting all users in db to check if username is unique or not.
	let { data } = await axios.get("http://localhost:4004/api/users");

	for (let users of data.users) {
		// Making sure if usernames are unique
		if (
			users.username == username1.value ||
			users.username == username2.value
		) {
			username1.value = "";
			username2.value = "";
			username1.placeholder = "Please input a Unique Username!";
			username1.style.border = "1px solid #f05d5d";
			username2.placeholder = "Please input a Unique Username!";
			username2.style.border = "1px solid #f05d5d";
			return;
		}
	}

	if (pVp.checked) {
		// This makes it so if the input on username2 is empty, it requires the user to input it, only if pvp is checked though.
		if (!username2.value) {
			username2.placeholder = "Please input a Username!";
			username2.style.border = "1px solid #f05d5d";
			return;
		}

		//Does not allow for usernames to be equal, and requests a new one.
		if (username1.value === username2.value) {
			username2.placeholder = "Usernames must be different!";
			username2.value = null;
			username2.style.border = "1px solid #f05d5d";
			return;
		}

		// Storing pVp usernames in the DB (individually because the post only takes one username)
		await axios.post("http://localhost:4004/api/users", {
			username: username1.value,
		});
		await axios.post("http://localhost:4004/api/users", {
			username: username2.value,
		});

		mode = "pVp";
	}

	if (pVai.checked) {
		//this is to set the difficulty variable to any radio input which is checked.
		let difficulty = document.querySelector(
			'input[name="difficulty"]:checked',
		);

		// If no difficulty is chosen, make the borders red to alert the user.
		if (!difficulty) {
			document.querySelectorAll("#difficulty-option").forEach((el) => {
				el.style.border = "1px solid #f05d5d";
			});
			return;
		}

		// Creating a request to the backend, to store create a new user row and store thier username.
		await axios.post("http://localhost:4004/api/users", {
			username: username1.value,
		});

		mode = "pVai";
	}

	if (pVnp.checked) {
		// Creating a request to the backend, to store create a new user row and store thier username. (await because this has to be completed before the user moves on)
		await axios.post("http://localhost:4004/api/users", {
			username: username1.value,
		});

		mode = "pVnp";
	}

	// pVp needs both usernames, other gamemodes only need one. because ai = one username, pVnp = diff browsers display diff usernames.
	if (mode === "pVp") {
		window.location.href = `../game/game.html?mode=${mode}&difficulty=${difficulty}&p1Username=${username1.value}&p2Username=${username2.value}`;
		return;
	}

	// ? introduces first paramter, & seperates the next parameters

	window.location.href = `../game/game.html?mode=${mode}&difficulty=${difficulty}&username=${username1.value}`;
});
