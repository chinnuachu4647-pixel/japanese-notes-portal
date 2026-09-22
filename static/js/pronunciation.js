document.addEventListener("DOMContentLoaded", function () {

    updatePronunciation();

});


function pronunciationEnabled() {

    return localStorage.getItem("pronunciation") !== "false";

}


function updatePronunciation() {

    removePronunciationButtons();

    if (!pronunciationEnabled()) {
        return;
    }

    addJapanesePronunciation();

}


function addJapanesePronunciation() {

    processJapaneseText(document.body);

}


function processJapaneseText(container) {

    const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode: function (node) {

                if (!node.nodeValue.trim()) {
                    return NodeFilter.FILTER_REJECT;
                }

                const parent = node.parentElement;

                if (!parent) {
                    return NodeFilter.FILTER_REJECT;
                }

                if (
                    parent.closest(
                    "script, style, textarea, input, select, button, a, .welcome-japanese, .daily-japanese, .word-japanese, .word-example, .quote-japanese, .dashboard-footer"
                    )
                ) {
                    return NodeFilter.FILTER_REJECT;
                }

                if (
                    parent.closest(".japanese-pronunciation-text")
                ) {
                    return NodeFilter.FILTER_REJECT;
                }

                if (
                    !/[ぁ-ゟ゠-ヿ一-龯々〆〄ー]/.test(
                        node.nodeValue
                    )
                ) {
                    return NodeFilter.FILTER_REJECT;
                }

                return NodeFilter.FILTER_ACCEPT;

            }
        }
    );


    const textNodes = [];

    let node;

    while ((node = walker.nextNode())) {

        textNodes.push(node);

    }


    textNodes.forEach(function (textNode) {

        replaceJapaneseText(textNode);

    });

}


function replaceJapaneseText(textNode) {

    const text = textNode.nodeValue;

    const fragment =
        document.createDocumentFragment();

    const regex =
        /[ぁ-ゟ゠-ヿ一-龯々〆〄ー]+/g;

    let lastIndex = 0;

    let match;


    while ((match = regex.exec(text))) {

        if (match.index > lastIndex) {

            fragment.appendChild(
                document.createTextNode(
                    text.substring(
                        lastIndex,
                        match.index
                    )
                )
            );

        }


        const japaneseWord = match[0];


        const wrapper =
            document.createElement("span");

        wrapper.className =
            "japanese-pronunciation-text";

        wrapper.dataset.japanese =
            japaneseWord;

        wrapper.textContent =
            japaneseWord;


        const speaker =
            document.createElement("span");

        speaker.className =
            "japanese-speaker";

        speaker.textContent =
            "🔊";

        speaker.title =
            "Pronounce Japanese";

        speaker.setAttribute(
            "role",
            "button"
        );

        speaker.setAttribute(
            "tabindex",
            "0"
        );


        speaker.addEventListener(
            "click",
            function (event) {

                event.preventDefault();
                event.stopPropagation();

                pronounceJapanese(
                    japaneseWord
                );

            }
        );


        speaker.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Enter" ||
                    event.key === " "
                ) {

                    event.preventDefault();

                    pronounceJapanese(
                        japaneseWord
                    );

                }

            }
        );


        wrapper.appendChild(
            speaker
        );


        fragment.appendChild(
            wrapper
        );


        lastIndex =
            regex.lastIndex;

    }


    if (lastIndex < text.length) {

        fragment.appendChild(
            document.createTextNode(
                text.substring(lastIndex)
            )
        );

    }


    textNode.parentNode.replaceChild(
        fragment,
        textNode
    );

}


function removePronunciationButtons() {

    const speakers =
        document.querySelectorAll(
            ".japanese-speaker"
        );

    speakers.forEach(function (speaker) {

        const wrapper =
            speaker.parentElement;

        if (!wrapper) {
            return;
        }

        const japaneseText =
            wrapper.dataset.japanese || "";

        wrapper.replaceWith(
            document.createTextNode(
                japaneseText
            )
        );

    });

}


function pronounceJapanese(text) {

    if (!pronunciationEnabled()) {

        window.speechSynthesis.cancel();

        return;

    }


    if (
        !("speechSynthesis" in window)
    ) {

        alert(
            "Your browser does not support Japanese pronunciation."
        );

        return;

    }


    window.speechSynthesis.cancel();


    const speech =
        new SpeechSynthesisUtterance(text);

    speech.lang =
        "ja-JP";

    speech.rate =
        0.85;

    speech.pitch =
        1;


    window.speechSynthesis.speak(
        speech
    );

}