document.getElementById("send-btn").addEventListener("click", handleSend);

document.getElementById("user-input").addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
        handleSend();
    }
});

async function handleSend() {
    const userInput = document.getElementById("user-input").value.trim();
    const chatBox = document.getElementById("chat-box");

    if (!userInput) return;

    appendMessage("user-message", userInput);
    document.getElementById("user-input").value = "";

    const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userInput }),
    });

    const data = await response.json();

    if (data.response) {
        appendMessage("bot-message", data.response);
    } else {
        appendMessage("bot-message", "Oops! Something went wrong.");
    }
}

function appendMessage(className, text) {
    const chatBox = document.getElementById("chat-box");
    cons
}
