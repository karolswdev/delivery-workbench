/* Delivery Workbench — interaction primitives.
 * Pure vanilla JS, no dependencies. Self-initialises on window.DW namespace.
 * All managers clean up via destroy()/unregister()/release(). */

(function () {
  "use strict";

  window.DW = window.DW || {};

  /* ── helpers ────────────────────────────────────────────────────────── */

  /** True when the user or deterministic snapshot mode requires reduced motion. */
  function prefersReducedMotion() {
    return document.documentElement.classList.contains("reduced-motion")
      || window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  /** Resolve a shared CSS duration token while respecting reduced motion. */
  function motionDuration(token, fallback) {
    if (prefersReducedMotion()) return 0;
    var raw = getComputedStyle(document.documentElement).getPropertyValue(token).trim();
    if (!raw) return fallback;
    if (raw.endsWith("ms")) return Number.parseFloat(raw);
    if (raw.endsWith("s")) return Number.parseFloat(raw) * 1000;
    return fallback;
  }

  /** Return a promise that resolves after a CSS transition/animation finishes. */
  function afterTransition(el, ms) {
    return new Promise(function (resolve) {
      if (ms <= 0) { resolve(); return; }
      var done = false;
      function finish() { if (!done) { done = true; resolve(); } }
      el.addEventListener("transitionend", finish, { once: true });
      /* Safety net — always resolve even if no transition fires. */
      setTimeout(finish, ms + 50);
    });
  }

  /** Focusable elements inside a container. */
  function focusableChildren(root) {
    return Array.from(root.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), ' +
      'textarea:not([disabled]), [tabindex]:not([tabindex="-1"]), summary'
    )).filter(function (el) {
      return el.offsetParent !== null; /* visible only */
    });
  }

  /* ── 1. DragManager ────────────────────────────────────────────────── */

  /**
   * Manages drag-and-drop with visual feedback using HTML5 drag-and-drop API.
   * @constructor
   */
  function DragManager() {
    this._registrations = [];
  }

  /**
   * Make children of a container draggable with visual feedback.
   * @param {HTMLElement} container  - The outer element containing draggable items.
   * @param {Object}      options
   * @param {string}      options.itemSelector     - Selector for draggable children.
   * @param {string}      options.dropZoneSelector - Selector for valid drop targets.
   * @param {string}     [options.ghostClass="dw-drag-ghost"] - CSS class for the drag ghost.
   * @param {Function}   [options.onDrop]          - Callback(item, target, position).
   * @returns {{ unregister: Function }} Handle to tear down this registration.
   */
  DragManager.prototype.register = function (container, options) {
    var opts = Object.assign({
      itemSelector: "[draggable]",
      dropZoneSelector: "[data-droppable]",
      ghostClass: "dw-drag-ghost",
      onDrop: null,
    }, options);

    var dragging = null;
    var ghost = null;
    var indicator = null;

    function createGhost(source) {
      var rect = source.getBoundingClientRect();
      var g = source.cloneNode(true);
      g.className += " " + opts.ghostClass;
      g.style.width = rect.width + "px";
      g.style.position = "fixed";
      g.style.pointerEvents = "none";
      g.style.zIndex = "9999";
      g.setAttribute("aria-hidden", "true");
      document.body.appendChild(g);
      return g;
    }

    function positionGhost(e) {
      if (!ghost) return;
      ghost.style.left = (e.clientX + 12) + "px";
      ghost.style.top = (e.clientY + 12) + "px";
    }

    function showIndicator(zone, e) {
      if (!indicator) {
        indicator = document.createElement("div");
        indicator.className = "dw-drop-indicator";
        indicator.setAttribute("aria-hidden", "true");
      }
      /* Determine position relative to sibling items inside the zone. */
      var children = Array.from(zone.querySelectorAll(opts.itemSelector));
      var insertBefore = null;
      for (var i = 0; i < children.length; i++) {
        var r = children[i].getBoundingClientRect();
        if (e.clientY < r.top + r.height / 2) { insertBefore = children[i]; break; }
      }
      if (insertBefore) {
        zone.insertBefore(indicator, insertBefore);
      } else {
        zone.appendChild(indicator);
      }
    }

    function removeIndicator() {
      if (indicator && indicator.parentNode) indicator.parentNode.removeChild(indicator);
    }

    function removeGhost() {
      if (ghost && ghost.parentNode) ghost.parentNode.removeChild(ghost);
      ghost = null;
    }

    function highlightZones(on) {
      var zones = container.querySelectorAll(opts.dropZoneSelector);
      for (var i = 0; i < zones.length; i++) {
        zones[i].classList.toggle("dw-drop-zone-active", on);
      }
    }

    function onDragStart(e) {
      var item = e.target.closest && e.target.closest(opts.itemSelector);
      if (!item) return;
      dragging = item;
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", "");
      /* Hide the browser default ghost by setting a 1x1 transparent image. */
      var img = new Image();
      img.src = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";
      e.dataTransfer.setDragImage(img, 0, 0);
      ghost = createGhost(item);
      positionGhost(e);
      highlightZones(true);
      item.classList.add("dw-dragging");
      container.dispatchEvent(new CustomEvent("dw-drag-start", { bubbles: true, detail: { item: item } }));
    }

    function onDrag(e) {
      positionGhost(e);
    }

    function onDragOver(e) {
      if (!dragging) return;
      var zone = e.target.closest && e.target.closest(opts.dropZoneSelector);
      if (!zone) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      showIndicator(zone, e);
      container.dispatchEvent(new CustomEvent("dw-drag-over", { bubbles: true, detail: { item: dragging, zone: zone } }));
    }

    function onDragLeave(e) {
      var zone = e.target.closest && e.target.closest(opts.dropZoneSelector);
      if (zone && e.relatedTarget && !zone.contains(e.relatedTarget)) {
        removeIndicator();
      }
    }

    function onDrop(e) {
      if (!dragging) return;
      var zone = e.target.closest && e.target.closest(opts.dropZoneSelector);
      if (!zone) return;
      e.preventDefault();
      /* Determine position index. */
      var children = Array.from(zone.querySelectorAll(opts.itemSelector));
      var position = children.length; /* default: end */
      for (var i = 0; i < children.length; i++) {
        var r = children[i].getBoundingClientRect();
        if (e.clientY < r.top + r.height / 2) { position = i; break; }
      }
      if (opts.onDrop) opts.onDrop(dragging, zone, position);
      cleanup();
    }

    function onDragEnd() {
      cleanup();
    }

    function cleanup() {
      if (dragging) {
        dragging.classList.remove("dw-dragging");
        container.dispatchEvent(new CustomEvent("dw-drag-end", { bubbles: true, detail: { item: dragging } }));
      }
      dragging = null;
      removeGhost();
      removeIndicator();
      highlightZones(false);
    }

    container.addEventListener("dragstart", onDragStart);
    container.addEventListener("drag", onDrag);
    container.addEventListener("dragover", onDragOver);
    container.addEventListener("dragleave", onDragLeave);
    container.addEventListener("drop", onDrop);
    container.addEventListener("dragend", onDragEnd);

    var reg = {
      container: container,
      unregister: function () {
        container.removeEventListener("dragstart", onDragStart);
        container.removeEventListener("drag", onDrag);
        container.removeEventListener("dragover", onDragOver);
        container.removeEventListener("dragleave", onDragLeave);
        container.removeEventListener("drop", onDrop);
        container.removeEventListener("dragend", onDragEnd);
        cleanup();
        var idx = this._registrations.indexOf(reg);
        if (idx > -1) this._registrations.splice(idx, 1);
      }.bind(this),
    };
    this._registrations.push(reg);
    return reg;
  };

  /** Tear down all registrations. */
  DragManager.prototype.destroy = function () {
    while (this._registrations.length) this._registrations[0].unregister();
  };

  /* ── 2. ResizeManager ──────────────────────────────────────────────── */

  /**
   * Makes an element a resize handle for an adjacent panel.
   * @constructor
   */
  function ResizeManager() {
    this._registrations = [];
  }

  /**
   * Register a resize divider.
   * @param {HTMLElement} divider  - The handle element.
   * @param {Object}      options
   * @param {"horizontal"|"vertical"} options.direction - Resize axis.
   * @param {HTMLElement}  options.target    - Element to resize.
   * @param {number}      [options.minSize=50]  - Minimum pixel size.
   * @param {number}      [options.maxSize=Infinity] - Maximum pixel size.
   * @param {number[]}    [options.snapPoints=[]] - Sizes to snap to within 8px.
   * @returns {{ unregister: Function }} Handle to tear down.
   */
  ResizeManager.prototype.register = function (divider, options) {
    var opts = Object.assign({
      direction: "horizontal",
      target: null,
      minSize: 50,
      maxSize: Infinity,
      snapPoints: [],
    }, options);

    var isHorizontal = opts.direction === "horizontal";
    var target = opts.target;
    var resizing = false;
    var startPos = 0;
    var startSize = 0;
    var defaultSize = null;
    var tooltip = null;

    divider.classList.add("dw-resize-divider");
    divider.classList.add(isHorizontal ? "dw-resize-horizontal" : "dw-resize-vertical");

    function getSize() {
      return isHorizontal ? target.offsetWidth : target.offsetHeight;
    }

    function setSize(px) {
      var clamped = Math.max(opts.minSize, Math.min(opts.maxSize, px));
      /* Snap to nearby points. */
      for (var i = 0; i < opts.snapPoints.length; i++) {
        if (Math.abs(clamped - opts.snapPoints[i]) <= 8) { clamped = opts.snapPoints[i]; break; }
      }
      if (isHorizontal) {
        target.style.width = clamped + "px";
      } else {
        target.style.height = clamped + "px";
      }
      return clamped;
    }

    function showTooltip(size) {
      if (!tooltip) {
        tooltip = document.createElement("div");
        tooltip.className = "dw-resize-tooltip";
        tooltip.setAttribute("aria-hidden", "true");
        document.body.appendChild(tooltip);
      }
      tooltip.textContent = Math.round(size) + "px";
      var rect = divider.getBoundingClientRect();
      if (isHorizontal) {
        tooltip.style.left = rect.left + "px";
        tooltip.style.top = (rect.top - 28) + "px";
      } else {
        tooltip.style.left = (rect.left + rect.width / 2 - 20) + "px";
        tooltip.style.top = (rect.top - 28) + "px";
      }
    }

    function hideTooltip() {
      if (tooltip && tooltip.parentNode) tooltip.parentNode.removeChild(tooltip);
      tooltip = null;
    }

    function onPointerDown(e) {
      if (e.button !== 0) return;
      resizing = true;
      startPos = isHorizontal ? e.clientX : e.clientY;
      startSize = getSize();
      if (defaultSize === null) defaultSize = startSize;
      divider.classList.add("dw-resize-active");
      divider.setPointerCapture(e.pointerId);
      e.preventDefault();
    }

    function onPointerMove(e) {
      if (!resizing) return;
      var delta = (isHorizontal ? e.clientX : e.clientY) - startPos;
      var newSize = setSize(startSize + delta);
      showTooltip(newSize);
      divider.dispatchEvent(new CustomEvent("dw-resize", {
        bubbles: true,
        detail: { size: newSize, direction: opts.direction },
      }));
    }

    function onPointerUp() {
      if (!resizing) return;
      resizing = false;
      divider.classList.remove("dw-resize-active");
      hideTooltip();
    }

    function onDoubleClick() {
      if (defaultSize !== null) {
        var size = setSize(defaultSize);
        divider.dispatchEvent(new CustomEvent("dw-resize", {
          bubbles: true,
          detail: { size: size, direction: opts.direction },
        }));
      }
    }

    divider.addEventListener("pointerdown", onPointerDown);
    divider.addEventListener("pointermove", onPointerMove);
    divider.addEventListener("pointerup", onPointerUp);
    divider.addEventListener("pointercancel", onPointerUp);
    divider.addEventListener("dblclick", onDoubleClick);

    var reg = {
      divider: divider,
      unregister: function () {
        divider.removeEventListener("pointerdown", onPointerDown);
        divider.removeEventListener("pointermove", onPointerMove);
        divider.removeEventListener("pointerup", onPointerUp);
        divider.removeEventListener("pointercancel", onPointerUp);
        divider.removeEventListener("dblclick", onDoubleClick);
        divider.classList.remove("dw-resize-divider", "dw-resize-horizontal", "dw-resize-vertical", "dw-resize-active");
        hideTooltip();
        var idx = this._registrations.indexOf(reg);
        if (idx > -1) this._registrations.splice(idx, 1);
      }.bind(this),
    };
    this._registrations.push(reg);
    return reg;
  };

  /** Tear down all registrations. */
  ResizeManager.prototype.destroy = function () {
    while (this._registrations.length) this._registrations[0].unregister();
  };

  /* ── 3. KeyboardNav ────────────────────────────────────────────────── */

  /**
   * Keyboard navigation manager using a roving-tabindex pattern.
   * @constructor
   */
  function KeyboardNav() {
    this._registrations = [];
  }

  /**
   * Apply roving tabindex: the focused item gets tabindex=0, all others -1.
   * @param {HTMLElement[]} items  - The list of navigable elements.
   * @param {HTMLElement}   active - The newly active element.
   */
  function setRovingTabindex(items, active) {
    for (var i = 0; i < items.length; i++) {
      items[i].setAttribute("tabindex", items[i] === active ? "0" : "-1");
    }
    active.focus({ preventScroll: true });
  }

  /**
   * Register arrow-key navigation between cards on a board layout.
   * Left/Right move between columns; Up/Down move within a column.
   * Home/End jump to first/last card.
   * @param {HTMLElement} container - The board element.
   * @returns {{ unregister: Function }}
   */
  KeyboardNav.prototype.registerBoard = function (container) {
    function handler(e) {
      var card = e.target.closest && e.target.closest("[draggable], [role='button'], .bcard");
      if (!card) return;
      var key = e.key;
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].indexOf(key) < 0) return;
      e.preventDefault();

      var columns = Array.from(container.querySelectorAll(".bcol, [data-col]"));
      var currentCol = card.closest(".bcol, [data-col]");
      var colIndex = columns.indexOf(currentCol);
      if (colIndex < 0) return;

      var cardsInCol = Array.from(currentCol.querySelectorAll("[draggable], .bcard"));
      var cardIndex = cardsInCol.indexOf(card);

      var targetCard = null;
      if (key === "ArrowUp") {
        targetCard = cardsInCol[Math.max(0, cardIndex - 1)];
      } else if (key === "ArrowDown") {
        targetCard = cardsInCol[Math.min(cardsInCol.length - 1, cardIndex + 1)];
      } else if (key === "ArrowLeft") {
        var prevCol = columns[Math.max(0, colIndex - 1)];
        var prevCards = Array.from(prevCol.querySelectorAll("[draggable], .bcard"));
        targetCard = prevCards[Math.min(cardIndex, prevCards.length - 1)] || prevCards[0];
      } else if (key === "ArrowRight") {
        var nextCol = columns[Math.min(columns.length - 1, colIndex + 1)];
        var nextCards = Array.from(nextCol.querySelectorAll("[draggable], .bcard"));
        targetCard = nextCards[Math.min(cardIndex, nextCards.length - 1)] || nextCards[0];
      } else if (key === "Home") {
        var allCards = Array.from(container.querySelectorAll("[draggable], .bcard"));
        targetCard = allCards[0];
      } else if (key === "End") {
        var allCards2 = Array.from(container.querySelectorAll("[draggable], .bcard"));
        targetCard = allCards2[allCards2.length - 1];
      }
      if (targetCard && targetCard !== card) {
        var allBoardCards = Array.from(container.querySelectorAll("[draggable], .bcard"));
        setRovingTabindex(allBoardCards, targetCard);
      }
    }

    container.addEventListener("keydown", handler);

    var reg = {
      unregister: function () {
        container.removeEventListener("keydown", handler);
        var idx = this._registrations.indexOf(reg);
        if (idx > -1) this._registrations.splice(idx, 1);
      }.bind(this),
    };
    this._registrations.push(reg);
    return reg;
  };

  /**
   * Register Tab navigation between panels and Escape to close.
   * @param {HTMLElement} container - The panel container.
   * @returns {{ unregister: Function }}
   */
  KeyboardNav.prototype.registerPanels = function (container) {
    function handler(e) {
      var panels = Array.from(container.querySelectorAll("[role='tabpanel'], .panel, section[id]"))
        .filter(function (p) { return p.offsetParent !== null; });
      if (!panels.length) return;

      if (e.key === "Escape") {
        var active = e.target.closest("[role='tabpanel'], .panel, section[id]");
        if (active) {
          active.hidden = true;
          e.preventDefault();
        }
        return;
      }

      if (e.key !== "Tab" || e.ctrlKey || e.metaKey) return;

      var current = document.activeElement;
      var currentPanel = current && current.closest("[role='tabpanel'], .panel, section[id]");
      var idx = panels.indexOf(currentPanel);
      if (idx < 0) return;

      var nextIdx = e.shiftKey
        ? (idx - 1 + panels.length) % panels.length
        : (idx + 1) % panels.length;

      var focusables = focusableChildren(panels[nextIdx]);
      if (focusables.length) {
        e.preventDefault();
        focusables[0].focus({ preventScroll: true });
      }
    }

    container.addEventListener("keydown", handler);

    var reg = {
      unregister: function () {
        container.removeEventListener("keydown", handler);
        var idx = this._registrations.indexOf(reg);
        if (idx > -1) this._registrations.splice(idx, 1);
      }.bind(this),
    };
    this._registrations.push(reg);
    return reg;
  };

  /**
   * Register Up/Down arrow navigation within a list with roving tabindex.
   * Home/End jump to first/last item.
   * @param {HTMLElement} container    - The list element.
   * @param {string}     itemSelector - Selector for list items.
   * @returns {{ unregister: Function }}
   */
  KeyboardNav.prototype.registerList = function (container, itemSelector) {
    itemSelector = itemSelector || "li, [role='option'], [role='menuitem']";

    function handler(e) {
      var items = Array.from(container.querySelectorAll(itemSelector))
        .filter(function (el) { return el.offsetParent !== null; });
      var current = e.target.closest && e.target.closest(itemSelector);
      var idx = items.indexOf(current);
      if (idx < 0) return;

      var key = e.key;
      if (["ArrowUp", "ArrowDown", "Home", "End"].indexOf(key) < 0) return;
      e.preventDefault();

      var nextIdx = key === "Home" ? 0
        : key === "End" ? items.length - 1
          : key === "ArrowUp" ? Math.max(0, idx - 1)
            : Math.min(items.length - 1, idx + 1);

      setRovingTabindex(items, items[nextIdx]);
    }

    container.addEventListener("keydown", handler);

    /* Initialise: first item tabindex=0, rest -1. */
    var initItems = Array.from(container.querySelectorAll(itemSelector));
    for (var i = 0; i < initItems.length; i++) {
      initItems[i].setAttribute("tabindex", i === 0 ? "0" : "-1");
    }

    var reg = {
      unregister: function () {
        container.removeEventListener("keydown", handler);
        var idx = this._registrations.indexOf(reg);
        if (idx > -1) this._registrations.splice(idx, 1);
      }.bind(this),
    };
    this._registrations.push(reg);
    return reg;
  };

  /** Tear down all registrations. */
  KeyboardNav.prototype.destroy = function () {
    while (this._registrations.length) this._registrations[0].unregister();
  };

  /* ── 4. TransitionManager ──────────────────────────────────────────── */

  /**
   * Smooth transitions for UI state changes. All methods return Promises.
   * All respect prefers-reduced-motion: when active, transitions complete
   * instantly (0ms) but still resolve the Promise.
   * @constructor
   */
  function TransitionManager() {}

  /**
   * Slide a panel in from a given direction.
   * @param {HTMLElement} element   - The panel to reveal.
   * @param {"left"|"right"|"bottom"} direction - Slide origin.
   * @returns {Promise<void>}
   */
  TransitionManager.prototype.slideIn = function (element, direction) {
    var ms = motionDuration("--motion-panel", 180);
    var axis = direction === "bottom" ? "translateY" : "translateX";
    var sign = direction === "left" ? "-100%" : "100%";

    element.style.transform = axis + "(" + sign + ")";
    element.style.opacity = "0";
    element.hidden = false;
    /* Force reflow so the start state is painted. */
    void element.offsetHeight;
    element.style.transition = "transform " + ms + "ms var(--motion-ease), opacity " + ms + "ms var(--motion-ease)";
    element.style.transform = "translate(0, 0)";
    element.style.opacity = "1";

    return afterTransition(element, ms).then(function () {
      element.style.transition = "";
      element.style.transform = "";
    });
  };

  /**
   * Slide a panel out toward a given direction.
   * @param {HTMLElement} element   - The panel to hide.
   * @param {"left"|"right"|"bottom"} direction - Slide destination.
   * @returns {Promise<void>}
   */
  TransitionManager.prototype.slideOut = function (element, direction) {
    var ms = motionDuration("--motion-short", 150);
    var axis = direction === "bottom" ? "translateY" : "translateX";
    var sign = direction === "left" ? "-100%" : "100%";

    element.style.transition = "transform " + ms + "ms var(--motion-ease), opacity " + ms + "ms var(--motion-ease)";
    element.style.transform = axis + "(" + sign + ")";
    element.style.opacity = "0";

    return afterTransition(element, ms).then(function () {
      element.hidden = true;
      element.style.transition = "";
      element.style.transform = "";
      element.style.opacity = "";
    });
  };

  /**
   * Fade an element in.
   * @param {HTMLElement} element
   * @returns {Promise<void>}
   */
  TransitionManager.prototype.fadeIn = function (element) {
    var ms = motionDuration("--motion-panel", 180);
    element.style.opacity = "0";
    element.hidden = false;
    void element.offsetHeight;
    element.style.transition = "opacity " + ms + "ms var(--motion-ease)";
    element.style.opacity = "1";

    return afterTransition(element, ms).then(function () {
      element.style.transition = "";
    });
  };

  /**
   * Fade an element out.
   * @param {HTMLElement} element
   * @returns {Promise<void>}
   */
  TransitionManager.prototype.fadeOut = function (element) {
    var ms = motionDuration("--motion-short", 150);
    element.style.transition = "opacity " + ms + "ms var(--motion-ease)";
    element.style.opacity = "0";

    return afterTransition(element, ms).then(function () {
      element.hidden = true;
      element.style.transition = "";
      element.style.opacity = "";
    });
  };

  /**
   * Animate a card from one position to another using the FLIP technique.
   * @param {HTMLElement} element  - The element to animate.
   * @param {DOMRect}     fromRect - Starting bounding rect.
   * @param {DOMRect}     toRect   - Ending bounding rect.
   * @returns {Promise<void>}
   */
  TransitionManager.prototype.cardMove = function (element, fromRect, toRect) {
    var ms = motionDuration("--motion-route", 200);
    var dx = fromRect.left - toRect.left;
    var dy = fromRect.top - toRect.top;
    var sx = fromRect.width / (toRect.width || 1);
    var sy = fromRect.height / (toRect.height || 1);

    element.style.transform = "translate(" + dx + "px, " + dy + "px) scale(" + sx + ", " + sy + ")";
    element.style.transformOrigin = "0 0";
    void element.offsetHeight;
    element.style.transition = "transform " + ms + "ms var(--motion-ease)";
    element.style.transform = "translate(0, 0) scale(1, 1)";

    return afterTransition(element, ms).then(function () {
      element.style.transition = "";
      element.style.transform = "";
      element.style.transformOrigin = "";
    });
  };

  /**
   * Collapse an element's height to zero.
   * @param {HTMLElement} element
   * @returns {Promise<void>}
   */
  TransitionManager.prototype.collapse = function (element) {
    var ms = motionDuration("--motion-panel", 180);
    var h = element.scrollHeight;
    element.style.height = h + "px";
    element.style.overflow = "hidden";
    void element.offsetHeight;
    element.style.transition = "height " + ms + "ms var(--motion-ease), opacity " + ms + "ms var(--motion-ease)";
    element.style.height = "0";
    element.style.opacity = "0";

    return afterTransition(element, ms).then(function () {
      element.hidden = true;
      element.style.transition = "";
      element.style.height = "";
      element.style.overflow = "";
      element.style.opacity = "";
    });
  };

  /**
   * Expand an element from zero height to its natural size.
   * @param {HTMLElement} element
   * @returns {Promise<void>}
   */
  TransitionManager.prototype.expand = function (element) {
    var ms = motionDuration("--motion-panel", 180);
    element.hidden = false;
    element.style.height = "0";
    element.style.overflow = "hidden";
    element.style.opacity = "0";
    void element.offsetHeight;
    var targetH = element.scrollHeight;
    element.style.transition = "height " + ms + "ms var(--motion-ease), opacity " + ms + "ms var(--motion-ease)";
    element.style.height = targetH + "px";
    element.style.opacity = "1";

    return afterTransition(element, ms).then(function () {
      element.style.transition = "";
      element.style.height = "";
      element.style.overflow = "";
    });
  };

  /* ── 5. FocusTrap ──────────────────────────────────────────────────── */

  /**
   * Focus trapping for modal-like panels. Keeps Tab/Shift+Tab within
   * a single element, restoring focus to the previously focused element
   * on release.
   * @constructor
   */
  function FocusTrap() {
    this._active = false;
    this._element = null;
    this._previousFocus = null;
    this._handler = null;
  }

  /**
   * Trap focus within an element.
   * @param {HTMLElement} element - The container to trap focus inside.
   */
  FocusTrap.prototype.trap = function (element) {
    if (this._active) this.release();

    this._element = element;
    this._previousFocus = document.activeElement;
    this._active = true;

    var self = this;
    this._handler = function (e) {
      if (e.key !== "Tab") return;

      var focusable = focusableChildren(self._element);
      if (!focusable.length) { e.preventDefault(); return; }

      var first = focusable[0];
      var last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus({ preventScroll: true });
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus({ preventScroll: true });
        }
      }
    };

    element.addEventListener("keydown", this._handler);

    /* Move focus into the trap. */
    var focusable = focusableChildren(element);
    if (focusable.length) {
      focusable[0].focus({ preventScroll: true });
    } else {
      element.setAttribute("tabindex", "-1");
      element.focus({ preventScroll: true });
    }
  };

  /**
   * Release the focus trap and restore focus to the previously focused element.
   */
  FocusTrap.prototype.release = function () {
    if (!this._active) return;

    if (this._element && this._handler) {
      this._element.removeEventListener("keydown", this._handler);
    }

    if (this._previousFocus && typeof this._previousFocus.focus === "function") {
      this._previousFocus.focus({ preventScroll: true });
    }

    this._active = false;
    this._element = null;
    this._previousFocus = null;
    this._handler = null;
  };

  /* ── Namespace registration ────────────────────────────────────────── */

  window.DW.DragManager = DragManager;
  window.DW.ResizeManager = ResizeManager;
  window.DW.KeyboardNav = KeyboardNav;
  window.DW.TransitionManager = TransitionManager;
  window.DW.FocusTrap = FocusTrap;

})();
