document.addEventListener('DOMContentLoaded', () => {
    const csrfToken = window.projectAjaxConfig?.csrfToken || window.communityChatConfig?.csrfToken || '';

    document.addEventListener('click', (event) => {
        const pendingGoogleButton = event.target.closest('[data-google-login-pending]');
        if (!pendingGoogleButton) return;
        if (window.showToast) {
            window.showToast(
                'Google sign-in is not configured',
                'Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in the server environment first.',
                'error',
                6000,
            );
        }
    });

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

    const createDiscussionItem = (item, refresh, collectionUrl, canReply) => {
        const row = document.createElement('article');
        row.className = 'discussion-item';

        const heading = document.createElement('div');
        heading.className = 'discussion-item-heading';

        const memberInfo = document.createElement('div');
        memberInfo.className = 'discussion-member-info';

        const avatar = document.createElement('div');
        avatar.className = 'discussion-avatar';

        if (item.profile_image_url) {
            const avatarImage = document.createElement('img');
            avatarImage.src = item.profile_image_url;
            avatarImage.alt = `Profile picture for ${item.username}`;
            avatar.appendChild(avatarImage);
        } else {
            avatar.textContent = item.username.charAt(0).toUpperCase();
        }

        const memberLink = document.createElement('a');
        memberLink.href = `/members/${encodeURIComponent(item.username)}/`;
        memberLink.textContent = item.username;

        memberInfo.append(avatar, memberLink);

        const timestamp = document.createElement('time');
        timestamp.textContent = item.created_at;

        heading.append(memberInfo, timestamp);

        const body = document.createElement('p');
        body.className = 'discussion-item-body';
        body.textContent = item.body;
        if (item.reply_to) {
            const replyContext = document.createElement('p');
            replyContext.className = 'discussion-reply-context';
            replyContext.textContent = `Reply to @${item.reply_to.username}: ${item.reply_to.body}`;
            row.append(heading, replyContext, body);
        } else {
            row.append(heading, body);
        }

        if (item.can_edit || canReply) {
            const actions = document.createElement('div');
            actions.className = 'discussion-item-actions';
            let editButton;
            let deleteButton;
            if (item.can_edit) {
                editButton = document.createElement('button');
                editButton.type = 'button';
                editButton.className = 'discussion-action-button';
                editButton.textContent = 'Edit';
                deleteButton = document.createElement('button');
                deleteButton.type = 'button';
                deleteButton.className = 'discussion-action-button discussion-action-danger';
                deleteButton.textContent = 'Delete';
                actions.append(editButton, deleteButton);
            }
            let replyButton;
            if (canReply) {
                replyButton = document.createElement('button');
                replyButton.type = 'button';
                replyButton.className = 'discussion-action-button';
                replyButton.textContent = 'Reply';
                actions.appendChild(replyButton);
            }
            row.appendChild(actions);

            editButton?.addEventListener('click', () => {
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

            deleteButton?.addEventListener('click', async () => {
                if (!window.confirm('Delete your message?')) return;
                try {
                    await sendForm(item.url, { action: 'delete' });
                    showSuccess('Your message was deleted.');
                    await refresh();
                } catch (error) {
                    showFailure(error.message);
                }
            });

            replyButton?.addEventListener('click', () => {
                const replyForm = document.createElement('form');
                replyForm.className = 'discussion-reply-form';
                const target = document.createElement('p');
                target.className = 'discussion-reply-target';
                target.textContent = `Replying to @${item.username}`;
                const input = document.createElement('textarea');
                input.maxLength = 2000;
                input.required = true;
                input.placeholder = 'Write a reply...';
                const submit = document.createElement('button');
                submit.type = 'submit';
                submit.className = 'button';
                submit.textContent = 'Send Reply';
                const cancel = document.createElement('button');
                cancel.type = 'button';
                cancel.className = 'button button-secondary';
                cancel.textContent = 'Cancel';
                replyForm.append(target, input, submit, cancel);
                row.appendChild(replyForm);
                replyButton.disabled = true;
                cancel.addEventListener('click', () => replyForm.remove());
                replyForm.addEventListener('submit', async (event) => {
                    event.preventDefault();
                    try {
                        const result = await sendForm(collectionUrl, { body: input.value, reply_to: item.id });
                        showSuccess(result.email_sent
                            ? 'Reply sent; an email notification was queued.'
                            : 'Reply saved, but its email notification could not be sent.');
                        await refresh();
                    } catch (error) {
                        showFailure(error.message);
                    }
                });
            });
        }
        return row;
    };

    const renderDiscussion = (container, items, refresh, collectionUrl, canReply) => {
        container.replaceChildren();
        if (!items.length) {
            const empty = document.createElement('p');
            empty.className = 'discussion-empty';
            empty.textContent = 'No messages yet.';
            container.appendChild(empty);
            return;
        }
        items.forEach((item) => container.appendChild(createDiscussionItem(item, refresh, collectionUrl, canReply)));
    };

    const loadComments = async (panel) => {
        const list = panel.querySelector('[data-discussion-list]');
        const toggle = panel.closest('[data-project-comments]')?.querySelector('[data-toggle-comments]');
        try {
            const response = await fetch(panel.dataset.commentsUrl);
            if (!response.ok) throw new Error('Could not load comments.');
            const comments = await response.json();
            const refresh = () => loadComments(panel);
            renderDiscussion(list, comments, refresh, panel.dataset.commentsUrl, Boolean(window.projectAjaxConfig?.canComment));
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
                renderDiscussion(chatList, messages, refreshChat, chatUrl, 
                    Boolean(window.communityChatConfig?.isAuthenticated));
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
