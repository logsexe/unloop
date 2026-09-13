package app.unloop.mobile

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

private val Ink = Color(0xFF090A0C)
private val Panel = Color(0xFF121419)
private val Muted = Color(0xFF9AA1AC)
private val Acid = Color(0xFFD9FF63)
private val Good = Color(0xFF8CE8AD)
private val Bad = Color(0xFFFF8E8E)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = Ink) {
                    UnloopApp()
                }
            }
        }
    }
}

@Composable
private fun UnloopApp() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var baseUrl by remember { mutableStateOf("http://10.0.2.2:8787") }
    var engineOnline by remember { mutableStateOf<Boolean?>(null) }
    var spotifyConnected by remember { mutableStateOf(false) }
    var spotifyConfigured by remember { mutableStateOf(false) }
    var statusText by remember { mutableStateOf("Check the UNLOOP engine to begin.") }
    var busy by remember { mutableStateOf(false) }

    var mode by remember { mutableStateOf("explore") }
    var limit by remember { mutableStateOf(30) }
    var language by remember { mutableStateOf("english_preferred") }
    var relatability by remember { mutableStateOf("balanced") }
    var playlistName by remember { mutableStateOf("") }
    var genre by remember { mutableStateOf("") }
    var lastPlaylist by remember { mutableStateOf<PlaylistResult?>(null) }

    fun api() = UnloopApi(baseUrl)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 28.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        Text(
            "GET BACK YOUR TIME · RENEW YOUR TASTE",
            color = Acid,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
        )
        Text("UNLOOP", color = Color.White, fontSize = 46.sp, fontWeight = FontWeight.Black)
        Text(
            "Discover better music without another feed. Build a finite batch, save it, then leave and listen.",
            color = Color(0xFFD2D6DC),
            fontSize = 18.sp,
            lineHeight = 25.sp,
        )

        PrincipleCard()

        SectionTitle("Engine")
        CardColumn {
            OutlinedTextField(
                value = baseUrl,
                onValueChange = { baseUrl = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("UNLOOP engine URL") },
                singleLine = true,
            )
            Text(
                "Emulator: http://10.0.2.2:8787 · Phone: use your computer's LAN IP.",
                color = Muted,
                fontSize = 12.sp,
            )
            Button(
                onClick = {
                    busy = true
                    scope.launch {
                        runCatching {
                            engineOnline = api().health()
                            val spotify = api().spotifyStatus()
                            spotifyConnected = spotify.connected
                            spotifyConfigured = spotify.configured
                            statusText = if (spotify.connected) {
                                "Spotify connected. Ready to discover."
                            } else {
                                "Engine online. Spotify is not connected yet."
                            }
                        }.onFailure {
                            engineOnline = false
                            statusText = it.message ?: "Could not reach UNLOOP."
                        }
                        busy = false
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Acid, contentColor = Ink),
                enabled = !busy,
            ) {
                Text("CHECK CONNECTION", fontWeight = FontWeight.Bold)
            }
            StatusLine("Engine", engineOnline == true)
            StatusLine("Spotify", spotifyConnected)
            Text(statusText, color = Muted, fontSize = 12.sp)
        }

        SectionTitle("Where you listen")
        ProviderCard("Spotify", if (spotifyConnected) "Connected" else "Available", true)
        ProviderCard("Apple Music", "Planned provider", false)
        ProviderCard("Navidrome", "Planned provider", false)

        if (!spotifyConnected) {
            OutlinedButton(
                onClick = {
                    scope.launch {
                        runCatching { api().spotifyAuthorizationUrl() }
                            .onSuccess { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(it))) }
                            .onFailure { statusText = it.message ?: "Could not start Spotify connection." }
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = engineOnline == true && spotifyConfigured,
            ) {
                Text("CONNECT SPOTIFY", color = Color.White)
            }
        }

        SectionTitle("Build a finite batch")
        CardColumn {
            ChoiceRow("Mode", listOf("safe", "explore", "deep_cut", "chaos"), mode) { mode = it }
            ChoiceRow("Tracks", listOf("15", "30", "45"), limit.toString()) { limit = it.toInt() }
            ChoiceRow(
                "Language",
                listOf("english_preferred", "english_only", "any"),
                language,
            ) { language = it }
            ChoiceRow(
                "Relatability",
                listOf("close", "balanced", "open"),
                relatability,
            ) { relatability = it }
            OutlinedTextField(
                value = genre,
                onValueChange = { genre = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Genre / scene · optional") },
                singleLine = true,
            )
            OutlinedTextField(
                value = playlistName,
                onValueChange = { playlistName = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Playlist name · optional") },
                placeholder = { Text("UNLOOP Discovery") },
                singleLine = true,
            )
            Button(
                onClick = {
                    busy = true
                    statusText = "Building your finite batch…"
                    scope.launch {
                        runCatching {
                            api().createPlaylist(
                                mode = mode,
                                limit = limit,
                                language = language,
                                relatability = relatability,
                                playlistName = playlistName,
                                genre = genre,
                            )
                        }.onSuccess {
                            lastPlaylist = it
                            statusText = "${it.trackCount} tracks ready. That's it — go listen."
                        }.onFailure {
                            statusText = it.message ?: "Discovery failed."
                        }
                        busy = false
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Acid, contentColor = Ink),
                enabled = spotifyConnected && !busy,
            ) {
                Text("BUILD DISCOVERY PLAYLIST", fontWeight = FontWeight.Bold)
            }
        }

        lastPlaylist?.let { result ->
            SectionTitle("Your batch is ready")
            CardColumn {
                Text("${result.trackCount} tracks", color = Color.White, fontSize = 24.sp, fontWeight = FontWeight.Black)
                Text("No next feed. No swipe queue. This batch ends here.", color = Muted)
                Button(
                    onClick = { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(result.playlistUrl))) },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("OPEN PLAYLIST")
                }
            }
        }

        Text(
            "No swiping. No infinite scroll. No sponsored ranking. No engagement traps.",
            color = Muted,
            fontSize = 12.sp,
        )
        Text("V1 Developer Preview", color = Muted, fontSize = 11.sp)
    }
}

@Composable
private fun PrincipleCard() {
    CardColumn {
        Text("Find music. Save the playlist. Leave.", color = Color.White, fontWeight = FontWeight.Bold)
        Text("A short session is a successful session.", color = Muted)
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(text, color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold)
}

@Composable
private fun CardColumn(content: @Composable () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Panel, RoundedCornerShape(18.dp))
            .padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        content()
    }
}

@Composable
private fun ProviderCard(name: String, status: String, active: Boolean) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Panel, RoundedCornerShape(16.dp))
            .padding(16.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Column {
            Text(name, color = Color.White, fontWeight = FontWeight.Bold)
            Text(status, color = if (active) Acid else Muted, fontSize = 12.sp)
        }
        Text(if (active) "AVAILABLE" else "PLANNED", color = if (active) Acid else Muted, fontSize = 11.sp)
    }
}

@Composable
private fun StatusLine(label: String, connected: Boolean) {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, color = Color.White)
        Text(if (connected) "CONNECTED" else "NOT CONNECTED", color = if (connected) Good else Bad, fontSize = 11.sp)
    }
}

@Composable
private fun ChoiceRow(label: String, values: List<String>, selected: String, onSelect: (String) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(7.dp)) {
        Text(label.uppercase(), color = Muted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            values.forEach { value ->
                if (value == selected) {
                    Button(onClick = { onSelect(value) }, colors = ButtonDefaults.buttonColors(containerColor = Acid, contentColor = Ink)) {
                        Text(value.replace('_', ' '), fontSize = 11.sp)
                    }
                } else {
                    OutlinedButton(onClick = { onSelect(value) }) {
                        Text(value.replace('_', ' '), color = Color.White, fontSize = 11.sp)
                    }
                }
            }
        }
    }
}
