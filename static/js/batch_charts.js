// Updated: prefer --batch-default, and fallback to client-side member expiry parsing when server counts are zero.
// Draws donuts and recalculates urgent/warning if needed.

(function () {
  'use strict';
  var MS_PER_DAY = 1000 * 60 * 60 * 24;

  function getCssVar(name) {
    var el = document.querySelector('.admin-dashboard') || document.documentElement;
    try {
      var cs = window.getComputedStyle(el);
      return (cs && cs.getPropertyValue(name)) ? cs.getPropertyValue(name).trim() : '';
    } catch (e) { return ''; }
  }

  var COLORS = (function() {
    var normal = getCssVar('--batch-normal') || getCssVar('--brand-500') || '#AEE4FF';
    var urgent = getCssVar('--batch-urgent') || '#D64545';
    var upcoming = getCssVar('--batch-upcoming') || '#F59E0B';
    var bg = getCssVar('--batch-bg') || '#F3F6F8';
    return { urgent: urgent, warning: upcoming, normal: normal, bg: bg };
  })();

  function parseDateSafe(s) {
    if (!s || s === 'N/A') return null;
    var d = new Date(s);
    if (!isNaN(d.getTime())) return new Date(d.getFullYear(), d.getMonth(), d.getDate());
    var parts = ('' + s).trim().split(/[-\/]/);
    if (parts.length === 3) {
      var y = parseInt(parts[0],10), m = parseInt(parts[1],10)-1, day = parseInt(parts[2],10);
      if (!isNaN(y) && !isNaN(m) && !isNaN(day)) return new Date(y,m,day);
    }
    return null;
  }

  function addYearsSafe(dateObj, years) {
    var d = new Date(dateObj.getTime());
    var y = d.getFullYear() + years;
    d.setFullYear(y);
    // handle Feb 29 -> Feb 28 if invalid
    if (d.getMonth() !== dateObj.getMonth()) {
      d.setMonth(1); d.setDate(28);
    }
    return d;
  }

  // normalize expiry: if expiry < today, advance by years until >= today (cap attempts)
  function normalizeExpiryToFuture(expiryDate, todayDate) {
    if (!expiryDate) return null;
    var e = new Date(expiryDate.getFullYear(), expiryDate.getMonth(), expiryDate.getDate());
    var attempts = 0;
    while (e < todayDate && attempts < 5) {
      e = addYearsSafe(e, 1);
      attempts++;
    }
    return e;
  }

  function buildSegments(total, urgent, upcoming) {
    var normal = Math.max(0, total - (urgent + upcoming));
    var segs = [];
    if (urgent > 0) segs.push({ value: urgent, color: COLORS.urgent, label: 'urgent' });
    if (upcoming > 0) segs.push({ value: upcoming, color: COLORS.warning, label: 'upcoming' });
    if (normal > 0) segs.push({ value: normal, color: COLORS.normal, label: 'normal' });
    return segs;
  }

  // helpers unchanged...
  function polarToCartesian(cx, cy, radius, angleDegrees) {
    var angleRadians = (angleDegrees) * Math.PI / 180.0;
    return { x: cx + (radius * Math.cos(angleRadians)), y: cy + (radius * Math.sin(angleRadians)) };
  }
  function describeArc(cx, cy, radius, startAngle, endAngle){
    var start = polarToCartesian(cx, cy, radius, endAngle);
    var end = polarToCartesian(cx, cy, radius, startAngle);
    var largeArcFlag = (endAngle - startAngle) <= 180 ? "0" : "1";
    return ["M", start.x, start.y, "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y].join(" ");
  }

  function drawDonut(svgEl, segments) {
    while (svgEl.firstChild) svgEl.removeChild(svgEl.firstChild);
    var total = segments.reduce(function (s, x) { return s + x.value; }, 0);
    var cx = 60, cy = 60, r = 46, thickness = 18;
    var ns = 'http://www.w3.org/2000/svg';

    // background ring
    var bgCircle = document.createElementNS(ns,'circle');
    bgCircle.setAttribute('cx', cx);
    bgCircle.setAttribute('cy', cy);
    bgCircle.setAttribute('r', r);
    bgCircle.setAttribute('fill', 'none');
    bgCircle.setAttribute('stroke', COLORS.bg);
    bgCircle.setAttribute('stroke-width', thickness);
    bgCircle.setAttribute('stroke-linecap', 'round');
    svgEl.appendChild(bgCircle);

    if (total === 0) {
      var full = document.createElementNS(ns,'path');
      full.setAttribute('d', describeArc(cx, cy, r, -90, 270));
      full.setAttribute('fill', 'none');
      full.setAttribute('stroke', COLORS.normal);
      full.setAttribute('stroke-width', thickness);
      full.setAttribute('stroke-linecap', 'round');
      svgEl.appendChild(full);
      return;
    }

    if (segments.length === 1 && segments[0].value === total) {
      var p = document.createElementNS(ns,'path');
      p.setAttribute('d', describeArc(cx, cy, r, -90, 270));
      p.setAttribute('fill', 'none');
      p.setAttribute('stroke', segments[0].color);
      p.setAttribute('stroke-width', thickness);
      p.setAttribute('stroke-linecap', 'round');
      svgEl.appendChild(p);
      return;
    }

    var startAngle = -90;
    segments.forEach(function (seg) {
      var portion = seg.value / total;
      var angle = portion * 360;
      var endAngle = startAngle + angle;
      var largeArc = angle > 180 ? 1 : 0;
      var start = polarToCartesian(cx, cy, r, endAngle);
      var end = polarToCartesian(cx, cy, r, startAngle);
      var d = ['M', start.x, start.y, 'A', r, r, 0, largeArc, 0, end.x, end.y].join(' ');
      var path = document.createElementNS(ns,'path');
      path.setAttribute('d', d);
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', seg.color);
      path.setAttribute('stroke-width', thickness);
      path.setAttribute('stroke-linecap', 'round');
      svgEl.appendChild(path);
      startAngle += angle;
    });
  }

  // compute counts from members_preview, using new thresholds:
  // URGENT: 0-15 days before renewal
  // UPCOMING: 30-60 days before renewal
  function computeCountsFromPreview(batchObj) {
    var total = 0, urgent = 0, upcoming = 0;
    if (!batchObj) return { total:0, urgent:0, upcoming:0 };

    // members_preview expected: [{ member_name, vehicles: [{ plate, expiry_date, days_left, status }] }, ...]
    var members = batchObj.members_preview || batchObj.members || [];
    if (!Array.isArray(members)) return { total:0, urgent:0, upcoming:0 };

    total = members.length;

    var today = (window._today_iso) ? parseDateSafe(window._today_iso) : new Date();
    var todayMid = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();

    members.forEach(function(member) {
      var memberUrgent = false;
      var memberUpcoming = false;

      // If preview has vehicles array
      var vehicles = Array.isArray(member.vehicles) ? member.vehicles : (member.members || []);
      if (!Array.isArray(vehicles) && member.expiry_date) {
        // legacy single-vehicle preview
        vehicles = [{ expiry_date: member.expiry_date, plate: member.plate || null }];
      }

      vehicles.forEach(function (v) {
        var expiryStr = v.expiry_date || v.expiry || null;
        var expiry = parseDateSafe(expiryStr);
        if (!expiry) return;
        expiry = normalizeExpiryToFuture(expiry, new Date(today.getFullYear(), today.getMonth(), today.getDate()));
        if (!expiry) return;
        var expiryMid = new Date(expiry.getFullYear(), expiry.getMonth(), expiry.getDate()).getTime();
        var diffMs = expiryMid - todayMid;
        var daysLeft = Math.ceil(diffMs / MS_PER_DAY);

        if (daysLeft >= 0 && daysLeft <= 15) memberUrgent = true;
        else if (daysLeft >= 30 && daysLeft <= 60 && !memberUrgent) memberUpcoming = true;
      });

      if (memberUrgent) urgent++;
      else if (memberUpcoming) upcoming++;
      // else counted as normal implicitly (normal = total - urgent - upcoming)
    });

    return { total: total, urgent: urgent, upcoming: upcoming };
  }

  function renderBatchCards() {
    var data = Array.isArray(window.batchCards) ? window.batchCards : [];
    var grid = document.getElementById('batchGrid');
    if (!grid) return;
    var cards = grid.querySelectorAll('.batch-card');
    cards.forEach(function (card, idx) {
      var total = parseInt(card.dataset.total || '0', 10) || 0;
      var urgent = parseInt(card.dataset.urgent || '0', 10) || 0;
      var upcoming = parseInt(card.dataset.warning || '0', 10) || 0; // note: attribute still named data-warning

      // if server counts zero or missing, compute from preview
      if ((!total || total === 0) && data.length) {
        var dataIdx = parseInt(card.getAttribute('data-batch-index'), 10);
        var useIdx = (!isNaN(dataIdx) ? dataIdx : idx);
        var batchObj = data[useIdx] || null;
        if (batchObj) {
          var counts = computeCountsFromPreview(batchObj);
          if (counts.total) {
            total = counts.total;
            urgent = counts.urgent;
            upcoming = counts.upcoming;
          }
        }
      }

      var svg = card.querySelector('.batch-svg');
      if (!svg) return;
      var segments = buildSegments(total, urgent, upcoming);
      drawDonut(svg, segments);

      var countEl = card.querySelector('.batch-count');
      if (countEl) countEl.textContent = String(total);

      var meta = card.querySelector('.batch-meta .batch-sub');
      if (meta) {
        var parts = [];
        if (urgent) parts.push(urgent + ' urgent');
        if (upcoming) parts.push(upcoming + ' upcoming');
        meta.textContent = parts.join(' · ');
      }

      var titleText = card.querySelector('.batch-title') ? card.querySelector('.batch-title').textContent.trim() : 'Batch';
      card.setAttribute('title', titleText + ': ' + total + ' members — ' + urgent + ' urgent, ' + upcoming + ' upcoming');
      card.setAttribute('aria-label', titleText + ': ' + total + ' members; ' + urgent + ' urgent; ' + upcoming + ' upcoming');
    });
  }

  function initRender() {
    renderBatchCards();
    document.addEventListener('batchCharts:refresh', renderBatchCards);
    var grid = document.getElementById('batchGrid');
    if (grid && window.MutationObserver) {
      var mo = new MutationObserver(function () {
        clearTimeout(grid._batchRenderT);
        grid._batchRenderT = setTimeout(renderBatchCards, 80);
      });
      mo.observe(grid, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-total','data-urgent','data-warning'] });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRender);
  } else {
    initRender();
  }

})();