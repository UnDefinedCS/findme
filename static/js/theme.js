const themeToggle = document.getElementById('theme-toggle');
const root = document.documentElement;
const themeIcon = document.querySelector('.theme-icon');

const currentTheme = localStorage.getItem('theme') || 'dark';
root.setAttribute('data-theme', currentTheme);
updateThemeIcon(currentTheme);

function updateThemeIcon(theme) {
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '\u2600\uFE0F' : '\u{1F319}';
    }
}

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const theme = root.getAttribute('data-theme');
        const newTheme = theme === 'dark' ? 'light' : 'dark';
        
        root.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}
