import fs from 'fs';

// --- Konfigurasi ---
const CLIENT_ID = process.env.SPOTIFY_CLIENT_ID;
const CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.SPOTIFY_REFRESH_TOKEN;

const NOW_PLAYING_ENDPOINT = 'https://api.spotify.com/v1/me/player/currently-playing';
const RECENTLY_PLAYED_ENDPOINT = 'https://api.spotify.com/v1/me/player/recently-played';
const TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token';

/**
 * Fungsi untuk mendapatkan Access Token baru.
 */
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
  const data = await response.json();
  if (!response.ok) throw new Error('Gagal mendapatkan access token.');
  return data.access_token;
}

/**
 * Fungsi untuk membuat baris tabel HTML dengan sedikit polesan.
 */
function createSongHtml(songItem, isNowPlaying = false) {
    const track = isNowPlaying ? songItem : songItem.track;
    if (!track?.album?.images[2]) return '';

    const timeText = isNowPlaying ? 'Now Playing' : 'Recently';
    const titleColor = isNowPlaying ? '#1DB954' : '#ffffff';

    return `
    <tr>
        <td width="65" valign="top">
            <a href="${track.external_urls.spotify}" target="_blank">
                <img src="${track.album.images[2].url}" width="60" height="60" alt="${track.name}" style="border-radius:4px;"/>
            </a>
        </td>
        <td valign="top">
            <a href="${track.external_urls.spotify}" target="_blank" style="text-decoration: none; font-weight: 600; font-size: 14px; color: ${titleColor};">
                ${track.name}
            </a>
            <br/>
            <span style="font-size: 12px; color: #8b949e;">${track.artists.map(a => a.name).join(', ')}</span>
        </td>
        <td width="90" valign="top" align="right">
            <span style="font-size: 12px; color: #8b949e;">${timeText}</span>
        </td>
    </tr>`;
}

/**
 * Fungsi utama untuk menjalankan semua logika.
 */
async function main() {
  try {
    const accessToken = await getAccessToken();
    const headers = { Authorization: `Bearer ${accessToken}` };
    let contentHtml = '';

    // Cek lagu yang sedang diputar
    const nowPlayingRes = await fetch(NOW_PLAYING_ENDPOINT, { headers });
    if (nowPlayingRes.status === 200) {
        const data = await nowPlayingRes.json();
        if (data?.is_playing) {
            contentHtml = '<table>' + createSongHtml(data.item, true) + '</table>';
        }
    } 
    
    // Jika tidak ada, ambil lagu terakhir
    if (!contentHtml) {
        const recentlyPlayedRes = await fetch(RECENTLY_PLAYED_ENDPOINT + '?limit=5', { headers });
        if (recentlyPlayedRes.ok) {
            const data = await recentlyPlayedRes.json();
            if (data?.items?.length > 0) {
                const songsHtml = data.items.map(song => createSongHtml(song, false)).join('');
                contentHtml = '<table>' + songsHtml + '</table>';
            }
        }
    }

    if (!contentHtml) contentHtml = 'Nothing playing right now.';

    // Update file README.md
    const readmePath = 'README.md'; // <-- INI BAGIAN YANG DIPERBAIKI
    const readme = fs.readFileSync(readmePath, 'utf-8');
    const newReadme = readme.replace(/[\s\S]*/, `\n${contentHtml}\n`);
    fs.writeFileSync(readmePath, newReadme);
    console.log('✅ Spotify data updated successfully!');

  } catch (error) {
      console.error('❌ Terjadi error pada proses utama:', error.message);
      process.exit(1);
  }
}

main();
