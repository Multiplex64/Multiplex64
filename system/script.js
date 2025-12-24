// System Scripts

// Init site upon initial load
function __init() {
    __navBar = document.body.classList.contains("__navOpen");
    window.addEventListener('popstate', function () {
        __goMainContent(window.location.pathname)
    }, false);
    searchInput = document.getElementById('__search')
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            _goto("/search/?q=" + encodeURIComponent(searchInput.value.trim()));
        }
    });
}

// Script to be run every time new page is navigated to
function __load() {
    anchors = document.querySelectorAll("a")
    for (var i = 0; i < anchors.length; i++) {
        anchor = anchors[i]
        if (!anchor.classList.contains("__linkListenerApplied")) {
            anchor.classList.add("__linkListenerApplied")
            if (!(/^(#|javascript:)/.test(anchor.getAttribute("href")))) {
                anchor.addEventListener("click", function (e) {
                    _goto(this.getAttribute("href"))
                    e.preventDefault()
                }, false);
            }
        }
    }
    ele = document.getElementById("__search")
    if (window.location.pathname == "/search") {
        queryString = window.location.search;
        urlParams = new URLSearchParams(queryString);
        ele.value = urlParams.get('q')
    } else {
        ele.value = ""
    }
}

document.addEventListener("DOMContentLoaded", function () {
    __init();
    __load();
});

// Set innerHTML of an object and inject JS
function __setInnerHTML(elm, html) {
    elm.innerHTML = html;
    Array.from(elm.querySelectorAll("script"))
        .forEach(oldScriptEl => {
            const newScriptEl = document.createElement("script");
            Array.from(oldScriptEl.attributes).forEach(attr => {
                newScriptEl.setAttribute(attr.name, attr.value)
            });
            const scriptText = document.createTextNode(oldScriptEl.innerHTML);
            newScriptEl.appendChild(scriptText);
            oldScriptEl.parentNode.replaceChild(newScriptEl, oldScriptEl);
        });
}

// Navigate to a page without full reload
async function __goMainContent(loc) {
    targetURL = new URL(loc, window.location.href)
    const response = await fetch("/null/page" + targetURL.pathname);
    val = await response.json();
    __setInnerHTML(document.querySelector("main"), val.data.html)
    document.title = val.meta.title
    if (val.meta.description) {
        document.querySelector('meta[name="description"]').setAttribute("content", val.meta.description);
    }
    if (val.meta.canonical) {
        document.querySelector('link[rel="canonical"]').setAttribute("href", val.meta.canonical);
    }
    __load();
}

// Toggle Navbar
function __toggleNav() {
    if (__navBar == true) {
        __navBar = false;
        document.body.classList.remove("__navOpen");
    } else {
        __navBar = true;
        document.body.classList.add("__navOpen");
    }
}

// Program Scripts

// Go to page
async function _goto(loc) {
    if (/^(?:[a-z]+:)|^(\/null|\/alt)/.test(loc)) {
        userConfirm = confirm("You are leaving Multiplex64. Are you sure you want to proceed?");
        if (userConfirm) {
            window.location.href = loc
        }
    } else {
        try {
            __goMainContent(loc)
        } catch (error) {
            console.error(error.message);
        }
        if (window.location.href !== new URL(loc, window.location.href).href) {
            window.history.pushState({}, "", loc);
        }
    }
}