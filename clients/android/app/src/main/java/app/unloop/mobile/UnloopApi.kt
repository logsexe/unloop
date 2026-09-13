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

data class PlaylistResult(
    val playlistUrl: String,
    val trackCount: Int,
)

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
        PlaylistResult(
            playlistUrl = json.getString("playlist_url"),
            trackCount = json.optJSONArray("tracks")?.length() ?: 0,
        )
    }

    private fun encode(value: String): String = URLEncoder.encode(value, Charsets.UTF_8.name())

    private fun request(method: String, path: String): JSONObject {
        val connection = (URL("$root$path").openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 12_000
            readTimeout = 60_000
            setRequestProperty("Accept", "application/json")
            doInput = true
            if (method == "POST") doOutput = true
        }
        try {
            if (method == "POST") connection.outputStream.use { }
            val stream = if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream
            val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (connection.responseCode !in 200..299) {
                val detail = runCatching { JSONObject(body).optString("detail") }.getOrNull()
                error(detail?.takeIf { it.isNotBlank() } ?: "UNLOOP request failed (${connection.responseCode})")
            }
            return JSONObject(body)
        } finally {
            connection.disconnect()
        }
    }
}
