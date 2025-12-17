async function fetchLyrics() {
  const title = document.getElementById("title").value;
  const artist = document.getElementById("artist").value;
  const duration = document.getElementById("duration").value;
  const btn = document.getElementById("search-btn");
  const resultContainer = document.getElementById("result-container");
  const lyricsDisplay = document.getElementById("lyrics-display");
  const copyBtn = document.getElementById("copy-btn");

  if (!title) {
    alert("Please enter a song title");
    return;
  }

  btn.disabled = true;
  btn.innerText = "Searching...";
  resultContainer.style.display = "none";
  copyBtn.style.display = "none";

  try {
    const query = new URLSearchParams({ title, artist, duration });
    const response = await fetch(`/api/lyrics?${query}`);
    const data = await response.json();

    resultContainer.style.display = "block";

    if (response.status === 200) {
      lyricsDisplay.innerHTML = `<pre id="lyrics-text">${data.lyrics}</pre>`;
      copyBtn.style.display = "block";
      copyBtn.innerText = "Copy Lyrics";
    } else {
      lyricsDisplay.innerHTML = `<div class="error">${data.message}</div>`;
    }
  } catch (err) {
    resultContainer.style.display = "block";
    lyricsDisplay.innerHTML = `<div class="error">Something went wrong during fetch</div>`;
  } finally {
    btn.disabled = false;
    btn.innerText = "Get Lyrics";
  }
}

async function copyToClipboard() {
  const lyricsText = document.getElementById("lyrics-text").innerText;
  const copyBtn = document.getElementById("copy-btn");

  try {
    await navigator.clipboard.writeText(lyricsText);
    const originalText = copyBtn.innerText;
    copyBtn.innerText = "Copied to clipboard";
    copyBtn.style.background = "#238636";

    setTimeout(() => {
      copyBtn.innerText = originalText;
      copyBtn.style.background = "#30363d";
    }, 2000);
  } catch (err) {
    alert("Failed to copy lyrics");
  }
}
