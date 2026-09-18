/* ==========================================================================
   ROMANTIC DIGITAL SCRAPBOOK JAVASCRIPT
   Features: Visitor Logging, Canvas Particles, Audio Synthesizer,
   Memory Carousel, Expandable News Article Reader, 3D Flip Cards & Wishes Board.
   ========================================================================== */

/* ==========================================================================
   KONFIGURASI MUSIK
   Pilih sumber lagu:
   - 'mp3'     : pakai file MP3 lokal di static/audio/romantic_bgm.mp3 (PALING AMAN)
   - 'youtube' : pakai link YouTube, isi youtubeVideoId dengan ID 11 karakter.
     Contoh: dari https://www.youtube.com/watch?v=450p7goxZqg
     ambil bagian 11 karakter setelah v= -> '450p7goxZqg'
   CATATAN: beberapa lagu dari music.youtube.com tidak boleh di-embed,
   kalau suaranya tetap tidak muncul, pakai mode 'mp3'.
   ========================================================================== */
const MUSIC_CONFIG = {
    source: 'lovesong.mp3',
    youtubeVideoId: 'Kf5pXDhx5Vc'
};

let _mensivYT = { onReady: null, _readyPending: false };
window.onYouTubeIframeAPIReady = function () {
    if (typeof _mensivYT.onReady === 'function') {
        _mensivYT.onReady();
    } else {
        _mensivYT._readyPending = true;
    }
};

document.addEventListener('DOMContentLoaded', () => {

    /* ==========================================================================
       TEMA TERANG / GELAP (mode manual; default mengikuti perangkat oleh
       inline script di index.html, tersimpan di localStorage)
       ========================================================================== */
    const themeToggleBtn = document.getElementById('themeToggleBtn');

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        try { localStorage.setItem('mensiv-theme', theme); } catch (e) {}
        if (themeToggleBtn) {
            themeToggleBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
    }

    if (themeToggleBtn) {
        const initialTheme =
            document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
        themeToggleBtn.textContent = initialTheme === 'dark' ? '☀️' : '🌙';
        themeToggleBtn.addEventListener('click', () => {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            applyTheme(isDark ? 'light' : 'dark');
        });
    }

    /* Kalau belum pernah pilih manual: ikuti perubahan tema perangkat */
    try {
        const mq = window.matchMedia('(prefers-color-scheme: dark)');
        const onSystemTheme = (e) => {
            let saved = null;
            try { saved = localStorage.getItem('mensiv-theme'); } catch (err) {}
            if (!saved) {
                document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
                if (themeToggleBtn) themeToggleBtn.textContent = e.matches ? '☀️' : '🌙';
            }
        };
        if (mq.addEventListener) mq.addEventListener('change', onSystemTheme);
        else if (mq.addListener) mq.addListener(onSystemTheme);
    } catch (e) {}

    // Global Audio State
    let isAudioPlaying = false;
    let audioContext = null;
    let synthOscillators = [];
    let ytPlayer = null;
    let ytReady = false;
    const bgAudio = document.getElementById('bgAudio');
    const vinylDisk = document.getElementById('vinylDisk');
    const musicStatus = document.getElementById('musicStatus');
    const audioIcon = document.getElementById('audioIcon');
    const toggleAudioBtn = document.getElementById('toggleAudioBtn');

    /* ==========================================================================
       1. HEADER NAVIGATION TAB SWITCHING
       ========================================================================== */
    const navBtns = document.querySelectorAll('.nav-btn');
    
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const targetEl = document.getElementById(targetId);
            
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            if (targetEl) {
                targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

/* ==========================================================================
        2. VISITOR VERIFICATION & GUESTBOOK LOGGING
       ========================================================================== */
    const guestForm = document.getElementById('guestForm');
    const guestModal = document.getElementById('guestModal');
    const visitorNameInput = document.getElementById('visitorName');

    // Kunci scroll halaman selama gate "isi data dulu" masih terbuka,
    // agar isi scrapbook di belakang tidak bisa diintip/di-scroll dulu.
    if (guestModal && !guestModal.classList.contains('hidden')) {
        document.body.style.overflow = 'hidden';
    }

    if (guestForm) {
        const guestSubmitBtn = guestForm.querySelector('button[type="submit"]');

        guestForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = visitorNameInput.value.trim();
            if (!name) return;

            if (guestSubmitBtn) guestSubmitBtn.disabled = true;

            try {
                const response = await fetch('/api/visit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });
                const data = await response.json();
                console.log('Visit Logged:', data);
            } catch (err) {
                console.warn('Logging visit failed, proceeding locally:', err);
            }

            guestModal.classList.add('hidden');
            document.body.style.overflow = '';
            if (guestSubmitBtn) guestSubmitBtn.disabled = false;
            playMusic();
        });
    }

/* ==========================================================================
        3. MUSIC PLAYER (YouTube + Web Audio Synthesizer Fallback)
       ========================================================================== */
    function createYouTubePlayer() {
        if (!window.YT || !window.YT.Player) return;
        try {
            ytPlayer = new YT.Player('ytMusicPlayer', {
                videoId: MUSIC_CONFIG.youtubeVideoId,
                playerVars: {
                    autoplay: 0,
                    controls: 0,
                    loop: 1,
                    playlist: MUSIC_CONFIG.youtubeVideoId,
                    playsinline: 1,
                    rel: 0,
                    mute: 0,
                    origin: window.location.origin
                },
                events: {
                    onReady: () => {
                        ytReady = true;
                        try {
                            ytPlayer.setVolume(80);
                            ytPlayer.unMute();
                        } catch (err) {}
                        console.log('YouTube player siap.');
                    },
                    onStateChange: (e) => {
                        if (e.data === 1) {
                            setPlayingState(true);
                        } else if (e.data === 0 || e.data === 2) {
                            setPlayingState(false);
                        }
                    },
                    onError: () => { ytReady = false; }
                }
            });
        } catch (err) {
            console.error('Gagal membuat player YouTube:', err);
            ytReady = false;
        }
    }

    if (MUSIC_CONFIG.source === 'youtube') {
        _mensivYT.onReady = createYouTubePlayer;
        if (_mensivYT._readyPending) {
            _mensivYT._readyPending = false;
            createYouTubePlayer();
        }
    }

    function playMusic() {
        if (isAudioPlaying) return;

        // Sumber 1: YouTube (mode 'youtube')
        if (MUSIC_CONFIG.source === 'youtube' && ytReady && ytPlayer) {
            try {
                ytPlayer.unMute();
                ytPlayer.setVolume(80);
                ytPlayer.playVideo();
                setTimeout(() => {
                    if (!isAudioPlaying && ytPlayer && ytPlayer.getPlayerState && ytPlayer.getPlayerState() !== 1) {
                        console.log('YouTube tidak mulai berbunyi, pakai fallback synth.');
                        startRomanticSynth();
                    }
                }, 1200);
                return;
            } catch (err) {
                console.log('YouTube play gagal, pakai fallback synth:', err);
            }
        }

        // Sumber 2: file MP3 lokal (mode 'mp3')
        if (bgAudio) {
            try {
                bgAudio.volume = 0.7;
                const p = bgAudio.play();
                if (p !== undefined) {
                    p.then(() => {
                        setPlayingState(true);
                    }).catch(err => {
                        console.log('MP3 gagal diputar, pakai fallback synth:', err);
                        startRomanticSynth();
                        setPlayingState(true);
                    });
                } else {
                    setPlayingState(true);
                }
            } catch (err) {
                startRomanticSynth();
                setPlayingState(true);
            }
            return;
        }

        // Sumber 3: melodi sintetis
        startRomanticSynth();
        setPlayingState(true);
    }

    function pauseMusic() {
        if (bgAudio && !bgAudio.paused) {
            bgAudio.pause();
        }
        if (ytReady && ytPlayer) {
            try { ytPlayer.pauseVideo(); } catch (err) {}
        }
        stopRomanticSynth();
        setPlayingState(false);
    }

    function setPlayingState(playing) {
        isAudioPlaying = playing;
        if (playing) {
            vinylDisk.classList.add('spinning');
            audioIcon.textContent = '⏸️';
            musicStatus.textContent = 'Sedang memutar 🎵';
        } else {
            vinylDisk.classList.remove('spinning');
            audioIcon.textContent = '▶️';
            musicStatus.textContent = 'Klik untuk memutar 🎵';
        }
    }

    if (toggleAudioBtn) {
        toggleAudioBtn.addEventListener('click', () => {
            if (isAudioPlaying) {
                pauseMusic();
            } else {
                playMusic();
            }
        });
    }

    const NOTE_HZ = {
        A3: 220.00, B3: 246.94, C4: 261.63, D4: 293.66, E4: 329.63,
        F4: 349.23, G4: 392.00, A4: 440.00, B4: 493.88, C5: 523.25,
        D5: 587.33, E5: 659.25, F5: 698.46, G5: 783.99, A5: 880.00
    };

    const ROMANTIC_STEPS = [
        { m: 'E5', b: 'A3' }, { m: 'C5', b: 'A3' }, { m: 'A4', b: 'A3' }, { m: 'C5', b: 'A3' },
        { m: 'D5', b: 'B3' }, { m: 'B4', b: 'B3' }, { m: 'G4', b: 'B3' }, { m: 'B4', b: 'B3' },
        { m: 'C5', b: 'A3' }, { m: 'A4', b: 'A3' }, { m: 'F4', b: 'A3' }, { m: 'A4', b: 'A3' },
        { m: 'G4', b: 'E3' }, { m: 'E4', b: 'E3' }, { m: 'D4', b: 'E3' }, { m: 'E4', b: 'E3' }
    ];

    let synthTimer = null;
    let synthStep = 0;

    function startRomanticSynth() {
        if (synthTimer) return;
        try {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            audioContext = new AudioCtx();
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
            synthStep = 0;

            const playStep = () => {
                if (!audioContext) return;
                const t = audioContext.currentTime + 0.05;
                const step = ROMANTIC_STEPS[synthStep % ROMANTIC_STEPS.length];
                playTone(step.m, t, 0.34, 0.12, 'triangle');
                playTone(step.b, t, 0.62, 0.05, 'sine');
                synthStep++;
            };

            playStep();
            synthTimer = setInterval(playStep, 300);
        } catch (e) {
            console.error('Web Audio Synth failed:', e);
        }
    }

    function playTone(note, startTime, dur, vol, type) {
        if (!NOTE_HZ[note] || !audioContext) return;
        try {
            const osc = audioContext.createOscillator();
            const gain = audioContext.createGain();
            osc.type = type;
            osc.frequency.value = NOTE_HZ[note];

            gain.gain.setValueAtTime(0.0001, startTime);
            gain.gain.exponentialRampToValueAtTime(vol, startTime + 0.04);
            gain.gain.exponentialRampToValueAtTime(0.0001, startTime + dur);

            osc.connect(gain);
            gain.connect(audioContext.destination);
            osc.start(startTime);
            osc.stop(startTime + dur + 0.05);
            synthOscillators.push(osc);
        } catch (e) {}
    }

    function stopRomanticSynth() {
        if (synthTimer) {
            clearInterval(synthTimer);
            synthTimer = null;
        }
        synthOscillators.forEach(item => {
            try { item.stop(); } catch (e) {}
        });
        synthOscillators = [];
        if (audioContext && audioContext.state !== 'closed') {
            audioContext.close();
            audioContext = null;
        }
    }

    /* ==========================================================================
       4. MEMORY CAROUSEL SLIDER LOGIC
       ========================================================================== */
    const carouselTrack = document.getElementById('carouselTrack');
    const carouselSlides = document.querySelectorAll('.carousel-slide');
    const prevSlideBtn = document.getElementById('prevSlideBtn');
    const nextSlideBtn = document.getElementById('nextSlideBtn');
    const dotsContainer = document.getElementById('carouselDots');
    const dots = dotsContainer ? dotsContainer.querySelectorAll('.dot') : [];

    let currentSlide = 0;
    const totalSlides = carouselSlides.length;
    let autoSlideTimer = null;

    function goToSlide(index) {
        if (index < 0) index = totalSlides - 1;
        if (index >= totalSlides) index = 0;
        currentSlide = index;

        if (carouselTrack) {
            carouselTrack.style.transform = `translateX(-${currentSlide * 100}%)`;
        }

        dots.forEach((dot, idx) => {
            if (idx === currentSlide) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }

    if (prevSlideBtn && nextSlideBtn) {
        prevSlideBtn.addEventListener('click', () => {
            goToSlide(currentSlide - 1);
            resetAutoSlide();
        });
        nextSlideBtn.addEventListener('click', () => {
            goToSlide(currentSlide + 1);
            resetAutoSlide();
        });
    }

    dots.forEach(dot => {
        dot.addEventListener('click', () => {
            const idx = parseInt(dot.getAttribute('data-index'), 10);
            goToSlide(idx);
            resetAutoSlide();
        });
    });

    function startAutoSlide() {
        if (totalSlides > 1) {
            autoSlideTimer = setInterval(() => {
                goToSlide(currentSlide + 1);
            }, 4500);
        }
    }

    function resetAutoSlide() {
        if (autoSlideTimer) {
            clearInterval(autoSlideTimer);
            startAutoSlide();
        }
    }

    startAutoSlide();

    /* ==========================================================================
       5. 3D FLIP CARDS INTERACTION (CLICK & TAP TO FLIP)
       ========================================================================== */
    const flipCards = document.querySelectorAll('.flip-card');
    flipCards.forEach(card => {
        card.addEventListener('click', (e) => {
            e.stopPropagation();
            card.classList.toggle('flipped');
        });
    });

    /* ==========================================================================
       6. EXPANDABLE NEWS ARTICLE READER MODAL (BACA SELENGKAPNYA)
       ========================================================================== */
    /* Baca Selengkapnya: cerita lengkap tampil melayang di atas kartu (tanpa ubah tata letak) */
    const storyPopup = document.getElementById('storyPopup');
    const storyPopupBackdrop = document.getElementById('storyPopupBackdrop');
    const storyPopupTitle = document.getElementById('storyPopupTitle');
    const storyPopupBody = document.getElementById('storyPopupBody');
    const storyPopupClose = document.getElementById('storyPopupClose');

    function closeStoryPopup() {
        if (!storyPopup) return;
        storyPopup.classList.remove('open');
        if (storyPopupBackdrop) storyPopupBackdrop.classList.add('hidden');
        setTimeout(() => storyPopup.classList.add('hidden'), 250);
    }

    document.querySelectorAll('.btn-read-more').forEach(btn => {
        const card = btn.closest('.news-card');
        if (!card) return;
        const excerpt = card.querySelector('.news-excerpt');

        function hideIfFit() {
            /* Teks pendek yang tidak terpotong -> otomatis tanpa tombol */
            btn.style.display = (excerpt && excerpt.scrollHeight <= excerpt.clientHeight + 2) ? 'none' : '';
        }
        hideIfFit();
        window.addEventListener('resize', hideIfFit);

        btn.addEventListener('click', () => {
            if (!storyPopup || !excerpt) return;

            const rect = card.getBoundingClientRect();
            const titleEl = card.querySelector('.news-title');
            storyPopupTitle.textContent = titleEl ? titleEl.textContent : 'Cerita Kita';
            storyPopupBody.textContent = excerpt.textContent;

            const width = Math.min(rect.width, 480, window.innerWidth - 20);
            const left = Math.max(10, Math.min(rect.left, window.innerWidth - width - 10));
            const top = Math.max(10, Math.min(rect.top + 6, window.innerHeight - 130));
            const maxH = Math.max(180, Math.min(rect.height - 12, window.innerHeight - top - 10));

            storyPopup.style.top = top + 'px';
            storyPopup.style.left = left + 'px';
            storyPopup.style.width = width + 'px';
            storyPopup.style.maxHeight = maxH + 'px';
            storyPopupBody.style.maxHeight = (maxH - 60) + 'px';

            storyPopup.classList.remove('hidden');
            if (storyPopupBackdrop) storyPopupBackdrop.classList.remove('hidden');
            requestAnimationFrame(() => storyPopup.classList.add('open'));
        });
    });

    if (storyPopupClose) {
        storyPopupClose.addEventListener('click', closeStoryPopup);
    }
    if (storyPopupBackdrop) {
        storyPopupBackdrop.addEventListener('click', closeStoryPopup);
    }

    /* ==========================================================================
       7. HTML5 CANVAS PARTICLE SYSTEM
       ========================================================================== */
    const canvas = document.getElementById('particleCanvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;

        window.addEventListener('resize', () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        });

        const particles = [];
        const particleCount = 35;

        class Particle {
            constructor() {
                this.reset();
            }

            reset() {
                this.x = Math.random() * width;
                this.y = Math.random() * -height;
                this.size = 8 + Math.random() * 12;
                this.speedY = 0.8 + Math.random() * 1.5;
                this.speedX = (Math.random() - 0.5) * 0.8;
                this.rotation = Math.random() * Math.PI * 2;
                this.rotationSpeed = (Math.random() - 0.5) * 0.03;
                this.opacity = 0.4 + Math.random() * 0.5;
                this.type = Math.random() > 0.4 ? 'petal' : 'heart';
            }

            update() {
                this.y += this.speedY;
                this.x += Math.sin(this.y * 0.01) + this.speedX;
                this.rotation += this.rotationSpeed;

                if (this.y > height + 20) {
                    this.reset();
                }
            }

            draw() {
                ctx.save();
                ctx.translate(this.x, this.y);
                ctx.rotate(this.rotation);
                ctx.globalAlpha = this.opacity;

                if (this.type === 'petal') {
                    ctx.fillStyle = '#E8A7A1';
                    ctx.beginPath();
                    ctx.moveTo(0, 0);
                    ctx.bezierCurveTo(this.size, -this.size, this.size * 1.5, this.size, 0, this.size * 1.5);
                    ctx.bezierCurveTo(-this.size * 1.5, this.size, -this.size, -this.size, 0, 0);
                    ctx.fill();
                } else {
                    ctx.fillStyle = '#E11D48';
                    ctx.beginPath();
                    const s = this.size * 0.6;
                    ctx.moveTo(0, 0);
                    ctx.bezierCurveTo(-s, -s, -s * 1.5, s * 0.5, 0, s * 1.5);
                    ctx.bezierCurveTo(s * 1.5, s * 0.5, s, -s, 0, 0);
                    ctx.fill();
                }

                ctx.restore();
            }
        }

        for (let i = 0; i < particleCount; i++) {
            particles.push(new Particle());
        }

        function animateParticles() {
            ctx.clearRect(0, 0, width, height);
            particles.forEach(p => {
                p.update();
                p.draw();
            });
            requestAnimationFrame(animateParticles);
        }

        animateParticles();
    }

    /* ==========================================================================
       8. EMOTION SELECTOR & WISHES SUBMISSION
       ========================================================================== */
    const emotionBtns = document.querySelectorAll('.emotion-btn');
    const selectedEmotionInput = document.getElementById('selectedEmotion');

    emotionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            emotionBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedEmotionInput.value = btn.getAttribute('data-emotion');
        });
    });

    const commentForm = document.getElementById('commentForm');
    const commentsList = document.getElementById('commentsList');
    const noCommentsText = document.getElementById('noCommentsText');

    if (commentForm) {
        commentForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const name = document.getElementById('commentName').value.trim();
            const message = document.getElementById('commentMessage').value.trim();
            const emotion = selectedEmotionInput ? selectedEmotionInput.value : '💐';

            if (!name || !message) return;

            try {
                const response = await fetch('/api/comments', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: name,
                        message: message,
                        emotion: emotion
                    })
                });

                const result = await response.json();

                if (result.status === 'success') {
                    const note = document.createElement('div');
                    note.className = 'comment-paper-note';
                    note.style.animation = 'modalPop 0.4s ease';
                    note.innerHTML = `
                        <div class="note-pin">📌</div>
                        <div class="note-header">
                            <span class="note-author">${escapeHtml(name)}</span>
                            <span class="note-emotion">${emotion}</span>
                        </div>
                        <p class="note-message">${escapeHtml(message)}</p>
                        <span class="note-time">Baru saja</span>
                    `;

                    if (noCommentsText) {
                        noCommentsText.remove();
                    }

                    commentsList.prepend(note);
                    document.getElementById('commentMessage').value = '';

                    note.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                } else {
                    alert(result.message || 'Gagal mengirim ucapan. Silakan coba lagi!');
                }
            } catch (err) {
                console.error('Wishes error:', err);
                alert('Gagal mengirim ucapan. Cek pesan error di konsol browser (F12).');
            }
        });
    }

    function escapeHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
});
