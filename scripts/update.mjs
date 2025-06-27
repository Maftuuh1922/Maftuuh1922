import fetch from 'node-fetch';
import fs from 'fs';

// Ambil access token dari environment variable yang diatur oleh GitHub Actions
const accessToken = process.env.SPOTIFY_ACCESS_TOKEN;

/**
 * Mengambil lagu yang terakhir diputar dari Spotify API.
 */
async function fetchSpotify() {
  const res = await fetch('https://api.spotify.com/v1/me/player/recently-played?limit=5', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  // Jika gagal, tampilkan pesan error yang jelas
  if (res.status !== 200) {
    const errorBody = await res.text();
    console.error(`⚠️ Gagal mengambil data dari Spotify. Status: ${res.status}`);
    console.error('Pesan Error:', errorBody);
    process.exit(1); // Hentikan script jika gagal
  }
  
  const data = await res.json();

  if (!data.items) {
    console.error("⚠️ Respons Spotify tidak memiliki 'items'. Mungkin token tidak valid atau cakupan tidak menyertakan 'user-read-recently-played'.");
    process.exit(1);
  }

  // Ambil hanya 5 lagu teratas dan ubah datanya
  return data.items.slice(0, 5).map(item => {
    const track = item.track;
    const timeAgo = new Date(item.played_at);

    return {
      title: track.name.replace(/\|/g, '-'), // Ganti karakter `|` agar tidak merusak tabel
      artist: track.artists.map(a => a.name).join(', ').replace(/\|/g, '-'),
      time: `<t:${Math.floor(timeAgo.getTime() / 1000)}:R>`, // Format waktu relatif Discord
      image: track.album.images[1]?.url || track.album.images[0]?.url,
      url: track.external_urls.spotify
    };
  });
}

/**
 * Memperbarui file README.md dengan data lagu.
 */
async function updateReadme() {
  try {
    const songs = await fetchSpotify();

    // 🎨 Layout menggunakan tabel Markdown asli
    
    // Header (kosong, karena kita tidak butuh judul kolom)
    const header = `| ${songs.map(() => ' ').join(' | ')} |`;
    // Separator (mengatur perataan tengah untuk setiap kolom)
    const separator = `| ${songs.map(() => ':---:').join(' | ')} |`;

    // Baris untuk gambar album
    const images = `| ${songs.map(song => `<a href="${song.url}" target="_blank"><img src="${song.image}" width="100" alt="${song.title}"></a>`).join(' | ')} |`;
    
    // Baris untuk judul lagu (bisa diklik)
    const titles = `| ${songs.map(song => `[${song.title}](${song.url})`).join(' | ')} |`;
    
    // Baris untuk artis
    const artists = `| ${songs.map(song => song.artist).join(' | ')} |`;

    // Gabungkan semua menjadi satu string tabel markdown
    const markdownTable = [header, separator, images, titles, artists].join('\n');

    const readmePath = 'README.md';
    const readme = fs.readFileSync(readmePath, 'utf8');

    // Ganti hanya bagian di antara tag spotify
    const updated = readme.replace(
      /[\s\S]*/,
      `\n<div align="center">\n\n${markdownTable}\n\n</div>\n`
    );

    fs.writeFileSync(readmePath, updated);
    console.log('✅ README diperbarui dengan layout tabel Markdown asli.');

  } catch (error) {
    console.error('❌ Terjadi kesalahan saat memperbarui README:', error);
  }
}

// Jalankan fungsi utama
await updateReadme();
