(function () {
  var banglaDigits = "০১২৩৪৫৬৭৮৯";

  function toBangla(value, width) {
    var text = String(value);
    while (text.length < width) {
      text = "0" + text;
    }
    return text.replace(/\d/g, function (digit) {
      return banglaDigits.charAt(Number(digit));
    });
  }

  function reducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function setPart(root, name, value) {
    var node = root.querySelector('[data-countdown-part="' + name + '"]');
    if (!node) {
      return;
    }
    var next = toBangla(value, 2);
    if (node.textContent !== next) {
      node.textContent = next;
      if (!reducedMotion()) {
        node.classList.add("is-changing");
        window.setTimeout(function () {
          node.classList.remove("is-changing");
        }, 180);
      }
    }
  }

  function writeStatus(root, message) {
    var status = root.querySelector("[data-countdown-status]");
    if (status) {
      status.textContent = message;
    }
  }

  function finish(root) {
    root.dataset.finished = "1";
    var message = root.dataset.endedMessage || "সময়সীমা শেষ হয়েছে। পরবর্তী ঘোষণার জন্য অপেক্ষা করুন।";
    var cards = root.querySelector("[data-countdown-cards]");
    if (cards) {
      cards.hidden = true;
    }
    writeStatus(root, message);
  }

  function tick(root) {
    if (root.dataset.finished === "1") {
      return;
    }
    var target = new Date(root.dataset.countdownTarget).getTime();
    if (Number.isNaN(target)) {
      finish(root);
      writeStatus(root, "সময় গণনা করা যাচ্ছে না।");
      return;
    }
    var diff = target - Date.now();
    if (diff <= 0) {
      finish(root);
      return;
    }
    var total = Math.floor(diff / 1000);
    var days = Math.floor(total / 86400);
    var hours = Math.floor((total % 86400) / 3600);
    var minutes = Math.floor((total % 3600) / 60);
    var seconds = total % 60;
    setPart(root, "days", days);
    setPart(root, "hours", hours);
    setPart(root, "minutes", minutes);
    setPart(root, "seconds", seconds);
    writeStatus(
      root,
      "বাকি সময় " + toBangla(days, 2) + " দিন " + toBangla(hours, 2) + " ঘণ্টা " +
        toBangla(minutes, 2) + " মিনিট " + toBangla(seconds, 2) + " সেকেন্ড"
    );
  }

  function startCountdowns() {
    document.querySelectorAll("[data-countdown]").forEach(function (root) {
      if (root.dataset.countdownStarted === "1" || root.dataset.finished === "1") {
        return;
      }
      root.dataset.countdownStarted = "1";
      tick(root);
      if (root.dataset.finished === "1") {
        return;
      }
      var timer = window.setInterval(function () {
        tick(root);
        if (root.dataset.finished === "1") {
          window.clearInterval(timer);
        }
      }, 1000);
    });
  }

  document.addEventListener("DOMContentLoaded", startCountdowns);
})();
