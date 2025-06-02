import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

interface Track {
    id: number;
    title: string;
    artist_id: number;
    album_id: number;
    genre_id: number;
    duration_ms: number;
    file_path: string;
    spotify_id: string;
    preview_url: string;
    explicit: boolean;
    popularity: number;
    tempo: number;
    energy: number;
    valence: number;
    danceability: number;
    created_at: string;
}

const TrackDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [track, setTrack] = useState<Track | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchTrack = async () => {
            try {
                const response = await axios.get<Track>(`http://localhost:8000/api/v1/tracks/${id}`);
                setTrack(response.data);
            } catch (err) {
                setError('Не удалось загрузить информацию о треке.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        if (id) {
            fetchTrack();
        }
    }, [id]);

    if (loading) return <div className="page-content">Загрузка трека...</div>;
    if (error) return <div className="page-content" style={{ color: 'red' }}>{error}</div>;
    if (!track) return <div className="page-content">Трек не найден.</div>;

    return (
        <div className="page-content track-detail-page">
            <h1>{track.title}</h1>
            <p>ID: {track.id}</p>
            <p>Длительность: {(track.duration_ms / 60000).toFixed(2)} мин</p>
            {/* Дополнительная информация о треке */}
            {track.file_path && <audio controls src={`http://localhost:8000/${track.file_path}`}></audio>}
        </div>
    );
};

export default TrackDetailPage; 