const gjI18n = (() => {
    const supportedLanguages = ["en", "es", "pt", "fr", "de", "it", "ar"];
    const rtlLanguages = new Set(["ar"]);
    const defaultLanguage = "en";
    const dictionaries = {};
    let currentLanguage = defaultLanguage;

    function normaliseLanguage(language) {
        if (!language) return defaultLanguage;
        const shortCode = language.toLowerCase().split("-")[0];
        return supportedLanguages.includes(shortCode) ? shortCode : defaultLanguage;
    }

    function getNestedValue(source, path) {
        return path.split(".").reduce((value, key) => value && value[key], source);
    }

    async function loadDictionary(language) {
        const safeLanguage = normaliseLanguage(language);
        if (dictionaries[safeLanguage]) return dictionaries[safeLanguage];
        try {
            const response = await fetch(`/static/i18n/${safeLanguage}.json`, { cache: "no-cache" });
            if (!response.ok) throw new Error("Missing translation file.");
            dictionaries[safeLanguage] = await response.json();
        } catch {
            dictionaries[safeLanguage] = {};
        }
        return dictionaries[safeLanguage];
    }

    function detectLanguage() {
        const params = new URLSearchParams(window.location.search);
        const fromUrl = params.get("lang");
        const fromStorage = localStorage.getItem("gjLanguage");
        const fromBrowser = navigator.languages?.find((language) => supportedLanguages.includes(normaliseLanguage(language))) || navigator.language;
        return normaliseLanguage(fromUrl || fromStorage || fromBrowser);
    }

    function t(key, fallback = "") {
        const value = getNestedValue(dictionaries[currentLanguage] || {}, key);
        const fallbackValue = getNestedValue(dictionaries[defaultLanguage] || {}, key);
        return value || fallbackValue || fallback || key;
    }

    function applyTranslations(root = document) {
        root.querySelectorAll("[data-i18n]").forEach((element) => {
            element.textContent = t(element.dataset.i18n, element.textContent);
        });

        root.querySelectorAll("[data-i18n-attr]").forEach((element) => {
            element.dataset.i18nAttr.split(";").forEach((pair) => {
                const [attribute, key] = pair.split(":").map((part) => part.trim());
                if (attribute && key) {
                    element.setAttribute(attribute, t(key, element.getAttribute(attribute) || ""));
                }
            });
        });
    }

    async function setLanguage(language) {
        currentLanguage = normaliseLanguage(language);
        await loadDictionary(defaultLanguage);
        await loadDictionary(currentLanguage);
        localStorage.setItem("gjLanguage", currentLanguage);
        document.documentElement.lang = currentLanguage;
        document.documentElement.dir = rtlLanguages.has(currentLanguage) ? "rtl" : "ltr";
        const selector = document.querySelector("#languageSelector");
        if (selector) selector.value = currentLanguage;
        applyTranslations();
        window.dispatchEvent(new CustomEvent("gj:languagechange", { detail: { language: currentLanguage } }));
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelector("#languageSelector")?.addEventListener("change", (event) => {
            setLanguage(event.target.value);
        });
        setLanguage(detectLanguage());
    });

    return {
        applyTranslations,
        getLanguage: () => currentLanguage,
        setLanguage,
        supportedLanguages,
        t,
    };
})();

window.gjI18n = gjI18n;
