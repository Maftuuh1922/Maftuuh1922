const fs = require("fs");
const fetch = require("node-fetch");

const accessToken = process.env.SPOTIFY_ACCESS_TOKEN;
const API = "https://api.spotify.com/v1/me/player/recently-played?limit=5";
const README_PATH = "README.md";

async function fetchSpotify() {
  const res = await fetch(API, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const data = await res.json();
  return data.items.map(item => {
    const track = item.track;
    return {
      name: track.name,
      artists: track.artists.map(a => a.name).join(", "),
      image: track.album.images.pop().url,
      playedAt: new Date(item.played_at).toLocaleTimeString("en-GB", { hour: '2-digit', minute: '2-digit' }),
    };
  });
}

function generateHTML(tracks) {
  const rows = tracks.map(t => `
  <tr>
    <td><img src="${t.image}" width="20" /> ${t.name}</td>
    <td>${t.artists}</td>
    <td>${t.playedAt}</td>
  </tr>`).join("\n");

  return `
<!--START_SECTION:spotify-->
<table>
  <thead>
    <tr><th>🎵 Judul Lagu</th><th>🎤 Artis</th><th>⏱️ Waktu</th></tr>
  </thead>
  <tbody>${rows}</tbody>
</table>
<!--END_SECTION:spotify-->`;
}

async function updateReadme() {
  const content = fs.readFileSync(README_PATH, "utf8");
  const start = "<!--START_SECTION:spotify-->";
  const end = "<!--END_SECTION:spotify-->";
  const regex = new RegExp(`${start}[\\s\\S]*?${end}`);

  const tracks = await fetchSpotify();
  const newSection = generateHTML(tracks);
  const updated = content.replace(regex, newSection);
  fs.writeFileSync(README_PATH, updated);
}

updateReadme();
