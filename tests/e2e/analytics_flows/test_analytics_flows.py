import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import asyncio


@pytest.mark.e2e
@pytest.mark.etl
class TestAnalyticsFlows:
    """E2E тесты аналитических процессов"""

    async def test_complete_etl_pipeline_flow(self, mock_clickhouse_service, mock_s3_service):
        """Полный сценарий ETL pipeline"""
        mock_s3_tracks = [
            {
                'key': 'tracks/user1/track1.mp3',
                'metadata': {
                    'title': 'Test Track 1',
                    'artist': 'Test Artist',
                    'duration': 180,
                    'upload_date': '2024-01-01T10:00:00Z'
                }
            },
            {
                'key': 'tracks/user2/track2.mp3', 
                'metadata': {
                    'title': 'Test Track 2',
                    'artist': 'Another Artist',
                    'duration': 210,
                    'upload_date': '2024-01-01T11:00:00Z'
                }
            }
        ]
        
        listening_events = [
            {
                'user_id': 1,
                'track_id': 'track1',
                'event_type': 'play',
                'timestamp': datetime.now() - timedelta(hours=1),
                'duration': 180,
                'platform': 'web',
                'location': 'US'
            },
            {
                'user_id': 2,
                'track_id': 'track1',
                'event_type': 'play',
                'timestamp': datetime.now() - timedelta(hours=2),
                'duration': 150,
                'platform': 'mobile',
                'location': 'UK'
            },
            {
                'user_id': 1,
                'track_id': 'track2',
                'event_type': 'skip',
                'timestamp': datetime.now() - timedelta(minutes=30),
                'duration': 45,
                'platform': 'web',
                'location': 'US'
            }
        ]
        
        track_stats = {}
        for event in listening_events:
            track_id = event['track_id']
            if track_id not in track_stats:
                track_stats[track_id] = {
                    'total_plays': 0,
                    'total_duration': 0,
                    'unique_listeners': set(),
                    'platforms': set(),
                    'locations': set()
                }
            
            track_stats[track_id]['total_plays'] += 1
            track_stats[track_id]['total_duration'] += event['duration']
            track_stats[track_id]['unique_listeners'].add(event['user_id'])
            track_stats[track_id]['platforms'].add(event['platform'])
            track_stats[track_id]['locations'].add(event['location'])
        
        for stats in track_stats.values():
            stats['unique_listeners'] = len(stats['unique_listeners'])
            stats['platforms'] = len(stats['platforms'])
            stats['locations'] = len(stats['locations'])
        
        mock_clickhouse_service.insert_user_activity.return_value = True
        mock_clickhouse_service.insert_track_stats.return_value = True
        
        result = await mock_clickhouse_service.insert_user_activity(listening_events)
        assert result is True
        
        aggregated_data = [
            {
                'track_id': track_id,
                'date': datetime.now().date(),
                **stats
            }
            for track_id, stats in track_stats.items()
        ]
        
        result = await mock_clickhouse_service.insert_track_stats(aggregated_data)
        assert result is True
        
        assert len(track_stats) == 2
        assert track_stats['track1']['total_plays'] == 2
        assert track_stats['track1']['unique_listeners'] == 2
        assert track_stats['track2']['total_plays'] == 1
        assert track_stats['track2']['unique_listeners'] == 1

    async def test_real_time_analytics_flow(self, mock_clickhouse_service):
        """Сценарий real-time аналитики"""
        real_time_events = []

        for i in range(20):
            event = {
                'user_id': (i % 5) + 1,  
                'track_id': f'track_{(i % 3) + 1}',  
                'event_type': 'play' if i % 3 != 0 else 'skip',
                'timestamp': datetime.now() - timedelta(minutes=i//2),
                'duration': 180 if i % 3 != 0 else 30,
                'platform': 'web' if i % 2 == 0 else 'mobile'
            }
            real_time_events.append(event)
        
        batch_size = 5
        batches = [
            real_time_events[i:i + batch_size]
            for i in range(0, len(real_time_events), batch_size)
        ]
        
        mock_clickhouse_service.insert_user_activity_batch.return_value = {
            'inserted_rows': batch_size,
            'execution_time': 0.1,
            'success': True
        }
        
        processed_batches = 0
        for batch in batches:
            result = await mock_clickhouse_service.insert_user_activity_batch(batch)
            assert result['success'] is True
            processed_batches += 1
        
        assert processed_batches == 4  
        
        mock_clickhouse_service.get_realtime_analytics.return_value = {
            'current_listeners': 3,
            'active_tracks': 3,
            'events_last_minute': 8,
            'events_last_hour': 20,
            'top_track_now': {
                'track_id': 'track_1',
                'current_plays': 7
            }
        }
        
        realtime_data = await mock_clickhouse_service.get_realtime_analytics()
        
        assert realtime_data['current_listeners'] > 0
        assert realtime_data['events_last_hour'] == 20
        assert 'top_track_now' in realtime_data

    async def test_daily_aggregation_flow(self, mock_clickhouse_service):
        """Сценарий ежедневной агрегации данных"""
        yesterday = datetime.now() - timedelta(days=1)
        daily_events = []
        
        for hour in range(24):
            for minute in range(0, 60, 15):  
                event_time = yesterday.replace(hour=hour, minute=minute, second=0)
                
                num_events = 1 if hour < 18 else 3
                
                for _ in range(num_events):
                    event = {
                        'user_id': (hour % 10) + 1,
                        'track_id': f'track_{(minute % 5) + 1}',
                        'event_type': 'play',
                        'timestamp': event_time,
                        'duration': 180,
                        'platform': 'web' if hour % 2 == 0 else 'mobile'
                    }
                    daily_events.append(event)
        
        hourly_stats = {}
        for event in daily_events:
            hour = event['timestamp'].hour
            if hour not in hourly_stats:
                hourly_stats[hour] = {
                    'hour': hour,
                    'total_plays': 0,
                    'unique_users': set(),
                    'unique_tracks': set(),
                    'web_plays': 0,
                    'mobile_plays': 0
                }
            
            stats = hourly_stats[hour]
            stats['total_plays'] += 1
            stats['unique_users'].add(event['user_id'])
            stats['unique_tracks'].add(event['track_id'])
            
            if event['platform'] == 'web':
                stats['web_plays'] += 1
            else:
                stats['mobile_plays'] += 1
        
        for stats in hourly_stats.values():
            stats['unique_users'] = len(stats['unique_users'])
            stats['unique_tracks'] = len(stats['unique_tracks'])
        
        mock_clickhouse_service.insert_hourly_stats.return_value = True
        
        hourly_data = list(hourly_stats.values())
        result = await mock_clickhouse_service.insert_hourly_stats(
            yesterday.date(), hourly_data
        )
        assert result is True
        
        assert len(hourly_stats) == 24  
        
        evening_hours = [stats for hour, stats in hourly_stats.items() if hour >= 18]
        morning_hours = [stats for hour, stats in hourly_stats.items() if hour < 12]
        
        avg_evening_plays = sum(s['total_plays'] for s in evening_hours) / len(evening_hours)
        avg_morning_plays = sum(s['total_plays'] for s in morning_hours) / len(morning_hours)
        
        assert avg_evening_plays > avg_morning_plays

    async def test_user_behavior_analysis_flow(self, mock_clickhouse_service):
        """Сценарий анализа поведения пользователей"""
        user_id = 1
        user_events = []
        
        for day in range(7):
            date = datetime.now() - timedelta(days=day)
            
            if date.weekday() < 5: 
                listening_sessions = 3
                session_length = 60  
            else:  
                listening_sessions = 5
                session_length = 90
            
            for session in range(listening_sessions):
                session_start = date.replace(
                    hour=9 + session * 3,
                    minute=0,
                    second=0
                )
                
                for minute in range(0, session_length, 4):  
                    event_time = session_start + timedelta(minutes=minute)
                    event = {
                        'user_id': user_id,
                        'track_id': f'track_{(minute // 4) % 10 + 1}',
                        'event_type': 'play' if minute % 12 != 8 else 'skip',
                        'timestamp': event_time,
                        'duration': 240 if minute % 12 != 8 else 60,
                        'platform': 'mobile' if date.weekday() >= 5 else 'web',
                        'session_id': f'session_{day}_{session}'
                    }
                    user_events.append(event)
        
        behavior_patterns = {
            'listening_sessions': {},
            'track_preferences': {},
            'time_patterns': {},
            'platform_usage': {'web': 0, 'mobile': 0},
            'completion_rates': {'full': 0, 'partial': 0}
        }
        
        sessions = {}
        for event in user_events:
            session_id = event['session_id']
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(event)
        
        behavior_patterns['listening_sessions']['total'] = len(sessions)
        behavior_patterns['listening_sessions']['avg_length'] = sum(
            len(session) for session in sessions.values()
        ) / len(sessions)
        
        for event in user_events:
            track_id = event['track_id']
            if track_id not in behavior_patterns['track_preferences']:
                behavior_patterns['track_preferences'][track_id] = 0
            behavior_patterns['track_preferences'][track_id] += 1
            
            behavior_patterns['platform_usage'][event['platform']] += 1
            
            if event['duration'] > 200:
                behavior_patterns['completion_rates']['full'] += 1
            else:
                behavior_patterns['completion_rates']['partial'] += 1
        
        user_profile = {
            'user_id': user_id,
            'analysis_date': datetime.now().date(),
            'total_events': len(user_events),
            'listening_sessions_per_week': behavior_patterns['listening_sessions']['total'],
            'avg_session_length': behavior_patterns['listening_sessions']['avg_length'],
            'favorite_tracks': sorted([
                (track_id, count) for track_id, count 
                in behavior_patterns['track_preferences'].items()
            ], key=lambda x: x[1], reverse=True)[:5],
            'platform_preference': 'mobile' if behavior_patterns['platform_usage']['mobile'] > behavior_patterns['platform_usage']['web'] else 'web',
            'completion_rate': behavior_patterns['completion_rates']['full'] / len(user_events)
        }
        
        mock_clickhouse_service.update_user_profile.return_value = True
        result = await mock_clickhouse_service.update_user_profile(user_profile)
        assert result is True
        
        assert user_profile['total_events'] > 0
        assert user_profile['listening_sessions_per_week'] == 7 * 3 + 2 * 5  
        assert len(user_profile['favorite_tracks']) > 0
        assert user_profile['completion_rate'] > 0

    @pytest.mark.slow
    async def test_large_scale_analytics_flow(self, mock_clickhouse_service):
        """Сценарий аналитики больших объемов данных"""
        large_dataset = []
        num_users = 1000
        num_tracks = 500
        days_back = 30
        
        for day in range(days_back):
            date = datetime.now() - timedelta(days=day)
            
            events_per_day = 5000 + (day % 7) * 1000  
            
            for _ in range(events_per_day):
                event = {
                    'user_id': (hash(f"{day}_{_}") % num_users) + 1,
                    'track_id': f'track_{(hash(f"{_}_{day}") % num_tracks) + 1}',
                    'event_type': 'play' if _ % 4 != 0 else 'skip',
                    'timestamp': date + timedelta(
                        hours=hash(f"{day}_{_}") % 24,
                        minutes=hash(f"{_}") % 60
                    ),
                    'duration': 180 if _ % 4 != 0 else 45,
                    'platform': ['web', 'mobile', 'desktop'][hash(f"{day}_{_}") % 3],
                    'location': ['US', 'UK', 'CA', 'DE', 'FR'][hash(f"{_}") % 5]
                }
                large_dataset.append(event)
        
        total_events = len(large_dataset)
        assert total_events > 100000  
        
        batch_size = 10000
        batches = [
            large_dataset[i:i + batch_size]
            for i in range(0, total_events, batch_size)
        ]
        
        mock_clickhouse_service.insert_user_activity_batch.return_value = {
            'inserted_rows': batch_size,
            'execution_time': 0.5,
            'success': True
        }
        
        async def process_batch(batch):
            return await mock_clickhouse_service.insert_user_activity_batch(batch)
        
        semaphore = asyncio.Semaphore(5)
        
        async def process_batch_with_limit(batch):
            async with semaphore:
                return await process_batch(batch)
        
        tasks = [process_batch_with_limit(batch) for batch in batches]
        results = await asyncio.gather(*tasks)
        
        assert all(result['success'] for result in results)
        assert len(results) == len(batches)
        
        regional_stats = {}
        for event in large_dataset[:10000]:  
            location = event['location']
            track_id = event['track_id']
            
            if location not in regional_stats:
                regional_stats[location] = {}
            if track_id not in regional_stats[location]:
                regional_stats[location][track_id] = 0
            
            regional_stats[location][track_id] += 1
        
        regional_top_tracks = {}
        for location, tracks in regional_stats.items():
            regional_top_tracks[location] = sorted(
                tracks.items(), key=lambda x: x[1], reverse=True
            )[:5]
        
        mock_clickhouse_service.save_regional_analytics.return_value = True
        result = await mock_clickhouse_service.save_regional_analytics(regional_top_tracks)
        assert result is True
        
        assert len(regional_stats) == 5 
        assert all(len(tracks) <= 5 for tracks in regional_top_tracks.values())

    async def test_data_quality_monitoring_flow(self, mock_clickhouse_service):
        """Сценарий мониторинга качества данных"""
        test_events = [
            {
                'user_id': 1,
                'track_id': 'track_1',
                'event_type': 'play',
                'timestamp': datetime.now(),
                'duration': 180,
                'platform': 'web'
            },
            {
                'user_id': None,
                'track_id': 'track_2',
                'event_type': 'play',
                'timestamp': datetime.now(),
                'duration': 180,
                'platform': 'web'
            },
            {
                'user_id': 2,
                'track_id': 'track_3',
                'event_type': 'play',
                'timestamp': datetime.now(),
                'duration': -10,  
                'platform': 'mobile'
            },
            {
                'user_id': 3,
                'track_id': 'track_4',
                'event_type': 'play',
                'timestamp': datetime(2020, 1, 1),  
                'duration': 200,
                'platform': 'web'
            },
            {
                'user_id': 1,
                'track_id': 'track_1',
                'event_type': 'play',
                'timestamp': datetime.now(),
                'duration': 180,
                'platform': 'web'
            }
        ]
        
        quality_issues = {
            'missing_user_id': 0,
            'invalid_duration': 0,
            'old_timestamps': 0,
            'duplicates': 0,
            'total_issues': 0
        }
        
        valid_events = []
        seen_events = set()
        
        for event in test_events:
            has_issues = False
            
            if event['user_id'] is None:
                quality_issues['missing_user_id'] += 1
                has_issues = True
            
            if event['duration'] < 0:
                quality_issues['invalid_duration'] += 1
                has_issues = True
            
            if event['timestamp'] < datetime.now() - timedelta(days=365):
                quality_issues['old_timestamps'] += 1
                has_issues = True
            
            event_key = (
                event['user_id'],
                event['track_id'],
                event['timestamp'].isoformat() if event['timestamp'] else None
            )
            if event_key in seen_events:
                quality_issues['duplicates'] += 1
                has_issues = True
            else:
                seen_events.add(event_key)
            
            if has_issues:
                quality_issues['total_issues'] += 1
            else:
                valid_events.append(event)
        
        quality_report = {
            'total_events': len(test_events),
            'valid_events': len(valid_events),
            'invalid_events': quality_issues['total_issues'],
            'data_quality_score': len(valid_events) / len(test_events),
            'issues_breakdown': quality_issues
        }
        
        mock_clickhouse_service.save_quality_report.return_value = True
        result = await mock_clickhouse_service.save_quality_report(quality_report)
        assert result is True
        
        assert quality_report['data_quality_score'] < 1.0  
        assert quality_report['issues_breakdown']['missing_user_id'] == 1
        assert quality_report['issues_breakdown']['invalid_duration'] == 1
        assert quality_report['issues_breakdown']['old_timestamps'] == 1
        assert quality_report['issues_breakdown']['duplicates'] == 1
        assert len(valid_events) == 1 
