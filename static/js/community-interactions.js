document.addEventListener('DOMContentLoaded', () => {
    const csrfToken = window.projectAjaxConfig?.csrfToken || window.communityChatConfig?.csrfToken || '';

    const showFailure = (message) => {
        if (window.showToast) {
            window.showToast('Gagal', message, 'error');
        }
    };

    const showSuccess = (message) => {
        if (window.showToast) {
            window.showToast('Berhasil', message, 'success');
        }
    };

    const sendForm = async (url, values) => {
        const body = new URLSearchParams(values);
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            },
            body: body.toString(),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(payload.message || 'Request failed.');
        }
        return payload;
    };

    const createDiscussionItem = (item, refresh) => {
        const row = document.createElement('article');
        row.className = 'discussion-item';

        const heading = document.createElement('div');
        heading.className = 'discussion-item-heading';
        const memberLink = document.createElement('a');
        memberLink.href = `/members/${encodeURIComponent(item.username)}/`;
        memberLink.textContent = item.username;
        const timestamp = document.createElement('time');
        timestamp.textContent = item.created_at;
        heading.append(memberLink, timestamp);

        const body = document.createElement('p');
        body.className = 'discussion-item-body';
        body.textContent = item.body;
        row.append(heading, body);

        if (item.can_edit) {
            const actions = document.createElement('div');
            actions.className = 'discussion-item-actions';
            const editButton = document.createElement('button');
            editButton.type = 'button';
            editButton.className = 'discussion-action-button';
            editButton.textContent = 'Edit';
            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'discussion-action-button discussion-action-danger';
            deleteButton.textContent = 'Delete';
            actions.append(editButton, deleteButton);
            row.appendChild(actions);

            editButton.addEventListener('click', () => {
                const editor = document.createElement('form');
                editor.className = 'discussion-edit-form';
                const input = document.createElement('textarea');
                input.maxLength = 2000;
                input.required = true;
                input.value = item.body;
                const saveButton = document.createElement('button');
                saveButton.type = 'submit';
                saveButton.className = 'button';
                saveButton.textContent = 'Save';
                const cancelButton = document.createElement('button');
                cancelButton.type = 'button';
                cancelButton.className = 'button button-secondary';
                cancelButton.textContent = 'Cancel';
                editor.append(input, saveButton, cancelButton);
                body.replaceWith(editor);
                actions.hidden = true;

                cancelButton.addEventListener('click', () => refresh());
                editor.addEventListener('submit', async (event) => {
                    event.preventDefault();
                    try {
                        await sendForm(item.url, { action: 'edit', body: input.value });
                        showSuccess('Your message was updated.');
                        await refresh();
                    } catch (error) {
                        showFailure(error.message);
                    }
                });
            });

            deleteButton.addEventListener('click', async () => {
                if (!window.confirm('Delete your message?')) return;
                try {
                    await sendForm(item.url, { action: 'delete' });
                    showSuccess('Your message was deleted.');
                    await refresh();
                } catch (error) {
                    showFailure(error.message);
                }
            });
        }
        return row;
    };

    const renderDiscussion = (container, items, refresh) => {
        container.replaceChildren();
        if (!items.length) {
            const empty = document.createElement('p');
            empty.className = 'discussion-empty';
            empty.textContent = 'No messages yet.';
            container.appendChild(empty);
            return;
        }
        items.forEach((item) => container.appendChild(createDiscussionItem(item, refresh)));
    };

    const loadComments = async (panel) => {
        const list = panel.querySelector('[data-discussion-list]');
        const toggle = panel.closest('[data-project-comments]')?.querySelector('[data-toggle-comments]');
        try {
            const response = await fetch(panel.dataset.commentsUrl);
            if (!response.ok) throw new Error('Could not load comments.');
            const comments = await response.json();
            const refresh = () => loadComments(panel);
            renderDiscussion(list, comments, refresh);
            if (toggle) toggle.textContent = `Comments (${comments.length})`;
        } catch (error) {
            list.textContent = error.message;
        }
    };

    document.addEventListener('click', (event) => {
        const toggle = event.target.closest('[data-toggle-comments]');
        if (!toggle) return;
        const panel = toggle.closest('[data-project-comments]')?.querySelector('[data-comments-panel]');
        if (!panel) return;
        const isOpen = panel.hidden;
        panel.hidden = !isOpen;
        toggle.setAttribute('aria-expanded', String(isOpen));
        if (isOpen) loadComments(panel);
    });

    document.addEventListener('submit', async (event) => {
        const commentForm = event.target.closest('[data-comment-form]');
        if (!commentForm) return;
        event.preventDefault();
        const input = commentForm.elements.body;
        try {
            await sendForm(commentForm.action, { body: input.value });
            input.value = '';
            showSuccess('Comment added.');
            await loadComments(commentForm.closest('[data-comments-panel]'));
        } catch (error) {
            showFailure(error.message);
        }
    });

    const chatList = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    if (!chatList || !chatForm || !window.communityChatConfig) return;

    const chatUrl = window.communityChatConfig.listUrl;
    const chatInput = document.getElementById('chat-message-input');
    const chatError = document.getElementById('chat-error');
    let lastChatSnapshot = '';

    const refreshChat = async () => {
        try {
            const response = await fetch(chatUrl);
            if (!response.ok) throw new Error('Could not load community messages.');
            const messages = await response.json();
            const snapshot = JSON.stringify(messages);
            if (snapshot !== lastChatSnapshot) {
                lastChatSnapshot = snapshot;
                renderDiscussion(chatList, messages, refreshChat);
                const scrollParent = chatList;
                scrollParent.scrollTop = scrollParent.scrollHeight;
            }
            if (chatError) chatError.hidden = true;
        } catch (error) {
            if (chatError) {
                chatError.textContent = error.message;
                chatError.hidden = false;
            }
        }
    };

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
            await sendForm(chatUrl, { body: chatInput.value });
            chatInput.value = '';
            showSuccess('Message sent.');
            await refreshChat();
        } catch (error) {
            showFailure(error.message);
        }
    });

    refreshChat();
    window.setInterval(refreshChat, 4000);
});
