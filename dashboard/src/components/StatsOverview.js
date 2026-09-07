import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  XAxis, YAxis, CartesianGrid, Legend,
} from 'recharts';
import { fetchStats } from '../api';

const COLORS = ['#1e3a5f', '#3b82f6', '#06b6d4', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444', '#6b7280'];

export default function StatsOverview() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch(e => setError(e.message));
  }, []);

  if (error)  return <div className="error-box">Failed to load stats: {error}</div>;
  if (!stats) return <div className="loading">Loading dashboard…</div>;

  const { counts, byIndustry, byLocation, bySource, byType, byMonth } = stats;

  const tiles = [
    { label: 'Total Tenders',   value: counts.total        || 0 },
    { label: 'RFI',             value: counts.rfi_count    || 0 },
    { label: 'RFP',             value: counts.rfp_count    || 0 },
    { label: 'Open',            value: counts.open_count   || 0 },
    { label: 'Closed',          value: counts.closed_count || 0 },
    { label: 'Active (future)', value: counts.active_count || 0 },
  ];

  const monthData = [...(byMonth || [])].reverse();

  return (
    <div>
      <h2 style={{ marginBottom: 16, fontSize: 18, fontWeight: 700, color: '#1f2328' }}>
        Dashboard Overview
      </h2>

      {/* Stat tiles */}
      <div className="stats-grid">
        {tiles.map(t => (
          <div key={t.label} className="stat-tile">
            <div className="value">{Number(t.value).toLocaleString()}</div>
            <div className="label">{t.label}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="charts-row">
        {/* By Industry */}
        <div className="chart-card">
          <h3>By Industry Area</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={byIndustry} layout="vertical" margin={{ left: 20, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="label" tick={{ fontSize: 11 }} width={150} />
              <Tooltip />
              <Bar dataKey="value" fill="#1e3a5f" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* By Type */}
        <div className="chart-card">
          <h3>By Tender Type</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={byType}
                dataKey="value"
                nameKey="label"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={({ label, percent }) => `${label} ${(percent * 100).toFixed(0)}%`}
              >
                {(byType || []).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* By Location */}
        <div className="chart-card">
          <h3>By Location</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={(byLocation || []).slice(0, 10)} layout="vertical" margin={{ left: 20, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="label" tick={{ fontSize: 11 }} width={120} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* By Source */}
        <div className="chart-card">
          <h3>By Source</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={bySource}
                dataKey="value"
                nameKey="label"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={({ label, percent }) => `${label} ${(percent * 100).toFixed(0)}%`}
              >
                {(bySource || []).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Monthly trend */}
        {monthData.length > 0 && (
          <div className="chart-card" style={{ gridColumn: '1 / -1' }}>
            <h3>Monthly Publication Trend (last 12 months)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={monthData} margin={{ left: 0, right: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
