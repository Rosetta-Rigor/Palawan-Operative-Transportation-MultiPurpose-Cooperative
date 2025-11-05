// Calendar UI script with renewal tracking integration
(function () {
  const MS_PER_DAY = 1000 * 60 * 60 * 24;
  const renewalEvents = window.renewalEvents || {};
  const batchCards = window.batchCards || [];

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

  function parseDateSafe(s) {
    if (!s || s === 'N/A') return null;
    const d = new Date(s);
    if (!isNaN(d.getTime())) return new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const parts = ('' + s).trim().split(/[-\/]/);
    if (parts.length === 3) {
      const y = parseInt(parts[0], 10), m = parseInt(parts[1], 10) - 1, day = parseInt(parts[2], 10);
      if (!isNaN(y) && !isNaN(m) && !isNaN(day)) return new Date(y, m, day);
    }
    return null;
  }

  function addYearsSafe(dateObj, years) {
    const d = new Date(dateObj.getTime());
    const y = d.getFullYear() + years;
    d.setFullYear(y);
    if (d.getMonth() !== dateObj.getMonth()) {
      d.setMonth(1); d.setDate(28);
    }
    return d;
  }

  function normalizeExpiryToFuture(expiryDate, todayDate) {
    if (!expiryDate) return null;
    let e = new Date(expiryDate.getFullYear(), expiryDate.getMonth(), expiryDate.getDate());
    let attempts = 0;
    while (e < todayDate && attempts < 5) {
      e = addYearsSafe(e, 1);
      attempts++;
    }
    return e;
  }

  // Compute renewals by date from batch data
  function computeRenewalsByDate() {
    const renewalsByDate = {};
    const todayObj = (window._today_iso) ? parseDateSafe(window._today_iso) : new Date();
    const todayMid = new Date(todayObj.getFullYear(), todayObj.getMonth(), todayObj.getDate());

    batchCards.forEach(batch => {
      const members = batch.members_preview || [];
      members.forEach(member => {
        const memberName = member.member_name || 'Unknown';
        const vehicles = Array.isArray(member.vehicles) ? member.vehicles : [];

        vehicles.forEach(v => {
          const expiryStr = v.expiry_date || null;
          if (!expiryStr) return;
          
          let expiry = parseDateSafe(expiryStr);
          if (!expiry) return;
          
          expiry = normalizeExpiryToFuture(expiry, todayMid);
          if (!expiry) return;

          const expiryYmd = formatYMD(expiry.getFullYear(), expiry.getMonth(), expiry.getDate());
          const diffMs = expiry.getTime() - todayMid.getTime();
          const daysLeft = Math.ceil(diffMs / MS_PER_DAY);

          let status = 'normal';
          if (daysLeft >= 0 && daysLeft <= 29) {
            status = 'urgent';
          } else if (daysLeft >= 30 && daysLeft <= 60) {
            status = 'upcoming';
          }

          if (!renewalsByDate[expiryYmd]) {
            renewalsByDate[expiryYmd] = { urgent: [], upcoming: [], normal: [] };
          }

          renewalsByDate[expiryYmd][status].push({
            member: memberName,
            plate: v.plate || 'N/A',
            daysLeft: daysLeft,
            status: status
          });
        });
      });
    });

    return renewalsByDate;
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

    const renewalsByDate = computeRenewalsByDate();

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

      // Check for renewals on this date
      const renewals = renewalsByDate[ymd];
      if (renewals) {
        // Determine most urgent status (urgent > upcoming)
        let dayStatus = 'normal';
        const hasUrgent = renewals.urgent && renewals.urgent.length > 0;
        const hasUpcoming = renewals.upcoming && renewals.upcoming.length > 0;
        const hasNormal = renewals.normal && renewals.normal.length > 0;
        
        if (hasUrgent) {
          dayStatus = 'urgent';
          cell.classList.add('urgent-renewal');
        } else if (hasUpcoming) {
          dayStatus = 'upcoming';
          cell.classList.add('upcoming-renewal');
        }

        // If there are any renewals, make the day clickable
        if (hasUrgent || hasUpcoming || hasNormal) {
          cell.classList.add('has-renewals');
          cell.style.cursor = 'pointer';
          cell.addEventListener('click', handleDayClick);
        }
      }

      // Legacy support for old renewalEvents format
      if (renewalEvents && renewalEvents[ymd]) {
        cell.classList.add('has-event');
        cell.style.cursor = 'pointer';
        // Ensure click handler is attached for legacy events too
        if (!cell.classList.contains('has-renewals')) {
          cell.addEventListener('click', handleDayClick);
        }
      }

      grid.appendChild(cell);
    }
  }

  function handleDayClick(e) {
    const target = e.currentTarget;
    const date = target.dataset.date;
    if (!date) return;

    // Navigate to renewal details page
    window.location.href = `/renewals/${date}/`;
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

  // Initialize calendar with delay to ensure batch data is loaded
  function initCalendar() {
    // Check if batchCards data is available
    if (!batchCards || batchCards.length === 0) {
      // Retry after 100ms if data not yet loaded
      setTimeout(initCalendar, 100);
      return;
    }
    renderCalendar(activeYear, activeMonth);
  }

  // Initial render with delay
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(initCalendar, 50);
    });
  } else {
    setTimeout(initCalendar, 50);
  }

  // Expose refresh function for external triggers
  window.refreshCalendar = function() {
    renderCalendar(activeYear, activeMonth);
  };
})();