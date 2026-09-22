/* =========================================================
   GLOBAL THEME CONTROLLER
========================================================= */

(function () {

    function applyTheme(theme) {
        const isDark = theme === "dark";

        document.body.classList.toggle("dark-mode", isDark);

        const buttons = document.querySelectorAll(
            "#theme-toggle, .theme-toggle"
        );

        buttons.forEach(function (button) {
            button.innerHTML = isDark
                ? "☀️ Light Mode"
                : "🌙 Dark Mode";
            button.setAttribute(
                "aria-label",
                isDark ? "Switch to light mode" : "Switch to dark mode"
            );
        });
    }

    function loadTheme() {
        const savedTheme = localStorage.getItem("theme") || "light";
        applyTheme(savedTheme);
    }

    function toggleTheme() {
        const isDark = document.body.classList.contains("dark-mode");
        const nextTheme = isDark ? "light" : "dark";

        localStorage.setItem("theme", nextTheme);
        applyTheme(nextTheme);
    }

    /* Apply saved theme immediately when this script runs. */
    loadTheme();

    /* Attach to the theme button if the current page has one. */
    document.addEventListener("DOMContentLoaded", function () {

        loadTheme();

        const buttons = document.querySelectorAll(
            "#theme-toggle, .theme-toggle"
        );

        buttons.forEach(function (button) {
            button.addEventListener("click", toggleTheme);
        });

    });

})();
