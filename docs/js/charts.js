/* ============================================================
   SCRIBAL FINGERPRINTS — Charts (Plotly.js configurations)
   Uses window.DATA_* globals loaded via script tags
   ============================================================ */

const COLORS = {
  accent:    '#2A7F8E',
  blue:      '#2C5F7C',
  gold:      '#C4963C',
  bg:        '#FAFAF8',
  text:      '#2D2D2D',
  muted:     '#6B6B6B',
  border:    '#E0DED8',
  bgCard:    '#FFFFFF',
};

const PLOTLY_LAYOUT = {
  paper_bgcolor: COLORS.bgCard,
  plot_bgcolor: COLORS.bgCard,
  font: { family: 'Inter, sans-serif', color: COLORS.text, size: 13 },
  margin: { t: 40, r: 30, b: 60, l: 60 },
  hoverlabel: { bgcolor: '#fff', bordercolor: COLORS.border, font: { size: 12 } },
};

const PLOTLY_CONFIG = { responsive: true, displayModeBar: false };

/* --- Type Distribution (Stacked Bar) --- */
function renderTypeChart(containerId) {
  const data = window.DATA_TYPES;
  if (!data) { console.error('Type counts data not loaded'); return; }

  const types = [
    { key: 'substitution_morphological', label: 'Morphological', color: '#2C5F7C' },
    { key: 'substitution_lexical',       label: 'Lexical',       color: '#C4963C' },
    { key: 'addition',                   label: 'Addition',      color: '#CB4335' },
    { key: 'omission',                   label: 'Omission',      color: '#7D3C98' },
    { key: 'substitution_word_order',    label: 'Word Order',    color: '#2A7F8E' },
  ];

  const manuscripts = data.map(d => d.manuscript);
  const traces = types.map(t => ({
    x: manuscripts,
    y: data.map(d => d[t.key] || 0),
    name: t.label,
    type: 'bar',
    marker: { color: t.color },
    hovertemplate: `%{x}: %{y} ${t.label} variants<extra></extra>`,
  }));

  const layout = {
    ...PLOTLY_LAYOUT,
    barmode: 'stack',
    xaxis: { title: 'Manuscript', tickfont: { size: 12 } },
    yaxis: { title: 'Variant Count' },
    legend: { orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center' },
  };

  Plotly.newPlot(containerId, traces, layout, PLOTLY_CONFIG);
}

/* --- Cumulative ARI (Line Chart) --- */
function renderCumulativeChart(containerId) {
  const data = window.DATA_CUMULATIVE;
  if (!data) { console.error('Cumulative data not loaded'); return; }

  const lineStyles = {
    'Baseline B': { color: '#2C5F7C', dash: 'solid', width: 2.5 },
    'Baseline A': { color: '#C4963C', dash: 'dash',  width: 2 },
    'Verse-matched': { color: '#2A7F8E', dash: 'dot', width: 2 },
  };

  const traces = Object.entries(data).map(([label, points]) => ({
    x: points.map(p => p.chapters),
    y: points.map(p => p.ari),
    name: label,
    type: 'scatter',
    mode: 'lines+markers',
    line: lineStyles[label] || { color: '#999', width: 1.5 },
    marker: { size: 5 },
    hovertemplate: `${label}<br>Chapters: %{x}<br>ARI: %{y:.4f}<extra></extra>`,
  }));

  const layout = {
    ...PLOTLY_LAYOUT,
    xaxis: { title: 'Chapters (cumulative)', dtick: 1 },
    yaxis: { title: 'ARI Value' },
    legend: { orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center' },
    shapes: [{
      type: 'line', x0: 13, x1: 13, y0: 0, y1: 1,
      yref: 'paper', line: { color: COLORS.muted, width: 1, dash: 'dot' },
    }],
    annotations: [{
      x: 13, y: 1.05, yref: 'paper',
      text: '~13-chapter threshold',
      showarrow: false,
      font: { size: 11, color: COLORS.muted },
    }],
  };

  Plotly.newPlot(containerId, traces, layout, PLOTLY_CONFIG);
}

/* --- Chapter Stability Heatmap --- */
function renderStabilityHeatmap(containerId) {
  const data = window.DATA_STABILITY;
  if (!data) { console.error('Stability data not loaded'); return; }

  const manuscripts = Object.keys(data);
  const allChapters = [...new Set(manuscripts.flatMap(ms => data[ms].map(d => d.chapter)))].sort((a,b) => a-b);

  const z = manuscripts.map(ms => {
    const msData = data[ms];
    return allChapters.map(ch => {
      const entry = msData.find(d => d.chapter === ch);
      return entry ? entry.distance : null;
    });
  });

  const trace = {
    z: z,
    x: allChapters.map(String),
    y: manuscripts,
    type: 'heatmap',
    colorscale: [
      [0,   '#FFF8E1'],
      [0.3, '#FFE082'],
      [0.5, '#FFA726'],
      [0.7, '#E65100'],
      [1,   '#B71C1C'],
    ],
    hovertemplate: '%{y} ch.%{x}: %{z:.3f}<extra></extra>',
    colorbar: { title: 'Distance<br>to Global', titleside: 'right', thickness: 15, len: 0.8 },
  };

  const layout = {
    ...PLOTLY_LAYOUT,
    xaxis: { title: 'Chapter', type: 'category' },
    yaxis: { title: '' },
    margin: { ...PLOTLY_LAYOUT.margin, l: 80 },
  };

  Plotly.newPlot(containerId, [trace], layout, PLOTLY_CONFIG);
}

/* --- Ablation Comparison (Grouped Bar) --- */
function renderAblationChart(containerId) {
  const data = window.DATA_STATS;
  if (!data) { console.error('Stats data not loaded'); return; }

  const panel = data.ablation_panel;
  const labels = panel.map(p => p.label);
  const dVals = panel.map(p => p.cohens_d);
  const ariVals = panel.map(p => p.ari);

  const annotations = [];
  panel.forEach((p, i) => {
    if (p.d_pct_drop > 0) {
      annotations.push({
        x: p.label, y: p.cohens_d,
        text: '\u2212' + p.d_pct_drop.toFixed(0) + '%',
        showarrow: true, arrowhead: 0, ax: 0, ay: -25,
        font: { size: 10, color: '#CB4335' },
        xref: 'x', yref: 'y',
      });
    }
  });

  const trace1 = {
    x: labels, y: dVals,
    name: "Cohen's d",
    type: 'bar',
    marker: { color: '#2C5F7C' },
    hovertemplate: "%{x}<br>Cohen's d: %{y:.4f}<extra></extra>",
  };

  const trace2 = {
    x: labels, y: ariVals,
    name: 'ARI',
    type: 'bar',
    marker: { color: '#2A7F8E' },
    hovertemplate: '%{x}<br>ARI: %{y:.4f}<extra></extra>',
  };

  const layout = {
    ...PLOTLY_LAYOUT,
    barmode: 'group',
    xaxis: { title: '' },
    yaxis: { title: 'Metric Value' },
    legend: { orientation: 'h', y: -0.15, x: 0.5, xanchor: 'center' },
    annotations: annotations,
  };

  Plotly.newPlot(containerId, [trace1, trace2], layout, PLOTLY_CONFIG);
}

/* --- Statistical Summary Table --- */
function renderStatsTable(containerId) {
  const data = window.DATA_STATS;
  if (!data) { console.error('Stats data not loaded'); return; }

  const configs = data.configs;
  const fmt = (v, dec) => typeof v === 'number' ? v.toFixed(dec) : '\u2014';
  const ci = (v, lo, hi, dec) => {
    if (typeof lo !== 'number' || typeof hi !== 'number') return fmt(v, dec);
    return `${fmt(v, dec)} [${fmt(lo, dec)}\u2013${fmt(hi, dec)}]`;
  };

  let html = `<table>
    <thead><tr>
      <th>Configuration</th>
      <th>N</th>
      <th>Cohen's d [95% CI]</th>
      <th>ARI</th>
      <th>Cram\u00e9r's V (sub)</th>
      <th>Odd\u2013Even \u03c1</th>
    </tr></thead><tbody>`;

  const nMap = {
    'Baseline B': '12,460', 'Baseline A': '10,481',
    'Verse-matched': '8,381', 'Function words only': '1,008',
    'Content masked': '12,460',
  };

  for (const [label, vals] of Object.entries(configs)) {
    const d = vals["Cohen's d"];
    const dLo = vals["Cohen's d_CI_Low"];
    const dHi = vals["Cohen's d_CI_High"];
    html += `<tr>
      <td><strong>${label}</strong></td>
      <td>${nMap[label] || '\u2014'}</td>
      <td>${ci(d, dLo, dHi, 4)}</td>
      <td>${fmt(vals['ARI'], 4)}</td>
      <td>${fmt(vals["Cramer's V Sub"], 4)}</td>
      <td>${fmt(vals['Odd_Even_Split_Rho'], 4)}</td>
    </tr>`;
  }
  html += '</tbody></table>';
  document.getElementById(containerId).innerHTML = html;
}
