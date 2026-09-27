package com.axali.unityai

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.speech.RecognizerIntent
import android.speech.tts.TextToSpeech
import android.view.Gravity
import android.widget.*
import java.util.Locale

class MainActivity : Activity(), TextToSpeech.OnInitListener {
    private lateinit var tts: TextToSpeech
    private lateinit var memory: Jellybox
    private lateinit var status: TextView
    private lateinit var transcript: TextView
    private val voiceRequest = 42

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        memory = Jellybox(this)
        tts = TextToSpeech(this, this)
        buildUi()
    }

    private fun buildUi() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(28, 36, 28, 28)
            setBackgroundColor(android.graphics.Color.rgb(7,8,12))
        }
        val title = TextView(this).apply { text = "AXALIAI"; textSize = 30f; setTextColor(-1); gravity = Gravity.CENTER }
        val subtitle = TextView(this).apply { text = "Unity • Android (plane) AI • In Development"; textSize = 14f; setTextColor(-3355444); gravity = Gravity.CENTER; setPadding(0,8,0,24) }
        status = TextView(this).apply { text = "Unity engine: ready\nJellybox: local memory ready\nDevice: Android host"; textSize = 15f; setTextColor(-1); setPadding(16,16,16,16) }
        transcript = TextView(this).apply { text = "Say something or type a command."; textSize = 18f; setTextColor(-1); setPadding(16,24,16,24) }
        val input = EditText(this).apply { hint = "Talk to Unity…"; setHintTextColor(-7829368); setTextColor(-1); setSingleLine(false) }
        val send = Button(this).apply { text = "SEND" }
        val listen = Button(this).apply { text = "🎙 LISTEN" }
        val remember = Button(this).apply { text = "SAVE TO JELLYBOX" }

        send.setOnClickListener { process(input.text.toString()) }
        listen.setOnClickListener { listen() }
        remember.setOnClickListener {
            val value = input.text.toString().trim()
            if (value.isNotEmpty()) {
                memory.save(value)
                speak("Saved to Jellybox.")
                status.text = "Unity engine: ready\nJellybox: memory saved\nDevice: Android host"
            }
        }
        root.addView(title); root.addView(subtitle); root.addView(status); root.addView(transcript)
        root.addView(input, LinearLayout.LayoutParams(-1, 0, 1f))
        root.addView(send); root.addView(listen); root.addView(remember)
        setContentView(root)
    }

    private fun process(raw: String) {
        val text = raw.trim()
        if (text.isEmpty()) return
        memory.save("USER: " + text)
        val response = when {
            text.contains("hello", true) || text.contains("are you there", true) ->
                "AXALIAI is here. Unity is running on the Android (plane) AI layer."
            text.contains("remember", true) -> { memory.save(text); "Saved to Jellybox." }
            text.contains("memory", true) -> "Jellybox is active with " + memory.count() + " local entries."
            else -> "Unity received your request. V1 is ready for controlled Android actions."
        }
        transcript.text = "You: " + text + "\n\nUnity: " + response
        speak(response)
    }

    private fun listen() {
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), 7); return
        }
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak to AXALIAI")
        }
        startActivityForResult(intent, voiceRequest)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == voiceRequest && resultCode == RESULT_OK) {
            val words = data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
            if (!words.isNullOrEmpty()) process(words[0])
        }
    }

    override fun onInit(result: Int) { if (result == TextToSpeech.SUCCESS) tts.language = Locale.US }
    private fun speak(text: String) { if (::tts.isInitialized) tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "axaliai-v1") }
    override fun onDestroy() { tts.stop(); tts.shutdown(); memory.close(); super.onDestroy() }
}
