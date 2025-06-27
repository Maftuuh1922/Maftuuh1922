const fs = require("fs");
const fetch = require("node-fetch");

const fetchSpotify = async () => {
  const res = await fetch("https://api.spotify.com/v1/me/player/recently-played?limit=5", {
    headers: {
      Authorization: `Bearer ${process.env.SPOTIFY_ACCESS_TOKEN}`,
    },
  });

  const data = await res.json();

  // ✅ Debug log untuk melihat respons API
  console.log("Spotify API Response:", JSON.stringify(data, null, 2));

  if (!data.items) {
    throw new Error("⚠️ Spotify response missing 'items'. Mungkin token tidak valid atau scope tidak mencakup 'user-read-recently-played'.");
  }

  return data.items.map(item => {
    const track = item.track;
    return {
      title: track.name,
      artist: track.artists.map(artist => artist.name).join(", "),
      albumImageUrl: track.album.images[0].url,
      playedAt: new Date(item.played_at).toLocaleString("id-ID", { timeZone: "Asia/Jakarta" }),
    };
  });
};

const updateReadme = async () => {
  const songs = await fetchSpotify();

  const markdown = `
<table>
  <thead>
    <tr>
      <th>🎵 Judul Lagu</th>
      <th>🎤 Artis</th>
      <th>⏱️ Waktu</th>
    </tr>
  </thead>
  <tbody>
    ${songs
      .map(
        song => `
    <tr>
      <td><img src="${song.albumImageUrl}" width="20" /> ${song.title}</td>
      <td>${song.artist}</td>
      <td>${song.playedAt}</td>
    </tr>`
      )
      .join("")}
  </tbody>
</table>
`.trim();

  const readme = fs.readFileSync("README.md", "utf-8");

  const newReadme = readme.replace(
    /<!--START_SECTION:spotify-->[\s\S]*<!--END_SECTION:spotify-->/,
    `<!--START_SECTION:spotify-->\n\n${markdown}\n\n<!--END_SECTION:spotify-->`
  );

  fs.writeFileSync("README.md", newReadme);
};

updateReadme().catch(error => {
  console.error(error);
  process.exit(1);
});
