/* ============================================================
   TEXTUAL VARIATION IN JOHN — Variant Explorer (DataTables)
   Uses window.DATA_VARIANTS loaded via script tag
   ============================================================ */

const TYPE_LABELS = {
  substitution_morphological: 'Morphological substitution',
  substitution_lexical: 'Lexical substitution',
  substitution_word_order: 'Word-order shift',
  addition: 'Addition',
  omission: 'Omission',
};
const WITNESS_ORDER = ['P66', 'ℵ', 'A', 'B', 'D'];

document.addEventListener('DOMContentLoaded', () => {
  try {
    const data = window.DATA_VARIANTS;
    if (!data) {
      console.error('Variant data not loaded');
      document.getElementById('explorer-container').innerHTML =
        '<p style="color:#CB4335;">Variant data could not be loaded.</p>';
      return;
    }

    const fill = (select, values, label = v => v) => {
      values.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v;
        opt.textContent = label(v);
        select.appendChild(opt);
      });
    };
    const order = (list, ref) => list.sort((a, b) => ref.indexOf(a) - ref.indexOf(b));

    const baselineSelect = document.getElementById('filter-baseline');
    const msSelect = document.getElementById('filter-ms');
    const typeSelect = document.getElementById('filter-type');
    fill(baselineSelect, order([...new Set(data.map(d => d.baseline))], WITNESS_ORDER));
    fill(msSelect, order([...new Set(data.map(d => d.manuscript))], WITNESS_ORDER));
    fill(typeSelect, Object.keys(TYPE_LABELS).filter(t => data.some(d => d.type === t)), t => TYPE_LABELS[t]);

    document.getElementById('sample-count').textContent = data.length.toLocaleString('en-GB');

    const greek = { createdCell: td => td.classList.add('greek-text') };
    const table = $('#variants-table').DataTable({
      data: data,
      columns: [
        { data: 'chapter', title: 'Ch.', type: 'num' },
        { data: 'verse_no', title: 'Verse', type: 'num',
          render: (v, kind, row) => (kind === 'display' || kind === 'filter') ? row.verse : v },
        { data: 'baseline', title: 'Baseline' },
        { data: 'manuscript', title: 'Witness' },
        { data: 'base_reading', title: 'Baseline reading', ...greek,
          render: v => v || '—' },
        { data: 'ms_reading', title: 'Witness reading', ...greek,
          render: v => v || '—' },
        { data: 'type', title: 'Type', render: v => TYPE_LABELS[v] || v },
      ],
      pageLength: 25,
      order: [[0, 'asc'], [1, 'asc']],
      language: {
        search: 'Search:',
        lengthMenu: 'Show _MENU_ entries',
        info: 'Showing _START_ to _END_ of _TOTAL_ variants',
      },
    });

    const exact = (col, val) => table.column(col).search(val ? `^${val}$` : '', true, false).draw();
    baselineSelect.addEventListener('change', () => exact(2, baselineSelect.value));
    msSelect.addEventListener('change', () => exact(3, msSelect.value));
    typeSelect.addEventListener('change', () =>
      exact(6, typeSelect.value ? TYPE_LABELS[typeSelect.value] : ''));

  } catch (err) {
    console.error('Explorer init error:', err);
    document.getElementById('explorer-container').innerHTML =
      '<p style="color:#CB4335;">Failed to load variant data. Please check the data files.</p>';
  }
});
