/* ════════════════════════════════════════════════════
   CyberSentinel — Interactive JavaScript
   ════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════
   🔧 CONFIGURATION — Change your GitHub repo here!
   ═══════════════════════════════════════════════════ */
const GITHUB_REPO = 'yourusername/cybersentinel';
// ↑ Change this to your actual GitHub username/repo
//   e.g. 'Jaex10x/CyberSentinel'

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initDownloadLinks();
    initTerminalAnimation();
    initDemoKeylogger();
    initDemoTimer();
    initDemoResources();
    initScrollAnimations();
});

/* ─── Download Links ─── */
function initDownloadLinks() {
    const repoUrl = `https://github.com/${GITHUB_REPO}`;
    const zipUrl = `${repoUrl}/archive/refs/heads/main.zip`;
    const cloneUrl = `https://github.com/${GITHUB_REPO}.git`;

    // Hero download button → direct ZIP download
    const heroBtn = document.getElementById('heroDownloadBtn');
    if (heroBtn) {
        heroBtn.href = zipUrl;
        heroBtn.setAttribute('target', '_blank');
        heroBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Don't trigger smooth scroll
        });
    }

    // Download section buttons
    const zipBtn = document.getElementById('downloadZipBtn');
    if (zipBtn) {
        zipBtn.href = zipUrl;
        zipBtn.setAttribute('target', '_blank');
    }

    const githubBtn = document.getElementById('downloadGithubBtn');
    if (githubBtn) {
        githubBtn.href = repoUrl;
        githubBtn.setAttribute('target', '_blank');
    }

    // Clone command text
    const cloneCmd = document.getElementById('cloneCmd');
    if (cloneCmd) {
        cloneCmd.textContent = `git clone ${cloneUrl}`;
    }

    // Install section clone command
    document.querySelectorAll('.install__code-block code').forEach(code => {
        if (code.textContent.includes('yourusername')) {
            code.textContent = `git clone ${cloneUrl}`;
        }
    });
}

/* ─── Navigation ─── */
function initNavigation() {
    const nav = document.getElementById('nav');
    const hamburger = document.getElementById('hamburger');
    const mobileMenu = document.getElementById('mobileMenu');

    // Scroll detection for nav background
    window.addEventListener('scroll', () => {
        nav.classList.toggle('scrolled', window.scrollY > 50);
    });

    // Hamburger menu toggle
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        mobileMenu.classList.toggle('open');
    });

    // Close mobile menu on link click
    mobileMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            mobileMenu.classList.remove('open');
        });
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(anchor.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

/* ─── Terminal Animation ─── */
function initTerminalAnimation() {
    const terminalBody = document.getElementById('terminalBody');
    if (!terminalBody) return;

    const lines = [
        { text: '', delay: 300 },
        { text: '   ______      __              _____            __  _            __', class: 'terminal__line--accent', delay: 50 },
        { text: '  / ____/_  __/ /_  ___  _____/ ___/___  ____  / /_(_)___  ___  / /', class: 'terminal__line--accent', delay: 50 },
        { text: ' / /   / / / / __ \\/ _ \\/ ___/\\__ \\/ _ \\/ __ \\/ __/ / __ \\/ _ \\/ /', class: 'terminal__line--accent', delay: 50 },
        { text: '/ /___/ /_/ / /_/ /  __/ /   ___/ /  __/ / / / /_/ / / / /  __/ /', class: 'terminal__line--accent', delay: 50 },
        { text: '\\____/\\__, /_.___/\\___/_/   /____/\\___/_/ /_/\\__/_/_/ /_/\\___/_/', class: 'terminal__line--accent', delay: 50 },
        { text: '     /____/', class: 'terminal__line--accent', delay: 300 },
        { text: '', delay: 100 },
        { text: '  Ethical Keystroke Monitoring Suite  •  v1.0.0', class: 'terminal__line--dim', delay: 500 },
        { text: '', delay: 100 },
        { text: '🔐 Do you accept the terms? [y/n]: y', class: 'terminal__line--warning', delay: 800 },
        { text: '✅ Consent granted. Session authorized.', class: 'terminal__line--success', delay: 500 },
        { text: '', delay: 200 },
        { text: '🚀 Starting monitoring modules...', class: 'terminal__line--accent', delay: 400 },
        { text: '  ✓ Keystroke engine started', class: 'terminal__line--success', delay: 300 },
        { text: '  ✓ Clipboard monitor started', class: 'terminal__line--success', delay: 300 },
        { text: '  ✓ Screenshot capture started', class: 'terminal__line--success', delay: 300 },
        { text: '  ✓ AES-256 encryption active', class: 'terminal__line--success', delay: 500 },
        { text: '', delay: 200 },
        { text: '📊 Launching live dashboard...', class: 'terminal__line--accent', delay: 600 },
        { text: '  ● MONITORING ACTIVE', class: 'terminal__line--success', delay: 0 },
    ];

    let lineIndex = 0;

    function addLine() {
        if (lineIndex >= lines.length) {
            // Restart after a pause
            setTimeout(() => {
                // Keep only the first command line
                terminalBody.innerHTML = '<div class="terminal__line"><span class="terminal__prompt">$</span> python main.py --mode monitor</div>';
                lineIndex = 0;
                addLine();
            }, 4000);
            return;
        }

        const lineData = lines[lineIndex];
        const div = document.createElement('div');
        div.className = `terminal__line ${lineData.class || ''}`;
        div.textContent = lineData.text;

        // Typing effect for command lines
        if (lineData.text.includes('$')) {
            div.innerHTML = `<span class="terminal__prompt">$</span> ${lineData.text.replace('$ ', '')}`;
        }

        terminalBody.appendChild(div);
        terminalBody.scrollTop = terminalBody.scrollHeight;
        lineIndex++;
        setTimeout(addLine, lineData.delay);
    }

    // Start animation after a brief delay
    setTimeout(addLine, 1500);
}

/* ─── Demo Keylogger ─── */
function initDemoKeylogger() {
    const keystrokePanel = document.getElementById('keystrokePanel');
    const keyCountBadge = document.getElementById('keyCount');
    const statTotalKeys = document.getElementById('statTotalKeys');
    const statKPM = document.getElementById('statKPM');

    if (!keystrokePanel) return;

    let totalKeys = 0;
    let startTime = null;
    let placeholder = keystrokePanel.querySelector('.demo__placeholder');

    // Special key mapping
    const specialKeys = {
        ' ': { text: '·', class: 'key-space' },
        'Enter': { text: ' ↵\n', class: 'key-enter' },
        'Backspace': { text: '⌫', class: 'key-backspace' },
        'Tab': { text: '[TAB]', class: 'key-special' },
        'Shift': { text: '', class: '' },
        'Control': { text: '', class: '' },
        'Alt': { text: '', class: '' },
        'Meta': { text: '', class: '' },
        'CapsLock': { text: '[CAPS]', class: 'key-special' },
        'Escape': { text: '[ESC]', class: 'key-special' },
        'ArrowUp': { text: '[↑]', class: 'key-special' },
        'ArrowDown': { text: '[↓]', class: 'key-special' },
        'ArrowLeft': { text: '[←]', class: 'key-special' },
        'ArrowRight': { text: '[→]', class: 'key-special' },
        'Delete': { text: '[DEL]', class: 'key-special' },
    };

    document.addEventListener('keydown', (e) => {
        // Remove placeholder on first key
        if (placeholder) {
            placeholder.remove();
            placeholder = null;
        }

        if (!startTime) startTime = Date.now();

        const special = specialKeys[e.key];
        let span = document.createElement('span');

        if (special) {
            if (!special.text) return; // Skip modifier-only keys
            span.className = special.class;
            if (e.key === 'Enter') {
                span.innerHTML = ' ↵<br>';
            } else {
                span.textContent = special.text;
            }
        } else if (e.key.length === 1) {
            span.className = 'key-char';
            span.textContent = e.key;
        } else {
            // Function keys, etc.
            span.className = 'key-special';
            span.textContent = `[${e.key.toUpperCase()}]`;
        }

        keystrokePanel.appendChild(span);
        totalKeys++;

        // Update stats
        keyCountBadge.textContent = `${totalKeys} keys`;
        statTotalKeys.textContent = totalKeys.toLocaleString();

        // Calculate KPM
        const elapsed = (Date.now() - startTime) / 60000; // minutes
        if (elapsed > 0) {
            statKPM.textContent = (totalKeys / elapsed).toFixed(1);
        }

        // Auto-scroll
        keystrokePanel.scrollTop = keystrokePanel.scrollHeight;

        // Flash effect on panel header
        const header = keystrokePanel.closest('.demo__panel').querySelector('.demo__panel-header');
        header.style.background = 'rgba(0, 212, 255, 0.1)';
        setTimeout(() => {
            header.style.background = 'rgba(255, 255, 255, 0.02)';
        }, 100);
    });
}

/* ─── Demo Timer ─── */
function initDemoTimer() {
    const timerEl = document.getElementById('demoTimer');
    const dateEl = document.getElementById('demoDate');

    if (!timerEl || !dateEl) return;

    let seconds = 0;

    function updateTimer() {
        const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
        const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        timerEl.textContent = `⏱ ${h}:${m}:${s}`;
        seconds++;
    }

    function updateDate() {
        const now = new Date();
        dateEl.textContent = `📅 ${now.toLocaleDateString()} ${now.toLocaleTimeString()}`;
    }

    updateTimer();
    updateDate();
    setInterval(updateTimer, 1000);
    setInterval(updateDate, 1000);
}

/* ─── Demo Resource Bars ─── */
function initDemoResources() {
    const cpuBar = document.getElementById('cpuBar');
    const cpuVal = document.getElementById('cpuVal');
    const ramBar = document.getElementById('ramBar');
    const ramVal = document.getElementById('ramVal');

    if (!cpuBar) return;

    function simulateResources() {
        // Simulate fluctuating CPU
        const cpu = Math.floor(15 + Math.random() * 30);
        cpuBar.style.width = `${cpu}%`;
        cpuVal.textContent = `${cpu}%`;

        // Simulate slowly changing RAM
        const ram = Math.floor(50 + Math.random() * 20);
        ramBar.style.width = `${ram}%`;
        ramVal.textContent = `${ram}%`;
    }

    setInterval(simulateResources, 3000);
}

/* ─── Scroll Animations ─── */
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px',
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Optional: unobserve after animation
                // observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements with data-aos attribute
    document.querySelectorAll('[data-aos]').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = `opacity 0.6s ease ${el.dataset.aosDelay || 0}ms, transform 0.6s ease ${el.dataset.aosDelay || 0}ms`;
        observer.observe(el);
    });

    // Also animate section headers
    document.querySelectorAll('.section-header, .feature-card, .arch__card, .mode-card, .ethical__card, .install__step, .download__card').forEach(el => {
        if (!el.dataset.aos) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(el);
        }
    });
}

// Visibility class for scroll animations
document.head.insertAdjacentHTML('beforeend', `
    <style>
        .visible {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    </style>
`);

/* ─── Copy Code ─── */
function copyCode(button) {
    const codeBlock = button.parentElement.querySelector('code');
    const text = codeBlock.textContent;

    navigator.clipboard.writeText(text).then(() => {
        const original = button.textContent;
        button.textContent = '✅';
        setTimeout(() => {
            button.textContent = original;
        }, 2000);
    }).catch(() => {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        button.textContent = '✅';
        setTimeout(() => {
            button.textContent = '📋';
        }, 2000);
    });
}
