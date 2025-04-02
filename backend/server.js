require('dotenv').config();
const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json()); // Allows sending JSON data

// MySQL Connection
const db = mysql.createConnection({
    host: 'localhost',      // Your MySQL host (change if needed)
    user: 'root',           // Your MySQL username
    password: '',           // Your MySQL password
    database: 'amazonproject' // Your database name
});

// Check DB Connection
db.connect(err => {
    if (err) {
        console.error('Database connection failed:', err.stack);
        return;
    }
    console.log('Connected to MySQL Database');
});

// Sample API Route to Fetch Data
app.get('/products', (req, res) => {
    db.query('SELECT * FROM Product', (err, results) => {
        if (err) {
            return res.status(500).json({ error: err.message });
        }
        res.json(results);
    });
});

// Start the server
app.listen(5000, () => {
    console.log('Server running on port 5000');
});
