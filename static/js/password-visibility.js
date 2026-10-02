document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[type="password"]').forEach((passwordInput) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'password-visibility-control';
        passwordInput.parentNode.insertBefore(wrapper, passwordInput);
        wrapper.appendChild(passwordInput);

        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'password-visibility-toggle';
        toggleButton.textContent = 'Show';
        toggleButton.setAttribute('aria-label', 'Show password');
        toggleButton.setAttribute('aria-pressed', 'false');
        wrapper.appendChild(toggleButton);

        toggleButton.addEventListener('click', () => {
            const showPassword = passwordInput.type === 'password';
            passwordInput.type = showPassword ? 'text' : 'password';
            toggleButton.textContent = showPassword ? 'Hide' : 'Show';
            toggleButton.setAttribute('aria-label', `${showPassword ? 'Hide' : 'Show'} password`);
            toggleButton.setAttribute('aria-pressed', String(showPassword));
        });
    });
});
