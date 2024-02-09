function translate_text(text, url, i) {
    const originalMsgText = document.getElementById('msg_text'+i).querySelector("#original-text");
    const translatedMsgText = document.getElementById('msg_text'+i).querySelector("#translated-text");
    if (translatedMsgText.style.display == 'none') {
      if(!translatedMsgText.innerHTML){
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
          translatedMsgText.innerHTML = data["translation"];
        })
        .catch(error => {
          console.error("Error:", error);
        });
      }
      translatedMsgText.style.display = 'inline';
      originalMsgText.style.display = 'none';
      

    } else {
      translatedMsgText.style.display = 'none';
      originalMsgText.style.display = 'inline';
    }
    

}