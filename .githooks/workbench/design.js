/* Design reference page — renders at #/design (dev-only).
 * Shows every component in every state across both themes.
 * Not linked from the production navigation. */

"use strict";

function designReferencePage() {
  return `
  <section class="design-ref" aria-labelledby="design-title">
    <h1 id="design-title">Component reference</h1>
    <p class="design-intro">Every component in every state, in the current theme.
      Toggle your OS theme to see the other palette. This page is dev-only.</p>

    <!-- Buttons -->
    <section class="design-section" aria-labelledby="design-buttons">
      <h2 id="design-buttons">Buttons</h2>
      <div class="design-grid">
        <div class="design-item">
          <span class="design-label">Primary</span>
          <dw-button variant="primary">Primary</dw-button>
        </div>
        <div class="design-item">
          <span class="design-label">Secondary</span>
          <dw-button variant="secondary">Secondary</dw-button>
        </div>
        <div class="design-item">
          <span class="design-label">Danger</span>
          <dw-button variant="danger">Danger</dw-button>
        </div>
        <div class="design-item">
          <span class="design-label">Ghost</span>
          <dw-button variant="ghost">Ghost</dw-button>
        </div>
        <div class="design-item">
          <span class="design-label">Disabled</span>
          <dw-button variant="primary" disabled>Disabled</dw-button>
        </div>
        <div class="design-item">
          <span class="design-label">Loading</span>
          <dw-button variant="primary" loading>Loading…</dw-button>
        </div>
      </div>
    </section>

    <!-- Status pills -->
    <section class="design-section" aria-labelledby="design-pills">
      <h2 id="design-pills">Status pills</h2>
      <div class="design-grid">
        <div class="design-item"><dw-status-pill status="backlog"></dw-status-pill></div>
        <div class="design-item"><dw-status-pill status="ready"></dw-status-pill></div>
        <div class="design-item"><dw-status-pill status="in-progress"></dw-status-pill></div>
        <div class="design-item"><dw-status-pill status="blocked"></dw-status-pill></div>
        <div class="design-item"><dw-status-pill status="on-hold"></dw-status-pill></div>
        <div class="design-item"><dw-status-pill status="done"></dw-status-pill></div>
      </div>
    </section>

    <!-- Badges -->
    <section class="design-section" aria-labelledby="design-badges">
      <h2 id="design-badges">Badges</h2>
      <div class="design-grid">
        <div class="design-item">
          <span class="design-label">Count</span>
          <dw-badge count="3"></dw-badge>
        </div>
        <div class="design-item">
          <span class="design-label">Alert</span>
          <dw-badge count="!" variant="alert"></dw-badge>
        </div>
        <div class="design-item">
          <span class="design-label">Needs you</span>
          <dw-badge count="1" variant="needs-you"></dw-badge>
        </div>
      </div>
    </section>

    <!-- Cards -->
    <section class="design-section" aria-labelledby="design-cards">
      <h2 id="design-cards">Cards</h2>
      <div class="design-grid design-grid-wide">
        <dw-card>
          <span slot="header">Default card</span>
          <p>Card body content with some text to show how it fills.</p>
        </dw-card>
        <dw-card elevated>
          <span slot="header">Elevated card</span>
          <p>This card has a stronger shadow.</p>
        </dw-card>
      </div>
    </section>

    <!-- Panels -->
    <section class="design-section" aria-labelledby="design-panels">
      <h2 id="design-panels">Panels</h2>
      <div class="design-grid design-grid-wide">
        <dw-panel title="Collapsible panel" collapsible>
          <p>Panel body content. This panel can be collapsed.</p>
        </dw-panel>
        <dw-panel title="Fixed panel">
          <p>This panel cannot be collapsed.</p>
        </dw-panel>
      </div>
    </section>

    <!-- Fold -->
    <section class="design-section" aria-labelledby="design-folds">
      <h2 id="design-folds">Fold / Disclosure</h2>
      <dw-fold label="Technical details">
        <p>Hidden content revealed on expand. Press Escape to close.</p>
        <pre><code>{ "some": "technical data" }</code></pre>
      </dw-fold>
    </section>

    <!-- Skeletons -->
    <section class="design-section" aria-labelledby="design-skeletons">
      <h2 id="design-skeletons">Loading skeletons</h2>
      <div class="design-grid design-grid-wide">
        <div class="design-item">
          <span class="design-label">Text (3 lines)</span>
          <dw-skeleton lines="3" variant="text"></dw-skeleton>
        </div>
        <div class="design-item">
          <span class="design-label">Card</span>
          <dw-skeleton variant="card"></dw-skeleton>
        </div>
        <div class="design-item">
          <span class="design-label">List</span>
          <dw-skeleton variant="list" lines="4"></dw-skeleton>
        </div>
      </div>
    </section>

    <!-- Empty state -->
    <section class="design-section" aria-labelledby="design-empty">
      <h2 id="design-empty">Empty states</h2>
      <dw-empty-state
        icon="📋"
        heading="No stories yet"
        message="Create your first story to get started."
        action-label="Create story"
        action-href="#/design">
      </dw-empty-state>
    </section>

    <!-- Stream lines -->
    <section class="design-section" aria-labelledby="design-stream">
      <h2 id="design-stream">Stream lines</h2>
      <div class="design-stream-demo">
        <dw-stream-line type="text" timestamp="14:32:01">Agent started working on WLA-33-01</dw-stream-line>
        <dw-stream-line type="tool-call" timestamp="14:32:03">Read pmo-roadmap/workbench/app.js (lines 1-150)</dw-stream-line>
        <dw-stream-line type="edit" timestamp="14:32:15">Edit pmo-roadmap/workbench/style.css (+12 -3)</dw-stream-line>
        <dw-stream-line type="question" timestamp="14:32:20">Should I use Preact or vanilla web components?</dw-stream-line>
        <dw-stream-line type="evidence" timestamp="14:33:01">Evidence captured: npm test (exit 0)</dw-stream-line>
      </div>
    </section>

    <!-- Toasts -->
    <section class="design-section" aria-labelledby="design-toasts">
      <h2 id="design-toasts">Toasts</h2>
      <div class="design-grid">
        <dw-button variant="secondary" onclick="document.body.appendChild(Object.assign(document.createElement('dw-toast'), {textContent: 'Story moved to in-progress', variant: 'info'}))">Show info</dw-button>
        <dw-button variant="secondary" onclick="document.body.appendChild(Object.assign(document.createElement('dw-toast'), {textContent: 'Evidence captured', variant: 'success'}))">Show success</dw-button>
        <dw-button variant="secondary" onclick="document.body.appendChild(Object.assign(document.createElement('dw-toast'), {textContent: 'Story has no evidence', variant: 'warning'}))">Show warning</dw-button>
        <dw-button variant="secondary" onclick="document.body.appendChild(Object.assign(document.createElement('dw-toast'), {textContent: 'Gate refused the commit', variant: 'error'}))">Show error</dw-button>
      </div>
    </section>

    <!-- Interactions -->
    <section class="design-section" aria-labelledby="design-interactions">
      <h2 id="design-interactions">Interaction primitives</h2>
      <h3>Keyboard shortcuts</h3>
      <table class="design-keys">
        <thead><tr><th>Shortcut</th><th>Action</th></tr></thead>
        <tbody>
          <tr><td><kbd>Ctrl+1</kbd>–<kbd>6</kbd></td><td>Toggle panels</td></tr>
          <tr><td><kbd>←</kbd> <kbd>→</kbd></td><td>Move between board columns</td></tr>
          <tr><td><kbd>↑</kbd> <kbd>↓</kbd></td><td>Move between cards in a column</td></tr>
          <tr><td><kbd>Escape</kbd></td><td>Close active panel / fold</td></tr>
          <tr><td><kbd>Tab</kbd></td><td>Move between panels</td></tr>
        </tbody>
      </table>
    </section>
  </section>`;
}

window.DW = window.DW || {};
window.DW.designReferencePage = designReferencePage;
