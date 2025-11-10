// Whiteboard quick-links builder (vanilla JS)
// Now polls a backend API for live pending counts and links.
// Expected API response (GET /api/pending_counts/):
// {
//   "counts": { "documents": 3, "accounts": 2, ... },
//   "links":  { "documents": "/approve_documents/", "accounts": "/accounts_list/", ... }
// }
//
// Fallback: window.pendingCounts / window.whiteboardLinks still supported.

(function () {
  'use strict';

  // Default whiteboard items (scalable: add new keys here when needed)
  var ITEMS = [
    { key: 'documents', title: 'Documents', icon: 'la la-file', defaultLink: '/approve_documents/' },
    { key: 'accounts', title: 'User accounts', icon: 'la la-user', defaultLink: '/accounts/' },
    { key: 'renewals', title: 'Renewals', icon: 'la la-calendar-check', defaultLink: '/renewals/' }
    // add new items here (must match keys returned by the API)
  ];

  // Build a single whiteboard item node
  function createItemNode(itemKey, title, iconClass, count, href) {
    var item = document.createElement('div');
    item.className = 'whiteboard-item';
    item.setAttribute('role', 'button');
    item.setAttribute('tabindex', '0');
    item.dataset.key = itemKey;

    var iconWrap = document.createElement('div');
    iconWrap.className = 'wb-icon';
    var i = document.createElement('i');
    i.className = iconClass;
    iconWrap.appendChild(i);
    item.appendChild(iconWrap);

    var meta = document.createElement('div');
    meta.className = 'wb-meta';
    var t = document.createElement('div');
    t.className = 'wb-title';
    t.textContent = title;
    var s = document.createElement('div');
    s.className = 'wb-sub';
    s.textContent = (count && count > 0) ? (count + ' pending') : 'No pending items';
    meta.appendChild(t);
    meta.appendChild(s);
    item.appendChild(meta);

    var badge = document.createElement('div');
    badge.className = 'wb-badge';
    if (count && count > 0) {
      badge.textContent = count;
      badge.classList.add('has-count'); // for red dot styling
    } else {
      badge.classList.add('empty');
      badge.innerHTML = '';
    }
    item.appendChild(badge);

    // click / keyboard behavior
    function activate() {
      if (href) {
        window.location.href = href;
      }
    }
    item.addEventListener('click', activate);
    item.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
        e.preventDefault();
        activate();
      }
    });

    return item;
  }

  // Build the entire whiteboard from counts/links
  function buildWhiteboardFromData(counts, links) {
    var container = document.getElementById('whiteboardList');
    if (!container) return;

    container.innerHTML = '';

    counts = counts || {};
    links = links || {};

    // preferred order: ITEMS then extra keys from links
    ITEMS.forEach(function (it) {
      var key = it.key;
      var count = parseInt(counts[key] || 0, 10) || 0;
      var href = links[key] || it.defaultLink || '#';
      var node = createItemNode(key, it.title, it.icon, count, href);
      if (count === 0) node.classList.add('wb-count-zero');
      container.appendChild(node);
    });

    // handle any extra keys provided by the API that are not in ITEMS
    Object.keys(links).forEach(function (k) {
      var known = ITEMS.some(function (x) { return x.key === k; });
      if (known) return;
      var count = parseInt(counts[k] || 0, 10) || 0;
      var node = createItemNode(k, k.replace(/_/g, ' ').replace(/\b\w/g, function(c){return c.toUpperCase();}), 'la la-bell', count, links[k]);
      if (count === 0) node.classList.add('wb-count-zero');
      container.appendChild(node);
    });
  }

  // Public update hook
  window.refreshWhiteboard = function (newCounts, newLinks) {
    if (newCounts) window.pendingCounts = newCounts;
    if (newLinks) window.whiteboardLinks = newLinks;
    buildWhiteboardFromData(window.pendingCounts || {}, window.whiteboardLinks || {});
  };

  // Fetch pending counts from API endpoint and update whiteboard
  function fetchPendingCounts(apiUrl) {
    apiUrl = apiUrl || '/api/pending_counts/';
    return fetch(apiUrl, {
      method: 'GET',
      credentials: 'same-origin',
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(function (res) {
      if (!res.ok) throw new Error('Network response was not ok');
      return res.json();
    })
    .then(function (json) {
      // support both { counts: {...}, links: {...} } and flat responses
      var counts = json.counts || json.pending_counts || {};
      var links = json.links || json.whiteboard_links || {};
      window.pendingCounts = counts;
      window.whiteboardLinks = links;
      buildWhiteboardFromData(counts, links);
    })
    .catch(function (err) {
      // if API fails, fall back to window.pendingCounts/window.whiteboardLinks if present
      console.warn('whiteboard: failed to fetch pending counts', err);
      buildWhiteboardFromData(window.pendingCounts || {}, window.whiteboardLinks || {});
    });
  }

  // Initialize: if server injected pendingCounts/links, use them immediately, then poll API
  function init() {
    // use any inline values provided on page
    if (window.pendingCounts || window.whiteboardLinks) {
      buildWhiteboardFromData(window.pendingCounts || {}, window.whiteboardLinks || {});
    }

    // initial fetch then periodic polling
    fetchPendingCounts();
    // refresh every 30 seconds (adjust as needed)
    setInterval(function () {
      fetchPendingCounts();
    }, 30000);
  }

  // DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();