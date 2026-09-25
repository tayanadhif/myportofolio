document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('project-search-input');
    const categorySelect = document.querySelector('#project-search-form select[name="category"]');
    const projectGrid = document.getElementById('project-grid');
    const projectCount = document.getElementById('project-count');
    const clearButton = document.getElementById('clear-project-search');

    if (!projectGrid) {
        return;
    }

    const getProjectCards = () => Array.from(projectGrid.querySelectorAll('.experience-card'));

    const updateProjectSummary = () => {
        const cards = getProjectCards();
        const searchValue = searchInput ? searchInput.value.trim().toLowerCase() : '';
        const categoryValue = categorySelect ? categorySelect.value : '';

        const visibleCards = cards.filter((card) => {
            const text = card.textContent.toLowerCase();
            const matchesSearch = !searchValue || text.includes(searchValue);
            const matchesCategory = !categoryValue || card.dataset.category === categoryValue || card.querySelector('.experience-category')?.textContent.trim().toLowerCase() === categoryValue.toLowerCase();
            return matchesSearch && matchesCategory;
        });

        cards.forEach((card) => {
            const shouldShow = visibleCards.includes(card);
            card.classList.toggle('hidden', !shouldShow);
        });

        const emptyState = projectGrid.querySelector('[data-empty-state="true"]');
        if (emptyState) {
            emptyState.classList.toggle('hidden', visibleCards.length > 0);
        }

        if (projectCount) {
            projectCount.textContent = String(visibleCards.length);
        }

        if (clearButton) {
            clearButton.classList.toggle('hidden', !searchInput || !searchInput.value.trim());
        }
    };

    if (searchInput) {
        searchInput.addEventListener('input', updateProjectSummary);
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', () => {
            const form = categorySelect.closest('form');
            if (form) {
                form.submit();
            }
        });
    }

    if (clearButton) {
        clearButton.addEventListener('click', () => {
            if (searchInput) {
                searchInput.value = '';
            }
            if (categorySelect) {
                categorySelect.value = '';
            }
            const form = (searchInput || categorySelect)?.closest('form');
            if (form) {
                form.submit();
            }
        });
    }

    const cards = getProjectCards();
    let draggedItemId = null;

    cards.forEach((card) => {
        if (card.draggable !== true && card.draggable !== 'true') {
            return;
        }

        card.addEventListener('dragstart', (event) => {
            draggedItemId = card.dataset.projectId;
            card.classList.add('dragging');
            event.dataTransfer.effectAllowed = 'move';
            event.dataTransfer.setData('text/plain', draggedItemId);
        });

        card.addEventListener('dragover', (event) => {
            event.preventDefault();
            card.classList.add('drag-over');
        });

        card.addEventListener('dragleave', () => {
            card.classList.remove('drag-over');
        });

        card.addEventListener('drop', (event) => {
            event.preventDefault();
            card.classList.remove('drag-over');

            if (!draggedItemId || draggedItemId === card.dataset.projectId) {
                return;
            }

            const sourceCard = projectGrid.querySelector(`.experience-card[data-project-id="${draggedItemId}"]`);
            const targetCard = card;
            if (!sourceCard || !targetCard) {
                return;
            }

            const cardsAfterReorder = getProjectCards();
            const sourceIndex = cardsAfterReorder.findIndex((item) => item.dataset.projectId === draggedItemId);
            const targetIndex = cardsAfterReorder.findIndex((item) => item.dataset.projectId === card.dataset.projectId);

            if (sourceIndex === -1 || targetIndex === -1) {
                return;
            }

            const [movedCard] = cardsAfterReorder.splice(sourceIndex, 1);
            cardsAfterReorder.splice(targetIndex, 0, movedCard);

            cardsAfterReorder.forEach((item) => projectGrid.appendChild(item));

            const projectOrder = cardsAfterReorder.map((item) => item.dataset.projectId).filter(Boolean);
            const csrfToken = window.projectOrderCsrf || '';
            const params = new URLSearchParams();
            projectOrder.forEach((projectId) => params.append('project_ids[]', projectId));

            fetch('/projects/reorder/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': csrfToken,
                },
                body: params.toString(),
            }).catch(() => {
                window.location.reload();
            });

            draggedItemId = null;
        });

        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            draggedItemId = null;
            getProjectCards().forEach((item) => item.classList.remove('drag-over'));
        });
    });

    updateProjectSummary();
});
