document.getElementById("lang").onchange = function(){
  fetch("lang_update", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({'language': this.value}),
  })
  .catch(error => {
    console.error("Error:", error);
  });
}