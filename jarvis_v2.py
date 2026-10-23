"""
JARVIS V2 - Python Voice Assistant
Features:
- Voice input + keyboard fallback
- Text-to-speech
- OpenAI AI chat with conversation memory
- Open websites/apps
- Google/YouTube search
- Notes: add/read/search/clear
- Screenshot
- Battery, CPU and RAM status
- Volume control (Windows)
- Lock / shutdown / restart commands (with confirmation)
- Better error handling
- API key is read from environment variable
"""

import datetime
import os
import platform
import random
import re
import subprocess
import sys
import urllib.parse
import webbrowser
from pathlib import Path

import pyttsx3
import speech_recognition as sr

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Optional libraries
try:
    import wikipedia
except ImportError:
    wikipedia = None

try:
    import pyjokes
except ImportError:
    pyjokes = None

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import psutil
except ImportError:
    psutil = None


# ============================================================
# SETTINGS
# ============================================================

ASSISTANT_NAME = "jarvis"
LANGUAGE = "en-IN"
USE_VOICE_OUTPUT = True

BASE_DIR = Path(__file__).resolve().parent
NOTES_FILE = BASE_DIR / "jarvis_notes.txt"

SYSTEM = platform.system()
AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MAX_HISTORY_MESSAGES = 12

# ============================================================
# OPENAI
# ============================================================

client = None

if OpenAI and OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"[AI setup error] {e}")
else:
    print("[!] OpenAI API key nahi mili. AI chat disabled hai.")


chat_history = [
    {
        "role": "system",
        "content": (
            "You are JARVIS, a smart and polite voice assistant. "
            "Reply in the same language the user uses: Hindi, English or Hinglish. "
            "Keep spoken answers concise, normally 2-4 sentences. "
            "Do not use markdown, bullet points or emojis unless the user asks."
        ),
    }
]


# ============================================================
# TEXT TO SPEECH
# ============================================================

engine = None

try:
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)

    voices = engine.getProperty("voices")
    if voices:
        # First available voice is generally supported on the system.
        engine.setProperty("voice", voices[0].id)

except Exception as e:
    print(f"[!] TTS start nahi hua: {e}")


def speak(text: str) -> None:
    """Print and optionally speak text."""
    if not text:
        return

    print(f"JARVIS: {text}")

    if USE_VOICE_OUTPUT and engine:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[TTS error] {e}")


# ============================================================
# SPEECH TO TEXT
# ============================================================

recognizer = sr.Recognizer()
recognizer.pause_threshold = 0.8
recognizer.dynamic_energy_threshold = True

MIC_WORKS = True


def listen() -> str:
    """Listen through microphone; fall back to keyboard if microphone fails."""

    global MIC_WORKS

    if MIC_WORKS:
        try:
            with sr.Microphone() as source:
                print("\nListening...")
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = recognizer.listen(
                    source,
                    timeout=6,
                    phrase_time_limit=10,
                )

            text = recognizer.recognize_google(
                audio,
                language=LANGUAGE,
            )

            print(f"You: {text}")
            return text.lower().strip()

        except sr.WaitTimeoutError:
            print("(No command heard)")
            return ""

        except sr.UnknownValueError:
            print("(Samajh nahi aaya)")
            return ""

        except sr.RequestError:
            speak("Speech service ya internet me problem hai.")
            return ""

        except (OSError, AttributeError) as e:
            print(f"[!] Microphone unavailable: {e}")
            print("[!] Text mode enabled.")
            MIC_WORKS = False

        except Exception as e:
            print(f"[Speech error] {e}")
            return ""

    try:
        return input("\nType command: ").lower().strip()
    except (EOFError, KeyboardInterrupt):
        return "exit"


# ============================================================
# AI
# ============================================================

def ask_ai(query: str) -> None:
    """Send a normal conversation query to OpenAI."""

    global chat_history

    if client is None:
        speak(
            "AI available nahi hai. OPENAI_API_KEY environment variable set karo."
        )
        return

    chat_history.append({"role": "user", "content": query})

    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=chat_history,
            max_tokens=300,
            temperature=0.7,
        )

        answer = response.choices[0].message.content

        if not answer:
            answer = "Mujhe iska jawab nahi mila."

        answer = answer.strip()

        chat_history.append(
            {"role": "assistant", "content": answer}
        )

        # Keep system prompt + recent messages.
        if len(chat_history) > MAX_HISTORY_MESSAGES + 1:
            chat_history = (
                [chat_history[0]]
                + chat_history[-MAX_HISTORY_MESSAGES:]
            )

        speak(answer)

    except Exception as e:
        print(f"[AI error] {e}")

        # Remove failed user message.
        if chat_history and chat_history[-1]["role"] == "user":
            chat_history.pop()

        speak("AI se connect nahi ho pa raha. Internet, API key ya API usage check karo.")


# ============================================================
# HELPERS
# ============================================================

def extract(query: str, remove_words) -> str:
    """Remove command words from a query."""
    for word in remove_words:
        query = re.sub(
            rf"\b{re.escape(word)}\b",
            " ",
            query,
            flags=re.IGNORECASE,
        )

    return " ".join(query.split()).strip()


def open_url(url: str, message: str = "") -> None:
    """Open a URL safely."""
    try:
        if message:
            speak(message)
        webbrowser.open(url)
    except Exception as e:
        print(f"[Browser error] {e}")
        speak("Browser open nahi ho saka.")


def run_command(cmd: str) -> bool:
    """Run a local command."""
    try:
        if SYSTEM == "Windows":
            subprocess.Popen(cmd, shell=True)
        else:
            subprocess.Popen(cmd, shell=True)

        return True

    except Exception as e:
        print(f"[Command error] {e}")
        return False


# ============================================================
# WEBSITES
# ============================================================

SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "linkedin": "https://www.linkedin.com",
    "stackoverflow": "https://stackoverflow.com",
    "chatgpt": "https://chatgpt.com",
    "maps": "https://maps.google.com",
}


# ============================================================
# APPLICATIONS
# ============================================================

APPS = {
    "Windows": {
        "notepad": "notepad",
        "calculator": "calc",
        "paint": "mspaint",
        "command prompt": "start cmd",
        "file explorer": "explorer",
        "vs code": "code",
        "chrome": "start chrome",
        "word": "start winword",
        "excel": "start excel",
    },
    "Darwin": {
        "notepad": 'open -a "TextEdit"',
        "calculator": 'open -a "Calculator"',
        "terminal": 'open -a "Terminal"',
        "vs code": 'open -a "Visual Studio Code"',
        "chrome": 'open -a "Google Chrome"',
    },
    "Linux": {
        "notepad": "gedit",
        "calculator": "gnome-calculator",
        "terminal": "gnome-terminal",
        "vs code": "code",
        "chrome": "google-chrome",
        "file explorer": "nautilus",
    },
}

ALIASES = {
    "calc": "calculator",
    "code": "vs code",
    "cmd": "command prompt",
    "files": "file explorer",
    "explorer": "file explorer",
}


# ============================================================
# BASIC COMMANDS
# ============================================================

def cmd_exit(q):
    speak("Goodbye! Phir milte hain.")
    return False


def cmd_greet(q):
    hour = datetime.datetime.now().hour

    if hour < 12:
        part = "morning"
    elif hour < 17:
        part = "afternoon"
    else:
        part = "evening"

    speak(f"Good {part}! Main aapki kya madad kar sakta hu?")


def cmd_time(q):
    speak(datetime.datetime.now().strftime("Abhi samay hai %I:%M %p."))


def cmd_date(q):
    speak(
        datetime.datetime.now().strftime(
            "Aaj ki date hai %d %B %Y, %A."
        )
    )


def cmd_help(q):
    speak(
        "Main apps aur websites open kar sakta hu, search, YouTube, "
        "notes, screenshot, battery, system status, jokes aur AI chat kar sakta hu."
    )


# ============================================================
# OPEN / SEARCH
# ============================================================

def cmd_open(q):
    target = extract(
        q,
        [
            ASSISTANT_NAME,
            "open",
            "kholo",
            "khol",
            "launch",
            "start",
            "please",
            "do",
            "the",
        ],
    )

    target = ALIASES.get(target, target)

    if not target:
        speak("Kya open karu?")
        return

    if target in SITES:
        open_url(SITES[target], f"Opening {target}.")
        return

    app = APPS.get(SYSTEM, {}).get(target)

    if app and run_command(app):
        speak(f"Opening {target}.")
        return

    speak(f"{target} mujhe nahi mila. Google pe search kar raha hu.")

    open_url(
        "https://www.google.com/search?q="
        + urllib.parse.quote(target)
    )


def cmd_search(q):
    topic = extract(
        q,
        [
            ASSISTANT_NAME,
            "search",
            "google",
            "for",
            "on",
            "about",
            "dhundo",
            "khojo",
            "please",
        ],
    )

    if not topic:
        speak("Kya search karu?")
        return

    speak(f"Google pe {topic} search kar raha hu.")

    open_url(
        "https://www.google.com/search?q="
        + urllib.parse.quote(topic)
    )


def cmd_play(q):
    song = extract(q,
        [
            ASSISTANT_NAME,
            "play",
            "chala",
            "chalao",
            "on",
            "youtube",
            "song",
            "gana",
            "please",
            "do",
        ],
    )

    if not song:
        speak("Kaunsa gaana ya video chalaun?")
        return

    speak(f"YouTube par {song} play kar raha hu.")

    search_url = (
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote(song)
    )

    open_url(search_url)


# ============================================================
# WIKIPEDIA
# ============================================================

def cmd_wikipedia(q):
    topic = extract(
        q,
        [
            ASSISTANT_NAME,
            "wikipedia",
            "search",
            "on",
            "about",
            "for",
            "tell",
            "me",
            "batao",
            "please",
        ],
    )

    if not topic:
        speak("Wikipedia pe kya dekhu?")
        return

    if wikipedia is None:
        speak("Wikipedia library installed nahi hai.")
        return

    try:
        speak("Wikipedia se dekh raha hu.")

        result = wikipedia.summary(
            topic,
            sentences=2,
            auto_suggest=False,
        )

        speak(result)

    except wikipedia.exceptions.DisambiguationError as e:
        options = ", ".join(e.options[:3])
        speak(
            f"Ye kai cheezon ko refer karta hai, jaise {options}. "
            "Thoda specific bolo."
        )

    except Exception as e:
        print(f"[Wikipedia error] {e}")
        speak("Iske baare me Wikipedia par information nahi mili.")


# ============================================================
# JOKES
# ============================================================

def cmd_joke(q):
    if pyjokes:
        try:
            speak(pyjokes.get_joke())
            return
        except Exception:
            pass

    speak(
        random.choice(
            [
                "Programmers ko nature pasand nahi, kyunki wahan bahut saare bugs hote hain.",
                "Maine computer ko thanda karne ke liye window khol di, ab Windows crash ho gayi.",
            ]
        )
    )


# ============================================================
# NOTES
# ============================================================

def cmd_note(q):
    note = extract(
        q,
        [
            ASSISTANT_NAME,
            "note",
            "make",
            "take",
            "a",
            "yaad",
            "rakh",
            "rakho",
            "likh",
            "lo",
            "kar",
            "this",
            "that",
            "please",
        ],
    )

    if not note:
        speak("Kya note karu?")
        return

    try:
        with open(NOTES_FILE, "a", encoding="utf-8") as file:
            timestamp = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
            file.write(f"[{timestamp}] {note}\n")

        speak("Note save kar liya.")

    except Exception as e:
        print(f"[Note error] {e}")
        speak("Note save nahi ho saka.")


def cmd_read_notes(q):
    if not NOTES_FILE.exists():
        speak("Abhi koi note nahi hai.")
        return

    try:
        notes = NOTES_FILE.read_text(encoding="utf-8").strip()

        if notes:
            # Voice output of extremely long files is inconvenient.
            lines = notes.splitlines()
            recent = "\n".join(lines[-10:])
            speak(recent)
        else:
            speak("Abhi koi note nahi hai.")

    except Exception as e:
        print(f"[Read notes error] {e}")
        speak("Notes read nahi ho sake.")


def cmd_clear_notes(q):
    try:
        if NOTES_FILE.exists():
            NOTES_FILE.write_text("", encoding="utf-8")

        speak("Saare notes clear kar diye.")

    except Exception as e:
        print(f"[Clear notes error] {e}")
        speak("Notes clear nahi ho sake.")


# ============================================================
# SCREENSHOT
# ============================================================

def cmd_screenshot(q):
    if pyautogui is None:
        speak("Screenshot ke liye pyautogui install karo.")
        return

    try:
        screenshot_dir = BASE_DIR / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)

        name = datetime.datetime.now().strftime(
            "screenshot_%Y%m%d_%H%M%S.png"
        )

        path = screenshot_dir / name

        pyautogui.screenshot().save(path)

        speak(f"Screenshot save ho gaya: {name}")

    except Exception as e:
        print(f"[Screenshot error] {e}")
        speak("Screenshot nahi liya ja saka.")


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def cmd_battery(q):
    if psutil is None:
        speak("Battery information ke liye psutil install karo.")
        return

    try:
        battery = psutil.sensors_battery()

        if battery is None:
            speak("Battery information available nahi hai.")
            return

        status = (
            "charging"
            if battery.power_plugged
            else "not charging"
        )

        speak(
            f"Battery {int(battery.percent)} percent hai "
            f"aur {status}."
        )

    except Exception as e:
        print(f"[Battery error] {e}")
        speak("Battery information nahi mil saki.")


def cmd_system_status(q):
    if psutil is None:
        speak("System status ke liye psutil install karo.")
        return

    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent

        speak(
            f"CPU usage {cpu} percent hai aur RAM usage {ram} percent hai."
        )

    except Exception as e:
        print(f"[System status error] {e}")
        speak("System information nahi mil saki.")


# ============================================================
# WINDOWS VOLUME
# ============================================================

def cmd_volume_up(q):
    if SYSTEM != "Windows" or pyautogui is None:
        speak("Volume control is system par available nahi hai.")
        return

    try:
        for _ in range(5):
            pyautogui.press("volumeup")

        speak("Volume badha diya.")

    except Exception as e:
        print(f"[Volume error] {e}")
        speak("Volume change nahi ho saka.")


def cmd_volume_down(q):
    if SYSTEM != "Windows" or pyautogui is None:
        speak("Volume control is system par available nahi hai.")
        return

    try:
        for _ in range(5):
            pyautogui.press("volumedown")

        speak("Volume kam kar diya.")

    except Exception as e:
        print(f"[Volume error] {e}")
        speak("Volume change nahi ho saka.")


def cmd_mute(q):
    if SYSTEM != "Windows" or pyautogui is None:
        speak("Mute control is system par available nahi hai.")
        return

    try:
        pyautogui.press("volumemute")
        speak("Volume mute toggle kar diya.")

    except Exception as e:
        print(f"[Mute error] {e}")
        speak("Mute nahi ho saka.")


# ============================================================
# POWER COMMANDS
# ============================================================

def confirm_action(action: str) -> bool:
    speak(f"Kya aap sure hain ki PC {action} karna hai? Yes ya no bolo.")

    answer = listen()

    return answer in {
        "yes",
        "haan",
        "ha",
        "yes please",
        "confirm",
    }


def cmd_lock(q):
    if SYSTEM != "Windows":
        speak("Lock command abhi Windows ke liye configured hai.")
        return

    if not confirm_action("lock"):
        speak("Theek hai, cancel kar diya.")
        return

    try:
        subprocess.run(
            ["rundll32.exe", "user32.dll,LockWorkStation"],
            check=False,
        )
    except Exception as e:
        print(f"[Lock error] {e}")
        speak("PC lock nahi ho saka.")


def cmd_shutdown(q):
    if SYSTEM != "Windows":
        speak("Shutdown command abhi Windows ke liye configured hai.")
        return

    if not confirm_action("shutdown"):
        speak("Theek hai, shutdown cancel kar diya.")
        return

    try:
        subprocess.Popen(
            ["shutdown", "/s", "/t", "10"],
            shell=False,
        )
        speak("PC 10 seconds me shutdown hoga.")

    except Exception as e:
        print(f"[Shutdown error] {e}")
        speak("Shutdown command execute nahi ho saki.")


def cmd_restart(q):
    if SYSTEM != "Windows":
        speak("Restart command abhi Windows ke liye configured hai.")
        return

    if not confirm_action("restart"):
        speak("Theek hai, restart cancel kar diya.")
        return

    try:
        subprocess.Popen(
            ["shutdown", "/r", "/t", "10"],
            shell=False,
        )
        speak("PC 10 seconds me restart hoga.")

    except Exception as e:
        print(f"[Restart error] {e}")
        speak("Restart command execute nahi ho saki.")


# ============================================================
# MEMORY
# ============================================================

def cmd_clear_memory(q):
    global chat_history

    chat_history = chat_history[:1]

    speak("AI conversation memory clear kar di.")


# ============================================================
# COMMAND TABLE
# ============================================================

COMMANDS = [
    (
        ["exit", "quit", "bye", "goodbye", "band kar", "stop"],
        cmd_exit,
    ),

    (
        ["hello", "hi", "hey", "namaste", "good morning"],
        cmd_greet,
    ),

    (
        ["what can you do", "help", "madad"],
        cmd_help,
    ),

    (
        ["forget everything", "clear memory", "bhool ja"],
        cmd_clear_memory,
    ),

    (
        ["clear notes", "delete notes", "notes clear"],
        cmd_clear_notes,
    ),

    (
        ["what time", "time kya", "current time", "the time", "samay", "baje"],
        cmd_time,
    ),

    (
        ["what date", "today's date", "current date", "date kya",
         "tarikh", "aaj ki date"],
        cmd_date,
    ),

    (
        ["read notes", "show notes", "mere notes"],
        cmd_read_notes,
    ),

    (
        ["make a note", "take a note", "note this", "note kar",
         "yaad rakh", "yaad rakho", "likh lo"],
        cmd_note,
    ),

    (
        ["screenshot", "screen shot"],
        cmd_screenshot,
    ),

    (
        ["system status", "cpu usage", "ram usage", "computer status"],
        cmd_system_status,
    ),

    (
        ["battery"],
        cmd_battery,
    ),

    (
        ["volume up", "increase volume", "volume badhao"],
        cmd_volume_up,
    ),

    (
        ["volume down", "decrease volume", "volume kam"],
        cmd_volume_down,
    ),

    (
        ["mute", "volume mute"],
        cmd_mute,
    ),

    (
        ["lock computer", "lock pc", "computer lock"],
        cmd_lock,
    ),

    (
        ["shutdown computer", "shutdown pc", "computer shutdown"],
        cmd_shutdown,
    ),

    (
        ["restart computer", "restart pc", "computer restart"],
        cmd_restart,
    ),

    (
        ["joke", "mazak", "chutkula"],
        cmd_joke,
    ),

    (
        ["play", "chala", "chalao"],
        cmd_play,
    ),

    (
        ["open", "kholo", "khol", "launch"],
        cmd_open,
    ),

    (
        ["wikipedia"],
        cmd_wikipedia,
    ),

    (
        ["search", "google", "dhundo", "khojo"],
        cmd_search,
    ),
]


# ============================================================
# COMMAND HANDLER
# ============================================================

def handle(query: str) -> bool:
    """Return True to continue, False to stop."""

    for keywords, handler in COMMANDS:
        for keyword in keywords:

            if re.search(
                rf"\b{re.escape(keyword)}\b",
                query,
                flags=re.IGNORECASE,
            ):
                return handler(query) is not False

    # No local command matched.
    ask_ai(query)

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    speak("Jarvis online. Boliye, kya karna hai?")

    while True:

        query = listen()

        if not query:
            continue

        # Remove wake word from the actual command.
        query = re.sub(
            rf"\b{re.escape(ASSISTANT_NAME)}\b",
            "",
            query,
            flags=re.IGNORECASE,
        ).strip()

        if not query:
            speak("Yes boss?")
            continue

        if not handle(query):
            break


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\nBye!")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        speak("Unexpected error aa gaya. Console me error check karo.")
