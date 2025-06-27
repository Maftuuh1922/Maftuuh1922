require('dotenv').config();
const fs = require('fs');
const fetch = require('node-fetch');

const token = process.env.SPOTIFY_ACCESS_TOKEN;
const readmePath = 'README.md';
const maxSongs = 5;

async function fetchRecentlyPlayed() {
  const res = await fetch('https://api.spotify.com/v1/me/player/recently-played?limit=' + maxSongs, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    console.error('Failed to fetch:', await res.text());
    process.exit(1);
  }

  const data = await res.json();
  return data.items;
}

function generateHTML(songs) {
  let html = `<div align="center" style="background:#121212;padding:20px;border-radius:12px;max-width:500px;margin:auto;">
  <h3><img src="https://upload.wikimedia.org/wikipedia/commons/8/84/Spotify_icon.svg" width="20"/> Spotify <span style="color:#1DB954">Recently Played</span></h3>\n`;

  for (const song of songs) {
    const track = song.track;
    const image = track.album.images[0]?.url || '';
    const name = track.name;
    const artist = track.artists.map(a => a.name).join(', ');
    const playedAt = new Date(song.played_at).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });

    html += `
    <div style="display:flex;align-items:center;margin:10px 0;">
      <img src="${image}" width="40" style="border-radius:5px;margin-right:10px;" />
      <div style="text-align:left;">
        <strong style="color:white;">${name}</strong><br/>
        <small style="color:gray;">${artist} • ${playedAt}</small>
      </div>
    </div>\n`;
  }

  html += `</div>`;
  return html;
}

function updateReadme(content) {
  const readme = fs.readFileSync(readmePath, 'utf-8');
  const newReadme = readme.replace(
    /<!--START_SECTION:spotify-->[\s\S]*<!--END_SECTION:spotify-->/,
    `<!--START_SECTION:spotify-->\n${content}\n<!--END_SECTION:spotify-->`
  );
  fs.writeFileSync(readmePath, newReadme);
}

(async () => {
  const songs = await fetchRecentlyPlayed();
  const htmlContent = generateHTML(songs);
  updateReadme(htmlContent);
})();
