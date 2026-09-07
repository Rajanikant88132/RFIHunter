/**
 * RFI Hunter — /api/tenders router
 *
 * GET  /api/tenders          — paginated, filtered list
 * GET  /api/tenders/:id      — single tender detail
 * GET  /api/stats            — summary counts for dashboard
 * GET  /api/filters           — lookup values (industries, locations, etc.)
 * GET  /api/scrape-runs      — scrape run history
 */
const express = require('express');
const router  = express.Router();
const pool    = require('./db');

// ── helpers ──────────────────────────────────────────────────────────────────

function toInt(val, fallback) {
  const n = parseInt(val, 10);
  return isNaN(n) ? fallback : n;
}

function buildWhereClause(q) {
  const conditions = [];
  const params     = [];

  if (q.type && q.type !== 'ALL') {
    conditions.push('t.type = ?');
    params.push(q.type.toUpperCase());
  }
  if (q.status && q.status !== 'ALL') {
    conditions.push('t.status = ?');
    params.push(q.status.toUpperCase());
  }
  if (q.industry_area_id) {
    conditions.push('t.industry_area_id = ?');
    params.push(toInt(q.industry_area_id, 0));
  }
  if (q.location_id) {
    conditions.push('t.location_id = ?');
    params.push(toInt(q.location_id, 0));
  }
  if (q.company_size && q.company_size !== 'ALL') {
    conditions.push('t.company_size = ?');
    params.push(q.company_size.toUpperCase());
  }
  if (q.source) {
    conditions.push('t.source = ?');
    params.push(q.source);
  }
  if (q.deadline_from) {
    conditions.push('t.deadline_date >= ?');
    params.push(q.deadline_from);
  }
  if (q.deadline_to) {
    conditions.push('t.deadline_date <= ?');
    params.push(q.deadline_to);
  }
  if (q.search) {
    // Full-text search on title + description
    conditions.push('MATCH(t.title, t.description) AGAINST(? IN BOOLEAN MODE)');
    params.push(q.search + '*');
  }
  if (q.min_score) {
    conditions.push('t.opportunity_score >= ?');
    params.push(toInt(q.min_score, 0));
  }

  const where = conditions.length ? 'WHERE ' + conditions.join(' AND ') : '';
  return { where, params };
}

// ── GET /api/tenders ──────────────────────────────────────────────────────────
router.get('/tenders', async (req, res) => {
  try {
    const page     = Math.max(1, toInt(req.query.page, 1));
    const pageSize = Math.min(100, Math.max(1, toInt(req.query.pageSize, 20)));
    const offset   = (page - 1) * pageSize;

    const sort    = ['published_date','deadline_date','title','estimated_value','opportunity_score']
                      .includes(req.query.sort) ? req.query.sort : 'published_date';
    const order   = req.query.order === 'ASC' ? 'ASC' : 'DESC';

    const { where, params } = buildWhereClause(req.query);

    const countSql = `
      SELECT COUNT(*) AS total
      FROM tenders t
      ${where}
    `;
    const dataSql = `
      SELECT
        t.id, t.external_id, t.source, t.type, t.status,
        t.title, t.description,
        t.contracting_authority, t.company_size,
        ia.name  AS industry_area,
        loc.name AS location,
        t.published_date, t.deadline_date,
        t.estimated_value, t.currency,
        t.source_url, t.cpv_codes, t.keywords,
        t.buyer_email, t.buyer_phone, t.pdf_urls,
        t.opportunity_score,
        t.created_at, t.updated_at
      FROM tenders t
      LEFT JOIN industry_areas ia  ON ia.id  = t.industry_area_id
      LEFT JOIN locations      loc ON loc.id = t.location_id
      ${where}
      ORDER BY t.${sort} ${order}
      LIMIT ? OFFSET ?
    `;

    const [[{ total }]] = await pool.query(countSql, params);
    const [rows]        = await pool.query(dataSql, [...params, pageSize, offset]);

    // Parse JSON fields — mysql2 may return them already parsed (object) or as strings
    function parseJsonField(val, fallback = []) {
      if (!val) return fallback;
      if (typeof val === 'string') { try { return JSON.parse(val); } catch { return fallback; } }
      return val; // already parsed by mysql2
    }
    rows.forEach(r => {
      r.cpv_codes = parseJsonField(r.cpv_codes);
      r.keywords  = parseJsonField(r.keywords);
      r.pdf_urls  = parseJsonField(r.pdf_urls);
    });

    res.json({
      data:       rows,
      pagination: { page, pageSize, total, totalPages: Math.ceil(total / pageSize) },
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error', detail: err.message });
  }
});

// ── GET /api/tenders/:id ─────────────────────────────────────────────────────
router.get('/tenders/:id', async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT t.*, ia.name AS industry_area, loc.name AS location
       FROM tenders t
       LEFT JOIN industry_areas ia  ON ia.id  = t.industry_area_id
       LEFT JOIN locations      loc ON loc.id = t.location_id
       WHERE t.id = ?`,
      [req.params.id],
    );
    if (!rows.length) return res.status(404).json({ error: 'Not found' });
    const r = rows[0];
    const pjf = (val, fb) => { if (!val) return fb; if (typeof val === 'string') { try { return JSON.parse(val); } catch { return fb; } } return val; };
    r.cpv_codes = pjf(r.cpv_codes, []);
    r.keywords  = pjf(r.keywords,  []);
    r.pdf_urls  = pjf(r.pdf_urls,  []);
    r.raw_data  = pjf(r.raw_data,  {});
    res.json(r);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── GET /api/stats ────────────────────────────────────────────────────────────
router.get('/stats', async (req, res) => {
  try {
    const [[counts]] = await pool.query(`
      SELECT
        COUNT(*)                            AS total,
        SUM(type = 'RFI')                   AS rfi_count,
        SUM(type = 'RFP')                   AS rfp_count,
        SUM(status = 'OPEN')                AS open_count,
        SUM(status = 'CLOSED')              AS closed_count,
        SUM(deadline_date >= CURDATE())     AS active_count
      FROM tenders
    `);

    const [byIndustry] = await pool.query(`
      SELECT ia.name AS label, COUNT(*) AS value
      FROM tenders t
      LEFT JOIN industry_areas ia ON ia.id = t.industry_area_id
      GROUP BY ia.name
      ORDER BY value DESC
    `);

    const [byLocation] = await pool.query(`
      SELECT loc.name AS label, COUNT(*) AS value
      FROM tenders t
      LEFT JOIN locations loc ON loc.id = t.location_id
      GROUP BY loc.name
      ORDER BY value DESC
    `);

    const [bySource] = await pool.query(`
      SELECT source AS label, COUNT(*) AS value
      FROM tenders
      GROUP BY source
      ORDER BY value DESC
    `);

    const [byType] = await pool.query(`
      SELECT type AS label, COUNT(*) AS value
      FROM tenders
      GROUP BY type
    `);

    const [byMonth] = await pool.query(`
      SELECT DATE_FORMAT(published_date, '%Y-%m') AS month, COUNT(*) AS value
      FROM tenders
      WHERE published_date IS NOT NULL
      GROUP BY month
      ORDER BY month DESC
      LIMIT 12
    `);

    res.json({ counts, byIndustry, byLocation, bySource, byType, byMonth });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── GET /api/filters ──────────────────────────────────────────────────────────
router.get('/filters', async (req, res) => {
  try {
    const [industries] = await pool.query('SELECT id, name FROM industry_areas ORDER BY name');
    const [locations]  = await pool.query('SELECT id, name FROM locations  ORDER BY name');
    const [sources]    = await pool.query('SELECT DISTINCT source FROM tenders ORDER BY source');
    res.json({
      industries,
      locations,
      sources: sources.map(r => r.source),
      types:   ['ALL', 'RFI', 'RFP', 'OTHER'],
      statuses:['ALL', 'OPEN', 'CLOSED', 'UNKNOWN'],
      companySizes: ['ALL', 'SME', 'LARGE', 'ANY'],
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── GET /api/scrape-runs ──────────────────────────────────────────────────────
router.get('/scrape-runs', async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT * FROM scrape_runs ORDER BY started_at DESC LIMIT 50`,
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
