import fs from 'fs';

// Konfigurasi
const CLIENT_ID = process.env.SPOTIFY_CLIENT_ID;
const CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.SPOTIFY_REFRESH_TOKEN;

const NOW_PLAYING_ENDPOINT = 'https://api.spotify.com/v1/me/player/currently-playing';
const RECENTLY_PLAYED_ENDPOINT = 'https://api.spotify.com/v1/me/player/recently-played';
const TOKEN_ENDPOINT = `https://accounts.spotify.com/api/token`;

// Fungsi untuk mendapatkan Access Token baru
async function getAccessToken() {
  const response = await fetch(TOKEN_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Authorization': 'Basic ' + Buffer.from(CLIENT_ID + ':' + CLIENT_SECRET).toString('base64'),
    },
    body: new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: REFRESH_TOKEN,
    }),
  });
  return response.json();
}

// Fungsi untuk membuat baris HTML lagu
function createSongHtml(song, isNowPlaying = false) {
    const timeText = isNowPlaying ? 'Now Playing' : 'Recently';
    const titleColor = isNowPlaying ? '#1DB954' : '#cbced2';

    return `
    <tr>
        <td width="70" valign="top">
            <a href="${song.track.external_urls.spotify}" target="_blank">
                <img src="${song.track.album.images[2].url}" width="60" height="60" alt="${song.track.name}"/>
            </a>
        </td>
        <td valign="middle">
            <a href="${song.track.external_urls.spotify}" target="_blank" style="text-decoration: none; font-weight: bold; color: ${titleColor};">
                ${song.track.name}
            </a>
            <br/>
            <span style="font-size: 13px; color: #8b949e;">${song.track.artists.map(a => a.name).join(', ')}</span>
        </td>
        <td width="100" valign="middle" align="right">
            <span style="font-size: 12px; color: #8b949e;">${timeText}</span>
        </td>
    </tr>`;
}

// Fungsi utama
async function main() {
  const { access_token } = await getAccessToken();

  // Cek Now Playing
  const nowPlayingRes = await fetch(NOW_PLAYING_ENDPOINT, { headers: { Authorization: `Bearer ${access_token}` } });
  let content = '';

  if (nowPlayingRes.status === 200) {
      const data = await nowPlayingRes.json();
      if (data.is_playing) {
          content = '<table>' + createSongHtml({ track: data.item }, true) + '</table>';
      }
  } 

  // Jika tidak ada yang diputar, ambil Recent Tracks
  if (!content) {
      const recentlyPlayedRes = await fetch(RECENTLY_PLAYED_ENDPOINT + '?limit=5', { headers: { Authorization: `Bearer ${access_token}` } });
      const data = await recentlyPlayedRes.json();
      const songsHtml = data.items.map(song => createSongHtml(song, false)).join('');
      content = '<table>' + songsHtml + '</table>';
  }

  // Update README
  const readme = fs.readFileSync('README.md', 'utf-8');
  const newReadme = readme.replace(/[\s\S]*/, `\n${content}\n`);
  fs.writeFileSync('README.md', newReadme);
  console.log('✅ Spotify data updated successfully!');
}

main();
