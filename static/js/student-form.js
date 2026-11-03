function bindInstitutePicker() {
  const search = document.getElementById("institute-search");
  const select = document.getElementById("id_institute");
  const preview = document.getElementById("category-preview");
  if (!select) {
    return;
  }
  const update = () => {
    const query = search ? search.value.trim().toLowerCase() : "";
    Array.from(select.options).forEach((option) => {
      if (!option.value) {
        return;
      }
      const name = (option.dataset.name || option.textContent || "").toLowerCase();
      option.hidden = Boolean(query) && !name.includes(query) && option.value !== select.value;
    });
    const selected = select.options[select.selectedIndex];
    if (preview) {
      preview.textContent = selected && selected.value ? selected.dataset.category || "" : "প্রতিষ্ঠান নির্বাচন করুন";
    }
  };
  if (search) {
    search.addEventListener("input", update);
  }
  select.addEventListener("change", update);
  update();
}

document.addEventListener("DOMContentLoaded", bindInstitutePicker);
