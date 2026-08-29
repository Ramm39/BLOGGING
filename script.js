/**
 * BudhiWorks - Core Client-side JavaScript
 * Handles active navigation, theme switching, mobile drawer menu, form validation, and live searching.
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initActiveNav();
  initMobileNav();
  initContactForm();
  initArticleSearch();
});

/**
 * 1. Theme Switcher with LocalStorage Persistence
 */
function initThemeToggle() {
  const toggleBtn = document.getElementById('themeToggleBtn');
  const colorSchemeMeta = document.querySelector('meta[name="color-scheme"]');

  // Load saved theme or default to system/dark
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    applyTheme(savedTheme);
  } else {
    // Default to dark mode for BudhiWorks aesthetic
    applyTheme('dark');
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('theme', newTheme);
    });
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (colorSchemeMeta) {
      colorSchemeMeta.content = theme;
    }
    if (toggleBtn) {
      toggleBtn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
      toggleBtn.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`);
    }
  }
}

/**
 * 2. Active Navigation Highlight
 */
function initActiveNav() {
  const currentPath = window.location.pathname.replace(/\/$/, '') || '/index.html';
  const navLinks = document.querySelectorAll('.nav-link');

  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;

    // Standardize comparison
    const targetPath = new URL(href, window.location.href).pathname.replace(/\/$/, '');
    
    if (currentPath === targetPath || (currentPath.endsWith('index.html') && targetPath.endsWith('index.html'))) {
      link.classList.add('active');
    } else if (currentPath === '' && (targetPath.endsWith('index.html') || targetPath === '')) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
}

/**
 * 3. Mobile Navigation Drawer Toggle
 */
function initMobileNav() {
  const mobileToggle = document.getElementById('mobileNavToggle');
  const navLinksContainer = document.getElementById('navLinks');

  if (mobileToggle && navLinksContainer) {
    mobileToggle.addEventListener('click', () => {
      const isOpen = navLinksContainer.classList.toggle('active');
      mobileToggle.setAttribute('aria-expanded', isOpen.toString());
      mobileToggle.innerHTML = isOpen ? '✕' : '☰';
    });

    // Close menu when clicking outside or resizing
    document.addEventListener('click', (e) => {
      if (!mobileToggle.contains(e.target) && !navLinksContainer.contains(e.target)) {
        navLinksContainer.classList.remove('active');
        mobileToggle.setAttribute('aria-expanded', 'false');
        mobileToggle.innerHTML = '☰';
      }
    });
  }
}

/**
 * 4. Contact Form Validation & Handling
 */
function initContactForm() {
  const contactForm = document.getElementById('contactForm');
  const alertContainer = document.getElementById('formAlert');

  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const name = document.getElementById('name')?.value.trim();
      const email = document.getElementById('email')?.value.trim();
      const subject = document.getElementById('subject')?.value.trim();
      const message = document.getElementById('message')?.value.trim();

      if (!name || !email || !subject || !message) {
        showAlert('Please fill in all required fields.', 'error');
        return;
      }

      if (!isValidEmail(email)) {
        showAlert('Please enter a valid email address.', 'error');
        return;
      }

      const body = `From: ${name} <${email}>\n\n${message}`;
      const mailto = `mailto:contact@budhiworks.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      window.location.href = mailto;
      showAlert('Opening your email client to send the message to contact@budhiworks.com. If nothing opens, email that address directly.', 'success');
    });
  }

  function showAlert(msg, type) {
    if (!alertContainer) return;
    alertContainer.textContent = msg;
    alertContainer.className = `form-alert ${type}`;
    alertContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
}

/**
 * 5. Article Filter & Search
 */
function initArticleSearch() {
  const searchInput = document.getElementById('articleSearchInput');
  const articleCards = document.querySelectorAll('.article-card');
  const filterButtons = document.querySelectorAll('.filter-btn');
  let activeFilter = 'all';

  if (articleCards.length === 0) return;

  function applyFilters() {
    const query = (searchInput?.value || '').toLowerCase().trim();

    articleCards.forEach(card => {
      const title = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
      const excerpt = card.querySelector('.card-excerpt')?.textContent.toLowerCase() || '';
      const category = card.getAttribute('data-category') || '';
      const categoryLabel = card.querySelector('.badge')?.textContent.toLowerCase() || '';
      const matchesFilter = activeFilter === 'all' || category === activeFilter;
      const matchesQuery =
        !query ||
        title.includes(query) ||
        excerpt.includes(query) ||
        categoryLabel.includes(query) ||
        category.toLowerCase().includes(query);

      card.style.display = matchesFilter && matchesQuery ? 'flex' : 'none';
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', applyFilters);
  }

  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      filterButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeFilter = btn.getAttribute('data-filter') || 'all';
      applyFilters();
    });
  });
}
