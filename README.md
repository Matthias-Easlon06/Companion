# Plunket

Desktop AI companion that sits on your screen. Uses OpenAI API to chat.

## Setup

1. Run `desktop_companion.py`
2. Get an API key from platform.openai.com/api-keys
3. Paste your key (starts with sk-) into the chat
4. Done

## Commands

- `/commands` - list all commands
- `/clear` - clear history
- `/mood [name]` - change face (happy, excited, sleepy, sad, surprised, thinking)
- `/reset` - reset API key

## Troubleshooting

**"ModuleNotFoundError: No module named 'PyQt5'"**
```bash
pip install PyQt5 requests
```

**"API Error: 401"**
Your API key is wrong or expired. Type `/reset` and enter a new one.

**"API Error: 429"**
You hit the rate limit or ran out of credits. Check your OpenAI account.

**Window is tiny/huge**
Edit line 106 in the code, change `self.setFixedSize(600, 650)` to whatever size you want.

**Face shows as boxes**
Your system doesn't support the Unicode characters. The app will still work fine.

**Can't drag the window**
Click and hold on the window background (not on buttons or text).

**Last letter disappears when I type**
This was a bug in earlier versions. Make sure you have the latest version of the file.

**Dependencies won't install**
Try installing manually:
```bash
python -m pip install --upgrade pip
pip install PyQt5 requests
```

**OpenAI API is expensive**
The app uses gpt-4o-mini which is pretty cheap. Each message costs fractions of a cent. You can set spending limits in your OpenAI account settings.
