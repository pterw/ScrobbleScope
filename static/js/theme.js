// static/js/theme.js
// Shared behaviour loaded via base.html for every page.
// Handles: dark-mode toggle persistence, back-to-top smooth scroll.
(function () {
    // Dark-mode toggle
    const darkSwitch = document.getElementById('darkSwitch');
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
        if (darkSwitch) darkSwitch.checked = true;
    }
    if (darkSwitch) {
        darkSwitch.addEventListener('change', function () {
            document.body.classList.toggle('dark-mode', this.checked);
            localStorage.setItem('darkMode', this.checked);
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
