(function (factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (typeof document !== "undefined") {
    const start = function () {
      api.bindDobInputs(document);
    };
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", start);
    } else {
      start();
    }
  }
})(function () {
  function digitsOnly(value) {
    return String(value || "").replace(/\D/g, "").slice(0, 8);
  }

  function formatDobValue(value) {
    const digits = digitsOnly(value);
    let formatted = "";
    for (let index = 0; index < digits.length; index += 1) {
      if (index === 2 || index === 4) {
        formatted += "/";
      }
      formatted += digits[index];
    }
    return formatted;
  }

  function digitCount(value, end) {
    return String(value || "").slice(0, end).replace(/\D/g, "").length;
  }

  function caretForDigitCount(formatted, count) {
    if (count <= 0) {
      return 0;
    }
    let seen = 0;
    const text = String(formatted || "");
    for (let index = 0; index < text.length; index += 1) {
      if (/\d/.test(text[index])) {
        seen += 1;
        if (seen === count) {
          return index + 1;
        }
      }
    }
    return text.length;
  }

  function nextDobState(value, start, end, edit) {
    const current = String(value || "");
    let from = start == null ? current.length : start;
    let to = end == null ? from : end;
    if (edit.type === "backspace" && from === to && from > 0) {
      from -= current[from - 1] === "/" ? 2 : 1;
      if (from < 0) {
        from = 0;
      }
    } else if (edit.type === "delete" && from === to && from < current.length) {
      to += current[from] === "/" ? 2 : 1;
      if (to > current.length) {
        to = current.length;
      }
    }
    const inserted = edit.type === "insert" ? String(edit.text || "") : "";
    const prefix = current.slice(0, from) + inserted;
    const formatted = formatDobValue(prefix + current.slice(to));
    const count = Math.min(digitCount(prefix, prefix.length), 8);
    return { value: formatted, caret: caretForDigitCount(formatted, count) };
  }

  function writeState(input, state) {
    input.value = state.value;
    if (typeof input.setSelectionRange === "function") {
      input.setSelectionRange(state.caret, state.caret);
    }
  }

  function bindDobInput(input) {
    if (input.dataset.dobBound === "1") {
      return;
    }
    input.dataset.dobBound = "1";
    input.setAttribute("inputmode", "numeric");
    input.setAttribute("autocomplete", "bday");
    input.setAttribute("spellcheck", "false");

    input.addEventListener("keydown", function (event) {
      if (event.ctrlKey || event.metaKey || event.altKey) {
        return;
      }
      if (event.key !== "Backspace" && event.key !== "Delete") {
        return;
      }
      const start = input.selectionStart;
      const end = input.selectionEnd;
      if (start == null || start !== end) {
        return;
      }
      const adjacent = event.key === "Backspace" ? input.value[start - 1] : input.value[start];
      if (adjacent !== "/") {
        return;
      }
      event.preventDefault();
      writeState(
        input,
        nextDobState(input.value, start, end, {
          type: event.key === "Backspace" ? "backspace" : "delete",
        })
      );
    });

    input.addEventListener("paste", function (event) {
      const clipboard = event.clipboardData || window.clipboardData;
      if (!clipboard) {
        return;
      }
      event.preventDefault();
      writeState(
        input,
        nextDobState(input.value, input.selectionStart, input.selectionEnd, {
          type: "insert",
          text: clipboard.getData("text"),
        })
      );
    });

    input.addEventListener("input", function () {
      const caret = input.selectionStart == null ? input.value.length : input.selectionStart;
      const count = Math.min(digitCount(input.value, caret), 8);
      const formatted = formatDobValue(input.value);
      if (formatted !== input.value) {
        input.value = formatted;
      }
      const next = caretForDigitCount(formatted, count);
      if (typeof input.setSelectionRange === "function" && input.selectionStart !== next) {
        input.setSelectionRange(next, next);
      }
    });
  }

  function bindDobInputs(root) {
    const scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll("[data-dob-mask]").forEach(bindDobInput);
  }

  return {
    formatDobValue: formatDobValue,
    caretForDigitCount: caretForDigitCount,
    nextDobState: nextDobState,
    bindDobInputs: bindDobInputs,
  };
});
