// System Scripts

function __init() {
    __navBar = 0;
    window.addEventListener('popstate', function () {
        __goMainContent(window.location.pathname)
    }, false);
}

function __load() {
    anchors = document.querySelectorAll("a")
    for (var i = 0; i < anchors.length; i++) {
        anchor = anchors[i]
        if (!anchor.classList.contains("__linkListenerApplied")) {
            if (!/^(tel:|mailto:|sms:|javascript:)/.test(anchor.href)) {
                anchor.classList.add("__linkListenerApplied")
                anchor.addEventListener("click", function () {
                    _goto(this.getAttribute("href"))
                    console.log("excecuted")
                    event.preventDefault();
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

async function __goMainContent(loc) {
    // Needs support for relative paths
    const response = await fetch("/__null/page/" + loc);
    if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
    }
    val = await response.text();
    __setInnerHTML(document.getElementById("__main"), val)
    __load();
}

function __checkSearch() {
    // Deprecated, replacement needed
    if (event.key === "Enter") {
        __search();
    }
}

function __search() {
    ele = document.getElementById("__search")
    _goto("/search?q=" + encodeURIComponent(ele.value.trim()));
}

function __toggleNav() {
    if (__navBar == 1) {
        __navBar = 0;
        document.body.classList.remove("__navOpen");
    } else {
        __navBar = 1;
        document.body.classList.add("__navOpen");
    }
}

// Program Scripts

async function _goto(loc) {
    urlDetect = new RegExp('^(?:[a-z+]+:)?//', 'i');
    if (urlDetect.test(loc)) {
        userConfirm = confirm("You are leaving Multiplex64. Are you sure you want to proceed?");
        if (userConfirm) {
            window.location.href = loc;
        }
    } else {
        window.history.pushState({}, "", loc);
        try {
            __goMainContent(loc)
        } catch (error) {
            console.error(error.message);
        }
    }
}

async function _getData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const json = await response.json();
        return json;
    } catch (error) {
        console.error(error.message);
    }
}

async function _postData(url, data) {
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const json = await response.json();
        return JSON.parse(json);
    } catch (error) {
        console.error(error.message);
    }
}