from datetime import UTC, datetime

from fastapi.testclient import TestClient

from unloop.api.app import app
from unloop.core.language import guess_track_language
from unloop.core.scoring import DiscoveryScorer
from unloop.domain.models import Candidate, DiscoveryPreferences, LanguagePreference, Listen, Provider, RelatabilityLevel, Track

client = TestClient(app)

def _track(track_id: str, *, title: str, taste: float = 0.8, year: int = 2024, explicit: bool = False, genres=("electronic",)) -> Candidate:
    g = guess_track_language(title)
    return Candidate(track=Track(id=track_id,title=title,artist_id='a'+track_id,artist_name='Artist',provider=Provider.SPOTIFY,genres=genres,release_year=year,explicit=explicit,language=g.language,language_confidence=g.confidence),taste_similarity=taste)

def test_non_latin_title_is_detected_as_non_english() -> None:
    guess = guess_track_language('夜に駆ける')
    assert guess.language == 'non_english'
    assert guess.confidence > 0.75

def test_english_only_filters_high_confidence_non_english() -> None:
    prefs = DiscoveryPreferences(language_preference=LanguagePreference.ENGLISH_ONLY, relatability=RelatabilityLevel.OPEN)
    ranked = DiscoveryScorer(preferences=prefs).rank([_track('1', title='夜に駆ける'), _track('2', title='Love Again')], [], limit=10)
    assert [x.track.id for x in ranked] == ['2']

def test_release_explicit_and_genre_filters() -> None:
    prefs = DiscoveryPreferences(release_year_min=2020, allow_explicit=False, required_genres=('electronic',), relatability=RelatabilityLevel.OPEN, language_preference=LanguagePreference.ANY)
    ranked = DiscoveryScorer(preferences=prefs).rank([_track('1',title='Love Again',year=2010),_track('2',title='Love Again',explicit=True),_track('3',title='Love Again',genres=('country',)),_track('4',title='Love Again')], [], limit=10)
    assert [x.track.id for x in ranked] == ['4']

def test_close_relatability_filters_low_affinity() -> None:
    prefs = DiscoveryPreferences(relatability=RelatabilityLevel.CLOSE, language_preference=LanguagePreference.ANY)
    ranked = DiscoveryScorer(preferences=prefs).rank([_track('1',title='Love Again',taste=0.6), _track('2',title='Love Again',taste=0.8)], [], limit=10)
    assert [x.track.id for x in ranked] == ['2']

def test_home_contains_guided_filters() -> None:
    text = client.get('/').text
    assert 'English preferred' in text
    assert 'Stay close to my taste' in text
    assert 'Genre / scene' in text
