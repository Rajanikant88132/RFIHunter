/**
 * RFI Hunter — MySQL connection pool (mysql2/promise)
 */
require('dotenv').config();
const mysql = require('mysql2/promise');

const pool = mysql.createPool({
  host:               process.env.DB_HOST     || 'localhost',
  port:               Number(process.env.DB_PORT || 3306),
  database:           process.env.DB_NAME     || 'rfihunter',
  user:               process.env.DB_USER     || 'rfihunter',
  password:           process.env.DB_PASS     || 'rfihunter_pass',
  charset:            'utf8mb4',
  connectionLimit:    10,
  waitForConnections: true,
  queueLimit:         0,
});

module.exports = pool;
