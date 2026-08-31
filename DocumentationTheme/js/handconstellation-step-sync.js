/*
 * Keeps a tutorial's right-hand code panel in sync with its focused step.
 *
 * The DocC renderer swaps the code listing when the focused step changes, but
 * the panel keeps whatever scroll offset the previous listing had. This script
 * scrolls only that inner panel so the lines highlighted for the current step
 * are visible.
 *
 * A tutorial page renders one steps column and one code panel per @Section, and
 * each column tracks its own focused step, so the work is done per section
 * rather than per page.
 *
 * It never touches the page scroll position, never runs on a code panel the
 * narrow-screen layout has hidden, and runs at most once per step change so a
 * reader who scrolls the code by hand is left alone. It depends on nothing but
 * a few stable DocC class names, so a renderer update can make it inert but
 * cannot make it misbehave.
 */
(function () {
  "use strict";

  var DESKTOP_QUERY = "(min-width: 736px)";
  var REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";
  var STEPS_SELECTOR = ".steps";
  var CODE_PANEL_SELECTOR = ".code-preview";
  var CODE_LINE_SELECTOR = ".code-line-container";
  var HIGHLIGHTED_SELECTOR = ".code-line-container.highlighted";
  var FOCUSED_STEP_SELECTOR = ".step.focused";
  var MODAL_PATTERN = /modal|fullscreen/i;
  var TOP_MARGIN_RATIO = 0.12;

  var lastFocusedStep = new WeakMap();
  var pendingCheck = false;
  var pendingGroups = [];
  var pendingFrame = null;

  function matches(query) {
    return typeof window.matchMedia === "function" && window.matchMedia(query).matches;
  }

  function isInsideModal(element) {
    for (var node = element; node; node = node.parentElement) {
      var name = node.getAttribute && node.getAttribute("class");
      if (name && MODAL_PATTERN.test(name)) {
        return true;
      }
    }
    return false;
  }

  /// Returns the section's code panel, or null when this step shows an image,
  /// or when the narrow-screen layout has hidden the panel.
  function codePanel(group) {
    var panel = group.querySelector(CODE_PANEL_SELECTOR);
    if (!panel || panel.offsetParent === null || isInsideModal(panel)) {
      return null;
    }
    return panel;
  }

  /// Walks up from a code line to the element that actually scrolls.
  function scrollingAncestor(element, boundary) {
    for (var node = element.parentElement; node; node = node.parentElement) {
      var overflowY = window.getComputedStyle(node).overflowY;
      var scrolls = overflowY === "auto" || overflowY === "scroll";
      if (scrolls && node.scrollHeight - node.clientHeight > 1) {
        return node;
      }
      if (node === boundary || node === document.body) {
        return null;
      }
    }
    return null;
  }

  /// A hidden page never runs the animation a smooth scroll needs, so jump
  /// there directly rather than leaving the panel where it was.
  function shouldAnimate() {
    return !document.hidden && !matches(REDUCED_MOTION_QUERY);
  }

  function scrollPanel(container, top) {
    var limit = Math.max(0, container.scrollHeight - container.clientHeight);
    var clamped = Math.max(0, Math.min(top, limit));
    if (shouldAnimate() && typeof container.scrollTo === "function") {
      container.scrollTo({ top: clamped, behavior: "smooth" });
    } else {
      container.scrollTop = clamped;
    }
  }

  function syncGroup(group) {
    if (!matches(DESKTOP_QUERY) || !document.contains(group)) {
      return;
    }

    var panel = codePanel(group);
    if (!panel) {
      return;
    }

    var highlighted = panel.querySelectorAll(HIGHLIGHTED_SELECTOR);
    var probe = highlighted.length ? highlighted[0] : panel.querySelector(CODE_LINE_SELECTOR);
    if (!probe) {
      return;
    }

    var container = scrollingAncestor(probe, panel);
    if (!container) {
      return;
    }

    if (!highlighted.length) {
      scrollPanel(container, 0);
      return;
    }

    var containerBox = container.getBoundingClientRect();
    var firstBox = highlighted[0].getBoundingClientRect();
    var lastBox = highlighted[highlighted.length - 1].getBoundingClientRect();
    var blockTop = firstBox.top - containerBox.top + container.scrollTop;
    var blockHeight = Math.max(lastBox.bottom - firstBox.top, firstBox.height);

    if (blockHeight < container.clientHeight) {
      scrollPanel(container, blockTop - (container.clientHeight - blockHeight) / 2);
    } else {
      scrollPanel(container, blockTop - container.clientHeight * TOP_MARGIN_RATIO);
    }
  }

  /// Waits two frames so the renderer has finished swapping the code listing.
  function flushPendingGroups() {
    pendingFrame = window.requestAnimationFrame(function () {
      pendingFrame = null;
      var groups = pendingGroups;
      pendingGroups = [];
      for (var i = 0; i < groups.length; i += 1) {
        syncGroup(groups[i]);
      }
    });
  }

  function scheduleSync(group) {
    if (pendingGroups.indexOf(group) === -1) {
      pendingGroups.push(group);
    }
    if (pendingFrame !== null) {
      return;
    }
    pendingFrame = window.requestAnimationFrame(flushPendingGroups);
  }

  function checkFocusedSteps() {
    pendingCheck = false;
    var groups = document.querySelectorAll(STEPS_SELECTOR);
    for (var i = 0; i < groups.length; i += 1) {
      var group = groups[i];
      var step = group.querySelector(FOCUSED_STEP_SELECTOR);
      if (lastFocusedStep.get(group) === step) {
        continue;
      }
      lastFocusedStep.set(group, step);
      if (step) {
        scheduleSync(group);
      }
    }
  }

  function handleMutations() {
    if (pendingCheck) {
      return;
    }
    pendingCheck = true;
    window.requestAnimationFrame(checkFocusedSteps);
  }

  function start() {
    if (typeof window.MutationObserver !== "function") {
      return;
    }
    // childList matters as much as the class attribute: the renderer mounts a
    // whole tutorial page with its first step already focused, so the initial
    // focus arrives as new nodes rather than as a class change.
    new window.MutationObserver(handleMutations).observe(document.body, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["class"]
    });
    checkFocusedSteps();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
