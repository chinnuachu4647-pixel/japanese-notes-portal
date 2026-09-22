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


let japaneseVoice = null;

function loadJapaneseVoice() {

    if (!("speechSynthesis" in window)) {
        return;
    }

    const voices = window.speechSynthesis.getVoices();

    japaneseVoice =
        voices.find(function (voice) {
            return voice.lang &&
                voice.lang.toLowerCase().startsWith("ja");
        }) || null;
}


// Load voices when available
if ("speechSynthesis" in window) {

    loadJapaneseVoice();

    window.speechSynthesis.addEventListener(
        "voiceschanged",
        loadJapaneseVoice
    );

}


function pronounceJapanese(text) {

    if (!pronunciationEnabled()) {
        return;
    }


    if (!("speechSynthesis" in window)) {

        alert(
            "Japanese pronunciation is not supported on this device."
        );

        return;
    }


    const synth = window.speechSynthesis;


    function speakNow() {

        synth.cancel();

        // Some mobile browsers can remain paused/stuck
        if (synth.paused) {
            synth.resume();
        }


        const speech =
            new SpeechSynthesisUtterance(text);


        speech.lang = "ja-JP";
        speech.rate = 0.85;
        speech.pitch = 1;
        speech.volume = 1;


        // Use a Japanese voice when the device provides one
        const voices = synth.getVoices();

        const voice =
            japaneseVoice ||
            voices.find(function (v) {
                return v.lang &&
                    v.lang.toLowerCase().startsWith("ja");
            });


        if (voice) {
            speech.voice = voice;
        }


        speech.onstart = function () {
            console.log(
                "Japanese pronunciation started:",
                text
            );
        };


        speech.onerror = function (event) {

            console.error(
                "Speech synthesis error:",
                event.error
            );

        };


        synth.speak(speech);

    }


    // Voices may not be ready immediately on mobile browsers
    const voices = synth.getVoices();


    if (voices.length > 0) {

        speakNow();

    } else {

        let handled = false;


        const handleVoices = function () {

            if (handled) {
                return;
            }

            handled = true;

            loadJapaneseVoice();
            speakNow();

        };


        synth.addEventListener(
            "voiceschanged",
            handleVoices,
            { once: true }
        );


        // Fallback for browsers that do not fire the event reliably
        setTimeout(function () {

            if (!handled) {
                handleVoices();
            }

        }, 1000);

    }

}