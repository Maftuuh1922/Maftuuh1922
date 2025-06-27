import fetch from 'node-fetch';
import fs from 'fs';

// Ambil access token dari environment variable
const accessToken = process.env.SPOTIFY_ACCESS_TOKEN;

// Endpoint API Spotify yang sebenarnya
const NOW_PLAYING_ENDPOINT = 'https://api.spotify.com/v1/me/player/currently-playing';
const RECENTLY_PLAYED_ENDPOINT = 'https://api.spotify.com/v1/me/player/recently-played?limit=5';

/**
 * Fungsi untuk mengambil data dari Spotify API
 * @param {string} url Endpoint API
 * @returns {Promise<object|null>}
 */
async function fetchFromSpotify(url) {
  const headers = { Authorization: `Bearer ${accessToken}` };
  try {
    const response = await fetch(url, { headers });
    if (response.status === 204) { // 204 No Content -> Tidak ada lagu yang diputar
      return null;
    }
    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`⚠️ Gagal mengambil data dari Spotify. Status: ${response.status}`);
      console.error('Pesan Error:', errorBody);
      return null;
    }
    return response.json();
  } catch (error) {
    console.error('❌ Error saat fetch ke Spotify:', error);
    return null;
  }
}

/**
 * Membuat baris tabel HTML untuk satu lagu
 * @param {object} song Objek lagu
 * @param {boolean} isNowPlaying Status apakah lagu sedang diputar
 * @returns {string}
 */
function createSongHtml(song, isNowPlaying = false) {
  const timeText = isNowPlaying ? 'Now Playing' : `<t:${Math.floor(new Date(song.played_at).getTime() / 1000)}:R>`;
  const titleColor = isNowPlaying ? '#1DB954' : '#cbced2'; // Warna hijau jika sedang diputar

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

/**
 * Fungsi utama untuk memperbarui README
 */
async function updateReadme() {
  let content = '';

  // 1. Cek lagu yang sedang diputar (Online)
  const nowPlayingData = await fetchFromSpotify(NOW_PLAYING_ENDPOINT);

  if (nowPlayingData && nowPlayingData.is_playing) {
    // Jika ada lagu yang sedang diputar, tampilkan lagu itu
    content = '<table width="100%">' + createSongHtml({ track: nowPlayingData.item }, true) + '</table>';
  } else {
    // 2. Jika tidak ada, ambil lagu yang terakhir diputar (Offline)
    const recentlyPlayedData = await fetchFromSpotify(RECENTLY_PLAYED_ENDPOINT);
    if (recentlyPlayedData && recentlyPlayedData.items) {
      let songsHtml = recentlyPlayedData.items.map(song => createSongHtml(song, false)).join('');
      content = '<table width="100%">' + songsHtml + '</table>';
    } else {
      content = 'Nothing playing right now.';
    }
  }

  // 3. Tulis ke file README.md
  try {
    const readmePath = 'README.md';
    const readme = fs.readFileSync(readmePath, 'utf8');
    const updated = readme.replace(
      /[\s\S]*/,
      `\n${content}\n`
    );
    fs.writeFileSync(readmePath, updated);
    console.log('✅ README diperbarui dengan status Spotify terbaru.');
  } catch (error) {
    console.error('❌ Gagal menulis ke file README.md:', error);
  }
}

await updateReadme();
