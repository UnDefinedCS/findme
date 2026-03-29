const themeToggle = document.getElementById('theme-toggle');
const root = document.documentElement;
const themeText = document.querySelector('.theme-text');

// Prevent transition animation on initial page load
root.style.transition = 'none';

const currentTheme = localStorage.getItem('theme') || 'dark';
root.setAttribute('data-theme', currentTheme);
updateThemeState(currentTheme);

// Re-enable transitions after initial load
setTimeout(() => {
    root.style.transition = '';
}, 50);

function updateThemeState(theme) {
    if (themeText) {
        themeText.textContent = theme === 'light' ? 'Light Mode' : 'Dark Mode';
    }
}

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const currentTheme = root.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        root.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeState(newTheme);
    });
}
