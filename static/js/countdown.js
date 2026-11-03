function startCountdowns() {
  document.querySelectorAll("[data-countdown-target]").forEach((element) => {
    const tick = () => {
      if (element.dataset.finished === "1") {
        return;
      }
      const target = new Date(element.dataset.countdownTarget).getTime();
      if (Number.isNaN(target)) {
        return;
      }
      const diff = target - Date.now();
      if (diff <= 0) {
        element.textContent = element.dataset.endedMessage || "সময়সীমা শেষ হয়েছে। পরবর্তী ঘোষণার জন্য অপেক্ষা করুন।";
        return;
      }
      const total = Math.floor(diff / 1000);
      const days = Math.floor(total / 86400);
      const hours = Math.floor((total % 86400) / 3600);
      const minutes = Math.floor((total % 3600) / 60);
      const seconds = total % 60;
      element.textContent = days + " দিন " + hours + " ঘণ্টা " + minutes + " মিনিট " + seconds + " সেকেন্ড";
      window.setTimeout(tick, 1000);
    };
    tick();
  });
}

document.addEventListener("DOMContentLoaded", startCountdowns);
