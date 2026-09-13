from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from unloop.core.config import Settings
from unloop.core.enrichment import MetadataEnrichmentService
from unloop.core.presets import PRESETS, preferences_for_mode
from unloop.core.taste import build_taste_clusters, calculate_artist_saturation
from unloop.core.service import DiscoveryService
from unloop.domain.models import (
    ArtistCooldown,
    DiscoveryMode,
    DiscoveryPreferences,
    FeedbackAction,
    EnrichmentReport,
    FeedbackEvent,
    RankedTrack,
    BatchAnalytics,
    StreamingService,
    StreamingServiceStatus,
    LanguagePreference,
    RelatabilityLevel,
)
from unloop.integrations.musicbrainz import MusicBrainzAPI
from unloop.integrations.listenbrainz import ListenBrainzAPI
from unloop.integrations.spotify.client import SpotifyAPI
from unloop.integrations.spotify.oauth import TOKEN_URL, create_pkce_request
from unloop.providers.mock import MockProvider
from unloop.providers.composite import CompositeCandidateProvider
from unloop.providers.listenbrainz import ListenBrainzCandidateProvider
from unloop.providers.spotify import SpotifyProvider
from unloop.storage import SQLiteStore

settings = Settings()
app = FastAPI(
    title="UNLOOP API",
    version="0.9.0-dev",
    description="Provider-agnostic music discovery optimized for novelty, not engagement.",
)

_provider = MockProvider()
_store = SQLiteStore(settings.database_path)
_service = DiscoveryService(_provider, _provider, _provider, store=_store)
_spotify_pending: dict[str, str] = {}
_spotify_tokens: dict[str, object] = {}




async def _refresh_spotify_token_if_needed() -> str:
    access_token = _spotify_tokens.get("access_token")
    expires_at = _spotify_tokens.get("expires_at")
    if not isinstance(access_token, str):
        raise HTTPException(status_code=409, detail="Spotify is not connected.")

    if isinstance(expires_at, datetime) and expires_at > datetime.now(UTC) + timedelta(seconds=60):
        return access_token

    refresh_token = _spotify_tokens.get("refresh_token")
    if not isinstance(refresh_token, str):
        # The current access token may still be usable even if Spotify omitted a refresh token.
        return access_token

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.spotify_client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.status_code >= 400:
        _spotify_tokens.clear()
        raise HTTPException(status_code=401, detail="Spotify session expired. Reconnect Spotify.")
    payload = response.json()
    _spotify_tokens["access_token"] = payload["access_token"]
    _spotify_tokens["expires_at"] = datetime.now(UTC) + timedelta(
        seconds=int(payload.get("expires_in", 3600))
    )
    if payload.get("refresh_token"):
        _spotify_tokens["refresh_token"] = payload["refresh_token"]
    return str(payload["access_token"])


async def _spotify_provider() -> SpotifyProvider:
    token = await _refresh_spotify_token_if_needed()
    return SpotifyProvider(SpotifyAPI(token), store=_store)


async def _live_discovery_service(
    preferences: DiscoveryPreferences | None = None,
) -> DiscoveryService:
    token = await _refresh_spotify_token_if_needed()
    spotify = SpotifyProvider(
        SpotifyAPI(token),
        store=_store,
        seed_genres=preferences.required_genres if preferences else (),
    )
    candidate_providers = [spotify]
    if settings.listenbrainz_username:
        lb = ListenBrainzAPI(token=settings.listenbrainz_token)
        candidate_providers.insert(0, ListenBrainzCandidateProvider(lb, spotify.api, settings.listenbrainz_username))
    candidates = CompositeCandidateProvider(candidate_providers)
    return DiscoveryService(spotify, candidates, spotify, store=_store)


class HealthResponse(BaseModel):
    status: str
    version: str


class PlaylistResponse(BaseModel):
    playlist_url: str
    tracks: list[RankedTrack]


class PhilosophyResponse(BaseModel):
    mission: str
    commitments: tuple[str, ...]
    non_goals: tuple[str, ...]


class SpotifyConnectionStart(BaseModel):
    authorization_url: str


class SpotifyConnectionStatus(BaseModel):
    configured: bool
    connected: bool
    persistent_tokens: bool = False


class EnrichmentStatus(BaseModel):
    cached_artists: int
    musicbrainz_enabled: bool


class ListenBrainzStatus(BaseModel):
    configured: bool
    username: str | None = None


class FeedbackRequest(BaseModel):
    track_id: str
    artist_id: str
    action: FeedbackAction
    artist_name: str | None = None
    cooldown_days: int | None = None




@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    return HTMLResponse(r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UNLOOP — Renew your taste</title>
<style>
:root{color-scheme:dark;--bg:#090a0c;--panel:#111318;--panel2:#171a20;--line:#292d35;--text:#f6f7f9;--muted:#939aa7;--good:#8ce8ad;--bad:#ff8e8e;--accent:#d9ff63}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}main{max-width:1080px;margin:auto;padding:42px 20px 90px}
a{color:inherit}.top{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.brand{font-size:56px;letter-spacing:-3px;font-weight:900;margin:0}.kicker{color:var(--accent);font-weight:850;text-transform:uppercase;letter-spacing:.12em;font-size:11px}.lead{font-size:21px;line-height:1.45;max-width:700px;color:#c8cdd5;margin-top:10px}.version{border:1px solid var(--line);border-radius:999px;padding:7px 10px;color:var(--muted);font-size:12px;white-space:nowrap}
.card{border:1px solid var(--line);background:var(--panel);border-radius:18px;padding:19px}.manifesto{border-left:3px solid var(--accent);margin:22px 0 34px}.muted{color:var(--muted)}h2{margin-top:34px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}.service{min-height:125px}.service.disabled{opacity:.45}.service.selected{outline:2px solid var(--accent)}.status{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}
.controls{display:grid;grid-template-columns:1fr 1fr;gap:12px}.wide{grid-column:1/-1}label{font-size:11px;color:var(--muted);display:block;margin-bottom:7px;text-transform:uppercase;letter-spacing:.08em}select,input{width:100%;padding:13px 14px;border-radius:11px;border:1px solid var(--line);background:#0c0e12;color:white;font:inherit}button,a.btn{border:1px solid transparent;border-radius:11px;padding:11px 15px;background:#252a31;color:white;font-weight:750;cursor:pointer;text-decoration:none;display:inline-block}button:hover,a.btn:hover{filter:brightness(1.08)}button:disabled{opacity:.5;cursor:not-allowed}button.primary{background:var(--accent);color:#090a0c}.chips{display:flex;gap:8px;flex-wrap:wrap}.chip{border:1px solid var(--line);border-radius:999px;padding:7px 10px;font-size:12px;color:#cbd0d8;background:#0c0e12}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:15px 0}.metric{background:var(--panel2);border-radius:13px;padding:14px}.metric strong{font-size:24px;display:block}.metric span{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.track{display:grid;grid-template-columns:58px 1fr auto;gap:14px;align-items:center;padding:14px 0;border-bottom:1px solid var(--line)}.art{width:58px;height:58px;border-radius:10px;object-fit:cover;background:#20242a}.track-title{font-weight:800}.track-meta{font-size:13px;color:var(--muted);margin-top:2px}.reason{font-size:12px;color:#bbc1ca;margin-top:5px}.actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}.actions button,.actions a{font-size:11px;padding:7px 9px}.actions .active-like{color:var(--good);border-color:var(--good)}.actions .active-bad{color:var(--bad);border-color:var(--bad)}.score{font-weight:850;font-variant-numeric:tabular-nums}.source{font-size:10px;color:var(--muted);max-width:170px;text-align:right;margin-top:4px}.hidden{display:none}.done{text-align:center;padding:34px 10px}.done h2{font-size:29px;margin-bottom:8px}.tabs{display:flex;gap:8px;margin:30px 0 12px}.tabs button.active{background:var(--accent);color:#090a0c}.panel{display:none}.panel.active{display:block}.cluster{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding:11px 0}.bar{height:7px;border-radius:999px;background:#242932;overflow:hidden;margin-top:6px}.bar>span{display:block;height:100%;background:var(--accent)}
@media(max-width:720px){.controls{grid-template-columns:1fr}.wide{grid-column:auto}.brand{font-size:46px}.top{display:block}.version{display:inline-block;margin-top:12px}.metrics{grid-template-columns:1fr 1fr}.track{grid-template-columns:50px 1fr}.art{width:50px;height:50px}.scorecol{display:none}}
</style></head><body><main>
<div class="top"><div><div class="kicker">Get back your time · Renew your taste</div><h1 class="brand">UNLOOP</h1><p class="lead">A streaming-service-agnostic discovery layer. No swiping. No doomscrolling. No ads. Ask for a finite batch, save it, then leave and listen.</p></div><div class="version">v0.9 dev</div></div>
<section class="card manifesto"><strong>Find music. Save the playlist. Leave.</strong><div class="muted" style="margin-top:7px">Success means better music found with less time spent inside UNLOOP.</div></section>
<div class="tabs"><button class="active" data-tab="discover">Discover</button><button data-tab="taste">Taste</button><button data-tab="analytics">Analytics</button></div>
<section id="discover" class="panel active">
<h2>Where you listen</h2><div id="services" class="grid"></div>
<h2>Build a finite batch</h2><section class="card"><div class="controls">
<div><label>Discovery mode</label><select id="mode"><option value="safe">Safe</option><option value="explore" selected>Explore</option><option value="deep_cut">Deep Cut</option><option value="chaos">Chaos</option></select></div>
<div><label>Tracks</label><select id="limit"><option>15</option><option selected>30</option><option>45</option></select></div>
<div><label>Language</label><select id="language"><option value="english_preferred" selected>English preferred</option><option value="english_only">English only · best effort</option><option value="any">Any language</option></select></div>
<div><label>Relatability</label><select id="relatability"><option value="close">Stay close to my taste</option><option value="balanced" selected>Balanced</option><option value="open">Open exploration</option></select></div>
<div><label>From year · optional</label><input id="yearMin" type="number" min="1900" max="2200" placeholder="2015"></div><div><label>To year · optional</label><input id="yearMax" type="number" min="1900" max="2200" placeholder="2026"></div>
<div class="wide"><label>Genre / scene · optional</label><input id="genre" maxlength="60" placeholder="electronic, R&B, indie…"></div>
<div class="wide"><label><input id="explicit" type="checkbox" checked style="width:auto;margin-right:8px">Allow explicit tracks</label></div>
<div class="wide"><label>Playlist name · leave blank for default</label><input id="playlistName" maxlength="100" placeholder="UNLOOP Discovery"></div>
<div class="wide"><div id="spotifyConnection" class="card" style="margin-bottom:12px;padding:14px"><strong>Spotify</strong> <span id="spotifyBadge" class="status">Checking…</span><div id="spotifyHint" class="muted" style="margin-top:5px">Checking connection status</div></div><button id="create" class="primary">Create discovery playlist</button> <button id="connect">Connect Spotify</button></div>
</div></section>
<section id="result" class="card hidden" style="margin-top:16px"><div id="summary"></div><div id="tracks"></div><div class="done"><h2>That’s it.</h2><p class="muted">No next feed. No swipe queue. Your finite batch is ready.</p><a id="openPlaylist" class="btn" target="_blank">Open playlist</a></div></section>
</section>
<section id="taste" class="panel"><section class="card"><div class="kicker">Your taste map</div><h2 style="margin-top:7px">Clusters, not a box.</h2><div id="tasteContent" class="muted">Connect your streaming service to load taste data.</div></section></section>
<section id="analytics" class="panel"><section class="card"><div class="kicker">Discovery yield</div><h2 style="margin-top:7px">Is UNLOOP actually finding good new music?</h2><div id="analyticsContent" class="muted">Create and rate a batch to build analytics.</div></section></section>
<p class="muted" style="margin-top:34px">Open-source developer build · <a href="/docs">API</a> · Spotify works today; Apple Music, Navidrome and Local Library remain provider adapters planned next.</p>
<script>
const $=s=>document.querySelector(s); const $$=s=>[...document.querySelectorAll(s)]; let lastTracks=[];
async function jsonFetch(url,opts){const r=await fetch(url,opts);let x={};try{x=await r.json()}catch{}if(!r.ok)throw new Error(x.detail||`Request failed (${r.status})`);return x}
async function loadServices(){try{const xs=await jsonFetch('/v1/streaming-services');$('#services').innerHTML=xs.map(x=>`<div class="card service ${x.available?'':'disabled'} ${x.connected?'selected':''}"><div class="status">${x.connected?'✓ Connected':x.status}</div><h3>${x.name}</h3><div class="muted">${x.connected?'Ready for discovery':(x.available?'Available now':'Provider adapter planned')}</div></div>`).join('');const sp=xs.find(x=>x.id==='spotify');if(sp?.connected){$('#spotifyBadge').textContent='✓ Connected';$('#spotifyBadge').style.color='var(--good)';$('#spotifyHint').textContent='Your Spotify account is connected and ready.';$('#connect').textContent='Spotify connected';$('#connect').disabled=true}else{$('#spotifyBadge').textContent='Not connected';$('#spotifyBadge').style.color='';$('#spotifyHint').textContent='Connect Spotify to build playlists from your listening history.';$('#connect').textContent='Connect Spotify';$('#connect').disabled=false}}catch(e){$('#spotifyBadge').textContent='Error';$('#spotifyHint').textContent=e.message}}
$('#connect').onclick=async()=>{try{const x=await jsonFetch('/v1/connections/spotify/start');location.href=x.authorization_url}catch(e){alert(e.message)}};
function trackUrl(t){return t.track.external_url||(`https://open.spotify.com/track/${encodeURIComponent(t.track.id)}`)}
async function sendFeedback(t,action,button){try{const body={track_id:t.track.id,artist_id:t.track.artist_id,artist_name:t.track.artist_name,action};if(action==='cooldown')body.cooldown_days=90;await jsonFetch('/v1/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});button.classList.add(action==='like'?'active-like':'active-bad');button.textContent=action==='cooldown'?'✓ 90d cooled':`✓ ${action}`;loadAnalytics()}catch(e){alert(e.message)}}
function renderTracks(xs){lastTracks=xs;$('#tracks').innerHTML=xs.map((t,i)=>`<div class="track"><img class="art" src="${t.track.image_url||''}" alt="" onerror="this.style.visibility='hidden'"><div><div class="track-title">${escapeHtml(t.track.title)}</div><div class="track-meta">${escapeHtml(t.track.artist_name)}${t.track.album_name?' · '+escapeHtml(t.track.album_name):''}</div><div class="reason">${(t.reasons||[]).slice(0,3).map(escapeHtml).join(' · ')}</div><div class="actions"><a class="btn" href="${trackUrl(t)}" target="_blank">Play ↗</a><button data-i="${i}" data-action="like">♡ Like</button><button data-i="${i}" data-action="skip">Skip</button><button data-i="${i}" data-action="dislike">Nope</button><button data-i="${i}" data-action="cooldown">Cool 90d</button></div></div><div class="scorecol"><div class="score">${Math.round(t.score.final_score*100)}</div><div class="source">${escapeHtml(t.source||'')}</div></div></div>`).join('');$$('.actions button').forEach(b=>b.onclick=()=>sendFeedback(lastTracks[+b.dataset.i],b.dataset.action,b))}
function escapeHtml(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
$('#create').onclick=async()=>{const q=new URLSearchParams({mode:$('#mode').value,limit:$('#limit').value,language_preference:$('#language').value,relatability:$('#relatability').value,allow_explicit:$('#explicit').checked?'true':'false'});const name=$('#playlistName').value.trim(),y1=$('#yearMin').value,y2=$('#yearMax').value,g=$('#genre').value.trim();if(name)q.set('playlist_name',name);if(y1)q.set('release_year_min',y1);if(y2)q.set('release_year_max',y2);if(g)q.set('genre',g);$('#create').disabled=true;$('#create').textContent='Building your finite batch…';try{const x=await jsonFetch('/v1/playlists/discovery?'+q,{method:'POST'});$('#summary').innerHTML=`<div class="kicker">Finite batch ready</div><h2>${x.tracks.length} tracks selected</h2><div class="chips"><span class="chip">${escapeHtml($('#mode').selectedOptions[0].text)}</span><span class="chip">${escapeHtml($('#language').selectedOptions[0].text)}</span><span class="chip">${escapeHtml($('#relatability').selectedOptions[0].text)}</span>${g?`<span class="chip">${escapeHtml(g)}</span>`:''}</div>`;renderTracks(x.tracks);$('#openPlaylist').href=x.playlist_url;$('#result').classList.remove('hidden');$('#result').scrollIntoView({behavior:'smooth'});loadAnalytics()}catch(e){alert(e.message)}finally{$('#create').disabled=false;$('#create').textContent='Create discovery playlist'}};
async function loadTaste(){try{const x=await jsonFetch('/v1/taste');const clusters=x.taste_clusters||[],sat=x.artist_saturation||[];$('#tasteContent').innerHTML=`<div class="metrics"><div class="metric"><strong>${x.recent_history?.unique_artists??0}</strong><span>Recent artists</span></div><div class="metric"><strong>${x.recent_history?.unique_tracks??0}</strong><span>Recent tracks</span></div><div class="metric"><strong>${x.metadata?.cached_artists??0}</strong><span>Enriched artists</span></div><div class="metric"><strong>${clusters.length}</strong><span>Taste clusters</span></div></div><h3>Taste clusters</h3>${clusters.length?clusters.map(c=>`<div class="cluster"><div><strong>${escapeHtml(c.name)}</strong><div class="muted" style="font-size:12px">${(c.evidence||[]).slice(0,4).map(escapeHtml).join(' · ')}</div><div class="bar"><span style="width:${Math.round(c.weight*100)}%"></span></div></div><strong>${Math.round(c.weight*100)}%</strong></div>`).join(''):'<p>No enriched clusters yet.</p>'}<h3>Most saturated artists</h3>${sat.slice(0,8).map(a=>`<div class="cluster"><span>${escapeHtml(a.artist_name)}</span><span>${Math.round(a.score)} · ${escapeHtml(a.status)}</span></div>`).join('')}` }catch(e){$('#tasteContent').textContent=e.message}}
async function loadAnalytics(){try{const xs=await jsonFetch('/v1/analytics/batches?limit=10');if(!xs.length){$('#analyticsContent').innerHTML='<p>No recorded batches yet.</p>';return}const latest=xs[0],rated=latest.liked+latest.disliked+latest.skipped;$('#analyticsContent').innerHTML=`<div class="metrics"><div class="metric"><strong>${Math.round(latest.novelty_rate*100)}%</strong><span>Novelty</span></div><div class="metric"><strong>${latest.new_artist_count}</strong><span>New artists</span></div><div class="metric"><strong>${latest.hit_rate==null?'—':Math.round(latest.hit_rate*100)+'%'}</strong><span>Hit rate</span></div><div class="metric"><strong>${rated}</strong><span>Rated</span></div></div><h3>Recent batches</h3>${xs.slice(0,6).map(b=>`<div class="cluster"><div><strong>${escapeHtml(b.mode)}</strong><div class="muted" style="font-size:12px">${new Date(b.created_at).toLocaleString()} · ${b.track_count} tracks</div></div><span>${Math.round(b.novelty_rate*100)}% new${b.hit_rate==null?'':' · '+Math.round(b.hit_rate*100)+'% hit'}</span></div>`).join('')}` }catch(e){$('#analyticsContent').textContent=e.message}}
$$('.tabs button').forEach(b=>b.onclick=()=>{$$('.tabs button').forEach(x=>x.classList.remove('active'));$$('.panel').forEach(x=>x.classList.remove('active'));b.classList.add('active');$('#'+b.dataset.tab).classList.add('active');if(b.dataset.tab==='taste')loadTaste();if(b.dataset.tab==='analytics')loadAnalytics()});
loadServices();window.addEventListener('focus',loadServices);document.addEventListener('visibilitychange',()=>{if(!document.hidden)loadServices()});window.addEventListener('pageshow',loadServices);
</script></main></body></html>""")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.9.0-dev")


@app.get("/v1/philosophy", response_model=PhilosophyResponse)
async def philosophy() -> PhilosophyResponse:
    return PhilosophyResponse(
        mission="Help people deliberately discover music without optimizing for engagement.",
        commitments=(
            "Free and open source",
            "Local-first preference and feedback data",
            "Explainable recommendations",
            "Provider independence",
            "No ads or sponsored ranking",
            "No paid placement",
            "No infinite scroll",
            "No swipe-to-discover feeds",
            "Finite discovery batches",
            "Streaming-service agnostic architecture",
            "No engagement-maximising ranking",
        ),
        non_goals=(
            "Maximise time in app",
            "Maximise clicks, streaks, or session length",
            "Build an advertising profile",
            "Lock taste data to one playback provider",
        ),
    )


@app.get("/v1/presets")
async def presets() -> list[dict[str, object]]:
    return [
        {
            "mode": preset.mode.value,
            "title": preset.title,
            "description": preset.description,
            "preferences": preset.preferences.model_dump(),
        }
        for preset in PRESETS.values()
    ]


@app.get("/v1/streaming-services", response_model=list[StreamingServiceStatus])
async def streaming_services() -> list[StreamingServiceStatus]:
    spotify_connected = "access_token" in _spotify_tokens
    return [
        StreamingServiceStatus(
            id=StreamingService.SPOTIFY, name="Spotify", available=True,
            connected=spotify_connected, status="connected" if spotify_connected else "ready",
            capabilities=("history", "catalogue", "playlist_export", "playback_handoff"),
        ),
        StreamingServiceStatus(
            id=StreamingService.APPLE_MUSIC, name="Apple Music", available=False,
            status="planned", capabilities=("history", "catalogue", "playlist_export", "playback_handoff"),
        ),
        StreamingServiceStatus(
            id=StreamingService.NAVIDROME, name="Navidrome", available=False,
            status="planned", capabilities=("history", "catalogue", "playlist_export"),
        ),
        StreamingServiceStatus(
            id=StreamingService.LOCAL, name="Local Library", available=False,
            status="planned", capabilities=("history", "catalogue", "playlist_export"),
        ),
    ]


@app.get("/v1/preferences", response_model=DiscoveryPreferences)
async def get_preferences() -> DiscoveryPreferences:
    return _store.load_preferences()


@app.put("/v1/preferences", response_model=DiscoveryPreferences)
async def put_preferences(preferences: DiscoveryPreferences) -> DiscoveryPreferences:
    _store.save_preferences(preferences)
    return preferences


@app.get("/v1/discover", response_model=list[RankedTrack])
async def discover(
    discovery_level: int | None = Query(default=None, ge=0, le=100),
    mode: DiscoveryMode | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    language_preference: LanguagePreference = LanguagePreference.ENGLISH_PREFERRED,
    relatability: RelatabilityLevel = RelatabilityLevel.BALANCED,
    release_year_min: int | None = Query(default=None, ge=1900, le=2200),
    release_year_max: int | None = Query(default=None, ge=1900, le=2200),
    allow_explicit: bool = True,
    genre: str | None = Query(default=None, max_length=60),
) -> list[RankedTrack]:
    preferences = preferences_for_mode(mode) if mode else _store.load_preferences()
    if discovery_level is not None:
        preferences.discovery_level = discovery_level
        preferences.mode = DiscoveryMode.CUSTOM
    preferences.language_preference = language_preference
    preferences.relatability = relatability
    preferences.release_year_min = release_year_min
    preferences.release_year_max = release_year_max
    preferences.allow_explicit = allow_explicit
    preferences.required_genres = (genre.strip(),) if genre and genre.strip() else ()
    service = await _live_discovery_service(preferences)
    return await service.generate(
        discovery_level=preferences.discovery_level,
        limit=limit,
        preferences=preferences,
    )


@app.post("/v1/playlists/discovery", response_model=PlaylistResponse)
async def create_discovery_playlist(
    discovery_level: int | None = Query(default=None, ge=0, le=100),
    mode: DiscoveryMode | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    playlist_name: str | None = Query(default=None, max_length=100),
    language_preference: LanguagePreference = LanguagePreference.ENGLISH_PREFERRED,
    relatability: RelatabilityLevel = RelatabilityLevel.BALANCED,
    release_year_min: int | None = Query(default=None, ge=1900, le=2200),
    release_year_max: int | None = Query(default=None, ge=1900, le=2200),
    allow_explicit: bool = True,
    genre: str | None = Query(default=None, max_length=60),
) -> PlaylistResponse:
    preferences = preferences_for_mode(mode) if mode else _store.load_preferences()
    if discovery_level is not None:
        preferences.discovery_level = discovery_level
        preferences.mode = DiscoveryMode.CUSTOM
    preferences.language_preference = language_preference
    preferences.relatability = relatability
    preferences.release_year_min = release_year_min
    preferences.release_year_max = release_year_max
    preferences.allow_explicit = allow_explicit
    preferences.required_genres = (genre.strip(),) if genre and genre.strip() else ()
    service = await _live_discovery_service(preferences)
    url, tracks = await service.publish(
        discovery_level=preferences.discovery_level,
        limit=limit,
        preferences=preferences,
        playlist_name=playlist_name,
    )
    return PlaylistResponse(playlist_url=url, tracks=tracks)


@app.post("/v1/feedback", response_model=FeedbackEvent)
async def feedback(request: FeedbackRequest) -> FeedbackEvent:
    now = datetime.now(UTC)
    cooldown_until: datetime | None = None
    if request.action is FeedbackAction.COOLDOWN:
        days = request.cooldown_days or 90
        if not 1 <= days <= 3650:
            raise HTTPException(status_code=422, detail="cooldown_days must be 1..3650")
        cooldown_until = now + timedelta(days=days)
        _store.set_artist_cooldown(
            ArtistCooldown(
                artist_id=request.artist_id,
                artist_name=request.artist_name or request.artist_id,
                until=cooldown_until,
                created_at=now,
            )
        )

    event = FeedbackEvent(
        track_id=request.track_id,
        artist_id=request.artist_id,
        action=request.action,
        created_at=now,
        cooldown_until=cooldown_until,
    )
    _store.record_feedback(event)
    _store.apply_feedback_to_recommendations(event)
    return event




@app.get("/v1/analytics/batches", response_model=list[BatchAnalytics])
async def batch_analytics(limit: int = Query(default=20, ge=1, le=100)) -> list[BatchAnalytics]:
    return _store.batch_analytics(limit=limit)


@app.get("/v1/recommendation-memory")
async def recommendation_memory() -> dict[str, int]:
    return {
        "remembered_tracks": len(_store.recommended_track_ids()),
        "feedback_events": len(_store.recent_feedback(limit=10000)),
    }


@app.get("/v1/cooldowns", response_model=list[ArtistCooldown])
async def cooldowns() -> list[ArtistCooldown]:
    return _store.active_cooldowns()


@app.delete("/v1/cooldowns/{artist_id}", status_code=204)
async def remove_cooldown(artist_id: str) -> None:
    _store.remove_artist_cooldown(artist_id)


@app.get("/v1/taste")
async def taste() -> dict[str, object]:
    provider = await _spotify_provider()
    summary = await provider.taste_summary()
    listens = await provider.recent_listens(limit=200)
    unique_tracks = {item.track.id for item in listens}
    unique_artists = {item.track.artist_id for item in listens}

    top_artists = await provider.top_artists_raw()
    top_tracks = await provider.top_tracks_raw(limit=50)
    top_artist_ids = [str(item.get("id")) for item in top_artists if item.get("id")]
    metadata = _store.artist_metadata_many(top_artist_ids)
    summary["taste_clusters"] = [item.model_dump() for item in build_taste_clusters(metadata)]

    recent_counts = Counter(item.track.artist_id for item in listens)
    names = {item.track.artist_id: item.track.artist_name for item in listens}
    for item in top_artists:
        if item.get("id") and item.get("name"):
            names.setdefault(str(item["id"]), str(item["name"]))
    top_track_counts = Counter(
        str(((item.get("artists") or [{}])[0]).get("id") or "")
        for item in top_tracks
        if ((item.get("artists") or [{}])[0]).get("id")
    )
    top_artist_ranks = {
        str(item["id"]): index + 1
        for index, item in enumerate(top_artists)
        if item.get("id")
    }
    saturation = calculate_artist_saturation(
        recent_artist_counts=recent_counts,
        recent_artist_names=names,
        top_track_artist_counts=top_track_counts,
        top_artist_ranks=top_artist_ranks,
        limit=20,
    )
    summary["artist_saturation"] = [item.model_dump() for item in saturation]
    summary["metadata"] = {
        "cached_artists": len(metadata),
        "top_artists_with_genres": sum(1 for item in metadata if item.genres),
        "top_artists_with_tags": sum(1 for item in metadata if item.tags),
    }
    summary["recent_history"] = {
        "listens_loaded": len(listens),
        "unique_tracks": len(unique_tracks),
        "unique_artists": len(unique_artists),
    }
    return summary


@app.get("/v1/enrichment/status", response_model=EnrichmentStatus)
async def enrichment_status() -> EnrichmentStatus:
    return EnrichmentStatus(
        cached_artists=len(_store.all_artist_metadata()),
        musicbrainz_enabled=bool(settings.musicbrainz_contact),
    )


@app.post("/v1/enrichment/musicbrainz", response_model=EnrichmentReport)
async def enrich_musicbrainz(
    limit: int = Query(default=12, ge=1, le=25),
    force: bool = False,
) -> EnrichmentReport:
    if not settings.musicbrainz_contact:
        raise HTTPException(
            status_code=503,
            detail="Set UNLOOP_MUSICBRAINZ_CONTACT to a project URL or contact email.",
        )
    provider = await _spotify_provider()
    client = MusicBrainzAPI(
        user_agent=f"UNLOOP/0.9.0 ( {settings.musicbrainz_contact} )"
    )
    service = MetadataEnrichmentService(provider, client, _store)
    return await service.enrich_top_artists(limit=limit, force=force)


@app.get("/v1/connections/listenbrainz", response_model=ListenBrainzStatus)
async def listenbrainz_status() -> ListenBrainzStatus:
    return ListenBrainzStatus(
        configured=bool(settings.listenbrainz_username),
        username=settings.listenbrainz_username or None,
    )


@app.get("/v1/connections/spotify", response_model=SpotifyConnectionStatus)
async def spotify_status() -> SpotifyConnectionStatus:
    return SpotifyConnectionStatus(
        configured=bool(settings.spotify_client_id),
        connected="access_token" in _spotify_tokens,
    )


@app.get("/v1/connections/spotify/start", response_model=SpotifyConnectionStart)
async def spotify_start() -> SpotifyConnectionStart:
    if not settings.spotify_client_id:
        raise HTTPException(
            status_code=503,
            detail="Set UNLOOP_SPOTIFY_CLIENT_ID before connecting Spotify.",
        )
    request = create_pkce_request(
        settings.spotify_client_id,
        settings.spotify_redirect_uri,
    )
    _spotify_pending.clear()
    _spotify_pending[request.state] = request.code_verifier
    return SpotifyConnectionStart(authorization_url=request.authorization_url)


@app.get("/v1/connections/spotify/callback", response_class=HTMLResponse)
async def spotify_callback(code: str, state: str) -> HTMLResponse:
    verifier = _spotify_pending.pop(state, None)
    if verifier is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.spotify_client_id,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
                "code_verifier": verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Spotify token exchange failed")
    payload = response.json()
    _spotify_tokens["access_token"] = payload["access_token"]
    _spotify_tokens["expires_at"] = datetime.now(UTC) + timedelta(
        seconds=int(payload.get("expires_in", 3600))
    )
    if payload.get("refresh_token"):
        _spotify_tokens["refresh_token"] = payload["refresh_token"]

    return HTMLResponse(
        """<!doctype html><html><body style='font-family:system-ui;background:#101114;color:#eee;padding:3rem'>
        <h1>Spotify connected.</h1><p>UNLOOP can now read your taste signals and build discovery batches.</p>
        <p><a style='color:#fff' href='/?spotify=connected'>Open UNLOOP</a> · <a style='color:#fff' href='/v1/taste'>View taste profile</a></p>
        <p style='color:#999'>Development tokens are currently kept in memory only.</p></body></html>"""
    )


@app.delete("/v1/connections/spotify", status_code=204)
async def spotify_disconnect() -> None:
    _spotify_tokens.clear()
    _spotify_pending.clear()
