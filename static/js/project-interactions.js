document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('project-search-form');
    const searchInput = document.getElementById('project-search-input');
    const categorySelect = document.querySelector('#project-search-form select[name="category"]');
    const sortSelect = document.querySelector('#project-search-form select[name="sort"]');
    const projectGrid = document.getElementById('project-grid');
    const projectCount = document.getElementById('project-count');
    const loadingState = document.getElementById('project-loading');
    const emptyState = document.getElementById('project-empty');
    const errorState = document.getElementById('project-error');
    const clearButton = document.getElementById('clear-project-search');
    const projectModal = document.getElementById('project-modal');
    const openProjectModalButton = document.getElementById('open-project-modal');
    const closeProjectModalButton = document.getElementById('close-project-modal');
    const projectCreateForm = document.getElementById('project-create-form');

    if (!projectGrid) {
        return;
    }

    const projectApiUrl = window.projectAjaxConfig?.projectsEndpoint || '/api/v1/projects/';
    let projectsAbortController;

    const getCookie = (name) => {
        const prefix = `${name}=`;
        const cookie = document.cookie.split(';').map((value) => value.trim())
            .find((value) => value.startsWith(prefix));
        return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : null;
    };

    const apiRequest = async (url, options = {}) => {
        const response = await fetch(url, {
            ...options,
            headers: {
                Accept: 'application/json',
                ...(options.body ? { 'Content-Type': 'application/json' } : {}),
                ...(options.method && options.method !== 'GET'
                    ? { 'X-CSRFToken': getCookie('csrftoken') || window.projectAjaxConfig?.csrfToken || '' }
                    : {}),
                ...options.headers,
            },
        });
        if (response.status === 204) return null;
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            const detail = Object.values(payload).flat()
                .filter((value) => typeof value === 'string').join(' ');
            const error = new Error(detail || `Request failed (HTTP ${response.status}).`);
            error.status = response.status;
            throw error;
        }
        return payload;
    };

    const setProjectState = (state) => {
        if (loadingState) loadingState.hidden = state !== 'loading';
        if (emptyState) emptyState.hidden = state !== 'empty';
        if (errorState) errorState.hidden = state !== 'error';
        projectGrid.hidden = state === 'loading' || state === 'empty' || state === 'error';
    };

    const escapeHtml = (value = '') => String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');

    const buildProjectCard = (project) => {
        const card = document.createElement('article');
        card.className = 'experience-card';
        card.dataset.projectId = project.id;
        card.dataset.category = project.category;
        card.draggable = window.projectAjaxConfig?.canEdit === true;

        const safeProjectId = escapeHtml(project.id || '');
        const safeStarCount = escapeHtml(project.star_count || 0);
        const safeCommentCount = escapeHtml(project.comment_count || 0);
        const commentsUrl = window.projectAjaxConfig?.commentsBaseUrl
            ? window.projectAjaxConfig.commentsBaseUrl.replace('00000000-0000-0000-0000-000000000000', safeProjectId)
            : '#';
        const image = project.project_image_url ? `<img src="${escapeHtml(project.project_image_url)}" alt="Gambar ${escapeHtml(project.title)}" class="project-image">` : '';
        const projectUrl = project.project_url ? `<a href="${escapeHtml(project.project_url)}" class="button">Lihat Project</a>` : '';
        const starLabel = project.is_starred ? '★ Unstar' : '☆ Star';
        const actionButtons = [];

        if (window.projectAjaxConfig && window.projectAjaxConfig.canEdit) {
            actionButtons.push(`<a href="${project.id ? `/projects/${safeProjectId}/update/` : '#'}" class="button button-secondary">Edit</a>`);
        }

        if (window.projectAjaxConfig && window.projectAjaxConfig.canDelete) {
            actionButtons.push(`
                <button type="button" class="button button-danger" data-delete-project-id="${safeProjectId}">
                    Hapus Project
                </button>
            `);
        }

        const starButton = window.projectAjaxConfig?.isAuthenticated
            ? `<button type="button" class="button button-secondary" data-star-project-id="${safeProjectId}">${starLabel} (${safeStarCount})</button>`
            : `<a href="${escapeHtml(window.projectAjaxConfig?.loginUrl || '/login/')}" class="button button-secondary">Login / Register to star (${safeStarCount})</a>`;

        card.innerHTML = `
            ${window.projectAjaxConfig?.canEdit ? '<div class="project-card-header"><span class="drag-handle" draggable="true" aria-label="Geser project" title="Geser project">⋮⋮</span></div>' : ''}
            ${image}
            <h2>${escapeHtml(project.title)}</h2>
            <span class="experience-category">${escapeHtml(project.tech_stack || '')}</span>
            <p class="experience-description">${escapeHtml(project.description || '').replace(/\n/g, '<br>')}</p>
            <div class="project-card-actions">
                <div class="project-actions">
                    ${projectUrl}
                    <span class="star-count">★ ${safeStarCount}</span>
                    ${starButton}
                    ${actionButtons.join('')}
                </div>
            </div>
            <section class="project-comments" data-project-comments="true">
                <button type="button" class="button button-secondary comment-toggle" data-toggle-comments="true" aria-expanded="false">
                    Comments (${safeCommentCount})
                </button>
                <div class="project-comments-panel" data-comments-panel="true" data-comments-url="${commentsUrl}" hidden>
                    <div class="discussion-list" data-discussion-list="true"></div>
                    ${window.projectAjaxConfig?.canComment ? `
                    <form class="discussion-compose-form" data-comment-form="true" action="${commentsUrl}">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${safeCsrfToken}">
                        <label class="visually-hidden" for="comment-${safeProjectId}">Write a comment</label>
                        <textarea id="comment-${safeProjectId}" name="body" rows="2" maxlength="2000" required placeholder="Write a comment..."></textarea>
                        <button type="submit" class="button">Comment</button>
                    </form>` : '<p><a href="/login/">Login</a> to comment.</p>'}
                </div>
            </section>
        `;

        return card;
    };

    const renderProjectList = (projects) => {
        projectGrid.innerHTML = '';

        if (!projects.length) {
            if (emptyState) {
                emptyState.textContent = searchInput && searchInput.value.trim()
                    ? 'Tidak ada project dengan nama tersebut.'
                    : 'Belum ada project yang ditambahkan.';
            }
            if (projectCount) {
                projectCount.textContent = '0';
            }
            setProjectState('empty');
            return;
        }

        projects.forEach((project) => {
            projectGrid.appendChild(buildProjectCard(project));
        });

        if (projectCount) {
            projectCount.textContent = String(projects.length);
        }
        setProjectState('ready');
    };

    const fetchProjects = () => {
        if (projectsAbortController) projectsAbortController.abort();
        projectsAbortController = new AbortController();
        const requestController = projectsAbortController;
        setProjectState('loading');
        const params = new URLSearchParams();
        const searchValue = searchInput ? searchInput.value.trim() : '';
        const categoryValue = categorySelect ? categorySelect.value : '';
        const sortValue = sortSelect ? sortSelect.value : 'position';

        if (searchValue) params.set('title', searchValue);
        if (categoryValue) params.set('category', categoryValue);
        if (sortValue) params.set('sort', sortValue);

        fetch(`${projectApiUrl}?${params.toString()}`, {
            headers: { Accept: 'application/json' },
            signal: requestController.signal,
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Project request failed (HTTP ${response.status}).`);
                }
                return response.json();
            })
            .then((data) => renderProjectList(Array.isArray(data) ? data : []))
            .catch(() => {
                if (requestController.signal.aborted) return;
                projectGrid.innerHTML = '';
                if (projectCount) {
                    projectCount.textContent = '0';
                }
                setProjectState('error');
            });
    };

    let debounceTimer = null;
    const debouncedFetchProjects = () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(fetchProjects, 300);
    };

    if (searchInput) {
        searchInput.addEventListener('input', debouncedFetchProjects);
    }

    if (searchForm) {
        searchForm.addEventListener('submit', (event) => {
            event.preventDefault();
            clearTimeout(debounceTimer);
            fetchProjects();
        });
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', fetchProjects);
    }

    if (sortSelect) {
        sortSelect.addEventListener('change', fetchProjects);
    }

    if (clearButton) {
        clearButton.addEventListener('click', () => {
            if (searchInput) {
                searchInput.value = '';
            }
            if (categorySelect) {
                categorySelect.value = '';
            }
            if (sortSelect) {
                sortSelect.value = 'position';
            }
            fetchProjects();
        });
    }

    const setModalVisibility = (show) => {
        if (!projectModal) return;
        projectModal.classList.toggle('hidden', !show);
    };

    if (openProjectModalButton) {
        openProjectModalButton.addEventListener('click', () => setModalVisibility(true));
    }

    if (closeProjectModalButton) {
        closeProjectModalButton.addEventListener('click', () => setModalVisibility(false));
    }

    if (projectModal) {
        projectModal.addEventListener('click', (event) => {
            if (event.target && event.target.dataset && event.target.dataset.closeProjectModal !== undefined) {
                setModalVisibility(false);
            }
        });
    }

    if (projectCreateForm) {
        projectCreateForm.addEventListener('submit', (event) => {
            event.preventDefault();

            const formData = new FormData(projectCreateForm);
            const payload = Object.fromEntries(
                ['title', 'description', 'tech_stack', 'project_url', 'project_image_url']
                    .map((name) => [name, formData.get(name)]),
            );
            const endpoint = window.projectAjaxConfig?.createProjectEndpoint || projectCreateForm.action;
            apiRequest(endpoint, {
                method: 'POST',
                body: JSON.stringify(payload),
            })
            .then(() => {
                projectCreateForm.querySelectorAll('[data-error-for]').forEach((fieldError) => {
                    fieldError.textContent = '';
                });
                projectCreateForm.reset();
                setModalVisibility(false);
                fetchProjects();
                if (window.showToast) {
                    window.showToast('Berhasil', 'Project berhasil ditambahkan!', 'success');
                }
            })
            .catch((error) => {
                if (window.showToast) {
                    window.showToast('Gagal', error.message || 'Tidak dapat terhubung ke server. Silakan coba lagi.', 'error');
                }
            });
        });
    }

    projectGrid.addEventListener('click', (event) => {
        const starButton = event.target.closest('[data-star-project-id]');
        if (starButton) {
            if (!window.projectAjaxConfig?.isAuthenticated) {
                window.location.assign(window.projectAjaxConfig?.loginUrl || '/login/');
                return;
            }
            const endpoint = window.projectAjaxConfig.starProjectEndpoint.replace(
                '00000000-0000-0000-0000-000000000000', starButton.dataset.starProjectId,
            );
            starButton.disabled = true;
            apiRequest(endpoint, { method: 'POST' })
                .then(() => fetchProjects())
                .then(() => window.showToast?.('Berhasil', 'Status star diperbarui.', 'success'))
                .catch((error) => {
                    if (error.status === 403 && !window.projectAjaxConfig?.isAuthenticated) {
                        window.location.assign(window.projectAjaxConfig?.loginUrl || '/login/');
                        return;
                    }
                    window.showToast?.('Gagal', error.message, 'error');
                })
                .finally(() => { starButton.disabled = false; });
            return;
        }

        const deleteButton = event.target.closest('[data-delete-project-id]');
        if (!deleteButton) {
            return;
        }

        const projectId = deleteButton.dataset.deleteProjectId;
        if (!projectId || !window.confirm('Hapus project ini?')) {
            return;
        }

        const endpoint = window.projectAjaxConfig.detailProjectEndpoint.replace(
            '00000000-0000-0000-0000-000000000000',
            projectId,
        );

        deleteButton.disabled = true;
        apiRequest(endpoint, { method: 'DELETE' })
            .then(() => {
                if (window.showToast) {
                    window.showToast('Berhasil', 'Project berhasil dihapus.', 'success');
                }
                fetchProjects();
            })
            .catch((error) => {
                deleteButton.disabled = false;
                if (window.showToast) {
                    window.showToast('Gagal', error.message || 'Tidak dapat menghapus project.', 'error');
                }
            });
    });

    let draggedItemId = null;

    projectGrid.addEventListener('dragstart', (event) => {
        const card = event.target.closest('.experience-card');
        if (!card || !card.draggable) return;
        draggedItemId = card.dataset.projectId;
        card.classList.add('dragging');
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', draggedItemId);
    });

    projectGrid.addEventListener('dragover', (event) => {
        const card = event.target.closest('.experience-card');
        if (!card || !draggedItemId || !card.draggable) return;
        event.preventDefault();
        card.classList.add('drag-over');
    });

    projectGrid.addEventListener('dragleave', (event) => {
        const card = event.target.closest('.experience-card');
        if (card && !card.contains(event.relatedTarget)) card.classList.remove('drag-over');
    });

    projectGrid.addEventListener('drop', (event) => {
        const targetCard = event.target.closest('.experience-card');
        if (!targetCard || !draggedItemId || !targetCard.draggable) return;
        event.preventDefault();
        targetCard.classList.remove('drag-over');

        if (draggedItemId === targetCard.dataset.projectId) return;

        const cardsAfterReorder = Array.from(projectGrid.querySelectorAll('.experience-card'));
        const sourceIndex = cardsAfterReorder.findIndex((item) => item.dataset.projectId === draggedItemId);
        const targetIndex = cardsAfterReorder.findIndex((item) => item.dataset.projectId === targetCard.dataset.projectId);
        if (sourceIndex === -1 || targetIndex === -1) return;

        const [movedCard] = cardsAfterReorder.splice(sourceIndex, 1);
        cardsAfterReorder.splice(targetIndex, 0, movedCard);
        cardsAfterReorder.forEach((item) => projectGrid.appendChild(item));

        const params = new URLSearchParams();
        cardsAfterReorder.forEach((card) => params.append('project_ids[]', card.dataset.projectId));
        fetch(window.projectAjaxConfig?.orderEndpoint || '/projects/reorder/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-CSRFToken': window.projectOrderCsrf || getCookie('csrftoken') || '',
            },
            body: params.toString(),
        }).then((response) => {
            if (!response.ok) throw new Error('Could not save project order.');
        }).catch(() => {
            window.location.reload();
        });
    });

    projectGrid.addEventListener('dragend', (event) => {
        const card = event.target.closest('.experience-card');
        if (card) card.classList.remove('dragging');
        draggedItemId = null;
        projectGrid.querySelectorAll('.experience-card').forEach((item) => {
            item.classList.remove('drag-over');
        });
    });

    if (searchInput && !searchInput.dataset.ajaxBound) {
        searchInput.dataset.ajaxBound = 'true';
    }
    if (clearButton && !clearButton.dataset.ajaxBound) {
        clearButton.dataset.ajaxBound = 'true';
    }
    if (categorySelect && !categorySelect.dataset.ajaxBound) {
        categorySelect.dataset.ajaxBound = 'true';
    }
    if (sortSelect && !sortSelect.dataset.ajaxBound) {
        sortSelect.dataset.ajaxBound = 'true';
    }

    fetchProjects();
});
