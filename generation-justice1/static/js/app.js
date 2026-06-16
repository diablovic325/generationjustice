const state = {
    user: null,
    canModerateComments: false,
};

const loginPresets = {
    member: {
        title: "Member Login",
        titleKey: "login.member.title",
        help: "For students, lawyers, and project members.",
        helpKey: "login.member.help",
        email: "demo@generationjustice.org",
        password: "demo123",
        hint: "Member demo: demo@generationjustice.org / demo123",
        hintKey: "login.member.hint",
        redirect: "/hub",
    },
    organizer: {
        title: "Organizer Login",
        titleKey: "login.organizer.title",
        help: "For organizers who moderate comments and support project activity.",
        helpKey: "login.organizer.help",
        email: "organizer@generationjustice.org",
        password: "organizer123",
        hint: "Organizer demo: organizer@generationjustice.org / organizer123",
        hintKey: "login.organizer.hint",
        redirect: "/comments",
    },
    admin: {
        title: "Admin Login",
        titleKey: "login.admin.title",
        help: "For main project administrators and leadership accounts.",
        helpKey: "login.admin.help",
        email: "admin@generationjustice.org",
        password: "admin123",
        hint: "Admin demo: admin@generationjustice.org / admin123",
        hintKey: "login.admin.hint",
        redirect: "/hub",
    },
};

function qs(selector, root = document) {
    return root.querySelector(selector);
}

function qsa(selector, root = document) {
    return Array.from(root.querySelectorAll(selector));
}

function t(key, fallback = "") {
    return window.gjI18n?.t(key, fallback) || fallback;
}

function setStatus(element, message, type = "ok") {
    if (!element) return;
    element.textContent = message;
    element.className = "status show " + type;
}

function clearStatus(element) {
    if (!element) return;
    element.textContent = "";
    element.className = "status";
}

async function postJson(url, data) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
    const payload = await response.json();
    if (!response.ok) {
        throw new Error(payload.detail || "Request failed.");
    }
    return payload;
}

async function deleteJson(url) {
    const response = await fetch(url, { method: "DELETE" });
    const payload = await response.json();
    if (!response.ok) {
        throw new Error(payload.detail || "Request failed.");
    }
    return payload;
}

function setLoginMode(mode = "member") {
    const preset = loginPresets[mode] || loginPresets.member;
    const modal = qs("#loginModal");
    if (modal) modal.dataset.loginMode = mode;
    if (qs("#loginTitle")) qs("#loginTitle").textContent = t(preset.titleKey, preset.title);
    if (qs("#loginHelp")) qs("#loginHelp").textContent = t(preset.helpKey, preset.help);
    if (qs("#loginEmail")) qs("#loginEmail").value = preset.email;
    if (qs("#loginPassword")) qs("#loginPassword").value = preset.password;
    if (qs("#loginDemoHint")) qs("#loginDemoHint").textContent = t(preset.hintKey, preset.hint);
}

function openLogin(mode = "member") {
    const modal = qs("#loginModal");
    if (!modal) return;
    setLoginMode(mode);
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
}

function closeLogin() {
    const modal = qs("#loginModal");
    if (!modal) return;
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
}

function updateAuthUI(user) {
    state.user = user;
    state.canModerateComments = Boolean(user?.can_moderate_comments);
    const chip = qs("#memberChip");
    const logoutButton = qs("#logoutButton");
    const loginButtons = qsa("[data-login-mode]");

    if (user) {
        if (chip) {
            chip.textContent = user.membership + " Member";
            chip.classList.add("show");
        }
        loginButtons.forEach((button) => button.classList.add("hidden"));
        logoutButton?.classList.remove("hidden");
        const commentName = qs("#commentName");
        if (commentName && !commentName.value) commentName.value = user.name;
    } else {
        chip?.classList.remove("show");
        loginButtons.forEach((button) => button.classList.remove("hidden"));
        logoutButton?.classList.add("hidden");
    }
    syncCommentModerationButtons();
}

async function loadCurrentUser() {
    try {
        const response = await fetch("/api/me");
        const payload = await response.json();
        updateAuthUI(payload.user);
    } catch {
        updateAuthUI(null);
    }
}

function maybeOpenLogin(error) {
    if (error.message.toLowerCase().includes("log in") || error.message.toLowerCase().includes("apply")) {
        openLogin("member");
    }
}

function createDeleteCommentButton(commentId) {
    const button = document.createElement("button");
    button.className = "danger-button delete-comment";
    button.type = "button";
    button.dataset.commentId = commentId;
    button.textContent = "Delete Comment";
    return button;
}

function syncCommentModerationButtons() {
    qsa(".comment").forEach((comment) => {
        const existing = qs(".delete-comment", comment);
        if (state.canModerateComments && comment.dataset.commentId && !existing) {
            comment.appendChild(createDeleteCommentButton(comment.dataset.commentId));
        }
        if (!state.canModerateComments && existing) {
            existing.remove();
        }
    });
}

function makeComment(comment) {
    const item = document.createElement("article");
    item.className = "comment";
    item.dataset.commentId = comment.id;
    item.innerHTML = "<strong></strong><small></small><p></p>";
    qs("strong", item).textContent = comment.user_name;
    qs("small", item).textContent = comment.created_at;
    qs("p", item).textContent = comment.text;
    if (state.canModerateComments) {
        item.appendChild(createDeleteCommentButton(comment.id));
    }
    return item;
}

function makeBroadcast(broadcast) {
    const item = document.createElement("article");
    item.className = "broadcast-item";
    item.innerHTML = "<strong></strong><span></span><small></small>";
    qs("strong", item).textContent = broadcast.title;
    qs("span", item).textContent = broadcast.message;
    qs("small", item).textContent =
        broadcast.target + " - " + broadcast.status + " - " + broadcast.created_at + " - by " + broadcast.created_by;
    return item;
}

function makeMiniItem(item, textKey = "summary") {
    const article = document.createElement("article");
    article.className = "mini-item";
    article.innerHTML = "<strong></strong><small></small><p></p>";
    qs("strong", article).textContent = item.title || item.country || "Submission";
    qs("small", article).textContent = (item.submitted_at || "") + " - " + (item.status || "");
    qs("p", article).textContent = item[textKey] || item.summary || item.abstract || item.motivation || "";
    return article;
}

function makeReply(reply) {
    const item = document.createElement("article");
    item.className = "reply";
    item.innerHTML = "<strong></strong><small></small><p></p>";
    qs("strong", item).textContent = reply.created_by;
    qs("small", item).textContent = reply.created_at;
    qs("p", item).textContent = reply.body;
    return item;
}

function makeTopic(topic) {
    const item = document.createElement("article");
    item.className = "discussion-topic";
    item.dataset.topicId = topic.id;
    item.innerHTML = `
        <div class="topic-head">
            <div>
                <h2></h2>
                <small></small>
            </div>
        </div>
        <p class="topic-body"></p>
        <div class="reply-list"></div>
        <form class="reply-form">
            <label>
                Reply with a detailed comment
                <textarea name="replyBody" placeholder="Write a thoughtful reply..." required></textarea>
            </label>
            <button class="button secondary" type="submit">Post Reply</button>
            <div class="status"></div>
        </form>
    `;
    qs("h2", item).textContent = topic.title;
    qs("small", item).textContent = "Started by " + topic.created_by + " - " + topic.created_at;
    qs(".topic-body", item).textContent = topic.body;
    qsa(".reply-form", item).forEach((form) => {
        form.dataset.topicId = topic.id;
    });
    return item;
}

function showBroadcastBanner(broadcast) {
    const host = qs("#liveBroadcastBannerHost");
    if (!host) return;
    host.innerHTML = "";
    const banner = document.createElement("section");
    banner.className = "broadcast-strip";
    banner.id = "liveBroadcastBanner";
    banner.innerHTML = "<strong></strong><span></span><small></small>";
    qs("strong", banner).textContent = broadcast.title;
    qs("span", banner).textContent = broadcast.message;
    qs("small", banner).textContent = broadcast.target + " - by " + broadcast.created_by;
    host.appendChild(banner);
}

function bindLogin() {
    qsa("[data-login-mode]").forEach((button) => {
        button.addEventListener("click", () => openLogin(button.dataset.loginMode));
    });
    qsa("[data-open-login]").forEach((button) => button.addEventListener("click", () => openLogin("member")));
    qs("#closeLoginButton")?.addEventListener("click", closeLogin);

    qs("#loginModal")?.addEventListener("click", (event) => {
        if (event.target.id === "loginModal") closeLogin();
    });

    qs("#loginForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const status = qs("#loginStatus");
        clearStatus(status);
        try {
            const payload = await postJson("/api/login", {
                email: qs("#loginEmail").value,
                password: qs("#loginPassword").value,
            });
            updateAuthUI(payload.user);
            setStatus(status, payload.message);
            setTimeout(() => {
                const mode = qs("#loginModal")?.dataset.loginMode || "member";
                const redirect = loginPresets[mode]?.redirect || "/hub";
                closeLogin();
                if (mode === "organizer" || mode === "admin" || location.pathname === "/membership") {
                    location.href = redirect;
                }
            }, 700);
        } catch (error) {
            setStatus(status, error.message, "error");
        }
    });

    qs("#logoutButton")?.addEventListener("click", async () => {
        await postJson("/api/logout", {});
        updateAuthUI(null);
        location.href = "/";
    });

    window.addEventListener("gj:languagechange", () => {
        const modal = qs("#loginModal");
        if (modal?.classList.contains("open")) {
            setLoginMode(modal.dataset.loginMode || "member");
        }
    });
}

function bindCarousels() {
    qsa("[data-carousel]").forEach((carousel) => {
        const track = qs(".carousel-track", carousel);
        const slides = qsa("[data-carousel-slide]", carousel);
        const dotsHost = qs("[data-carousel-dots]", carousel);
        if (!track || slides.length === 0) return;

        let activeIndex = 0;
        let timer = null;
        const interval = Number(carousel.dataset.carouselInterval || 6500);
        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        function renderDots() {
            if (!dotsHost) return;
            dotsHost.innerHTML = "";
            slides.forEach((_, index) => {
                const dot = document.createElement("button");
                dot.className = "carousel-dot";
                dot.type = "button";
                dot.setAttribute("aria-label", t("carousel.goToSlide", "Go to slide") + " " + (index + 1));
                dot.addEventListener("click", () => {
                    goToSlide(index);
                    restart();
                });
                dotsHost.appendChild(dot);
            });
        }

        function goToSlide(index) {
            activeIndex = (index + slides.length) % slides.length;
            track.style.setProperty("--carousel-index", activeIndex);
            slides.forEach((slide, slideIndex) => {
                const isActive = slideIndex === activeIndex;
                slide.classList.toggle("is-active", isActive);
                slide.setAttribute("aria-hidden", String(!isActive));
            });
            (dotsHost ? qsa(".carousel-dot", dotsHost) : []).forEach((dot, dotIndex) => {
                dot.classList.toggle("is-active", dotIndex === activeIndex);
                dot.setAttribute("aria-current", dotIndex === activeIndex ? "true" : "false");
            });
        }

        function stop() {
            if (timer) window.clearInterval(timer);
            timer = null;
        }

        function start() {
            if (reduceMotion || slides.length < 2 || timer) return;
            timer = window.setInterval(() => goToSlide(activeIndex + 1), interval);
        }

        function restart() {
            stop();
            start();
        }

        qs("[data-carousel-prev]", carousel)?.addEventListener("click", () => {
            goToSlide(activeIndex - 1);
            restart();
        });
        qs("[data-carousel-next]", carousel)?.addEventListener("click", () => {
            goToSlide(activeIndex + 1);
            restart();
        });
        carousel.addEventListener("mouseenter", stop);
        carousel.addEventListener("mouseleave", start);
        carousel.addEventListener("focusin", stop);
        carousel.addEventListener("focusout", start);
        window.addEventListener("gj:languagechange", () => {
            renderDots();
            goToSlide(activeIndex);
        });

        renderDots();
        goToSlide(0);
        start();
    });
}

function bindDonation() {
    const widget = qs("[data-donation-widget]");
    if (!widget) return;

    const customAmount = qs("#customDonationAmount", widget);
    const selectedFrequency = qs("#selectedDonationFrequency", widget);
    const selectedTier = qs("#selectedDonationTier", widget);
    const selectedAmount = qs("#selectedDonationAmount", widget);
    const status = qs("#donationStatus", widget);

    function setActive(buttons, activeButton) {
        buttons.forEach((button) => button.classList.toggle("is-active", button === activeButton));
    }

    qsa("[data-donation-frequency]", widget).forEach((button) => {
        button.addEventListener("click", () => {
            selectedFrequency.value = button.dataset.donationFrequency;
            setActive(qsa("[data-donation-frequency]", widget), button);
            clearStatus(status);
        });
    });

    qsa("[data-donation-tier]", widget).forEach((button) => {
        button.addEventListener("click", () => {
            selectedTier.value = button.dataset.donationTier;
            selectedAmount.value = button.dataset.donationAmount;
            customAmount.value = "";
            setActive(qsa("[data-donation-tier]", widget), button);
            clearStatus(status);
        });
    });

    customAmount?.addEventListener("input", () => {
        const value = Number(customAmount.value);
        if (value > 0) {
            selectedTier.value = "custom";
            selectedAmount.value = String(value);
            qsa("[data-donation-tier]", widget).forEach((button) => button.classList.remove("is-active"));
        }
        clearStatus(status);
    });

    qs("#donationPreviewForm", widget)?.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearStatus(status);
        try {
            const payload = await postJson("/api/donations/preview", {
                frequency: selectedFrequency.value,
                tier: selectedTier.value,
                amount: Number(selectedAmount.value),
            });
            setStatus(status, payload.message || t("donate.status.prepared", "Donation preview prepared. Payments are not active yet."));
        } catch (error) {
            setStatus(status, error.message, "error");
        }
    });
}

function bindApplication() {
    qs("#applicationForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const status = qs("#applicationStatus");
        clearStatus(status);
        try {
            const payload = await postJson("/api/apply", {
                name: qs("#applyName").value,
                address: qs("#applyAddress").value,
                city: qs("#applyCity").value,
                country: qs("#applyCountry").value,
                email: qs("#applyEmail").value,
                phone: qs("#applyPhone").value,
                organization: qs("#applyOrganization").value,
                password: qs("#applyPassword").value,
                membership: qs("#applyMembership").value,
                interests: qs("#applyInterests").value,
            });
            updateAuthUI(payload.user);
            setStatus(status, payload.message);
            const certificate = qs("#applicationCertificate");
            if (certificate) {
                certificate.classList.remove("hidden");
                qs("#certificateNamePreview").textContent = payload.user.name;
                qs("#certificateNumberPreview").textContent = payload.user.registration_number;
            }
        } catch (error) {
            setStatus(status, error.message, "error");
        }
    });
}

function bindComments() {
    qs("#commentForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const status = qs("#commentStatus");
        clearStatus(status);
        try {
            const payload = await postJson("/api/comments", {
                name: qs("#commentName")?.value || "",
                text: qs("#commentText").value,
            });
            qs("#commentList")?.prepend(makeComment(payload.comment));
            qs("#commentText").value = "";
            setStatus(status, "Comment posted.");
        } catch (error) {
            setStatus(status, error.message, "error");
            maybeOpenLogin(error);
        }
    });

    qs("#commentList")?.addEventListener("click", async (event) => {
        const button = event.target.closest(".delete-comment");
        if (!button) return;
        const commentId = button.dataset.commentId;
        const comment = button.closest(".comment");
        button.disabled = true;
        try {
            await deleteJson("/api/comments/" + commentId);
            comment?.remove();
        } catch (error) {
            button.disabled = false;
            alert(error.message);
            maybeOpenLogin(error);
        }
    });
}

function bindDiscussions() {
    qs("#topicForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const status = qs("#topicStatus");
        clearStatus(status);
        try {
            const payload = await postJson("/api/discussions/topics", {
                title: qs("#topicTitle").value,
                body: qs("#topicBody").value,
            });
            qs("#discussionList")?.prepend(makeTopic(payload.topic));
            event.target.reset();
            setStatus(status, "Discussion topic launched.");
        } catch (error) {
            setStatus(status, error.message, "error");
            maybeOpenLogin(error);
        }
    });

    qs("#discussionList")?.addEventListener("submit", async (event) => {
        if (!event.target.classList.contains("reply-form")) return;
        event.preventDefault();
        const form = event.target;
        const status = qs(".status", form);
        clearStatus(status);
        try {
            const payload = await postJson("/api/discussions/replies", {
                topic_id: Number(form.dataset.topicId),
                body: qs("textarea", form).value,
            });
            form.closest(".discussion-topic").querySelector(".reply-list").appendChild(makeReply(payload.reply));
            form.reset();
            setStatus(status, "Reply posted.");
        } catch (error) {
            setStatus(status, error.message, "error");
            maybeOpenLogin(error);
        }
    });
}

function bindEssays() {
    qs("#essayForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const status = qs("#essayStatus");
        clearStatus(status);
        try {
            const payload = await postJson("/api/essays", {
                title: qs("#essayTitle").value,
                country: qs("#essayCountry").value,
                summary: qs("#essaySummary").value,
            });
            qs("#essaySubmissionList")?.prepend(makeMiniItem(payload.entry, "summary"));
            event.target.reset();
            setStatus(status, payload.message);
        } catch (error) {
            setStatus(status, error.message, "error");
            maybeOpenLogin(error);
        }
    });
}

function bindArticles() {
    qs("#articleForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const status = qs("#articleStatus");
        clearStatus(status);
        try {
            const payload = await postJson("/api/articles", {
                title: qs("#articleTitle").value,
                category: qs("#articleCategory").value,
                abstract: qs("#articleAbstract").value,
            });
            qs("#articleSubmissionList")?.prepend(makeMiniItem(payload.article, "abstract"));
            event.target.reset();
            setStatus(status, payload.message);
        } catch (error) {
            setStatus(status, error.message, "error");
            maybeOpenLogin(error);
        }
    });
}

function bindInternships() {
    qs("#internshipForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const status = qs("#internshipStatus");
        clearStatus(status);
        try {
            const payload = await postJson("/api/internships/apply", {
                project_id: Number(qs("#internshipProject").value),
                motivation: qs("#internshipMotivation").value,
            });
            qs("#internshipSubmissionList")?.prepend(makeMiniItem(payload.application, "motivation"));
            event.target.reset();
            setStatus(status, payload.message);
        } catch (error) {
            setStatus(status, error.message, "error");
            maybeOpenLogin(error);
        }
    });
}

function updateBroadcastPreview() {
    const title = qs("#broadcastTitle")?.value || "";
    const target = qs("#broadcastTarget")?.value || "";
    const message = qs("#broadcastMessage")?.value || "";
    if (qs("#broadcastTitlePreview")) qs("#broadcastTitlePreview").textContent = title;
    if (qs("#broadcastTargetPreview")) qs("#broadcastTargetPreview").textContent = target;
    if (qs("#broadcastMessagePreview")) qs("#broadcastMessagePreview").textContent = message;
}

function bindBroadcast() {
    ["#broadcastTitle", "#broadcastTarget", "#broadcastMessage"].forEach((selector) => {
        qs(selector)?.addEventListener("input", updateBroadcastPreview);
        qs(selector)?.addEventListener("change", updateBroadcastPreview);
    });

    qs("#broadcastForm")?.addEventListener("submit", (event) => {
        event.preventDefault();
        updateBroadcastPreview();
        setStatus(qs("#broadcastStatus"), "Preview updated.");
    });

    qs("#startBroadcastButton")?.addEventListener("click", async () => {
        const status = qs("#broadcastStatus");
        clearStatus(status);
        try {
            const payload = await postJson("/api/broadcasts", {
                title: qs("#broadcastTitle").value,
                target: qs("#broadcastTarget").value,
                message: qs("#broadcastMessage").value,
            });
            qs("#broadcastList")?.prepend(makeBroadcast(payload.broadcast));
            showBroadcastBanner(payload.broadcast);
            setStatus(status, "Broadcast is now running.");
        } catch (error) {
            setStatus(status, error.message, "error");
            maybeOpenLogin(error);
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    bindLogin();
    bindCarousels();
    bindDonation();
    bindApplication();
    bindComments();
    bindDiscussions();
    bindEssays();
    bindArticles();
    bindInternships();
    bindBroadcast();
    loadCurrentUser();
});
