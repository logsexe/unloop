package app.unloop.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val Ink = Color(0xFF090A0C)
private val Panel = Color(0xFF121419)
private val Line = Color(0xFF2A2E35)
private val Muted = Color(0xFF9AA1AC)
private val Acid = Color(0xFFD9FF63)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = Ink) {
                    UnloopHome()
                }
            }
        }
    }
}

@Composable
private fun UnloopHome() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 28.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        Text("GET BACK YOUR TIME · RENEW YOUR TASTE", color = Acid, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        Text("UNLOOP", color = Color.White, fontSize = 46.sp, fontWeight = FontWeight.Black)
        Text(
            "Discover better music without another feed. Build a finite batch, save it, then leave and listen.",
            color = Color(0xFFD2D6DC),
            fontSize = 18.sp,
            lineHeight = 25.sp,
        )

        PrincipleCard()

        Text("Where you listen", color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        ProviderCard("Spotify", "Ready for integration", true)
        ProviderCard("Apple Music", "Planned provider", false)
        ProviderCard("Navidrome", "Planned provider", false)

        Text("Your next batch", color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        BatchCard()

        Text(
            "No swiping. No infinite scroll. No sponsored ranking.",
            color = Muted,
            fontSize = 12.sp,
        )
    }
}

@Composable
private fun PrincipleCard() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Panel, RoundedCornerShape(18.dp))
            .padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Text("Find music. Save the playlist. Leave.", color = Color.White, fontWeight = FontWeight.Bold)
        Text("A short session is a successful session.", color = Muted)
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
private fun BatchCard() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Panel, RoundedCornerShape(18.dp))
            .padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Explore · 30 tracks", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 18.sp)
        Text("English preferred · Balanced relatability", color = Muted)
        Text("Finite by design. No next-feed queue after the batch ends.", color = Muted, fontSize = 13.sp)
        Spacer(Modifier.height(2.dp))
        Button(
            onClick = { },
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = Acid, contentColor = Ink),
        ) {
            Text("BUILD DISCOVERY BATCH", fontWeight = FontWeight.Bold)
        }
        OutlinedButton(onClick = { }, modifier = Modifier.fillMaxWidth()) {
            Text("CONNECTIONS", color = Color.White)
        }
    }
}
