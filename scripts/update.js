import fetch from 'node-fetch';
import fs from 'fs/promises';

const accessToken = process.env.SPOTIFY_ACCESS_TOKEN;

async function fetchSpotifyTopTracks() {
  const res = await fetch('https://api.spotify.com/v1/me/top/tracks?limit=5&time_range=short_term', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  const data = await res.json();
  if (!data.items) {
    console.error("⚠️ Spotify response missing 'items'. Cek token atau scope 'user-top-read'.");
    process.exit(1);
  }

  return data.items.map(track => ({
    title: track.name,
    artist: track.artists.map(a => a.name).join(', '),
    time: '', // top tracks tidak memiliki waktu putar
    image: track.album.images.pop().url,
  }));
}

async function updateReadme() {
  const songs = await fetchSpotifyTopTracks();
  const tableRows = songs.map(song => {
    return `  <tr>
    <td><img src="${song.image}" width="20" /> ${song.title}</td>
    <td>${song.artist}</td>
    <td>${song.time || '-'}</td>
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

  const readme = await fs.readFile('README.md', 'utf8');
  const updated = readme.replace(
    /<!--START_SECTION:spotify-->[\s\S]*<!--END_SECTION:spotify-->/,
    `<!--START_SECTION:spotify-->\n${table}\n<!--END_SECTION:spotify-->`
  );
  await fs.writeFile('README.md', updated);
}

await updateReadme();
