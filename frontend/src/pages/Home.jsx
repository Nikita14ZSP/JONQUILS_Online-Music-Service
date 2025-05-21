import { useState, useEffect } from "react";
import SongList from "../components/SongList";
import SearchBar from "../components/SearchBar";
import { fetchSongs } from "../api/musicService";

function Home() {
  const [songs, setSongs] = useState([]);
  const [filteredSongs, setFilteredSongs] = useState([]);

  useEffect(() => {
    fetchSongs().then(data => {
      setSongs(data);
      setFilteredSongs(data);
    });
  }, []);

  function handleSearch(query) {
    const q = query.toLowerCase();
    setFilteredSongs(
      songs.filter(song =>
        song.title.toLowerCase().includes(q) || song.artist.toLowerCase().includes(q)
      )
    );
  }

  return (
    <div>
      <h1>🎵 Музыкальный сервис</h1>
      <SearchBar onSearch={handleSearch} />
      <SongList songs={filteredSongs} />
    </div>
  );
}

export default Home;

