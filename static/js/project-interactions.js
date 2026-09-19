document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('project-search-input');
    const projectGrid = document.getElementById('project-grid');
    const projectCount = document.getElementById('project-count');
    const clearButton = document.getElementById('clear-project-search');

    if (!searchInput || !projectGrid) {
        return;
    }

    const updateProjectSummary = () => {
        const cards = Array.from(projectGrid.querySelectorAll('.experience-card'));
        const visibleCards = cards.filter((card) => {
            const text = card.textContent.toLowerCase();
            const searchValue = searchInput.value.trim().toLowerCase();
            return !searchValue || text.includes(searchValue);
        });

        cards.forEach((card) => {
            card.classList.toggle('hidden', !visibleCards.includes(card));
        });

        const emptyState = projectGrid.querySelector('[data-empty-state="true"]');
        if (emptyState) {
            emptyState.classList.toggle('hidden', visibleCards.length > 0);
        }

        if (projectCount) {
            projectCount.textContent = String(visibleCards.length);
        }

        if (clearButton) {
            clearButton.classList.toggle('hidden', !searchInput.value.trim());
        }
    };

    searchInput.addEventListener('input', updateProjectSummary);

    if (clearButton) {
        clearButton.addEventListener('click', () => {
            searchInput.value = '';
            updateProjectSummary();
            searchInput.focus();
        });
    }

    updateProjectSummary();
});
