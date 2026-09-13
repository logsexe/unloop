package app.unloop.mobile

import java.net.HttpURLConnection
import java.net.URLEncoder
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

data class SpotifyStatus(
    val configured: Boolean,
    val connected: Boolean,
)

data class TrackResult(
    val id: String,
    val artistId: String,
    val title: String,
    val artistName: String,
    val reason: String,
    val score: Int,
)

data class PlaylistResult(
    val playlistUrl: String,
    val tracks: List<TrackResult>,
) {
    val trackCount: Int get() = tracks.size
}

class UnloopApi(private val baseUrl: String) {
    private val root = baseUrl.trimEnd('/')

    suspend fun health(): Boolean = withContext(Dispatchers.IO) {
        request("GET", "/health").optString("status") == "ok"
    }

    suspend fun spotifyStatus(): SpotifyStatus = withContext(Dispatchers.IO) {
        val json = request("GET", "/v1/connections/spotify")
        SpotifyStatus(
            configured = json.optBoolean("configured"),
            connected = json.optBoolean("connected"),
        )
    }

    suspend fun spotifyAuthorizationUrl(): String = withContext(Dispatchers.IO) {
        request("GET", "/v1/connections/spotify/start").getString("authorization_url")
    }

    suspend fun createPlaylist(
        mode: String,
        limit: Int,
        language: String,
        relatability: String,
        playlistName: String,
        genre: String,
    ): PlaylistResult = withContext(Dispatchers.IO) {
        val query = buildList {
            add("mode=${encode(mode)}")
            add("limit=$limit")
            add("language_preference=${encode(language)}")
            add("relatability=${encode(relatability)}")
            if (playlistName.isNotBlank()) add("playlist_name=${encode(playlistName)}")
            if (genre.isNotBlank()) add("genre=${encode(genre)}")
        }.joinToString("&")
        val json = request("POST", "/v1/playlists/discovery?$query")
        val rawTracks = json.optJSONArray("tracks")
        val tracks = buildList {
            if (rawTracks != null) {
                for (index in 0 until rawTracks.length()) {
                    val ranked = rawTracks.optJSONObject(index) ?: continue
                    val track = ranked.optJSONObject("track") ?: continue
                    val reasons = ranked.optJSONArray("reasons")
                    val reason = if (reasons != null && reasons.length() > 0) {
                        reasons.optString(0)
                    } else {
                        "Selected by UNLOOP"
                    }
                    val finalScore = ranked.optJSONObject("score")?.optDouble("final_score", 0.0) ?: 0.0
                    add(
                        TrackResult(
                            id = track.optString("id"),
                            artistId = track.optString("artist_id"),
                            title = track.optString("title"),
                            artistName = track.optString("artist_name"),
                            reason = reason,
                            score = (finalScore * 100).toInt(),
                        )
                    )
                }
            }
        }
        PlaylistResult(
            playlistUrl = json.getString("playlist_url"),
            tracks = tracks,
        )
    }

    suspend fun feedback(track: TrackResult, action: String) = withContext(Dispatchers.IO) {
        val payload = JSONObject()
            .put("track_id", track.id)
            .put("artist_id", track.artistId)
            .put("artist_name", track.artistName)
            .put("action", action)
        if (action == "cooldown") payload.put("cooldown_days", 90)
        request("POST", "/v1/feedback", payload.toString())
    }

    private fun encode(value: String): String = URLEncoder.encode(value, Charsets.UTF_8.name())

    private fun request(method: String, path: String, jsonBody: String? = null): JSONObject {
        val connection = (URL("$root$path").openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 12_000
            readTimeout = 60_000
            setRequestProperty("Accept", "application/json")
            doInput = true
            if (method == "POST") {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
        }
        try {
            if (method == "POST") {
                connection.outputStream.use { stream ->
                    if (jsonBody != null) stream.write(jsonBody.toByteArray())
                }
            }
            val stream = if (connection.responseCode in 200..299) {
                connection.inputStream
            } else {
                connection.errorStream
            }
            val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (connection.responseCode !in 200..299) {
                val detail = runCatching { JSONObject(body).optString("detail") }.getOrNull()
                error(detail?.takeIf { it.isNotBlank() } ?: "UNLOOP request failed (${connection.responseCode})")
            }
            return if (body.isBlank()) JSONObject() else JSONObject(body)
        } finally {
            connection.disconnect()
        }
    }
}
