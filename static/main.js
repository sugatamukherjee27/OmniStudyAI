document.addEventListener("DOMContentLoaded", () => {
    // ---- Ambient animated network background (signature futuristic element) ----
    const canvas = document.createElement("canvas");
    canvas.id = "bg-canvas";
    document.body.prepend(canvas);
    const ctx = canvas.getContext("2d");

    let width, height, particles;
    const PARTICLE_COUNT = 70;
    const LINK_DIST = 130;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }

    function initParticles() {
        particles = Array.from({ length: PARTICLE_COUNT }, () => ({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.35,
            vy: (Math.random() - 0.5) * 0.35,
        }));
    }

    function step() {
        ctx.clearRect(0, 0, width, height);

        for (const p of particles) {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0 || p.x > width) p.vx *= -1;
            if (p.y < 0 || p.y > height) p.vy *= -1;
        }

        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const a = particles[i], b = particles[j];
                const dx = a.x - b.x, dy = a.y - b.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < LINK_DIST) {
                    ctx.strokeStyle = `rgba(0, 229, 255, ${0.12 * (1 - dist / LINK_DIST)})`;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(a.x, a.y);
                    ctx.lineTo(b.x, b.y);
                    ctx.stroke();
                }
            }
        }

        for (const p of particles) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 1.6, 0, Math.PI * 2);
            ctx.fillStyle = "rgba(0, 229, 255, 0.55)";
            ctx.fill();
        }

        if (!reduceMotion) requestAnimationFrame(step);
    }

    resize();
    initParticles();
    if (!reduceMotion) {
        requestAnimationFrame(step);
    } else {
        step();
    }
    window.addEventListener("resize", () => {
        resize();
        initParticles();
    });

    // ---- Ripple effect on all buttons ----
    document.querySelectorAll(".btn").forEach((btn) => {
        btn.addEventListener("click", function (e) {
            const rect = btn.getBoundingClientRect();
            const ripple = document.createElement("span");
            const size = Math.max(rect.width, rect.height);
            ripple.className = "ripple";
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
            ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
            btn.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });

    // Auto-dismiss Flash notifications after 5 seconds
    setTimeout(() => {
        document.querySelectorAll(".flash-msg").forEach(el => {
            el.style.transition = "opacity 0.5s ease";
            el.style.opacity = "0";
            setTimeout(() => el.remove(), 500);
        });
    }, 5000);

    // Interactive File Upload Box
    const fileInput = document.getElementById("audio_file");
    const dropzone = document.getElementById("file-dropzone");
    const fileNameDisplay = document.getElementById("file-name-display");

    if (fileInput && dropzone) {
        dropzone.addEventListener("click", () => fileInput.click());

        fileInput.addEventListener("change", (e) => {
            if (e.target.files && e.target.files.length > 0) {
                fileNameDisplay.textContent = `Selected: ${e.target.files[0].name}`;
                dropzone.style.borderColor = "#00e5ff";
            }
        });

        dropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropzone.style.backgroundColor = "rgba(0, 229, 255, 0.08)";
        });

        dropzone.addEventListener("dragleave", () => {
            dropzone.style.backgroundColor = "";
        });

        dropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropzone.style.backgroundColor = "";
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                fileNameDisplay.textContent = `Selected: ${fileInput.files[0].name}`;
                dropzone.style.borderColor = "#00e5ff";
            }
        });
    }

    // AI Processing Spinner Overlay
    const promptForm = document.getElementById("prompt-form");
    const loaderOverlay = document.getElementById("loader-overlay");
    const loaderTitle = document.getElementById("loader-title");
    const loaderSubtitle = document.getElementById("loader-subtitle");

    const DOC_EXTENSIONS = ["pdf", "docx", "doc"];
    const AUDIO_VIDEO_EXTENSIONS = ["mp3", "mp4", "wav", "m4a", "mov", "avi", "webm", "ogg", "aac", "flac", "mkv"];

    function getLoaderMessage(file) {
        if (!file) {
            return { title: "AI Synthesizing Content...", subtitle: "Analyzing your text & generating output" };
        }
        const ext = file.name.split(".").pop().toLowerCase();
        if (DOC_EXTENSIONS.includes(ext)) {
            return { title: "Extracting Text...", subtitle: "Reading your document & preparing content" };
        }
        if (AUDIO_VIDEO_EXTENSIONS.includes(ext) || file.type.startsWith("audio/") || file.type.startsWith("video/")) {
            return { title: "Transcribing Audio...", subtitle: "Converting speech to text & analyzing structure" };
        }
        return { title: "AI Synthesizing Content...", subtitle: "Transcribing audio & analyzing structure" };
    }

    if (promptForm && loaderOverlay) {
        promptForm.addEventListener("submit", () => {
            const file = fileInput && fileInput.files && fileInput.files.length > 0 ? fileInput.files[0] : null;
            const { title, subtitle } = getLoaderMessage(file);
            if (loaderTitle) loaderTitle.textContent = title;
            if (loaderSubtitle) loaderSubtitle.textContent = subtitle;
            loaderOverlay.style.display = "flex";
        });
    }
});