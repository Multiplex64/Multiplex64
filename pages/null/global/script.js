function __init() {
    ele = document.getElementById("__search")
    if (window.location.pathname == "/search") {
        queryString = window.location.search;
        urlParams = new URLSearchParams(queryString);
        ele.value = urlParams.get('q')
    } else {
        ele.value = ""
    }
}
__init();

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

async function __goto(loc) {
    window.history.pushState({}, "", loc);
    try {
        nextURL = new URL("./" + loc, window.location)
        const response = await fetch("./" + nextURL.pathname + "/index.html");
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        val = await response.text();
        __setInnerHTML(document.getElementById("__main"), val)
        __init();
    } catch (error) {
        console.error(error.message);
    }
}

function __checkSearch() {
    if (event.key === "Enter") {
        __search();
    }
}

function __search() {
    ele = document.getElementById("__search")
    __goto("/search?q=" + encodeURIComponent(ele.value.trim()));
}
__navBar = 0;

function toggleNav() {
    if (__navBar == 1) {
        __navBar = 0;
        document.body.classList.remove("__navOpen");
    } else {
        __navBar = 1;
        document.body.classList.add("__navOpen");
    }
}
async function __getData(url) {
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
async function __postData(url, data) {
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