from typing import List, Optional
from fastapi import HTTPException

from app.schemas.track import Track, TrackCreate, TrackUpdate

# Временное хранилище в памяти
FAKE_DB_TRACKS: List[Track] = [
    Track(id=1, title="Bohemian Rhapsody", artist_name="Queen", duration_ms=354000, genre="Rock", release_year=1975),
    Track(id=2, title="Stairway to Heaven", artist_name="Led Zeppelin", duration_ms=482000, genre="Rock", release_year=1971),
    Track(id=3, title="Smells Like Teen Spirit", artist_name="Nirvana", duration_ms=301000, genre="Grunge", release_year=1991),
    Track(id=4, title="Hotel California", artist_name="Eagles", duration_ms=390000, genre="Rock", release_year=1976),
    Track(id=5, title="Imagine", artist_name="John Lennon", duration_ms=183000, genre="Pop", release_year=1971),
]

class TrackService:
    def get_all_tracks(self, skip: int = 0, limit: int = 10) -> List[Track]:
        return FAKE_DB_TRACKS[skip : skip + limit]

    def get_track_by_id(self, track_id: int) -> Optional[Track]:
        for track in FAKE_DB_TRACKS:
            if track.id == track_id:
                return track
        return None

    def create_track(self, track_in: TrackCreate) -> Track:
        new_id = max(t.id for t in FAKE_DB_TRACKS) + 1 if FAKE_DB_TRACKS else 1
        new_track = Track(id=new_id, **track_in.model_dump())
        FAKE_DB_TRACKS.append(new_track)
        return new_track

    def update_track(self, track_id: int, track_in: TrackUpdate) -> Optional[Track]:
        track = self.get_track_by_id(track_id)
        if not track:
            return None
        
        update_data = track_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(track, key, value)
        return track

    def delete_track(self, track_id: int) -> Optional[Track]:
        track = self.get_track_by_id(track_id)
        if not track:
            return None
        FAKE_DB_TRACKS.remove(track)
        return track

    def search_tracks(self, query: str, genre: Optional[str] = None, year: Optional[int] = None, limit: int = 10) -> List[Track]:
        results = []
        for track in FAKE_DB_TRACKS:
            match = True
            if query.lower() not in track.title.lower() and (not track.artist_name or query.lower() not in track.artist_name.lower()):
                match = False
            
            if genre and (not track.genre or genre.lower() not in track.genre.lower()):
                match = False
            
            if year and track.release_year != year:
                match = False
            
            if match:
                results.append(track)
            
            if len(results) >= limit:
                break
        return results

track_service = TrackService() 