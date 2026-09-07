import React, { useEffect, useState } from 'react';
import { fetchScrapeRuns } from '../api';

export default function ScrapeRuns() {
  const [runs,  setRuns]  = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchScrapeRuns()
      .then(setRuns)
      .catch(e => setError(e.message));
  }, []);

  if (error) return <div className="error-box">Error: {error}</div>;
  if (!runs) return <div className="loading">Loading scrape history…</div>;

  return (
    <div>
      <h2 style={{ marginBottom: 16, fontSize: 18, fontWeight: 700, color: '#1f2328' }}>
        Scrape Run History
      </h2>

      {runs.length === 0 ? (
        <div className="empty">No scrape runs recorded yet. Start the scraper to see data here.</div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="runs-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Source</th>
                <th>Status</th>
                <th>Started</th>
                <th>Finished</th>
                <th>New</th>
                <th>Updated</th>
                <th>Errors</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {runs.map(r => (
                <tr key={r.id}>
                  <td>{r.id}</td>
                  <td>{r.source}</td>
                  <td>
                    <span className={`badge ${
                      r.status === 'SUCCESS' ? 'badge-open' :
                      r.status === 'FAILED'  ? 'badge-closed' : 'badge-other'
                    }`}>{r.status}</span>
                  </td>
                  <td style={{ fontSize: 12 }}>{r.started_at  ? new Date(r.started_at).toLocaleString()  : '—'}</td>
                  <td style={{ fontSize: 12 }}>{r.finished_at ? new Date(r.finished_at).toLocaleString() : '—'}</td>
                  <td style={{ color: '#065f46', fontWeight: 600 }}>{r.records_new}</td>
                  <td style={{ color: '#1d4ed8', fontWeight: 600 }}>{r.records_upd}</td>
                  <td style={{ color: r.records_err > 0 ? '#dc2626' : 'inherit', fontWeight: 600 }}>{r.records_err}</td>
                  <td style={{ fontSize: 11, color: '#6b7280', maxWidth: 200, wordBreak: 'break-word' }}>
                    {r.error_msg || ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
