import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

// Создаем локальный экземпляр axios
const api = axios.create({
    baseURL: 'http://localhost:8001',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Добавляем интерцептор для токена
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

interface Album {
    id: number;
    title: string;
    release_date?: string;
    cover_image_url?: string;
    created_at: string;
}

interface Track {
    id: number;
    title: string;
    album_id?: number;
    duration_ms?: number;
    explicit: boolean;
    popularity: number;
    created_at: string;
}

const ArtistDashboard: React.FC = () => {
    const [albums, setAlbums] = useState<Album[]>([]);
    const [tracks, setTracks] = useState<Track[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [artistStats, setArtistStats] = useState<any>(null);

    const artistId = localStorage.getItem('artist_id');

    const fetchArtistContent = async () => {
        if (!artistId) return;

        try {
            setLoading(true);
            
            // Получаем альбомы артиста
            const albumsResponse = await api.get(`/api/v1/albums/artist/${artistId}`);
            setAlbums(albumsResponse.data);

            // Получаем треки артиста
            const tracksResponse = await api.get(`/api/v1/artists/${artistId}/tracks`);
            setTracks(tracksResponse.data);

            // Получаем статистику артиста (если есть такой эндпоинт)
            try {
                const statsResponse = await api.get(`/api/v1/artists/${artistId}/stats`);
                setArtistStats(statsResponse.data);
            } catch (statsError) {
                console.log('Stats endpoint not available');
            }

        } catch (err: any) {
            console.error("Failed to fetch artist content:", err);
            setError("Не удалось загрузить контент артиста.");
        } finally {
            setLoading(false);
        }
    };

    const deleteTrack = async (trackId: number) => {
        if (!window.confirm('Вы уверены, что хотите удалить этот трек?')) return;

        try {
            await api.delete(`/api/v1/tracks/${trackId}`);
            setTracks(tracks.filter(track => track.id !== trackId));
        } catch (err: any) {
            console.error("Failed to delete track:", err);
            alert("Не удалось удалить трек.");
        }
    };

    const deleteAlbum = async (albumId: number) => {
        if (!window.confirm('Вы уверены, что хотите удалить этот альбом? Все треки в альбоме также будут удалены.')) return;

        try {
            await api.delete(`/api/v1/albums/${albumId}`);
            setAlbums(albums.filter(album => album.id !== albumId));
            // Обновляем список треков, удаляя треки из удаленного альбома
            setTracks(tracks.filter(track => track.album_id !== albumId));
        } catch (err: any) {
            console.error("Failed to delete album:", err);
            alert("Не удалось удалить альбом.");
        }
    };

    useEffect(() => {
        fetchArtistContent();
    }, [artistId]);

    if (loading) {
        return <div>Загрузка контента артиста...</div>;
    }

    return (
        <div style={{ marginTop: '20px' }}>
            <h2>Панель артиста</h2>
            {error && <p style={{ color: 'red' }}>{error}</p>}

            {/* Статистика */}
            {artistStats && (
                <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
                    gap: '15px', 
                    marginBottom: '20px' 
                }}>
                    <div style={{ 
                        padding: '15px', 
                        backgroundColor: '#333', 
                        borderRadius: '8px', 
                        textAlign: 'center' 
                    }}>
                        <h4>Треков</h4>
                        <p style={{ fontSize: '24px', margin: '0', color: '#1DB954' }}>
                            {artistStats.total_tracks || tracks.length}
                        </p>
                    </div>
                    <div style={{ 
                        padding: '15px', 
                        backgroundColor: '#333', 
                        borderRadius: '8px', 
                        textAlign: 'center' 
                    }}>
                        <h4>Альбомов</h4>
                        <p style={{ fontSize: '24px', margin: '0', color: '#1DB954' }}>
                            {artistStats.total_albums || albums.length}
                        </p>
                    </div>
                </div>
            )}

            <div style={{ marginBottom: '20px' }}>
                <h3>Быстрые действия</h3>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <Link 
                        to="/edit-artist-profile" 
                        style={{ 
                            padding: '10px 20px', 
                            backgroundColor: '#4CAF50', 
                            color: 'white', 
                            textDecoration: 'none', 
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: 'bold'
                        }}
                    >
                        🎨 Редактировать профиль
                    </Link>
                    <Link 
                        to="/upload-album" 
                        style={{ 
                            padding: '10px 20px', 
                            backgroundColor: '#2196F3', 
                            color: 'white', 
                            textDecoration: 'none', 
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: 'bold'
                        }}
                    >
                        💿 Создать альбом
                    </Link>
                    <Link 
                        to="/upload-track" 
                        style={{ 
                            padding: '10px 20px', 
                            backgroundColor: '#FF9800', 
                            color: 'white', 
                            textDecoration: 'none', 
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: 'bold'
                        }}
                    >
                        🎵 Загрузить трек
                    </Link>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                {/* Альбомы */}
                <div>
                    <h3>Мои альбомы ({albums.length})</h3>
                    {albums.length === 0 ? (
                        <p style={{ color: '#ccc' }}>У вас пока нет альбомов.</p>
                    ) : (
                        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                            {albums.map((album) => (
                                <div 
                                    key={album.id} 
                                    style={{ 
                                        padding: '10px', 
                                        marginBottom: '10px', 
                                        backgroundColor: '#333', 
                                        borderRadius: '4px' 
                                    }}
                                >
                                    <h4 style={{ margin: '0 0 5px 0' }}>{album.title}</h4>
                                    <p style={{ margin: '0', color: '#ccc', fontSize: '14px' }}>
                                        ID: {album.id} | 
                                        Создан: {new Date(album.created_at).toLocaleDateString()}
                                        {album.release_date && ` | Выпуск: ${new Date(album.release_date).toLocaleDateString()}`}
                                    </p>
                                    {album.cover_image_url && (
                                        <img 
                                            src={album.cover_image_url} 
                                            alt={album.title}
                                            style={{ width: '50px', height: '50px', objectFit: 'cover', marginTop: '5px' }}
                                            onError={(e) => {
                                                (e.target as HTMLImageElement).style.display = 'none';
                                            }}
                                        />
                                    )}
                                    <button
                                        onClick={() => deleteAlbum(album.id)}
                                        style={{
                                            marginTop: '10px',
                                            padding: '5px 10px',
                                            backgroundColor: '#f44336',
                                            color: 'white',
                                            border: 'none',
                                            borderRadius: '4px',
                                            cursor: 'pointer',
                                            fontSize: '12px'
                                        }}
                                    >
                                        🗑️ Удалить альбом
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Треки */}
                <div>
                    <h3>Мои треки ({tracks.length})</h3>
                    {tracks.length === 0 ? (
                        <p style={{ color: '#ccc' }}>У вас пока нет треков.</p>
                    ) : (
                        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                            {tracks.map((track) => (
                                <div 
                                    key={track.id} 
                                    style={{ 
                                        padding: '10px', 
                                        marginBottom: '10px', 
                                        backgroundColor: '#333', 
                                        borderRadius: '4px' 
                                    }}
                                >
                                    <h4 style={{ margin: '0 0 5px 0' }}>
                                        {track.title}
                                        {track.explicit && <span style={{ color: 'red', marginLeft: '5px' }}>[E]</span>}
                                    </h4>
                                    <p style={{ margin: '0', color: '#ccc', fontSize: '14px' }}>
                                        ID: {track.id} | 
                                        Популярность: {track.popularity}
                                        {track.duration_ms && ` | ${Math.floor(track.duration_ms / 60000)}:${Math.floor((track.duration_ms % 60000) / 1000).toString().padStart(2, '0')}`}
                                        {track.album_id && ` | Альбом ID: ${track.album_id}`}
                                    </p>
                                    <p style={{ margin: '0', color: '#ccc', fontSize: '12px' }}>
                                        Создан: {new Date(track.created_at).toLocaleDateString()}
                                    </p>
                                    <button
                                        onClick={() => deleteTrack(track.id)}
                                        style={{
                                            marginTop: '10px',
                                            padding: '5px 10px',
                                            backgroundColor: '#f44336',
                                            color: 'white',
                                            border: 'none',
                                            borderRadius: '4px',
                                            cursor: 'pointer',
                                            fontSize: '12px'
                                        }}
                                    >
                                        🗑️ Удалить трек
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ArtistDashboard;
