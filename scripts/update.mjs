import fetch from 'node-fetch';
import fs from 'fs';

const accessToken = process.env.SPOTIFY_ACCESS_TOKEN;

async function fetchSpotify() {
  const res = await fetch('https://api.spotify.com/v1/me/top/tracks?limit=5&time_range=short_term', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  const data = await res.json();

  if (!data.items) {
    console.error("⚠️ Spotify response missing 'items'. Mungkin token tidak valid atau scope tidak mencakup 'user-top-read'.");
    process.exit(1);
  }

  return data.items.map(track => {
    return {
      title: track.name,
      artist: track.artists.map(a => a.name).join(', '),
      time: 'Sering diputar 🎧',
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
      <th>📈 Keterangan</th>
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

await updateReadme();
