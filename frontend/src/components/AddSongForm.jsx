import { useState } from "react";
import { createSong } from "../api/musicService";

function AddSongForm({ onAdd }) {
  const [form, setForm] = useState({
    title: "",
    artist: "",
    genre: "",
    release_year: ""
  });

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.title || !form.artist) return;
    const newSong = await createSong({
      ...form,
      release_year: Number(form.release_year)
    });
    onAdd(newSong);
    setForm({ title: "", artist: "", genre: "", release_year: "" });
  }

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: "20px" }}>
      <input
        name="title"
        placeholder="Название"
        value={form.title}
        onChange={handleChange}
        required
      />
      <input
        name="artist"
        placeholder="Исполнитель"
        value={form.artist}
        onChange={handleChange}
        required
      />
      <input
        name="genre"
        placeholder="Жанр"
        value={form.genre}
        onChange={handleChange}
      />
      <input
        name="release_year"
        type="number"
        placeholder="Год выпуска"
        value={form.release_year}
        onChange={handleChange}
      />
      <button type="submit">Добавить песню</button>
    </form>
  );
}

export default AddSongForm;

