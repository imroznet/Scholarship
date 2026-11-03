(function () {
  var storageKey = "cgs-announcement-dismissed";

  document.querySelectorAll("[data-announcement-dismiss]").forEach(function (link) {
    link.addEventListener("click", function () {
      var token = link.getAttribute("data-token") || "";
      try {
        window.localStorage.setItem(storageKey, token);
      } catch (error) {
        return;
      }
    });
  });
})();
