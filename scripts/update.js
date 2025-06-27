const fs = require("fs");
const path = require("path");

// 🎵 Ganti ini nanti kalau sudah ambil dari Spotify API secara live
const data = [
  {
    title: "RE FORRO",
    artist: "CA7RIEL & Paco Amoroso",
    time: "59 sec ago",
    cover: "https://i.scdn.co/image/ab67616d00001e0202e228d55f8d560e0e7ed5b3",
  },
  {
    title: "BABY GANGSTA",
    artist: "CA7RIEL & Paco Amoroso",
    time: "5 min ago",
    cover: "https://i.scdn.co/image/ab67616d00001e02a97dd39032ef94d184701d95",
  },
  {
    title: "EL ÚNICO",
    artist: "CA7RIEL & Paco Amoroso",
    time: "7 min ago",
    cover: "https://i.scdn.co/image/ab67616d00001e02a97dd39032ef94d184701d95",
  },
  {
    title: "Welcome to the Black Parade",
    artist: "My Chemical Romance",
    time: "10 min ago",
    cover: "https://i.scdn.co/image/ab67616d00001e0278126e50c02dbeb62fc9a8c2",
  },
  {
    title: "Guggenheim Assemble",
    artist: "Daniel Pemberton",
    time: "36 min ago",
    cover: "https://i.scdn.co/image/ab67616d00001e021d7fc15118a5a9f4d6de0864",
  }
];

const tableHeader = `
<table>
  <thead>
    <tr>
      <th>🎵 Judul Lagu</th>
      <th>🎤 Artis</th>
      <th>⏱️ Waktu</th>
    </tr>
  </thead>
  <tbody>
`;

const tableFooter = `
  </tbody>
</table>
`;

const rows = data.map(song => `
  <tr>
    <td><img src="${song.cover}" width="20" /> ${song.title}</td>
    <td>${song.artist}</td>
    <td>${song.time}</td>
  </tr>
`).join("");

const fullTable = tableHeader + rows + tableFooter;

const readmePath = path.join(__dirname, "..", "README.md");
let readme = fs.readFileSync(readmePath, "utf8");

readme = readme.replace(
  /<!--START_SECTION:spotify-->[\s\S]*<!--END_SECTION:spotify-->/,
  `<!--START_SECTION:spotify-->\n${fullTable}\n<!--END_SECTION:spotify-->`
);

fs.writeFileSync(readmePath, readme);
console.log("✅ Updated README with Spotify data");
