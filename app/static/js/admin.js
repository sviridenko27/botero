const sectionSelect = document.getElementById("sectionSelect");
const categorySelect = document.getElementById("categorySelect");

const sectionCategories = {
  serial: [
    { value: "cakes", label: "Торты" },
    { value: "pastries", label: "Пирожные" },
  ],
  catalog: [
    { value: "wedding", label: "Свадебные" },
    { value: "birthday", label: "День рождения" },
    { value: "kids", label: "Детские" },
  ],
};

function syncCategoryOptions() {
  const section = sectionSelect.value;
  const options = sectionCategories[section] || [];

  categorySelect.innerHTML = "";
  options.forEach((option) => {
    const optionNode = document.createElement("option");
    optionNode.value = option.value;
    optionNode.textContent = option.label;
    categorySelect.appendChild(optionNode);
  });
}

if (sectionSelect && categorySelect) {
  sectionSelect.addEventListener("change", syncCategoryOptions);
  syncCategoryOptions();
}
