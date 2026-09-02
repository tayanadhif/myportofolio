const body = document.body;
const toggleButton = document.querySelector('.theme-toggle');
const toggleIcon = document.querySelector('.theme-toggle__icon');

const applyTheme = (theme) => {
    const isDark = theme === 'dark';
    body.classList.toggle('dark-mode', isDark);
    if (toggleIcon) {
        toggleIcon.textContent = isDark ? '☀️' : '🌙';
    }
    if (toggleButton) {
        toggleButton.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
    }
};

const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    applyTheme(savedTheme);
} else {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(prefersDark ? 'dark' : 'light');
}

if (toggleButton) {
    toggleButton.addEventListener('click', () => {
        const nextTheme = body.classList.contains('dark-mode') ? 'light' : 'dark';
        localStorage.setItem('theme', nextTheme);
        applyTheme(nextTheme);
    });
}
