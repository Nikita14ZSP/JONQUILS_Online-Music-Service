const API_BASE = "http://localhost:8000/music";

export async function fetchSongs() {
  const res = await fetch(API_BASE);
  return await res.json();
}

export async function createSong(song) {
  const res = await fetch(API_BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(song),
  });
  return await res.json();
}

