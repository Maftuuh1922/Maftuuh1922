const axios = require('axios');
require('dotenv').config();

const {
  SPOTIFY_CLIENT_ID,
  SPOTIFY_CLIENT_SECRET,
  SPOTIFY_REFRESH_TOKEN
} = process.env;

async function refreshToken() {
  const response = await axios.post('https://accounts.spotify.com/api/token',
    new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: SPOTIFY_REFRESH_TOKEN,
    }),
    {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Authorization: 'Basic ' + Buffer.from(`${SPOTIFY_CLIENT_ID}:${SPOTIFY_CLIENT_SECRET}`).toString('base64'),
      },
    }
  );

  const data = response.data;
  console.log(`access_token=${data.access_token}`);
  if (data.refresh_token) {
    console.log(`refresh_token=${data.refresh_token}`);
  }
}

refreshToken().catch(err => {
  console.error('❌ Gagal refresh token:', err.response?.data || err.message);
  process.exit(1);
});
