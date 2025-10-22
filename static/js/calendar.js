// Calendar UI script (expects window.renewalEvents to be set before this file is loaded)
(function () {
  const renewalEvents = window.renewalEvents || {};

  const monthYearEl = document.getElementById('calendarMonthYear');
  const grid = document.getElementById('calendarGrid');
  const prevBtn = document.getElementById('calPrev');
  const nextBtn = document.getElementById('calNext');

  let today = new Date();
  let activeYear = today.getFullYear();
  let activeMonth = today.getMonth(); // 0-indexed

  function formatYMD(y, m, d) {
    const mm = String(m + 1).padStart(2, '0');
    const dd = String(d).padStart(2, '0');
    return `${y}-${mm}-${dd}`;
  }

  function clearGrid() {
    if (grid) grid.innerHTML = '';
  }

  function renderCalendar(year, month) {
    if (!grid || !monthYearEl) return;
    grid.innerHTML = '';
    const first = new Date(year, month, 1);
    const last = new Date(year, month + 1, 0);
    const startDay = first.getDay();
    const daysInMonth = last.getDate();

    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    monthYearEl.textContent = `${monthNames[month]} ${year}`;

    for (let i = 0; i < startDay; i++) {
      const empty = document.createElement('div');
      empty.className = 'calendar-day empty';
      grid.appendChild(empty);
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const ymd = formatYMD(year, month, d);
      const cell = document.createElement('div');
      cell.className = 'calendar-day';
      cell.setAttribute('data-date', ymd);

      const num = document.createElement('div');
      num.className = 'day-number';
      num.textContent = d;
      cell.appendChild(num);

      if (renewalEvents && renewalEvents[ymd]) {
        cell.classList.add('has-event');
        cell.dataset.events = JSON.stringify(renewalEvents[ymd]);
        cell.addEventListener('mouseenter', showTooltip);
        cell.addEventListener('mousemove', moveTooltip);
        cell.addEventListener('mouseleave', hideTooltip);
        cell.addEventListener('touchstart', function (e) {
          e.preventDefault();
          showTooltip(e);
        }, { passive: false });
      }

      grid.appendChild(cell);
    }
  }

  // tooltip
  const tooltip = document.createElement('div');
  tooltip.className = 'calendar-tooltip';
  document.body.appendChild(tooltip);

  function showTooltip(e) {
    const target = e.currentTarget || e.target;
    const raw = target.dataset.events;
    if (!raw) return;
    let events;
    try { events = JSON.parse(raw); } catch (err) { events = []; }
    tooltip.innerHTML = '';
    events.slice(0, 5).forEach(ev => {
      const it = document.createElement('div');
      it.className = 'item';
      it.textContent = `${ev.plate} — ${ev.member}`;
      tooltip.appendChild(it);
    });
    if (events.length > 5) {
      const more = document.createElement('div');
      more.className = 'meta';
      more.textContent = `+ ${events.length - 5} more`;
      tooltip.appendChild(more);
    }
    tooltip.classList.add('visible');
    positionTooltip(e);
  }

  function moveTooltip(e) {
    positionTooltip(e);
  }

  function positionTooltip(e) {
    const x = (e.touches && e.touches[0]) ? e.touches[0].clientX : e.clientX;
    const y = (e.touches && e.touches[0]) ? e.touches[0].clientY : e.clientY;
    tooltip.style.left = (x) + 'px';
    tooltip.style.top = (y - 12) + 'px';
  }

  function hideTooltip() {
    tooltip.classList.remove('visible');
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', function () {
      activeMonth--;
      if (activeMonth < 0) { activeMonth = 11; activeYear--; }
      renderCalendar(activeYear, activeMonth);
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener('click', function () {
      activeMonth++;
      if (activeMonth > 11) { activeMonth = 0; activeYear++; }
      renderCalendar(activeYear, activeMonth);
    });
  }

  // initial render
  renderCalendar(activeYear, activeMonth);

  // close tooltip when clicking outside calendar
  document.addEventListener('click', function (e) {
    if (!e.target.closest('#renewalCalendar')) hideTooltip();
  });
})();