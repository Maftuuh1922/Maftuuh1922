import fetch from 'node-fetch';
import fs from 'fs';

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
    process.exit(1);
  }

  return data.items.map(item => {
    const track = item.track;
    const timeAgo = new Date(item.played_at);

    return {
      title: track.name,
      artist: track.artists.map(a => a.name).join(', '),
      time: `<t:${Math.floor(timeAgo.getTime() / 1000)}:R>`,
      image: track.album.images[1]?.url || track.album.images[0]?.url,
    };
  });
}

async function updateReadme() {
  const songs = await fetchSpotify();

  // 🎨 Gaya layout kartu (berjajar horizontal)
  const items = songs.map(song => {
    return `<a href="https://open.spotify.com/search/${encodeURIComponent(song.title + ' ' + song.artist)}" target="_blank">
  <img src="${song.image}" width="100" alt="${song.title}" title="${song.title} - ${song.artist} (${song.time})"/>
</a>`;
  }).join('\n');

  const section = `
<p align="center">
  ${items}
</p>`;

  const readme = fs.readFileSync('README.md', 'utf8');

  const updated = readme.replace(
    /<!--START_SECTION:spotify-->[\s\S]*<!--END_SECTION:spotify-->/,
    `<!--START_SECTION:spotify-->\n${section}\n<!--END_SECTION:spotify-->`
  );

  fs.writeFileSync('README.md', updated);
}

await updateReadme();
