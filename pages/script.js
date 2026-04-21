// System Scripts

// Init site upon initial load
document.addEventListener("DOMContentLoaded", function () {

    // Script to be run every time new page is navigated to
    function load() {
        // Override anchors
        anchors = document.querySelectorAll("a")
        for (var i = 0; i < anchors.length; i++) {
            anchor = anchors[i]
            if (!anchor.classList.contains("_normal")) {
                anchor.classList.add("_normal")
                if (!(/^(#|javascript:)/.test(anchor.getAttribute("href")))) {
                    anchor.addEventListener("click", function (e) {
                        _goto(this.getAttribute("href"))
                        e.preventDefault()
                    }, false);
                }
            }
        }
        // Fill search box with text
        ele = document.getElementById("__search")
        if (window.location.pathname == "/search") {
            queryString = window.location.search;
            urlParams = new URLSearchParams(queryString);
            ele.value = urlParams.get('q')
        } else {
            ele.value = ""
        }
    }

    // Navigate to a page without full reload
    window._goto = async function (loc, history = true) {
        if (/^(?:[a-z]+:)|^(\/null|\/alt)/.test(loc)) {
            /*
            Confirm box disabled
            userConfirm = confirm("You are leaving Multiplex64. Are you sure you want to proceed?");
            if (userConfirm) {
                window.location.href = loc
            }
            */
            window.location.href = loc
        } else {

            // Set innerHTML of an object and inject JS
            function setInnerHTML(elm, html) {
                elm.innerHTML = html;
                Array.from(elm.querySelectorAll("script")).forEach(oldScriptEl => {
                    const newScriptEl = document.createElement("script");
                    Array.from(oldScriptEl.attributes).forEach(attr => {
                        newScriptEl.setAttribute(attr.name, attr.value)
                    });
                    const scriptText = document.createTextNode(oldScriptEl.innerHTML);
                    newScriptEl.appendChild(scriptText);
                    oldScriptEl.parentNode.replaceChild(newScriptEl, oldScriptEl);
                });
            }
            // Format JSON data to update page
            function setPage(val) {
                setInnerHTML(document.querySelector("main"), val.data.html)
                document.title = val.meta.title
                if (val.meta.title) {
                    document.querySelector('meta[property="og:title"]').setAttribute("content", val.meta.title);
                }
                if (val.meta.description) {
                    document.querySelector('meta[name="description"]').setAttribute("content", val.meta.description);
                    document.querySelector('meta[property="og:description"]').setAttribute("content", val.meta.description);
                }
                if (val.meta.canonical) {
                    document.querySelector('link[rel="canonical"]').setAttribute("href", val.meta.canonical);
                    document.querySelector('meta[property="og:url"]').setAttribute("content", val.meta.canonical);
                }
                load();
            }
            // Try to load page
            targetURL = new URL(loc, window.location.href)
            try {
                const response = await fetch("/null/page" + targetURL.pathname + targetURL.search)
                const val = await response.json();
                setPage(val);
            } catch (error) {
                const val = {
                    "data": {
                        "html": `<div style="text-align:center;width:100%;">
                        <h1 style="font-size:64px;margin-top:32px;margin-bottom:16px">Uh oh!</h1> <br> We couldn't connect you to our server. 
                        Check your internet connection.</div>`
                    },
                    "meta": {
                        "title": "Error",
                        "description": "A network error occured."
                    }
                };
                setPage(val);
            }
            if (window.location.href !== new URL(loc, window.location.href).href && history == true) {
                window.history.pushState({}, "", loc);
            }
        }
    }

    // Search bar
    searchInput = document.getElementById('__search')
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            _goto("/search/?q=" + encodeURIComponent(searchInput.value.trim()));
        }
    });

    // Toggling navbar
    const navButton = document.getElementById("__navButton")
    navButton.addEventListener("click", function () {
        if (document.body.classList.contains("__navOpen")) {
            document.body.classList.remove("__navOpen");
        } else {
            document.body.classList.add("__navOpen");
        }
    })

    // Travelling backwards in history
    window.addEventListener('popstate', function () {
        _goto(window.location.pathname, false)
    });
    load();
});

// Toggle page fullscreen
function _fullscreen() {
    if (!document.fullscreenElement &&
        !document.mozFullScreenElement && !document.webkitFullscreenElement) {
        if (document.documentElement.requestFullscreen) {
            document.documentElement.requestFullscreen();
        } else if (document.documentElement.mozRequestFullScreen) {
            document.documentElement.mozRequestFullScreen();
        } else if (document.documentElement.webkitRequestFullscreen) {
            document.documentElement.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
        }
    } else {
        if (document.cancelFullScreen) {
            document.cancelFullScreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitCancelFullScreen) {
            document.webkitCancelFullScreen();
        }
    }
}