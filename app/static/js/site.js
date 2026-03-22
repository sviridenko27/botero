const filterRoot = document.getElementById("catalogFilters");
const catalogItems = Array.from(document.querySelectorAll(".catalog-item"));

if (filterRoot) {
  filterRoot.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-filter]");
    if (!button) return;

    const selectedFilter = button.dataset.filter;
    const filterButtons = Array.from(filterRoot.querySelectorAll("button[data-filter]"));

    filterButtons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");

    catalogItems.forEach((item) => {
      const isAll = selectedFilter === "all";
      const isVisible = isAll || item.dataset.category === selectedFilter;
      item.style.display = isVisible ? "flex" : "none";
    });
  });
}
