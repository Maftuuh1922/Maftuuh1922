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
    console.error("⚠️ Respons Spotify tidak memiliki 'items'. Mungkin token tidak valid atau cakupan tidak menyertakan 'user-read-recently-played'.");
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
      url: track.external_urls.spotify
    };
  });
}

async function updateReadme() {
  const songs = await fetchSpotify();

  // 🎨 Gaya layout kartu
  const items = songs.map(song => {
    return `
<a href="${song.url}" target="_blank" style="text-decoration: none;">
  <div style="display: flex; align-items: center; margin: 10px 0; background-color: #282828; border-radius: 8px; padding: 10px; color: white;">
    <img src="${song.image}" width="64" height="64" alt="${song.title}" style="border-radius: 4px; margin-right: 15px;"/>
    <div style="display: flex; flex-direction: column;">
      <strong style="font-size: 16px; color: #1DB954;">${song.title}</strong>
      <span style="font-size: 14px; color: #b3b3b3;">${song.artist}</span>
      <span style="font-size: 12px; color: #b3b3b3;">${song.time}</span>
    </div>
  </div>
</a>`;
  }).join('\n');

  const section = `
<div align="center">
  ${items}
</div>`;

  const readme = fs.readFileSync('README.md', 'utf8');

  const updated = readme.replace(
    /[\s\S]*/,
    `\n${section}\n`
  );

  fs.writeFileSync('README.md', updated);
  console.log('✅ README diperbarui dengan data Spotify');
}

await updateReadme();
