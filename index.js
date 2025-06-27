import fs from "fs";
import SpotifyWebApi from "spotify-web-api-node";

const spotifyApi = new SpotifyWebApi({
  clientId: process.env.SPOTIFY_CLIENT_ID,
  clientSecret: process.env.SPOTIFY_CLIENT_SECRET,
});

spotifyApi.setRefreshToken(process.env.SPOTIFY_REFRESH_TOKEN);

async function updateSpotify() {
  try {
    const data = await spotifyApi.refreshAccessToken();
    spotifyApi.setAccessToken(data.body.access_token);

    const recentlyPlayed = await spotifyApi.getMyRecentlyPlayedTracks({ limit: 5 });
    const items = recentlyPlayed.body.items;

    const markdown = `
### 🎧 Recently Played

| 🎵 Judul Lagu | 👨‍🎤 Artis | ⏱ Waktu |
|--------------|-----------------------------|-------------|
${items
  .map((item) => {
    const song = item.track;
    return `| ![](${song.album.images[2].url}) ${song.name} | ${song.artists.map(a => a.name).join(", ")} | ${formatTime(item.played_at)} |`;
  })
  .join("\n")}
`;

    const readme = fs.readFileSync("README.md", "utf8");
    const newReadme = readme.replace(
      /<!--START_SECTION:spotify-->[\s\S]*<!--END_SECTION:spotify-->/,
      `<!--START_SECTION:spotify-->\n${markdown}\n<!--END_SECTION:spotify-->`
    );

    fs.writeFileSync("README.md", newReadme);
    console.log("README.md updated successfully!");

  } catch (err) {
    console.error("Error updating Spotify:", err);
  }
}

function formatTime(time) {
  const date = new Date(time);
  return date.toLocaleTimeString("id-ID", { hour: '2-digit', minute: '2-digit' });
}

updateSpotify();
