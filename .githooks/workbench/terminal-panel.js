"use strict";

/**
 * Integrated terminal panel — command-runner fallback (WLA-33-04).
 *
 * A full PTY requires WebSocket support the stdlib HTTP server does not
 * provide. This panel instead sends individual commands to
 * POST /api/terminal/exec and renders stdout/stderr in a scrollable
 * monospace area. Only dw and git commands are accepted server-side.
 */

window.DW = window.DW || {};

(function () {
  var HISTORY_KEY = "delivery-workbench.terminal-history";
  var MAX_HISTORY = 200;

  function loadHistory() {
    try {
      var raw = localStorage.getItem(HISTORY_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) return parsed;
      }
    } catch (_err) { /* ignore */ }
    return [];
  }

  function saveHistory(entries) {
    try {
      var trimmed = entries.slice(-MAX_HISTORY);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed));
    } catch (_err) { /* ignore */ }
  }

  /**
   * TerminalPanel
   *
   * Usage:
   *   var term = new TerminalPanel();
   *   term.open();   // show the panel
   *   term.close();  // hide the panel
   *   term.render(); // (re-)render into the DOM
   */
  function TerminalPanel() {
    this._history = loadHistory();
    this._historyIndex = -1;
    this._pendingInput = "";
    this._visible = false;
    this._container = null;
    this._outputEl = null;
    this._inputEl = null;
    this._promptPath = "";
    this._running = false;
    this._abortController = null;
  }

  TerminalPanel.prototype.open = function () {
    this._visible = true;
    this.render();
    if (this._container) {
      this._container.style.display = "";
      this._container.removeAttribute("collapsed");
    }
    if (this._inputEl) {
      focusElement(this._inputEl);
    }
  };

  TerminalPanel.prototype.close = function () {
    this._visible = false;
    if (this._container) {
      this._container.style.display = "none";
    }
  };

  TerminalPanel.prototype.render = function () {
    if (this._container) {
      // Already rendered — just ensure visibility state is correct
      this._container.style.display = this._visible ? "" : "none";
      return;
    }

    // Build the panel structure
    var panel = document.createElement("dw-panel");
    panel.setAttribute("title", "Terminal");
    panel.setAttribute("collapsible", "");
    panel.classList.add("terminal-panel");

    var wrapper = document.createElement("div");
    wrapper.className = "terminal-wrapper";

    // Output area
    var output = document.createElement("pre");
    output.className = "terminal-output";
    output.setAttribute("aria-live", "polite");
    output.setAttribute("role", "log");
    output.setAttribute("aria-label", "Terminal output");
    wrapper.appendChild(output);
    this._outputEl = output;

    // Prompt line
    var promptLine = document.createElement("div");
    promptLine.className = "terminal-prompt";

    var promptLabel = document.createElement("span");
    promptLabel.className = "terminal-prompt-path";
    promptLabel.textContent = "$ ";
    this._promptLabel = promptLabel;
    promptLine.appendChild(promptLabel);

    var input = document.createElement("input");
    input.type = "text";
    input.className = "terminal-input";
    input.setAttribute("autocomplete", "off");
    input.setAttribute("autocorrect", "off");
    input.setAttribute("autocapitalize", "off");
    input.setAttribute("spellcheck", "false");
    input.setAttribute("aria-label", "Terminal command input");
    input.placeholder = "Type a dw or git command...";
    promptLine.appendChild(input);
    this._inputEl = input;

    wrapper.appendChild(promptLine);
    panel.appendChild(wrapper);

    // Keyboard handling
    var self = this;
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        var cmd = input.value.trim();
        if (cmd && !self._running) {
          self._exec(cmd);
        }
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        self._navigateHistory(-1);
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        self._navigateHistory(1);
      } else if (e.key === "c" && e.ctrlKey) {
        e.preventDefault();
        if (self._running && self._abortController) {
          self._abortController.abort();
          self._appendOutput("\n^C\n", "terminal-stderr");
          self._running = false;
          self._setInputEnabled(true);
        }
      }
    });

    // Insert into the page
    var appEl = document.getElementById("app");
    if (appEl) {
      appEl.parentNode.insertBefore(panel, appEl.nextSibling);
    } else {
      document.body.appendChild(panel);
    }

    this._container = panel;
    if (!this._visible) {
      panel.style.display = "none";
    }

    // Fetch the repo root path for the prompt
    this._fetchPromptPath();
  };

  TerminalPanel.prototype._fetchPromptPath = function () {
    var self = this;
    fetch("/api/status")
      .then(function (r) { return r.json(); })
      .then(function (envelope) {
        if (envelope && envelope.data && envelope.data.root) {
          self._promptPath = envelope.data.root;
        } else if (envelope && envelope.data && envelope.data.workspace && envelope.data.workspace.root) {
          self._promptPath = envelope.data.workspace.root;
        }
        if (self._promptPath && self._promptLabel) {
          self._promptLabel.textContent = self._promptPath + " $ ";
        }
      })
      .catch(function () { /* keep default prompt */ });
  };

  TerminalPanel.prototype._exec = function (command) {
    var self = this;

    // Add to history
    if (this._history.length === 0 || this._history[this._history.length - 1] !== command) {
      this._history.push(command);
      saveHistory(this._history);
    }
    this._historyIndex = -1;
    this._pendingInput = "";

    // Show the command in the output
    var promptPrefix = this._promptPath ? this._promptPath + " $ " : "$ ";
    this._appendOutput(promptPrefix + command + "\n", "terminal-command");

    // Clear input and show loading state
    this._inputEl.value = "";
    this._running = true;
    this._setInputEnabled(false);

    // Show skeleton loading
    var skeleton = document.createElement("dw-skeleton");
    skeleton.setAttribute("lines", "2");
    skeleton.setAttribute("variant", "text");
    skeleton.className = "terminal-loading";
    this._outputEl.appendChild(skeleton);
    this._scrollToBottom();

    // Send to server
    this._abortController = new AbortController();
    fetch("/api/terminal/exec", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: command }),
      signal: this._abortController.signal
    })
      .then(function (r) { return r.json(); })
      .then(function (envelope) {
        // Remove skeleton
        if (skeleton.parentNode) skeleton.parentNode.removeChild(skeleton);

        if (!envelope.ok) {
          var errMsg = (envelope.data && envelope.data.error) || "Command failed";
          self._appendOutput(errMsg + "\n", "terminal-stderr");
        } else {
          var data = envelope.data;
          if (data.stdout) {
            self._appendOutput(data.stdout, "terminal-stdout");
            if (!data.stdout.endsWith("\n")) self._appendOutput("\n", "terminal-stdout");
          }
          if (data.stderr) {
            self._appendOutput(data.stderr, "terminal-stderr");
            if (!data.stderr.endsWith("\n")) self._appendOutput("\n", "terminal-stderr");
          }
          if (data.exit_code !== 0) {
            self._appendOutput("exit " + data.exit_code + "\n", "terminal-exit-code");
          }
        }

        self._running = false;
        self._setInputEnabled(true);
        focusElement(self._inputEl);
      })
      .catch(function (err) {
        if (skeleton.parentNode) skeleton.parentNode.removeChild(skeleton);
        if (err.name !== "AbortError") {
          self._appendOutput("Error: " + err.message + "\n", "terminal-stderr");
        }
        self._running = false;
        self._setInputEnabled(true);
        focusElement(self._inputEl);
      });
  };

  TerminalPanel.prototype._appendOutput = function (text, className) {
    var span = document.createElement("span");
    span.className = className || "";
    span.textContent = text;
    this._outputEl.appendChild(span);
    this._scrollToBottom();
  };

  TerminalPanel.prototype._scrollToBottom = function () {
    if (this._outputEl) {
      this._outputEl.scrollTop = this._outputEl.scrollHeight;
    }
  };

  TerminalPanel.prototype._setInputEnabled = function (enabled) {
    if (this._inputEl) {
      this._inputEl.disabled = !enabled;
      if (enabled) {
        this._inputEl.classList.remove("terminal-disabled");
      } else {
        this._inputEl.classList.add("terminal-disabled");
      }
    }
  };

  TerminalPanel.prototype._navigateHistory = function (direction) {
    if (this._history.length === 0) return;

    if (this._historyIndex === -1 && direction === -1) {
      // Starting to navigate up from the bottom
      this._pendingInput = this._inputEl.value;
      this._historyIndex = this._history.length - 1;
    } else if (direction === -1) {
      // Going further back
      this._historyIndex = Math.max(0, this._historyIndex - 1);
    } else if (direction === 1) {
      // Going forward
      this._historyIndex = this._historyIndex + 1;
      if (this._historyIndex >= this._history.length) {
        // Back to current input
        this._historyIndex = -1;
        this._inputEl.value = this._pendingInput;
        return;
      }
    }

    if (this._historyIndex >= 0 && this._historyIndex < this._history.length) {
      this._inputEl.value = this._history[this._historyIndex];
    }
  };

  window.DW.TerminalPanel = TerminalPanel;
})();
