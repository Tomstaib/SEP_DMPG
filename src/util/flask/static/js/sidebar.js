// static/sidebar.js
function toggleSidebar() {
    var sidebar = document.getElementById("sidebar");
    var topbar = document.getElementById("topbar");
    var mainContent = document.getElementById("main-content");

    sidebar.classList.toggle("collapsed");
    topbar.classList.toggle("collapsed");
    mainContent.classList.toggle("collapsed");
}
