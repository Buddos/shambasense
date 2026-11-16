(() => {
    const toggle = document.querySelector(".menu-toggle");
    const navigation = document.querySelector(".public-nav");

    if (!toggle || !navigation) {
        return;
    }

    const closeMenu = () => {
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open navigation menu");
        navigation.classList.remove("is-open");
    };

    toggle.addEventListener("click", () => {
        const isOpen = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!isOpen));
        toggle.setAttribute(
            "aria-label",
            isOpen ? "Open navigation menu" : "Close navigation menu",
        );
        navigation.classList.toggle("is-open", !isOpen);
    });

    navigation.addEventListener("click", (event) => {
        if (event.target.closest("a")) {
            closeMenu();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeMenu();
            toggle.focus();
        }
    });

    document.addEventListener("click", (event) => {
        if (!navigation.contains(event.target) && !toggle.contains(event.target)) {
            closeMenu();
        }
    });
})();
