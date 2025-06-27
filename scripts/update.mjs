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
      image: track.album.images[0].url,
    };
  });
}

async function updateReadme() {
  const songs = await fetchSpotify();

  const cards = songs.map(song => {
    return `
<div align="left" style="margin-bottom: 12px; display: flex; align-items: center; background-color: #181818; padding: 12px; border-radius: 10px;">
  <img src="${song.image}" alt="${song.title}" width="64" height="64" style="border-radius: 8px; margin-right: 16px;" />
  <div>
    <strong style="color: #1DB954;">${song.title}</strong><br/>
    <span style="color: #ccc;">${song.artist}</span><br/>
    <small style="color: #888;">${song.time}</small>
  </div>
</div>`;
  }).join('\n');

  const readme = fs.readFileSync('README.md', 'utf8');
  const updated = readme.replace(
    /<!--START_SECTION:spotify-->[\s\S]*<!--END_SECTION:spotify-->/,
    `<!--START_SECTION:spotify-->\n${cards}\n<!--END_SECTION:spotify-->`
  );
  fs.writeFileSync('README.md', updated);
}

await updateReadme();
