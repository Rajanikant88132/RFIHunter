import React, { useState } from 'react';
import StatsOverview from './components/StatsOverview';
import TenderList    from './components/TenderList';
import TenderDetail  from './components/TenderDetail';
import ScrapeRuns    from './components/ScrapeRuns';
import './App.css';

export default function App() {
  const [tab, setTab]       = useState('dashboard');
  const [selected, setSelected] = useState(null);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-brand">
          <span className="header-flag">🇫🇮</span>
          <h1>RFI Hunter</h1>
          <span className="header-sub">Finland RFI &amp; RFP Aggregator</span>
        </div>
        <nav className="header-nav">
          {[
            { id: 'dashboard', label: 'Dashboard' },
            { id: 'tenders',   label: 'Browse Tenders' },
            { id: 'runs',      label: 'Scrape History' },
          ].map(t => (
            <button
              key={t.id}
              className={`nav-btn ${tab === t.id ? 'active' : ''}`}
              onClick={() => { setTab(t.id); setSelected(null); }}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="app-main">
        {tab === 'dashboard' && <StatsOverview />}
        {tab === 'tenders' && !selected && (
          <TenderList onSelect={id => setSelected(id)} />
        )}
        {tab === 'tenders' && selected && (
          <TenderDetail id={selected} onBack={() => setSelected(null)} />
        )}
        {tab === 'runs' && <ScrapeRuns />}
      </main>

      <footer className="app-footer">
        RFI Hunter • Data sourced from HILMA, TED, Hankintailmoitukset, Business Finland, Traficom
      </footer>
    </div>
  );
}
