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
        if (renewals.urgent && renewals.urgent.length > 0) {
          dayStatus = 'urgent';
          cell.classList.add('urgent-renewal');
        } else if (renewals.upcoming && renewals.upcoming.length > 0) {
          dayStatus = 'upcoming';
          cell.classList.add('upcoming-renewal');
        }

        // Combine all renewals for tooltip
        const allRenewals = [
          ...(renewals.urgent || []),
          ...(renewals.upcoming || []),
          ...(renewals.normal || [])
        ];

        if (allRenewals.length > 0) {
          cell.dataset.renewals = JSON.stringify(allRenewals);
          cell.dataset.status = dayStatus;
          cell.addEventListener('mouseenter', showTooltip);
          cell.addEventListener('mousemove', moveTooltip);
          cell.addEventListener('mouseleave', hideTooltip);
          cell.addEventListener('click', handleDayClick);
          cell.addEventListener('touchstart', function (e) {
            e.preventDefault();
            showTooltip(e);
          }, { passive: false });
        }
      }

      // Legacy support for old renewalEvents format
      if (renewalEvents && renewalEvents[ymd]) {
        cell.classList.add('has-event');
        if (!cell.dataset.renewals) {
          cell.dataset.events = JSON.stringify(renewalEvents[ymd]);
        }
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
    
    // Try new renewals format first
    let renewals = null;
    const renewalsRaw = target.dataset.renewals;
    if (renewalsRaw) {
      try { renewals = JSON.parse(renewalsRaw); } catch (err) { }
    }

    // Fallback to old events format
    if (!renewals) {
      const eventsRaw = target.dataset.events;
      if (eventsRaw) {
        try { renewals = JSON.parse(eventsRaw); } catch (err) { }
      }
    }

    if (!renewals || renewals.length === 0) return;

    tooltip.innerHTML = '';

    // Add header with count
    const header = document.createElement('div');
    header.className = 'tooltip-header';
    header.style.fontWeight = '700';
    header.style.marginBottom = '8px';
    header.style.borderBottom = '1px solid rgba(255,255,255,0.2)';
    header.style.paddingBottom = '6px';
    
    const status = target.dataset.status || 'normal';
    const statusLabel = status === 'urgent' ? '🔴 Urgent Renewals' : 
                        status === 'upcoming' ? '🟡 Upcoming Renewals' : 'Renewals';
    header.textContent = `${statusLabel} (${renewals.length})`;
    tooltip.appendChild(header);

    // Show up to 2 renewals
    renewals.slice(0, 2).forEach(renewal => {
      const item = document.createElement('div');
      item.className = 'tooltip-item';
      item.style.marginBottom = '4px';
      item.style.fontSize = '0.85rem';
      
      const memberName = renewal.member || renewal.member_name || 'Unknown';
      const plate = renewal.plate || 'N/A';
      const daysText = renewal.daysLeft !== undefined ? ` (${renewal.daysLeft}d)` : '';
      
      item.textContent = `${memberName} — ${plate}${daysText}`;
      tooltip.appendChild(item);
    });

    // Show "more" indicator if needed
    if (renewals.length > 2) {
      const more = document.createElement('div');
      more.className = 'tooltip-more';
      more.style.marginTop = '6px';
      more.style.paddingTop = '6px';
      more.style.borderTop = '1px solid rgba(255,255,255,0.2)';
      more.style.fontSize = '0.8rem';
      more.style.opacity = '0.8';
      more.textContent = `+ ${renewals.length - 2} more (click to view all)`;
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
    tooltip.style.left = x + 'px';
    tooltip.style.top = (y - 10) + 'px';
    tooltip.style.transform = 'translate(-50%, -100%)';
  }

  function hideTooltip() {
    tooltip.classList.remove('visible');
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

  // close tooltip when clicking outside calendar
  document.addEventListener('click', function (e) {
    if (!e.target.closest('#renewalCalendar')) hideTooltip();
  });
})();