const themeToggle = document.getElementById('theme-toggle');
const root = document.documentElement;
const themeText = document.querySelector('.theme-text');

const currentTheme = localStorage.getItem('theme') || 'dark';
root.setAttribute('data-theme', currentTheme);
updateThemeState(currentTheme);

function updateThemeState(theme) {
    if (themeToggle && themeText) {
        themeToggle.checked = theme === 'light';
        themeText.textContent = theme === 'light' ? 'Light Mode' : 'Dark Mode';
    }
}

if (themeToggle) {
    themeToggle.addEventListener('change', () => {
        const newTheme = themeToggle.checked ? 'light' : 'dark';
        
        root.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeState(newTheme);
    });
}
