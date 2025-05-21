function SongList({ songs }) {
  return (
    <ul>
      {songs.map((song) => (
        <li key={song.id}>
          {song.artist} – {song.title} ({song.genre}, {song.release_year})
        </li>
      ))}
    </ul>
  );
}

export default SongList;

