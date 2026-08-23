// static/js/theme.js
// Shared behaviour loaded via base.html for every page.
// Handles: dark-mode toggle persistence, back-to-top smooth scroll.
(function () {
    // The theme is written in two places on purpose, for as long as the
    // strangler migration runs:
    //   data-theme on <html>  -- daisyUI keys on it, and so does shell.css
    //   .dark-mode on <body>  -- the seven legacy stylesheets still key on it
    // WP-8 retires the second write once no Bootstrap page is left.
    function applyTheme(isDark) {
        document.documentElement.setAttribute(
            'data-theme', isDark ? 'dark' : 'light');
        document.body.classList.toggle('dark-mode', isDark);
    }

    const darkSwitch = document.getElementById('darkSwitch');

    // An inline script in base.html already set data-theme before first paint,
    // so read the decision back from the element rather than recomputing it
    // and risking the two disagreeing.
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    applyTheme(isDark);
    if (darkSwitch) darkSwitch.checked = isDark;

    if (darkSwitch) {
        darkSwitch.addEventListener('change', function () {
            applyTheme(this.checked);
            try {
                localStorage.setItem('darkMode', this.checked);
            } catch (error) {
                // Storage can throw in private mode. The theme still applies
                // for this page view; it just will not survive a reload.
            }
        });
    }

    // Back-to-top button (present only on pages that inject it via
    // {% block page_footer_extra %}, e.g. results.html)
    const backToTop = document.getElementById('back-to-top');
    if (backToTop) {
        backToTop.addEventListener('click', function (e) {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
})();
