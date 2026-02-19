/* ============================================================
   SCRIBAL FINGERPRINTS — Explorer (DataTables init)
   Uses window.DATA_VARIANTS loaded via script tag
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  try {
    const data = window.DATA_VARIANTS;
    if (!data) { 
      console.error('Variant data not loaded');
      document.getElementById('explorer-container').innerHTML =
        '<p style="color:#CB4335;">Variant data could not be loaded.</p>';
      return;
    }

    // Populate filter dropdowns
    const manuscripts = [...new Set(data.map(d => d.manuscript))].sort();
    const types = [...new Set(data.map(d => d.type))].sort();

    const msSelect = document.getElementById('filter-ms');
    const typeSelect = document.getElementById('filter-type');

    manuscripts.forEach(ms => {
      const opt = document.createElement('option');
      opt.value = ms;
      opt.textContent = ms;
      msSelect.appendChild(opt);
    });

    types.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t;
      opt.textContent = t.replace(/_/g, ' ');
      typeSelect.appendChild(opt);
    });

    // Update sample count
    document.getElementById('sample-count').textContent = data.length.toLocaleString();

    // Init DataTable
    const table = $('#variants-table').DataTable({
      data: data,
      columns: [
        { data: 'chapter', title: 'Ch.' },
        { data: 'verse', title: 'Verse' },
        { data: 'manuscript', title: 'MS' },
        {
          data: 'base_reading', title: 'Base Reading',
          createdCell: function(td) { td.classList.add('greek-text'); }
        },
        {
          data: 'ms_reading', title: 'MS Reading',
          createdCell: function(td) { td.classList.add('greek-text'); }
        },
        {
          data: 'type', title: 'Type',
          render: function(val) {
            return val.replace(/_/g, ' ');
          }
        },
      ],
      pageLength: 25,
      order: [[0, 'asc'], [1, 'asc']],
      language: {
        search: 'Search:',
        lengthMenu: 'Show _MENU_ entries',
        info: 'Showing _START_ to _END_ of _TOTAL_ variants',
      },
      dom: 'lfrtip',
    });

    // Custom filters
    msSelect.addEventListener('change', () => {
      const val = msSelect.value;
      table.column(2).search(val ? `^${val}$` : '', true, false).draw();
    });

    typeSelect.addEventListener('change', () => {
      const val = typeSelect.value;
      const searchStr = val ? val.replace(/_/g, ' ') : '';
      table.column(5).search(searchStr, false, false).draw();
    });

  } catch (err) {
    console.error('Explorer init error:', err);
    document.getElementById('explorer-container').innerHTML =
      '<p style="color:#CB4335;">Failed to load variant data. Please check the data files.</p>';
  }
});
