import fs from 'fs';

// Konfigurasi dari GitHub Secrets
const CLIENT_ID = process.env.SPOTIFY_CLIENT_ID;
const CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.SPOTIFY_REFRESH_TOKEN;

const NOW_PLAYING_ENDPOINT = 'https://api.spotify.com/v1/me/player/currently-playing';
const RECENTLY_PLAYED_ENDPOINT = 'https://api.spotify.com/v1/me/player/recently-played';
const TOKEN_ENDPOINT = `https://accounts.spotify.com/api/token`;

// Fungsi untuk mendapatkan Access Token baru menggunakan Refresh Token
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
  if (!response.ok) {
    console.error('Gagal mendapatkan access token:', data);
    throw new Error('Gagal mendapatkan access token');
  }
  return data;
}

// Fungsi untuk membuat baris HTML dari data lagu
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

// Fungsi utama yang menjalankan semua logika
async function main() {
  try {
    const { access_token } = await getAccessToken();
    const headers = { Authorization: `Bearer ${access_token}` };
    let content = '';

    // 1. Cek lagu yang sedang diputar (Now Playing)
    const nowPlayingRes = await fetch(NOW_PLAYING_ENDPOINT, { headers });

    if (nowPlayingRes.status === 200) {
        const data = await nowPlayingRes.json();
        if (data && data.is_playing) {
            content = '<table>' + createSongHtml({ track: data.item }, true) + '</table>';
        }
    } 
    
    // 2. Jika tidak ada yang diputar, ambil lagu terakhir (Recently Played)
    if (!content) {
        const recentlyPlayedRes = await fetch(RECENTLY_PLAYED_ENDPOINT + '?limit=5', { headers });
        
        // --- INI BAGIAN PERBAIKANNYA ---
        // Cek apakah request berhasil sebelum memproses data
        if (recentlyPlayedRes.ok) {
          const data = await recentlyPlayedRes.json();
          // Cek apakah 'items' benar-benar ada di dalam data
          if (data && data.items) {
            const songsHtml = data.items.map(song => createSongHtml(song, false)).join('');
            content = '<table>' + songsHtml + '</table>';
          } else {
            content = 'Could not retrieve recent tracks.';
            console.warn('Respons recently played tidak berisi items:', data);
          }
        } else {
          content = 'Could not connect to Spotify API for recent tracks.';
          console.error('Gagal mengambil recently played. Status:', recentlyPlayedRes.status);
        }
    }

    // 3. Update file README.md
    const readme = fs.readFileSync('README.md', 'utf-8');
    const newReadme = readme.replace(/[\s\S]*/, `\n${content}\n`);
    fs.writeFileSync('README.md', newReadme);
    console.log('✅ Spotify data updated successfully!');

  } catch (error) {
    console.error('❌ Terjadi error pada proses utama:', error);
    // Keluar dengan kode error agar GitHub tahu ada yang salah
    process.exit(1
