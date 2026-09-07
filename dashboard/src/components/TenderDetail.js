import React, { useEffect, useState } from 'react';
import { fetchTender } from '../api';

function MetaItem({ label, value, href }) {
  return (
    <div className="meta-item">
      <div className="meta-label">{label}</div>
      <div className="meta-val">
        {href
          ? <a href={href} target="_blank" rel="noopener noreferrer">{value || href}</a>
          : (value || '—')
        }
      </div>
    </div>
  );
}

function ScoreBadge({ score }) {
  const color = score >= 70 ? '#065f46' : score >= 50 ? '#92400e' : '#374151';
  const bg    = score >= 70 ? '#d1fae5' : score >= 50 ? '#fef3c7' : '#f3f4f6';
  return (
    <span style={{
      display: 'inline-block', padding: '2px 10px', borderRadius: 12,
      fontSize: 13, fontWeight: 700, color, background: bg,
    }}>
      {score}/100
    </span>
  );
}

export default function TenderDetail({ id, onBack }) {
  const [tender, setTender] = useState(null);
  const [error,  setError]  = useState(null);

  useEffect(() => {
    setTender(null);
    fetchTender(id)
      .then(setTender)
      .catch(e => setError(e.message));
  }, [id]);

  if (error)   return <div className="error-box">Error: {error} <button className="btn btn-ghost" onClick={onBack}>← Back</button></div>;
  if (!tender) return <div className="loading">Loading tender…</div>;

  const typeClass   = tender.type === 'RFI' ? 'badge-rfi' : tender.type === 'RFP' ? 'badge-rfp' : 'badge-other';
  const statusClass = tender.status === 'OPEN' ? 'badge-open' : tender.status === 'CLOSED' ? 'badge-closed' : 'badge-other';

  const pdfs = Array.isArray(tender.pdf_urls) ? tender.pdf_urls : [];

  return (
    <div>
      <button className="btn btn-ghost" onClick={onBack} style={{ marginBottom: 16 }}>
        ← Back to list
      </button>

      <div className="card">
        {/* ── Header ── */}
        <div className="detail-header">
          <h2>{tender.title}</h2>
          <span className={`badge ${typeClass}`}>{tender.type}</span>
          <span className={`badge ${statusClass}`}>{tender.status}</span>
        </div>

        {/* ── Opportunity Score ── */}
        <div style={{ marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="meta-label" style={{ margin: 0 }}>Opportunity Score</span>
          <ScoreBadge score={tender.opportunity_score ?? 0} />
        </div>

        {/* ── Meta grid ── */}
        <div className="detail-meta-grid">
          <MetaItem label="Source"                value={tender.source} />
          <MetaItem label="Contracting Authority" value={tender.contracting_authority} />
          <MetaItem label="Industry Area"         value={tender.industry_area} />
          <MetaItem label="Location"              value={tender.location} />
          <MetaItem label="Company Size"          value={tender.company_size} />
          <MetaItem label="Published"             value={tender.published_date} />
          <MetaItem label="Deadline"              value={tender.deadline_date} />
          <MetaItem label="Estimated Value"
            value={tender.estimated_value
              ? `${Number(tender.estimated_value).toLocaleString()} ${tender.currency}`
              : null}
          />
          <MetaItem label="External ID" value={tender.external_id} />
        </div>

        {/* ── Buyer Contact ── */}
        {(tender.buyer_email || tender.buyer_phone) && (
          <div style={{ marginBottom: 20 }}>
            <div className="meta-label" style={{ marginBottom: 8 }}>Buyer Contact</div>
            <div style={{
              background: '#f0fdf4', border: '1px solid #bbf7d0',
              borderRadius: 8, padding: '12px 16px',
              display: 'flex', flexWrap: 'wrap', gap: 20,
            }}>
              {tender.buyer_email && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 16 }}>✉️</span>
                  <a
                    href={`mailto:${tender.buyer_email}`}
                    style={{ color: '#065f46', fontWeight: 600, fontSize: 14 }}
                  >
                    {tender.buyer_email}
                  </a>
                </div>
              )}
              {tender.buyer_phone && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 16 }}>📞</span>
                  <a
                    href={`tel:${tender.buyer_phone}`}
                    style={{ color: '#1e40af', fontWeight: 600, fontSize: 14 }}
                  >
                    {tender.buyer_phone}
                  </a>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Documents & PDFs ── */}
        {pdfs.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <div className="meta-label" style={{ marginBottom: 8 }}>Documents & PDFs</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {pdfs.map((doc, i) => (
                <a
                  key={i}
                  href={doc.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 8,
                    padding: '8px 14px', borderRadius: 6,
                    background: '#eff6ff', border: '1px solid #bfdbfe',
                    color: '#1d4ed8', textDecoration: 'none', fontSize: 13,
                    fontWeight: 500, width: 'fit-content',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = '#dbeafe'}
                  onMouseLeave={e => e.currentTarget.style.background = '#eff6ff'}
                >
                  <span style={{ fontSize: 16 }}>
                    {doc.name && doc.name.toLowerCase().includes('pdf') ? '📄' : '🔗'}
                  </span>
                  {doc.name || doc.url}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* ── Description ── */}
        {tender.description && (
          <div style={{ marginBottom: 20 }}>
            <div className="meta-label" style={{ marginBottom: 6 }}>Description</div>
            <div className="detail-desc">{tender.description}</div>
          </div>
        )}

        {/* ── CPV Codes ── */}
        {tender.cpv_codes && tender.cpv_codes.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div className="meta-label" style={{ marginBottom: 6 }}>CPV Codes</div>
            <div className="tag-list">
              {tender.cpv_codes.map(c => <span key={c} className="tag">{c}</span>)}
            </div>
          </div>
        )}

        {/* ── Keywords ── */}
        {tender.keywords && tender.keywords.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div className="meta-label" style={{ marginBottom: 6 }}>Keywords</div>
            <div className="tag-list">
              {tender.keywords.map(k => <span key={k} className="tag">{k}</span>)}
            </div>
          </div>
        )}

        {/* ── Source link ── */}
        {tender.source_url && (
          <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid #e5e7eb' }}>
            <a href={tender.source_url} target="_blank" rel="noopener noreferrer">
              View original notice ↗
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
