package com.example.kin.presentation

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.speech.RecognizerIntent
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.wear.compose.material.Text
import com.airbnb.lottie.compose.*
import com.example.kin.presentation.network.ChatRequest
import com.example.kin.presentation.network.KinClient
import com.example.kin.presentation.network.WatchConfig
import com.example.kin.presentation.sensors.KinSensors
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        setContent {
            KinScreen()
        }
    }
}

@Composable
fun KinScreen() {
    val context = LocalContext.current
    val sensors = remember { KinSensors(context) }
    var config by remember { mutableStateOf(WatchConfig("idle", "", "#FFFFFF")) }

    // VOICE HANDLER
    val voiceLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val results = result.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
            val spokenText = results?.get(0) ?: ""

            if (spokenText.isNotEmpty()) {
                sensors.vibrateSuccess()
                Toast.makeText(context, "Sending...", Toast.LENGTH_SHORT).show()

                CoroutineScope(Dispatchers.IO).launch {
                    try {
                        KinClient.api.sendChat(ChatRequest(spokenText))
                        CoroutineScope(Dispatchers.Main).launch {
                            Toast.makeText(context, "Sent Success!", Toast.LENGTH_SHORT).show()
                        }
                    } catch (e: Exception) {
                        Log.e("Kin", "Send failed: ${e.message}")
                        CoroutineScope(Dispatchers.Main).launch {
                            Toast.makeText(context, "Error: ${e.message}", Toast.LENGTH_LONG).show()
                        }
                    }
                }
            }
        }
    }

    // POLLING LOOP
    LaunchedEffect(Unit) {
        while(true) {
            try { config = KinClient.api.getConfig() } catch (_: Exception) {}
            delay(3000)
        }
    }

    // UI
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            .clickable {
                sensors.vibrateTick()
                val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak to Kin...")
                }
                try {
                    voiceLauncher.launch(intent)
                } catch (e: Exception) {
                    Toast.makeText(context, "No Voice App Found", Toast.LENGTH_SHORT).show()
                }
            },
        contentAlignment = Alignment.Center
    ) {
        if (config.animation_url.isNotEmpty()) {
            val composition by rememberLottieComposition(LottieCompositionSpec.Url(config.animation_url))

            // 1. Calculate progress
            val progress by animateLottieCompositionAsState(
                composition = composition,
                iterations = LottieConstants.IterateForever
            )

            // 2. Draw the animation using the raw float value
            LottieAnimation(
                composition = composition,
                progress = progress,     // <--- FIXED: No curly braces!
                modifier = Modifier.size(120.dp)
            )
        }

        Text(
            text = config.status,
            color = try {
                Color(android.graphics.Color.parseColor(config.primary_color))
            } catch(e: Exception) { Color.White },
            modifier = Modifier.align(Alignment.BottomCenter).padding(bottom = 20.dp)
        )
    }
}