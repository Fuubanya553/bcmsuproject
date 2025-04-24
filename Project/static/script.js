console.log("Script loaded!");

document.addEventListener("DOMContentLoaded", () => {
  const askButton = document.getElementById("askButton");
  const clearButton = document.getElementById("clearButton");
  const inputBox = document.getElementById("inputText");
  const outputBox = document.getElementById("outputText");

  askButton.addEventListener("click", () => {
    const question = inputBox.value.trim();
    if (!question) return;

    outputBox.textContent = "Thinking...";

    fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    })
    .then(res => {
      if (!res.ok) {
        // If it's not JSON, try to read the text to help with debugging
        return res.text().then(text => {
          throw new Error(`Server error ${res.status}: ${text}`);
        });
      }
      return res.json();
    })
    .then(data => {
      if (data.response) {
        // If using marked.js for Markdown parsing
        outputBox.innerHTML = marked.parse(data.response);
      } else {
        outputBox.textContent = "No response received.";
      }
    })
    .catch(err => {
      outputBox.textContent = "Error: " + err.message;
      console.error("Fetch error:", err);
    });
  });

  clearButton.addEventListener("click", () => {
    inputBox.value = "";
    outputBox.textContent = "Waiting for your question...";
  });
});