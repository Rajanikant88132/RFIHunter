/**
 * RFI Hunter — Express server bootstrap
 */
require('dotenv').config();
const express     = require('express');
const cors        = require('cors');
const helmet      = require('helmet');
const morgan      = require('morgan');
const rateLimit   = require('express-rate-limit');
const routes      = require('./routes');

const app  = express();
const PORT = process.env.API_PORT || 4000;

// ── middleware ────────────────────────────────────────────────────────────────
app.use(helmet({ contentSecurityPolicy: false }));
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

app.use(
  '/api',
  rateLimit({ windowMs: 60_000, max: 200, standardHeaders: true, legacyHeaders: false }),
);

// ── routes ────────────────────────────────────────────────────────────────────
app.use('/api', routes);

// Health check
app.get('/health', (_req, res) => res.json({ status: 'ok', ts: new Date().toISOString() }));

// 404 fallback
app.use((_req, res) => res.status(404).json({ error: 'Not found' }));

// ── start ─────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`RFI Hunter API listening on http://0.0.0.0:${PORT}`);
});

module.exports = app;
