import fs from 'fs';

// --- Konfigurasi ---
// Mengambil data rahasia dari GitHub Secrets
const CLIENT_ID = process.env.SPOTIFY_CLIENT_ID;
const CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.SPOTIFY_REFRESH_TOKEN;

// Endpoint API Spotify
const NOW_PLAYING_ENDPOINT = 'https://api.spotify.com/v1/me/player/currently-playing';
const RECENTLY_PLAYED_ENDPOINT = 'https://api.spotify.com/v1/me/player/recently-played';
const TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token';

/**
 * Fungsi untuk mendapatkan Access Token baru menggunakan Refresh Token.
 * Jika gagal, akan melempar error agar workflow berhenti.
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

  if (!response.ok) {
    console.error('Gagal mendapatkan access token:', data);
    throw new Error('Gagal mendapatkan access token dari Spotify.');
  }
  return data.access_token;
}

/**
 * Fungsi untuk membuat baris tabel HTML dari data lagu.
 */
function createSongHtml(songItem, isNowPlaying = false) {
    // Menyesuaikan struktur data antara 'now playing' dan 'recently played'
    const track = isNowPlaying ? songItem : songItem.track;

    // Pengaman jika data lagu tidak lengkap
    if (!track || !track.album || !track.album.images[2]) {
        console.warn('Data lagu tidak lengkap, dilewati:', track);
        return '';
    }

    const timeText = isNowPlaying ? 'Now Playing' : 'Recently';
    const titleColor = isNowPlaying ? '#1DB954' : '#cbced2'; // Warna hijau jika sedang diputar

    return `
    <tr>
        <td width="70" valign="top">
            <a href="${track.external_urls.spotify}" target="_blank">
                <img src="${track.album.images[2].url}" width="60" height="60" alt="${track.name}"/>
            </a>
        </td>
        <td valign="middle">
            <a href="${track.external_urls.spotify}" target="_blank" style="text-decoration: none; font-weight: bold; color: ${titleColor};">
                ${track.name}
            </a>
            <br/>
            <span style="font-size: 13px; color: #8b949e;">${track.artists.map(a => a.name).join(', ')}</span>
        </td>
        <td width="100" valign="middle" align="right">
            <span style="font-size: 12px; color: #8b949e;">${timeText}</span>
        </td>
    </tr>`;
}

/**
 * Fungsi utama yang menjalankan semua logika.
 */
async function main() {
  try {
    const accessToken = await getAccessToken();
    const headers = { Authorization: `Bearer ${accessToken}` };
    let contentHtml = '';

    // 1. Cek lagu yang sedang diputar (Online)
    const nowPlayingRes = await fetch(NOW_PLAYING_ENDPOINT, { headers });
    if (nowPlayingRes.status === 200) {
        const data = await nowPlayingRes.json();
        if (data && data.is_playing) {
            contentHtml = '<table>' + createSongHtml(data.item, true) + '</table>';
        }
    } 
    
    // 2. Jika tidak ada yang diputar, ambil lagu terakhir (Offline)
    if (!contentHtml) {
        const recentlyPlayedRes = await fetch(RECENTLY_PLAYED_ENDPOINT + '?limit=5', { headers });
        if (recentlyPlayedRes.ok) {
            const data = await recentlyPlayedRes.json();
            if (data && data.items && data.items.length > 0) {
                const songsHtml = data.items.map(song => createSongHtml(song, false)).join('');
                contentHtml = '<table>' + songsHtml + '</table>';
            }
        }
    }

    // Fallback jika tidak ada data sama sekali
    if (!contentHtml) {
        contentHtml = 'Nothing playing right now.';
    }

    // 3. Update file README.md
    const readmePath = 'README.md';
    const readme = fs.readFileSync(readmePath, 'utf-8');
    const newReadme = readme.replace(/[\s\S]*/, `\n${contentHtml}\n`);
    fs.writeFileSync(readmePath, newReadme);
    console.log('✅ Spotify data updated successfully!');

  } catch (error) {
      console.error('❌ Terjadi error pada proses utama:', error.message);
      // Keluar dengan kode error agar GitHub tahu ada yang salah
      process.exit(1);
  }
}

// Menjalankan skrip utama
main();
