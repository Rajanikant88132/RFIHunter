import React, { useEffect, useState, useCallback } from 'react';
import { fetchTenders, fetchFilters } from '../api';

const EMPTY_FILTERS = {
  search:          '',
  type:            'ALL',
  status:          'ALL',
  industry_area_id:'',
  location_id:     '',
  company_size:    'ALL',
  source:          '',
  deadline_from:   '',
  deadline_to:     '',
  min_score:       '',
};

function Badge({ type, status }) {
  if (type) {
    const cls = type === 'RFI' ? 'badge-rfi' : type === 'RFP' ? 'badge-rfp' : 'badge-other';
    return <span className={`badge ${cls}`}>{type}</span>;
  }
  const cls = status === 'OPEN' ? 'badge-open' : status === 'CLOSED' ? 'badge-closed' : 'badge-other';
  return <span className={`badge ${cls}`}>{status}</span>;
}

export default function TenderList({ onSelect }) {
  const [data,    setData]    = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [pending, setPending] = useState(EMPTY_FILTERS);
  const [page,    setPage]    = useState(1);
  const [meta,    setMeta]    = useState(null);
  const [sort,    setSort]    = useState('published_date');
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const [lookups, setLookups] = useState({ industries: [], locations: [], sources: [], types: [], statuses: [], companySizes: [] });

  // Load filter lookups once
  useEffect(() => {
    fetchFilters().then(setLookups).catch(console.error);
  }, []);

  const load = useCallback((f, pg) => {
    setLoading(true);
    setError(null);
    const params = { ...f, page: pg, pageSize: 20, sort };
    // strip empty
    Object.keys(params).forEach(k => { if (!params[k] || params[k] === 'ALL') delete params[k]; });
    fetchTenders(params)
      .then(r => { setData(r.data); setMeta(r.pagination); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [sort]);

  useEffect(() => { load(filters, page); }, [filters, page, sort, load]);

  const applyFilters = () => { setFilters({ ...pending }); setPage(1); };
  const clearFilters = () => { setPending(EMPTY_FILTERS); setFilters(EMPTY_FILTERS); setPage(1); };

  const handleKey = e => { if (e.key === 'Enter') applyFilters(); };

  return (
    <div>
      {/* ── Filter Panel ── */}
      <div className="filters-panel">
        <div className="filter-group search-group">
          <label>Search (title / description)</label>
          <input
            type="text"
            placeholder="e.g. cloud infrastructure, terveys…"
            value={pending.search}
            onChange={e => setPending(p => ({ ...p, search: e.target.value }))}
            onKeyDown={handleKey}
          />
        </div>

        <div className="filter-group">
          <label>Type</label>
          <select value={pending.type} onChange={e => setPending(p => ({ ...p, type: e.target.value }))}>
            {lookups.types.map(t => <option key={t}>{t}</option>)}
          </select>
        </div>

        <div className="filter-group">
          <label>Status</label>
          <select value={pending.status} onChange={e => setPending(p => ({ ...p, status: e.target.value }))}>
            {lookups.statuses.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>

        <div className="filter-group">
          <label>Industry Area</label>
          <select value={pending.industry_area_id} onChange={e => setPending(p => ({ ...p, industry_area_id: e.target.value }))}>
            <option value="">All Industries</option>
            {lookups.industries.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
        </div>

        <div className="filter-group">
          <label>Location</label>
          <select value={pending.location_id} onChange={e => setPending(p => ({ ...p, location_id: e.target.value }))}>
            <option value="">All Locations</option>
            {lookups.locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
        </div>

        <div className="filter-group">
          <label>Company Size</label>
          <select value={pending.company_size} onChange={e => setPending(p => ({ ...p, company_size: e.target.value }))}>
            {lookups.companySizes.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>

        <div className="filter-group">
          <label>Source</label>
          <select value={pending.source} onChange={e => setPending(p => ({ ...p, source: e.target.value }))}>
            <option value="">All Sources</option>
            {lookups.sources.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="filter-group">
          <label>Deadline From</label>
          <input type="date" value={pending.deadline_from} onChange={e => setPending(p => ({ ...p, deadline_from: e.target.value }))} />
        </div>

        <div className="filter-group">
          <label>Deadline To</label>
          <input type="date" value={pending.deadline_to} onChange={e => setPending(p => ({ ...p, deadline_to: e.target.value }))} />
        </div>

        <div className="filter-group">
          <label>Sort By</label>
          <select value={sort} onChange={e => { setSort(e.target.value); setPage(1); }}>
            <option value="published_date">Published Date</option>
            <option value="deadline_date">Deadline</option>
            <option value="title">Title</option>
            <option value="estimated_value">Value</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: 8, alignSelf: 'flex-end' }}>
          <button className="btn btn-primary" onClick={applyFilters}>Search</button>
          <button className="btn btn-ghost"   onClick={clearFilters}>Clear</button>
        </div>
      </div>

      {/* ── Error ── */}
      {error && <div className="error-box">Error: {error}</div>}

      {/* ── Results count ── */}
      {meta && (
        <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 10 }}>
          {Number(meta.total).toLocaleString()} result{meta.total !== 1 ? 's' : ''}
          {' '}— page {meta.page} of {meta.totalPages}
        </div>
      )}

      {/* ── Table ── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div className="loading">Loading…</div>
        ) : !data || data.length === 0 ? (
          <div className="empty">No tenders found. Try adjusting filters.</div>
        ) : (
          <div className="tender-table-wrap">
            <table className="tender-table">
              <thead>
                <tr>
                  <th style={{ width: 42, textAlign: 'center' }}>Score</th>
                  <th>Title / Authority</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Industry</th>
                  <th>Location</th>
                  <th>Source</th>
                  <th>Deadline</th>
                  <th style={{ textAlign: 'center' }}>Docs</th>
                  <th style={{ textAlign: 'center' }}>Contact</th>
                </tr>
              </thead>
              <tbody>
                {data.map(t => {
                  const pdfCount = Array.isArray(t.pdf_urls) ? t.pdf_urls.length : 0;
                  const hasEmail = !!t.buyer_email;
                  const hasPhone = !!t.buyer_phone;
                  return (
                  <tr key={t.id}>
                    <td style={{ textAlign: 'center', fontWeight: 700, fontSize: 13,
                      color: t.opportunity_score >= 70 ? '#065f46' : t.opportunity_score >= 50 ? '#92400e' : '#374151' }}>
                      {t.opportunity_score || 0}
                    </td>
                    <td className="title-cell">
                      <div
                        className="title-link"
                        role="button"
                        tabIndex={0}
                        onClick={() => onSelect(t.id)}
                        onKeyDown={e => e.key === 'Enter' && onSelect(t.id)}
                      >
                        {t.title.length > 90 ? t.title.slice(0, 90) + '…' : t.title}
                      </div>
                      {t.contracting_authority && (
                        <div className="authority">{t.contracting_authority}</div>
                      )}
                    </td>
                    <td><Badge type={t.type} /></td>
                    <td><Badge status={t.status} /></td>
                    <td style={{ fontSize: 12 }}>{t.industry_area || '—'}</td>
                    <td style={{ fontSize: 12 }}>{t.location      || '—'}</td>
                    <td style={{ fontSize: 12, color: '#6b7280' }}>{t.source}</td>
                    <td style={{ fontSize: 12, whiteSpace: 'nowrap', color: t.deadline_date && new Date(t.deadline_date) < new Date() ? '#dc2626' : 'inherit' }}>
                      {t.deadline_date || '—'}
                    </td>
                    <td style={{ textAlign: 'center', fontSize: 13 }}>
                      {pdfCount > 0
                        ? <span title={`${pdfCount} document(s)`} style={{ cursor: 'pointer', color: '#1d4ed8' }}
                            onClick={() => onSelect(t.id)}>📄 {pdfCount}</span>
                        : <span style={{ color: '#d1d5db' }}>—</span>
                      }
                    </td>
                    <td style={{ textAlign: 'center', fontSize: 13 }}>
                      {(hasEmail || hasPhone) ? (
                        <span
                          title={[hasEmail && t.buyer_email, hasPhone && t.buyer_phone].filter(Boolean).join(' | ')}
                          style={{ cursor: 'default' }}
                        >
                          {hasEmail && '✉️'}{hasPhone && '📞'}
                        </span>
                      ) : <span style={{ color: '#d1d5db' }}>—</span>}
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Pagination ── */}
      {meta && meta.totalPages > 1 && (
        <div className="pagination">
          <button onClick={() => setPage(1)}         disabled={page <= 1}>«</button>
          <button onClick={() => setPage(p => p - 1)} disabled={page <= 1}>‹</button>

          {Array.from({ length: Math.min(7, meta.totalPages) }, (_, i) => {
            const half  = 3;
            let start = Math.max(1, page - half);
            let end   = Math.min(meta.totalPages, start + 6);
            start = Math.max(1, end - 6);
            return start + i;
          }).map(p => (
            <button
              key={p}
              className={p === page ? 'current' : ''}
              onClick={() => setPage(p)}
            >{p}</button>
          ))}

          <button onClick={() => setPage(p => p + 1)}           disabled={page >= meta.totalPages}>›</button>
          <button onClick={() => setPage(meta.totalPages)}      disabled={page >= meta.totalPages}>»</button>
          <span className="page-info">{meta.total} total</span>
        </div>
      )}
    </div>
  );
}
