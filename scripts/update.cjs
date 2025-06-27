const fetch = require('node-fetch');
const fs = require('fs');

const accessToken = process.env.SPOTIFY_ACCESS_TOKEN;

async function fetchSpotify() {
  const res = await fetch('https://api.spotify.com/v1/me/player/recently-played?limit=5', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  const data = await res.json();

  if (!data.items) {
    console.error("⚠️ Spotify response missing 'items'. Mungkin token tidak valid atau scope tidak mencakup 'user-read-recently-played'.");
    console.error("Spotify API Response:", data);
    process.exit(1);
  }

  return data.items.map(item => {
    const track = item.track;
    const timeAgo = new Date(item.played_at);
    return {
      title: track.name,
      artist: track.artists.map(a => a.name).join(', '),
      time: `<t:${Math.floor(timeAgo.getTime() / 1000)}:R>`,
      image: track.album.images.pop().url,
    };
  });
}

async function updateReadme() {
  const songs = await fetchSpotify();

  const tableRows = songs.map(song => {
    return `  <tr>
    <td><img src="${song.image}" width="20" /> ${song.title}</td>
    <td>${song.artist}</td>
    <td>${song.time}</td>
  </tr>`;
  }).join('\n');

  const table = `
<table>
  <thead>
    <tr>
      <th>🎵 Judul Lagu</th>
      <th>🎤 Artis</th>
      <th>⏱️ Waktu</th>
    </tr>
  </thead>
  <tbody>
${tableRows}
  </tbody>
</table>`;

  const readme = fs.readFileSync('README.md', 'utf8');
  const updated = readme.replace(
    /<!--START_SECTION:spotify-->[\s\S]*<!--END_SECTION:spotify-->/,
    `<!--START_SECTION:spotify-->\n${table}\n<!--END_SECTION:spotify-->`
  );

  fs.writeFileSync('README.md', updated);
}

updateReadme().catch(err => {
  console.error("❌ Gagal update README:", err);
  process.exit(1);
});
