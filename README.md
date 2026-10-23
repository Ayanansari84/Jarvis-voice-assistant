# JARVIS V2 — Python Voice Assistant

JARVIS V2 is a desktop voice assistant written in Python. It can listen for commands, speak responses, open selected apps and websites, search Google/YouTube, save notes, take screenshots, report basic system information, and answer general questions through the OpenAI API.

> **Project status:** Portfolio/demo project. Test the features on your own computer before relying on them. Some features depend on your operating system, microphone, internet connection, API access, and optional packages.

## Features

- Voice input with keyboard fallback when the microphone is unavailable
- Text-to-speech responses
- OpenAI chat responses with short conversation history
- Open selected websites and desktop applications
- Google search and YouTube video/song search
- Wikipedia summaries and programming jokes (optional packages)
- Save, read, and clear notes
- Screenshot capture (optional package)
- Battery, CPU, and RAM status (optional package)
- Windows volume controls (optional package)
- Windows lock, shutdown, and restart commands with confirmation

## Requirements

- Python 3.10 or newer recommended
- A microphone and speakers/headphones for voice features
- Internet connection for Google speech recognition and OpenAI chat
- An OpenAI API key for AI chat; API usage may incur charges
- Windows is the main target for volume, lock, shutdown, and restart commands. Other operating systems have limited app mappings.

## Setup on Windows (VS Code)

1. Install Python from [python.org](https://www.python.org/downloads/) and enable **Add Python to PATH** during setup.
2. Download or clone this repository.
3. Open the project folder in VS Code.
4. Open the VS Code terminal and create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt and run:

   ```bat
   .venv\Scripts\activate.bat
   ```

5. Install the dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

   **Microphone note:** `SpeechRecognition` uses PyAudio for microphone input. If PyAudio installation fails, resolve that dependency for your Python version before testing voice input. Keyboard fallback may work if microphone initialization fails.

6. Set your OpenAI API key in the current PowerShell terminal (replace the placeholder with your own key):

   ```powershell
   $env:OPENAI_API_KEY="your-api-key-here"
   ```

   Optional: choose a model by setting `OPENAI_MODEL`. The default in this project is `gpt-4o-mini`.

   ```powershell
   $env:OPENAI_MODEL="gpt-4o-mini"
   ```

   Do not paste your API key into the Python file or commit it to GitHub. The environment variable above applies to the current terminal session.

7. Start the assistant:

   ```powershell
   python jarvis_v2.py
   ```

## Example commands

Speak or type commands such as:

- `hello`
- `what time is it`
- `what is the date`
- `open YouTube`
- `open calculator`
- `search Python decorators`
- `play relaxing music`
- `make a note buy notebooks`
- `read notes`
- `screenshot`
- `system status`
- `battery`
- `volume up`
- `lock computer`
- `clear memory`
- `exit`

Command recognition is based on keywords, so phrasing may affect which command is selected. Say `exit` or type `exit` to quit.

## Files created at runtime

- `jarvis_notes.txt` — notes saved by the assistant
- `screenshots/` — screenshots captured when the optional screenshot dependency is installed

These are local runtime files and should generally not be committed to the repository.

## Privacy and safety notes

- Speech-to-text uses the Google Web Speech recognition service through the `SpeechRecognition` package; voice recognition therefore requires an internet connection.
- AI prompts are sent to the OpenAI API when AI chat is enabled. Review the applicable service terms and privacy policies before using it.
- Keep your API key private. If a key is accidentally committed, revoke it and create a new one.
- Shutdown and restart commands affect the computer. Use them only when intended; the program asks for confirmation first.
- Review code before running it, especially commands that interact with your operating system.

## Known limitations

- Voice recognition may fail in noisy environments or without a working microphone/PyAudio setup.
- Some app names and commands are platform-specific.
- Optional features are disabled or show a message when their package is unavailable.
- The assistant is keyword-driven, not a continuously listening wake-word engine.
- This project has not been packaged as a standalone executable.

## Project structure

```text
jarvis-v2/
├── jarvis_v2.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## License

This project is distributed under the MIT License. See `LICENSE`.
