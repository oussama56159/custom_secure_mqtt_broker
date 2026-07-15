(function () {
    function sameOrigin(url) {
        return url.origin === window.location.origin;
    }

    function pageContent() {
        return document.querySelector("#page-content");
    }

    function setLoading(isLoading) {
        document.body.classList.toggle("is-loading", isLoading);
    }

    function runInlineScripts(container) {
        container.querySelectorAll("script").forEach((oldScript) => {
            const newScript = document.createElement("script");
            Array.from(oldScript.attributes).forEach((attr) => newScript.setAttribute(attr.name, attr.value));
            newScript.textContent = oldScript.textContent;
            oldScript.replaceWith(newScript);
        });
    }

    async function replacePage(response, pushUrl) {
        const html = await response.text();
        const doc = new DOMParser().parseFromString(html, "text/html");
        const nextContent = doc.querySelector("#page-content");
        const currentContent = pageContent();
        const currentHasShell = !!document.querySelector(".app-shell");
        const nextHasShell = !!doc.querySelector(".app-shell");
        if (currentHasShell !== nextHasShell) {
            window.location.href = response.url;
            return;
        }
        if (!nextContent || !currentContent) {
            window.location.href = response.url;
            return;
        }
        document.title = doc.title;
        currentContent.innerHTML = nextContent.innerHTML;
        runInlineScripts(currentContent);
        if (pushUrl) {
            history.pushState({}, "", response.url);
        }
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    async function visit(url, options) {
        setLoading(true);
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    "X-Requested-With": "fetch",
                    ...(options && options.headers ? options.headers : {}),
                },
                redirect: "follow",
            });
            await replacePage(response, true);
        } catch (error) {
            window.location.href = url;
        } finally {
            setLoading(false);
        }
    }

    document.addEventListener("click", (event) => {
        const link = event.target.closest("a[href]");
        if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
            return;
        }
        const url = new URL(link.href, window.location.href);
        if (!sameOrigin(url) || link.target || link.hasAttribute("download") || url.hash || link.hasAttribute("data-full-load")) {
            return;
        }
        event.preventDefault();
        visit(url.toString(), { method: "GET" });
    });

    document.addEventListener("submit", (event) => {
        const form = event.target;
        if (!form.matches("form") || event.defaultPrevented) {
            return;
        }
        const url = new URL(form.action || window.location.href, window.location.href);
        if (!sameOrigin(url)) {
            return;
        }
        event.preventDefault();
        const method = (form.method || "GET").toUpperCase();
        const body = method === "GET" ? null : new FormData(form);
        if (method === "GET") {
            const params = new URLSearchParams(new FormData(form));
            url.search = params.toString();
        }
        visit(url.toString(), { method, body });
    });

    window.addEventListener("popstate", () => {
        visit(window.location.href, { method: "GET" });
    });
})();
