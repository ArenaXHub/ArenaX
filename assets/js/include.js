document.addEventListener("DOMContentLoaded", function() {
    const navElement = document.getElementById('navbar');
    if (!navElement) return;

    // 1. Fetch and inject the navbar structure
    fetch('/partials/navbar.html')
        .then(response => response.text())
        .then(data => {
            navElement.innerHTML = data;
            renderDynamicNav();
        });
});

function renderDynamicNav() {
    const body = document.body;
    const logoImg = document.getElementById('nav-logo-img');
    const navList = document.getElementById('dynamic-nav-list');

    if (body.classList.contains('event-page')) {
        // EVENT PAGE CONFIGURATION
        logoImg.src = "/assets/image/Xbadminton.jpg";
        navList.innerHTML = `
            <li><a href="/" class="nav-link">HOME</a></li>
            <li><a href="#overview" class="nav-link">DETAILS</a></li>
            <li><a href="#certificate" class="nav-link">CERTIFICATION</a></li>
            <li><a href="https://forms.gle/yy6FWAuHSe1KSzyd9" class="nav-link nav-register-btn">REGISTER</a></li>
        `;
    } else {
        // MASTER BRAND CONFIGURATION (Home/About)
        logoImg.src = "/assets/image/brand_symbol.png";
        navList.innerHTML = `
            <li><a href="/" class="nav-link">Home</a></li>
            <li><a href="#method" class="nav-link">The Method</a></li>
            <li><a href="/events" class="nav-link">Events</a></li>
        `;
    }
}