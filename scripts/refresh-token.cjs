import 'dotenv/config';
import fetch from 'node-fetch';
import fs from 'fs';

const clientId = process.env.SPOTIFY_CLIENT_ID;
const clientSecret = process.env.SPOTIFY_CLIENT_SECRET;
const refreshToken = process.env.SPOTIFY_REFRESH_TOKEN;

const basic = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

const response = await fetch('https://accounts.spotify.com/api/token', {
  method: 'POST',
  headers: {
    Authorization: `Basic ${basic}`,
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    grant_type: 'refresh_token',
    refresh_token: refreshToken,
  }),
});

if (!response.ok) {
  const err = await response.json();
  console.error(`❌ Gagal refresh token:`, err);
  process.exit(1);
}

const data = await response.json();
console.log(`access_token=${data.access_token}`);
