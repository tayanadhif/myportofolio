document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('portfolio-search-form');
    const searchInput = document.getElementById('portfolio-search-input');
    const grid = document.getElementById('portfolio-grid');
    const loadingState = document.getElementById('portfolio-loading');
    const emptyState = document.getElementById('portfolio-empty');
    const errorState = document.getElementById('portfolio-error');
    const config = window.portfolioAjaxConfig;

    if (!form || !searchInput || !grid || !loadingState || !emptyState || !errorState || !config) {
        return;
    }

    const setState = (state) => {
        loadingState.hidden = state !== 'loading';
        emptyState.hidden = state !== 'empty';
        errorState.hidden = state !== 'error';
        grid.hidden = state === 'loading' || state === 'empty' || state === 'error';
    };

    const createTextElement = (tagName, className, text) => {
        const element = document.createElement(tagName);
        element.className = className;
        element.textContent = text || '';
        return element;
    };

    const buildCard = (item) => {
        const card = document.createElement('article');
        card.className = 'experience-card';

        card.appendChild(createTextElement('span', 'experience-category', item.category));
        card.appendChild(createTextElement('h2', '', item.title));
        card.appendChild(createTextElement('p', 'experience-description', item.description));

        const actions = document.createElement('div');
        actions.className = 'project-card-actions';
        const actionGroup = document.createElement('div');
        actionGroup.className = 'project-actions';

        if (item.link) {
            const link = document.createElement('a');
            link.className = 'button';
            link.href = item.link;
            link.target = '_blank';
            link.rel = 'noreferrer';
            link.textContent = 'Lihat detail';
            actionGroup.appendChild(link);
        }

        actionGroup.appendChild(createTextElement('span', 'star-count', `★ ${item.star_count || 0}`));

        if (config.canDelete) {
            const deleteForm = document.createElement('form');
            deleteForm.method = 'post';
            deleteForm.action = config.deleteBaseUrl.replace('00000000-0000-0000-0000-000000000000', item.id);
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = config.csrfToken;
            const deleteButton = document.createElement('button');
            deleteButton.type = 'submit';
            deleteButton.className = 'button button-danger';
            deleteButton.textContent = 'Hapus Portfolio';
            deleteForm.append(csrfInput, deleteButton);
            actionGroup.appendChild(deleteForm);
        }

        actions.appendChild(actionGroup);
        card.appendChild(actions);
        return card;
    };

    const loadPortfolio = async () => {
        setState('loading');
        const params = new URLSearchParams();
        const query = searchInput.value.trim();
        if (query) {
            params.set('title', query);
        }

        try {
            const response = await fetch(`${config.endpoint}?${params.toString()}`);
            if (!response.ok) {
                throw new Error('Portfolio request failed');
            }

            const items = await response.json();
            grid.replaceChildren(...items.map(buildCard));
            if (items.length === 0) {
                emptyState.textContent = query
                    ? 'Tidak ada portfolio dengan judul tersebut.'
                    : 'Belum ada item portofolio yang ditambahkan.';
                setState('empty');
                return;
            }
            setState('ready');
        } catch (error) {
            grid.replaceChildren();
            setState('error');
        }
    };

    let debounceTimer;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(loadPortfolio, 300);
    });
    form.addEventListener('submit', (event) => {
        event.preventDefault();
        clearTimeout(debounceTimer);
        loadPortfolio();
    });

    loadPortfolio();
});