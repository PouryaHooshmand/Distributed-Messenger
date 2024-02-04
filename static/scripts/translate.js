function translate_text(text, url, i) {
    const msgText = document.getElementById('msg_text'+i);

    fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({'text': text}),
      })
      .then((response) => response.json())
      .then(data => {
        // Handle the response from the server (if needed)
        msgText.textContent = data["translation"];
      })
      .catch(error => {
        console.error("Error:", error);
      });

}