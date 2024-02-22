function translate_text(text, url, i) {
    const originalMsgText = document.getElementById('msg_text'+i).querySelector(".original-text");
    const translatedMsgText = document.getElementById('msg_text'+i).querySelector(".translated-text");
    const lang = document.getElementById("lang").value;
    if (translatedMsgText.style.display == 'none') {
      if(!translatedMsgText.innerHTML){
        fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({'text': text, 'language': lang}),
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

document.getElementById("lang").onchange = function(){
  document.getElementById("language").value = document.getElementById("lang").value;
  const translatedElements = document.querySelectorAll('.translated-text');

  translatedElements.forEach(element => {
      element.innerHTML = '';
      element.style.display = 'none';
  });

  const originalElements = document.querySelectorAll('.original-text');

  originalElements.forEach(element => {
      element.style.display = 'inline';
  });
}