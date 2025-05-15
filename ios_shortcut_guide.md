# iOS Shortcut Guide for Daily Meditation App

This guide will help you create an iOS Shortcut to access your Daily Meditation API and play personalized meditations based on your mood.

## Prerequisites

- An iOS device running iOS 13 or later
- The Shortcuts app installed
- Your Daily Meditation API deployed and accessible via a public URL

## Creating the Shortcut

1. Open the Shortcuts app on your iOS device
2. Tap the "+" button in the top right to create a new shortcut
3. Tap "Add Action"
4. Search for "Text" and select "Text" action
5. Enter the URL of your API, e.g., `https://daily-meditation.onrender.com/generate-meditation`
6. Add another action by tapping "+"
7. Search for "Ask for Input" and select it
8. Configure the input as follows:
   - Question: "How are you feeling today?"
   - Input Type: "Text"
   - Default Answer: "calm" (or leave blank)
9. Add another action by tapping "+"
10. Search for "Ask for Input" and select it again
11. Configure this input as follows:
    - Question: "Choose a language (english/french)"
    - Input Type: "Text"
    - Default Answer: "english"
12. Add another action by tapping "+"
13. Search for "Dictionary" and select "Dictionary" action
14. Add two key-value pairs:
    - Key: `mood`
    - Text: Select the "Provided Input" variable from step 8
    - Key: `language`
    - Text: Select the "Provided Input" variable from step 11
15. Add another action by tapping "+"
16. Search for "Get Contents of URL" and select it
17. For URL, select the Text variable from step 5
18. For Method, select "POST"
19. For Request Body, select "JSON" and use the Dictionary variable from step 14
20. For Headers, add a key-value pair:
    - Key: `Content-Type`
    - Value: `application/json`
21. Add another action by tapping "+"
22. Search for "Play Sound" and select it
23. For Sound, select the "Contents of URL" output from the previous step

## Using the Shortcut

1. Tap on the shortcut in the Shortcuts app or your home screen
2. When prompted, enter how you're feeling (e.g., "calm", "focused", "energized")
3. Choose your preferred language ("english" or "french")
4. The shortcut will call the API, which will:
   - Search the web for meditation audio matching your mood
   - Download the best matching audio file
   - Check the audio quality to ensure it meets standards
   - Return the high-quality meditation
5. The meditation will automatically play on your device

## Customizing the Shortcut

- You can rename the shortcut by tapping on its name at the top
- Add it to your home screen for quick access
- Set up specific moods and languages as quick options instead of free text input

## Troubleshooting

- If you receive an error, check that your API is running and accessible
- Ensure your mood input is one of the supported moods (refer to the `/available-moods` endpoint)
- Ensure your language input is one of the supported languages (refer to the `/available-languages` endpoint)
- Check your internet connection

## Advanced Usage

- You can schedule the shortcut to run at specific times using the Automation feature
- Integrate with other shortcuts or voice commands via Siri
- Add conditions to suggest different moods based on time of day or calendar events 