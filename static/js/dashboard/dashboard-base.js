// Dashboard Base JavaScript
document.addEventListener('DOMContentLoaded', function () {
    // Sidebar toggle functionality
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const profileButton = document.getElementById('profileButton');
    const profileMenu = document.getElementById('profileMenu');
    const navItems = document.querySelectorAll('.nav-item');

    // Load sidebar state from localStorage
    const sidebarState = localStorage.getItem('sidebarCollapsed');
    if (sidebarState === 'true') {
        sidebar.classList.add('collapsed');
    }

    // Toggle sidebar
    sidebarToggle?.addEventListener('click', function () {
        sidebar.classList.toggle('collapsed');
        const isCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebarCollapsed', isCollapsed);

        // Update toggle icon
        const icon = sidebarToggle.querySelector('i');
        if (icon) {
            if (isCollapsed) {
                icon.className = 'ti ti-layout-sidebar-left-expand';
            } else {
                icon.className = 'ti ti-layout-sidebar-right-expand';
            }
        }

        // Close profile menu when collapsing
        if (isCollapsed && profileMenu) {
            profileMenu.classList.remove('active');
            profileButton.classList.remove('active');
        }
    });

    // Profile dropdown functionality
    profileButton?.addEventListener('click', function (e) {
        e.stopPropagation();
        profileMenu.classList.toggle('active');
        profileButton.classList.toggle('active');
    });

    // Close profile menu when clicking outside
    document.addEventListener('click', function (e) {
        if (profileMenu && !profileMenu.contains(e.target) && !profileButton.contains(e.target)) {
            profileMenu.classList.remove('active');
            profileButton.classList.remove('active');
        }
    });

    // Prevent menu from closing when clicking inside it
    profileMenu?.addEventListener('click', function (e) {
        e.stopPropagation();
    });

    // Mobile menu functionality
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    let sidebarOverlay = document.querySelector('.sidebar-overlay');

    // Create overlay if it doesn't exist
    if (!sidebarOverlay) {
        sidebarOverlay = document.createElement('div');
        sidebarOverlay.className = 'sidebar-overlay';
        document.body.appendChild(sidebarOverlay);
    }

    // Mobile menu toggle handler
    function toggleMobileSidebar() {
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('mobile-open');
            sidebarOverlay.classList.toggle('active');

            // Toggle mobile header visibility
            const mobileHeader = document.querySelector('.mobile-header');
            if (mobileHeader) {
                mobileHeader.classList.toggle('sidebar-open');
            }

            // Update mobile menu icon
            const icon = mobileMenuToggle?.querySelector('i');
            if (icon) {
                if (sidebar.classList.contains('mobile-open')) {
                    icon.className = 'ti ti-x';
                } else {
                    icon.className = 'ti ti-menu-2';
                }
            }

            // Prevent body scroll when sidebar is open
            document.body.style.overflow = sidebar.classList.contains('mobile-open') ? 'hidden' : '';
        }
    }

    // Close mobile sidebar
    function closeMobileSidebar() {
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('mobile-open');
            sidebarOverlay.classList.remove('active');
            document.body.style.overflow = '';

            // Show mobile header again
            const mobileHeader = document.querySelector('.mobile-header');
            if (mobileHeader) {
                mobileHeader.classList.remove('sidebar-open');
            }

            const icon = mobileMenuToggle?.querySelector('i');
            if (icon) {
                icon.className = 'ti ti-menu-2';
            }
        }
    }

    // Mobile menu toggle event
    mobileMenuToggle?.addEventListener('click', toggleMobileSidebar);

    // Close sidebar when clicking overlay
    sidebarOverlay.addEventListener('click', closeMobileSidebar);

    // Close sidebar when clicking nav items on mobile
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                closeMobileSidebar();
            }
        });
    });

    // Handle active navigation items
    const currentPath = window.location.pathname;

    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href === currentPath) {
            item.classList.add('active');
        }
    });

    // Add keyboard shortcuts
    document.addEventListener('keydown', function (e) {
        // Alt + S to toggle sidebar (desktop) or Escape to close mobile sidebar
        if (e.altKey && e.key === 's' && window.innerWidth > 768) {
            e.preventDefault();
            sidebarToggle?.click();
        }

        // Escape to close mobile sidebar or profile menu
        if (e.key === 'Escape') {
            if (window.innerWidth <= 768 && sidebar.classList.contains('mobile-open')) {
                closeMobileSidebar();
            } else if (profileMenu?.classList.contains('active')) {
                profileMenu.classList.remove('active');
                profileButton.classList.remove('active');
            }
        }
    });

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            if (window.innerWidth <= 768) {
                // Mobile: ensure sidebar is closed and remove collapsed state
                closeMobileSidebar();
                sidebar.classList.remove('collapsed');
            } else {
                // Desktop: close mobile sidebar and restore collapsed state
                closeMobileSidebar();

                // Restore collapsed state from localStorage on desktop
                const savedState = localStorage.getItem('sidebarCollapsed');
                if (savedState === 'true') {
                    sidebar.classList.add('collapsed');
                }
            }
        }, 250);
    });

    // Initialize Tippy.js tooltips for collapsed sidebar
    let tippyInstances = [];

    function initializeTooltips() {
        // Destroy existing instances
        tippyInstances.forEach(instance => instance.destroy());
        tippyInstances = [];

        // Only create tooltips if sidebar is collapsed
        if (sidebar.classList.contains('collapsed')) {
            const navItems = document.querySelectorAll('.nav-item[data-tooltip]');

            navItems.forEach(item => {
                const instance = tippy(item, {
                    content: item.getAttribute('data-tooltip'),
                    placement: 'right',
                    offset: [0, 12],
                    theme: 'dark',
                    animation: 'fade',
                    duration: [200, 150],
                    delay: [300, 0],
                    arrow: true,
                    hideOnClick: false,
                    trigger: 'mouseenter focus',
                    zIndex: 10000,
                    appendTo: 'parent'
                });
                tippyInstances.push(instance);
            });
        }
    }

    // Initialize tooltips on load if collapsed
    initializeTooltips();

    // Reinitialize tooltips when sidebar is toggled
    const originalToggleHandler = sidebarToggle?.onclick;
    sidebarToggle?.addEventListener('click', function () {
        // Wait for the transition to complete
        setTimeout(() => {
            initializeTooltips();
        }, 350); // Slightly longer than CSS transition
    });
});
