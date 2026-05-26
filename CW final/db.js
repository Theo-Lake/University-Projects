const Database = require("sqlite3").verbose().Database; // Verbose allows for stack traces in error messages, so the error isnt vague
// .database is the constructor module
const db = new Database("database.db"); //creates database.db

db.exec(`
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        highScorePvP INTEGER DEFAULT 0,
        highScoreAI INTEGER DEFAULT 0,
        highScoreNP INTEGER DEFAULT 0
    )
    `);

module.exports = db; //exports the db connection
