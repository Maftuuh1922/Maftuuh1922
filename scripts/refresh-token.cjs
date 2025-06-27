require('dotenv').config();
const axios = require('axios');
const fs = require('fs');

const {
  SPOTIFY_CLIENT_ID,
  SPOTIFY_CLIENT_SECRET,
  SPOTIFY_REFRESH_TOKEN,
} = process.env;

(async () => {
  console.log("📦 Refreshing Spotify access token...");

  try {
    const response = await axios.post(
      'https://accounts.spotify.com/api/token',
      new URLSearchParams({
        grant_type: 'refresh_token',
        refresh_token: SPOTIFY_REFRESH_TOKEN,
      }),
      {
        headers: {
          'Authorization': 'Basic ' + Buffer.from(`${SPOTIFY_CLIENT_ID}:${SPOTIFY_CLIENT_SECRET}`).toString('base64'),
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const accessToken = response.data.access_token;
    console.log(`✅ Access Token: ${accessToken}`);
    fs.writeFileSync('token.env', `access_token=${accessToken}`);
  } catch (error) {
    console.error("❌ Gagal refresh token:", error.response?.data || error.message);
    process.exit(1);
  }
})();
