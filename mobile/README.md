# Axaliai mobile app

This is a minimal Expo app starter for the Unity-AI-Voice-Interface project.

## Setup

```bash
cd mobile
npm install
npm start
```

## Important

Edit `mobile/App.js` and replace:

```javascript
const API_URL = "https://your-render-app.onrender.com";
```

with your actual Render backend URL.

## Usage

- Launch in Expo Go or emulator
- type a question
- tap Voice for browser-based recognition on web
- the app sends requests to `/chat` on your Render backend
