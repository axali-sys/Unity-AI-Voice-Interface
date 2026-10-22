import React, { useEffect, useRef, useState } from "react";
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import * as Speech from "expo-speech";

const API_URL = "https://your-render-app.onrender.com";

export default function App() {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hello — I’m Axaliai. Ask me anything." },
  ]);
  const [input, setInput] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollToEnd({ animated: true });
    }
  }, [messages]);

  async function sendMessage(customText) {
    const text = (customText ?? input).trim();
    if (!text) return;

    const userMessage = { role: "user", text };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: text,
          workspace_id: "mobile-demo",
          actor: "mobile-user",
          messages: messages.concat(userMessage),
          use_memory: true,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || "Assistant request failed");
      }

      const assistantText =
        data.message ||
        data.response ||
        data.summary ||
        "I’m ready to help.";

      const newMessage = { role: "assistant", text: assistantText };
      setMessages((prev) => [...prev, newMessage]);

      if (Platform.OS !== "web") {
        Speech.speak(assistantText, {
          rate: 0.95,
          pitch: 1.0,
        });
      }
    } catch (error) {
      const fallback = {
        role: "assistant",
        text: "The backend is not reachable. Check your Render URL and token configuration.",
      };
      setMessages((prev) => [...prev, fallback]);
      Alert.alert("Connection error", error.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function startVoiceInput() {
    if (Platform.OS === "web") {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

      if (!SpeechRecognition) {
        Alert.alert("Voice not supported", "Web Speech API is not available in this browser.");
        return;
      }

      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
      };

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);

      recognition.start();
      return;
    }

    Alert.alert(
      "Mobile voice input",
      "For native mobile, use a voice provider like OpenAI Whisper or a custom backend voice endpoint."
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Axaliai</Text>
        <Text style={styles.subtitle}>Voice-first AI assistant</Text>
      </View>

      <ScrollView style={styles.chat} ref={scrollRef}>
        {messages.map((message, index) => (
          <View
            key={`${index}`}
            style={[
              styles.messageRow,
              message.role === "user" ? styles.userRow : styles.assistantRow,
            ]}
          >
            <Text
              style={[
                styles.messageBubble,
                message.role === "user" ? styles.userBubble : styles.assistantBubble,
              ]}
            >
              {message.text}
            </Text>
          </View>
        ))}
      </ScrollView>

      <View style={styles.inputRow}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="Ask Axaliai..."
          style={styles.input}
          multiline
        />
        <Pressable
          style={[styles.sendButton, isLoading && styles.disabledButton]}
          onPress={() => sendMessage()}
          disabled={isLoading}
        >
          <Text style={styles.sendText}>{isLoading ? "Sending..." : "Send"}</Text>
        </Pressable>
      </View>

      <Pressable style={styles.voiceButton} onPress={startVoiceInput}>
        <Text style={styles.voiceText}>{isListening ? "Listening..." : "Voice"}</Text>
      </Pressable>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#071827",
    padding: 16,
  },
  header: {
    paddingTop: 30,
    paddingBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: "#f2f8ff",
  },
  subtitle: {
    color: "#9ec7ef",
    fontSize: 14,
    marginTop: 6,
  },
  chat: {
    flex: 1,
    marginBottom: 12,
  },
  messageRow: {
    marginBottom: 12,
  },
  userRow: {
    alignItems: "flex-end",
  },
  assistantRow: {
    alignItems: "flex-start",
  },
  messageBubble: {
    maxWidth: "80%",
    padding: 12,
    borderRadius: 14,
    lineHeight: 20,
  },
  userBubble: {
    backgroundColor: "#67d2ff",
    color: "#071827",
  },
  assistantBubble: {
    backgroundColor: "#1f2d3f",
    color: "#eaf3ff",
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: "#122133",
    color: "#f3f7ff",
    borderRadius: 12,
    padding: 12,
    minHeight: 56,
    borderWidth: 1,
    borderColor: "#2d4566",
  },
  sendButton: {
    backgroundColor: "#6d7cff",
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 14,
    minWidth: 96,
    alignItems: "center",
    justifyContent: "center",
  },
  sendText: {
    color: "#071827",
    fontWeight: "700",
  },
  voiceButton: {
    marginTop: 12,
    backgroundColor: "#0d2037",
    borderRadius: 12,
    padding: 12,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#4ea6ff",
  },
  voiceText: {
    color: "#dfeefe",
    fontWeight: "700",
  },
  disabledButton: {
    opacity: 0.5,
  },
});
