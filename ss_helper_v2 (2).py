import os
import sys
import subprocess
import ctypes
import urllib.request
import urllib.error
import zipfile
import shutil
import json
import sqlite3
import shutil
import tempfile
import hashlib
import struct
import re
import threading
import time
from datetime import datetime

# ── Admin check ───────────────────────────────────────────────────────────────

def is_admin(): # appdata
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def relaunch_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1
    )
    sys.exit()

# ── Helpers ───────────────────────────────────────────────────────────────────

def header(title):
    print()
    print("  " + "═" * 68)
    print(f"   {title}")
    print("  " + "═" * 68)

def found(msg):
    print(f"  \033[92m[FOUND]\033[0m {msg}")

def info(msg):
    print(f"  \033[94m[~]\033[0m {msg}")

def warn(msg):
    print(f"  \033[93m[!]\033[0m {msg}")

def red(msg):
    print(f"  \033[91m[!!]\033[0m {msg}")

def run(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return ""

def pause():
    input("\n  Press Enter to return to menu...")

def clear():
    os.system("cls")

# ── Path Inspector (shown whenever something suspicious is detected) ───────────

def show_path_options(label, path):
    """Interactive prompt to view/open a detected suspicious path."""
    print()
    print(f"  \033[93m[?] Inspect detected item: {label}\033[0m")
    print(f"      Path: {path}")
    print()
    print("      [1] Open containing folder in Explorer")
    print("      [2] Copy path to clipboard")
    print("      [3] Show file details (size, dates)")
    print("      [4] Skip")
    choice = input("      Action: ").strip()
    if choice == "1":
        if os.path.exists(path):
            if os.path.isfile(path):
                subprocess.Popen(f'explorer /select,"{path}"', shell=True)
            else:
                subprocess.Popen(f'explorer "{path}"', shell=True)
        else:
            warn("Path no longer exists on disk.")
    elif choice == "2":
        try:
            subprocess.run(f'echo {path}| clip', shell=True)
            info("Path copied to clipboard.")
        except Exception as e:
            warn(f"Clipboard failed: {e}")
    elif choice == "3":
        if os.path.exists(path):
            size  = os.path.getsize(path)
            mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
            ctime = datetime.fromtimestamp(os.path.getctime(path)).strftime("%Y-%m-%d %H:%M:%S")
            print(f"      Size     : {size // 1024} KB ({size} bytes)")
            print(f"      Modified : {mtime}")
            print(f"      Created  : {ctime}")
            print(f"      Full path: {path}")
        else:
            warn("Path no longer exists on disk.")
    print()

APPDATA      = os.environ.get("APPDATA", "")
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
TEMP         = os.environ.get("TEMP", "")
USERPROFILE  = os.environ.get("USERPROFILE", "")
MINECRAFT    = os.path.join(APPDATA, ".minecraft")
PROGRAMDATA  = os.environ.get("PROGRAMDATA", "C:\\ProgramData")
DOWNLOADS    = os.path.join(LOCALAPPDATA, "ChichoSSHelper")

OCEAN_API_BASE = "https://anticheat.ac/api/pins"
WEBHOOK_URL = "https://discord.com/api/webhooks/1508632099416969297/RhG9LWyqzwvV_KVgvqlLccyqCUZVVFL1tpbqIXBN_R_G7WtwuXRoFHq5urXA9IuHgvcM"

CHEAT_CLIENTS = [
    "Wurst", "Impact", "Meteor", "Aristois", "Liquidbounce", "Sigma",
    "Ares", "Future", "Vape", "Astolfo", "Drip", "Salhack", "Entropy",
    "Inertia", "Raven", "Novoline", "Wolfram", "PyroHax", "Rekt",
    "Remix", "XRay", "Horion", "Phi", "Hybrid", "Rusher", "cyemer",
    "Prestige", "velaris", "bleach", "vapor", "dusk", "azura", "vertex",
    "nexus", "rise", "lucid", "ketamine", "reflex", "exodus", "zenith"
]

SUSPICIOUS_PROCS = [
    "cheat", "hack", "inject", "ghost", "vape", "sigma",
    "future", "meteor", "wurst", "aristois", "payload", "rat",
    "keylog", "prestige", "bleach", "vapor", "dusk"
]

SUSPICIOUS_INJECTION_MODULES = [
    "inject", "hook", "cheat", "vape", "sigma",
    "future", "meteor", "wurst", "aristois", "payload"
]

# ── Download helper ───────────────────────────────────────────────────────────

def download_and_open(url, filename):
    os.makedirs(DOWNLOADS, exist_ok=True)
    dest = os.path.join(DOWNLOADS, filename)

    if os.path.exists(dest):
        info(f"Already downloaded: {filename}  —  opening...")
        _open_file_or_folder(dest)
        pause()
        return

    info(f"Downloading: {filename}")
    info(f"URL: {url}")
    print()

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk = 8192
            with open(dest, "wb") as f:
                while True:
                    data = response.read(chunk)
                    if not data:
                        break
                    f.write(data)
                    downloaded += len(data)
                    if total:
                        pct = min(downloaded * 100 // total, 100)
                        bar = ("█" * (pct // 5)).ljust(20)
                        print(f"\r  [{bar}] {pct}%  ({downloaded // 1024} KB)", end="", flush=True)
        print()

    except Exception as e:
        print()
        warn(f"Download failed: {e}")
        if os.path.exists(dest):
            os.remove(dest)
        pause()
        return

    if not os.path.exists(dest) or os.path.getsize(dest) == 0:
        warn("Downloaded file is empty or missing.")
        pause()
        return

    info(f"Saved to: {dest}")

    if filename.lower().endswith(".zip"):
        folder_name = filename[:-4]
        extract_dir = os.path.join(DOWNLOADS, folder_name)
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(dest, "r") as z:
                z.extractall(extract_dir)
            info(f"Extracted to: {extract_dir}")
            _open_file_or_folder(extract_dir)
        except Exception as e:
            warn(f"Extraction failed: {e}")
            info("Opening ZIP directly...")
            os.startfile(dest)
    else:
        _open_file_or_folder(dest)

    pause()


def _open_file_or_folder(path):
    try:
        if os.path.isdir(path):
            subprocess.Popen(f'explorer "{path}"')
        else:
            os.startfile(path)
    except Exception as e:
        warn(f"Could not open: {e}")

# ── Original checks ───────────────────────────────────────────────────────────

def check_appdata():
    clear()
    header("AppData Cheat Client Check")
    found_any = False
    for client in CHEAT_CLIENTS:
        for base in [APPDATA, LOCALAPPDATA]:
            path = os.path.join(base, client)
            if os.path.exists(path):
                found(f"{client}  →  {path}")
                found_any = True
                show_path_options(client, path)
    if not found_any:
        info("No known cheat client folders found.")
    info("Scanning for .jar files in AppData...")
    out = run(f'dir "{APPDATA}" /s /b *.jar 2>nul')
    for line in out.splitlines():
        if ".minecraft" not in line.lower():
            warn(f"JAR outside .minecraft: {line}")
            show_path_options(os.path.basename(line), line)
    info("Scanning for .dll files with suspicious names...")
    out = run(f'dir "{APPDATA}" /s /b *.dll 2>nul')
    for line in out.splitlines():
        if any(s in line.lower() for s in ["inject","hook","cheat"]):
            warn(f"Suspicious DLL: {line}")
            show_path_options(os.path.basename(line), line)
    pause()

def check_processes():
    clear()
    header("Running Processes")
    info("Java processes:")
    print(run("tasklist /fi \"imagename eq javaw.exe\" /v"))
    print(run("tasklist /fi \"imagename eq java.exe\" /v"))
    info("Scanning Java modules for injected DLLs...")
    scan_java_injection()
    info("Scanning for suspicious process names...")
    all_procs = run("tasklist").lower()
    for s in SUSPICIOUS_PROCS:
        if s in all_procs:
            found(f"Process matching keyword: {s}")
            send_to_webhook("N/A (Process Scan)", {
                "result": "Suspicious Process Detected",
                "game": "Running Processes",
                "detects": [s],
                "country": "N/A",
                "scantime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
    info("Full process list:")
    print(run("tasklist /v"))
    pause()

def scan_java_injection():
    found_any = False
    for proc in ["javaw.exe", "java.exe"]:
        out = run(f'tasklist /m /fi "imagename eq {proc}"')
        if not out:
            continue
        for line in out.splitlines():
            text = line.lower()
            if proc in text and any(k in text for k in SUSPICIOUS_INJECTION_MODULES):
                found(f"Injected module in {proc}: {line.strip()}")
                found_any = True
                send_to_webhook("N/A (Injection Scan)", {
                    "result": "Injection Detected",
                    "game": "Java Process",
                    "detects": [line.strip()],
                    "country": "N/A",
                    "scantime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
    if not found_any:
        info("No suspicious injected modules found in Java processes.")


def find_launcher_paths(name):
    candidates = []
    if name == "norisk":
        candidates = [
            os.path.join(LOCALAPPDATA, "norisk"),
            os.path.join(APPDATA, "norisk"),
        ]
    elif name == "prism":
        candidates = [
            os.path.join(APPDATA, "PrismLauncher"),
            os.path.join(APPDATA, "prismlauncher"),
            os.path.join(APPDATA, "prism-launcher"),
            os.path.join(APPDATA, "Prism Launcher"),
            os.path.join(LOCALAPPDATA, "Programs", "Prism Launcher"),
            os.path.join(LOCALAPPDATA, "PrismLauncher"),
        ]
    elif name == "lunar":
        candidates = [
            os.path.join(USERPROFILE, ".lunarclient", "offline", "multiver", "mods"),
            os.path.join(USERPROFILE, ".lunarclient", "offline"),
            os.path.join(USERPROFILE, ".lunarclient", "profiles"),
            os.path.join(USERPROFILE, ".lunarclient"),
            os.path.join(APPDATA, "LunarClient"),
            os.path.join(LOCALAPPDATA, "Programs", "Lunar Client"),
        ]
    elif name == "feather":
        candidates = [
            os.path.join(APPDATA, "feather"),
            os.path.join(APPDATA, "FeatherClient"),
            os.path.join(LOCALAPPDATA, "Programs", "Feather"),
        ]
    elif name == "modrinth":
        candidates = [
            os.path.join(APPDATA, "ModrinthApp", "profiles"),
            os.path.join(APPDATA, "ModrinthApp"),
            os.path.join(APPDATA, "com.modrinth.theseus", "profiles"),
            os.path.join(LOCALAPPDATA, "ModrinthApp", "profiles"),
            os.path.join(LOCALAPPDATA, "ModrinthApp"),
            os.path.join(LOCALAPPDATA, "com.modrinth.theseus"),
            os.path.join(LOCALAPPDATA, "Programs", "Modrinth App"),
        ]
    elif name == "curseforge":
        candidates = [
            os.path.join(USERPROFILE, "curseforge", "minecraft", "Instances"),
            os.path.join(APPDATA, "CurseForge"),
            os.path.join(LOCALAPPDATA, "CurseForge"),
            os.path.join(APPDATA, "Overwolf", "CurseForge"),
        ]
    elif name == "badlion":
        candidates = [
            os.path.join(APPDATA, "badlion client"),
            os.path.join(APPDATA, "Badlion Client"),
            os.path.join(LOCALAPPDATA, "Programs", "Badlion Client"),
        ]
    elif name == "tlauncher":
        candidates = [
            os.path.join(APPDATA, ".tlauncher"),
            os.path.join(APPDATA, "TLauncher"),
        ]
    elif name == "multimc":
        candidates = [
            os.path.join(APPDATA, "MultiMC"),
            os.path.join(LOCALAPPDATA, "Programs", "MultiMC"),
        ]
    elif name == ".minecraft":
        candidates = [os.path.join(MINECRAFT, "mods")]

    return [p for p in candidates if os.path.exists(p)]


def check_minecraft():
    clear()
    header(".minecraft Folder Check")
    if not os.path.exists(MINECRAFT):
        warn(".minecraft folder not found.")
        pause()
        return
    for folder in ["mods", "versions", "config", "resourcepacks", "shaderpacks"]:
        path = os.path.join(MINECRAFT, folder)
        info(f"{folder}:")
        if os.path.exists(path):
            files = os.listdir(path)
            if files:
                for f in files:
                    print(f"    {f}")
            else:
                print("    Empty.")
        else:
            print("    Not found.")

    info("launcher_profiles.json — version entries:")
    lp = os.path.join(MINECRAFT, "launcher_profiles.json")
    if os.path.exists(lp):
        try:
            with open(lp, "r", errors="ignore") as f:
                data = json.load(f)
            profiles = data.get("profiles", {})
            for k, v in profiles.items():
                vname = v.get("lastVersionId", "?")
                name  = v.get("name", k)
                jpath = v.get("javaDir", "default Java")
                print(f"    [{name}]  version={vname}  java={jpath}")
                if jpath and "program files" not in jpath.lower() and jpath != "default Java":
                    warn(f"Non-standard Java path in profile '{name}': {jpath}")
        except Exception as e:
            warn(f"Could not parse launcher_profiles.json: {e}")
    else:
        info("No launcher_profiles.json found.")

    info("Checking latest.log for suspicious keywords...")
    log = os.path.join(MINECRAFT, "logs", "latest.log")
    if os.path.exists(log):
        with open(log, "r", errors="ignore") as f:
            for line in f:
                if any(k in line.lower() for k in ["cheat","inject","wurst","sigma","vape","hacked"]):
                    warn(f"Suspicious log entry: {line.strip()}")
    else:
        info("No latest.log found.")
    pause()


def scan_launcher_mods():
    clear()
    header("Minecraft Launcher / Mods Reader")
    print("  [1] norisk")
    print("  [2] prism")
    print("  [3] lunar")
    print("  [4] feather")
    print("  [5] modrinth")
    print("  [6] curseforge")
    print("  [7] badlion")
    print("  [8] tlauncher")
    print("  [9] multimc")
    print("  [10] .minecraft mods")
    print("  [0] Return to menu")
    print()

    choice = input("  Launcher choice: ").strip()
    mapping = {
        "1": "norisk", "2": "prism", "3": "lunar", "4": "feather",
        "5": "modrinth", "6": "curseforge", "7": "badlion",
        "8": "tlauncher", "9": "multimc", "10": ".minecraft",
    }

    if choice == "0":
        return

    launcher = mapping.get(choice)
    if not launcher:
        warn("Invalid launcher selection.")
        pause()
        return

    candidates = find_launcher_paths(launcher)
    if not candidates:
        warn(f"No automatic path found for {launcher}.")
        custom = input("  Enter a custom launcher folder path or press Enter to cancel: ").strip()
        if not custom or not os.path.exists(custom):
            warn("No valid path selected.")
            pause()
            return
        candidates = [custom]

    selected_path = candidates[0]
    info(f"Scanning launcher path: {selected_path}")
    matches = []
    for root, _, files in os.walk(selected_path):
        for filename in files:
            if filename.lower().endswith((".jar", ".zip", ".json")):
                matches.append(os.path.relpath(os.path.join(root, filename), selected_path))
                if len(matches) >= 250:
                    break
        if len(matches) >= 250:
            break

    lines = [
        f"Launcher scan: {launcher}",
        f"Path: {selected_path}",
        f"Found {len(matches)} mod / metadata files",
        "",
    ]

    if matches:
        for m in matches:
            lines.append(m)
    else:
        lines.append("No mod or launcher metadata files found in this path.")

    filename = f"launcher_mods_{launcher}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    dump_to_downloads(filename, "\n".join(lines))


def check_minecraft_launchers():
    clear()
    header("Minecraft Launcher / Profile Scanner")
    launchers = ["norisk", "prism", "lunar", "feather", "modrinth",
                 "curseforge", "badlion", "tlauncher", "multimc", ".minecraft"]
    for launcher in launchers:
        candidates = find_launcher_paths(launcher)
        if not candidates:
            warn(f"{launcher}: not found")
            continue
        found(f"{launcher}:")
        for path in candidates:
            print(f"    {path}")
            if os.path.isdir(path):
                total = sum(len(files) for _, _, files in os.walk(path))
                print(f"      Files: {total}")
    pause()


def check_java_arguments():
    clear()
    header("Java Process Argument Scanner")
    cmd = 'wmic process where "name=\'javaw.exe\' or name=\'java.exe\'" get ProcessId,CommandLine /format:list'
    out = run(cmd)
    if not out:
        info("No java processes found.")
        pause()
        return

    suspicious = ["-javaagent", "inject", "mixin", "tweakclass", "forge", "fabric", "plugin", "agent"]
    lines = out.splitlines()
    flagged = False
    for line in lines:
        text = line.strip()
        if not text:
            continue
        if any(k in text.lower() for k in suspicious):
            warn(text)
            flagged = True
        else:
            print(f"  {text}")

    if not flagged:
        info("No suspicious Java command-line arguments detected.")
    pause()


def check_suspicious_folders():
    clear()
    header("Suspicious Cheat Folder Scanner")
    bases = [
        APPDATA,
        LOCALAPPDATA,
        os.path.join(USERPROFILE, "Downloads"),
        os.path.join(USERPROFILE, "Desktop"),
        os.environ.get("PROGRAMFILES", "C:\\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
        os.path.join(USERPROFILE, ".minecraft"),
    ]
    extra_names = ["badlion", "impact", "salhack", "liquidbounce", "disabler",
                   "meteor", "exploit", "payload", "bleach", "vapor", "dusk",
                   "azura", "vertex", "nexus", "rise", "lucid"]
    all_names = sorted(set(CHEAT_CLIENTS + extra_names), key=str.lower)

    found_any = False
    for base in bases:
        if not base or not os.path.exists(base):
            continue
        for name in all_names:
            path = os.path.join(base, name)
            if os.path.exists(path):
                found(f"{path}")
                found_any = True
                show_path_options(name, path)

    if not found_any:
        info("No suspicious cheat folders found in common locations.")
    pause()


def check_ocean_api():
    clear()
    header("Ocean Anti-Cheat — Scan Lookup")

    print("  Tell the suspect to:")
    print("  1. Go to  https://anticheat.ac")
    print("  2. Download and run the Ocean scan tool")
    print("  3. Send you the PIN it generates")
    print()

    pin = input("  Enter the suspect's Ocean PIN: ").strip()
    if not pin:
        warn("No pin entered.")
        pause()
        return

    url = f"https://anticheat.ac/api/pins/{pin}"
    info(f"Fetching results for pin {pin}...")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        warn(f"HTTP Error {e.code}: {e.reason} — is the PIN correct?")
        pause()
        return
    except Exception as e:
        warn(f"Request failed: {e}")
        pause()
        return

    try:
        data = json.loads(raw)
    except Exception:
        warn("Non-JSON response from Ocean API. Raw output:")
        print(raw[:3000])
        pause()
        return

    if not isinstance(data, dict):
        warn("Unexpected response format.")
        print(raw[:3000])
        pause()
        return

    print()
    game     = data.get("pin_type") or data.get("game", "N/A")
    scantime = data.get("scantime") or data.get("scan_time", "N/A")
    country  = data.get("country", "N/A")
    sentence = data.get("result") or data.get("sentence") or data.get("verdict", "N/A")

    if isinstance(sentence, str):
        sl = sentence.lower()
        if any(k in sl for k in ["cheat", "guilty", "detected", "ban"]):
            sentence_display = f"\033[91m{sentence}\033[0m"
        elif any(k in sl for k in ["warn", "suspicious"]):
            sentence_display = f"\033[93m{sentence}\033[0m"
        elif any(k in sl for k in ["clean", "not guilty", "clear"]):
            sentence_display = f"\033[92m{sentence}\033[0m"
        else:
            sentence_display = sentence
    else:
        sentence_display = str(sentence)

    print(f"  Game:      {game}")
    print(f"  Scan Time: {scantime}")
    print(f"  Pin:       {pin}")
    print(f"  Country:   {country}")
    print(f"  Verdict:   {sentence_display}")

    if isinstance(sentence, str) and any(k in sentence.lower() for k in ["cheat", "guilty", "detected", "ban"]):
        info("Positive result detected — sending to webhook...")
        send_to_webhook(pin, data)

    def _print_list(field_names, label, colour=None):
        raw_value = None
        for name in field_names:
            if name in data:
                raw_value = data[name]
                break
        if raw_value is None:
            return

        if isinstance(raw_value, str):
            try:
                entries = json.loads(raw_value.replace("'", '"'))
            except Exception:
                entries = [e.strip() for e in raw_value.split("\n") if e.strip()]
        else:
            entries = raw_value if isinstance(raw_value, list) else [str(raw_value)]

        if not entries:
            return

        print(f"\n  {label}:")
        for item in entries:
            parts = str(item).split(":::")
            main  = parts[0].strip()
            extra = "  →  " + "  |  ".join(p.strip() for p in parts[1:] if p.strip()) if len(parts) > 1 else ""
            if colour:
                print(f"    {colour}{main}\033[0m{extra}")
            else:
                print(f"    {main}{extra}")

    _print_list(["detects", "detections", "detect_list"],   "Detections",       "\033[91m")
    _print_list(["warnings", "warns", "warning_list"],      "Warnings",         "\033[93m")
    _print_list(["suspicious", "suspicious_files"],         "Suspicious Files",  "\033[93m")
    _print_list(["execlist", "exec_list", "executed"],      "Exec List")

    known = {
        "pin_type","game","scantime","scan_time","country","result",
        "sentence","verdict","pin","detects","detections","detect_list",
        "warnings","warns","warning_list","suspicious","suspicious_files",
        "execlist","exec_list","executed"
    }
    extras = {k: v for k, v in data.items() if k not in known and v}
    if extras:
        print("\n  Additional fields:")
        for k, v in extras.items():
            print(f"    {k}: {v}")

    pause()


def send_to_webhook(pin, data):
    WEBHOOK_URL = "https://discord.com/api/webhooks/1508632099416969297/RhG9LWyqzwvV_KVgvqlLccyqCUZVVFL1tpbqIXBN_R_G7WtwuXRoFHq5urXA9IuHgvcM"

    game     = data.get("pin_type") or data.get("game", "N/A")
    scantime = data.get("scantime") or data.get("scan_time") or data.get("scantime", "N/A")
    country  = data.get("country", "N/A")
    sentence = data.get("result") or data.get("sentence") or data.get("verdict", "N/A")

    detects_raw = None
    for field in ["detects", "detections", "detect_list"]:
        if field in data:
            detects_raw = data[field]
            break

    if isinstance(detects_raw, list):
        detects = detects_raw
    elif isinstance(detects_raw, str):
        detects = [e.strip() for e in detects_raw.split("\n") if e.strip()]
    else:
        detects = []

    detects_str = "\n".join(f"• {d}" for d in detects) if detects else "None listed"

    embed = {
        "title": "🚨 Positive SS Result",
        "color": 0xFF0000,
        "fields": [
            {"name": "PIN",        "value": str(pin),       "inline": True},
            {"name": "Game",       "value": str(game),      "inline": True},
            {"name": "Country",    "value": str(country),   "inline": True},
            {"name": "Verdict",    "value": str(sentence),  "inline": False},
            {"name": "Scan Time",  "value": str(scantime),  "inline": False},
            {"name": "Detections", "value": detects_str,    "inline": False},
        ],
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + ".000Z",
    }

    payload = json.dumps({"embeds": [embed]}).encode("utf-8")

    try:
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            info(f"Webhook sent! Status: {resp.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        warn(f"Webhook HTTP error {e.code}: {e.reason} — {body}")
    except Exception as e:
        warn(f"Webhook failed: {e}")


# ── Browser Forensics ─────────────────────────────────────────────────────────

BROWSER_PROFILES = {
    "Chrome":  os.path.join(LOCALAPPDATA, r"Google\Chrome\User Data"),
    "Edge":    os.path.join(LOCALAPPDATA, r"Microsoft\Edge\User Data"),
    "Brave":   os.path.join(LOCALAPPDATA, r"BraveSoftware\Brave-Browser\User Data"),
    "Opera":   os.path.join(APPDATA,      r"Opera Software\Opera Stable"),
    "Vivaldi": os.path.join(LOCALAPPDATA, r"Vivaldi\User Data"),
}

FIREFOX_ROOT = os.path.join(APPDATA, r"Mozilla\Firefox\Profiles")


def _chromium_db_copy(db_path):
    tmp = tempfile.mktemp(suffix=".db")
    shutil.copy2(db_path, tmp)
    return tmp


def _chromium_profiles(browser_root):
    profiles = []
    if not os.path.isdir(browser_root):
        return profiles
    for entry in os.listdir(browser_root):
        full = os.path.join(browser_root, entry)
        if os.path.isdir(full) and (entry == "Default" or entry.startswith("Profile")):
            profiles.append(full)
    return profiles


def check_browser_history():
    clear()
    header("Browser History Viewer")
    any_found = False

    for browser, root in BROWSER_PROFILES.items():
        profiles = _chromium_profiles(root)
        if not profiles:
            continue
        info(f"{browser}:")
        any_found = True
        for profile in profiles:
            hist_db = os.path.join(profile, "History")
            if not os.path.exists(hist_db):
                continue
            try:
                tmp = _chromium_db_copy(hist_db)
                conn = sqlite3.connect(tmp)
                cur  = conn.cursor()
                cur.execute("""
                    SELECT url, title, visit_count,
                           datetime(last_visit_time/1000000-11644473600, 'unixepoch', 'localtime')
                    FROM urls
                    ORDER BY last_visit_time DESC
                    LIMIT 50
                """)
                rows = cur.fetchall()
                conn.close()
                os.remove(tmp)
                print(f"    Profile: {os.path.basename(profile)}  ({len(rows)} recent URLs shown)")
                for url, title, visits, ts in rows:
                    title = (title or "")[:60]
                    print(f"      [{ts}] ({visits}x)  {title}")
                    print(f"               {url[:100]}")
            except Exception as e:
                warn(f"    Could not read {browser} history ({os.path.basename(profile)}): {e}")

    if os.path.isdir(FIREFOX_ROOT):
        any_found = True
        info("Firefox:")
        for profile in os.listdir(FIREFOX_ROOT):
            places = os.path.join(FIREFOX_ROOT, profile, "places.sqlite")
            if not os.path.exists(places):
                continue
            try:
                tmp = _chromium_db_copy(places)
                conn = sqlite3.connect(tmp)
                cur  = conn.cursor()
                cur.execute("""
                    SELECT p.url, p.title, p.visit_count,
                           datetime(h.visit_date/1000000, 'unixepoch', 'localtime')
                    FROM moz_places p
                    JOIN moz_historyvisits h ON h.place_id = p.id
                    ORDER BY h.visit_date DESC
                    LIMIT 50
                """)
                rows = cur.fetchall()
                conn.close()
                os.remove(tmp)
                print(f"    Profile: {profile}  ({len(rows)} recent URLs shown)")
                for url, title, visits, ts in rows:
                    title = (title or "")[:60]
                    print(f"      [{ts}] ({visits}x)  {title}")
                    print(f"               {url[:100]}")
            except Exception as e:
                warn(f"    Could not read Firefox history ({profile}): {e}")

    if not any_found:
        info("No browser profile folders found.")
    pause()


def check_browser_downloads():
    clear()
    header("Browser Downloads Viewer")
    any_found = False

    for browser, root in BROWSER_PROFILES.items():
        profiles = _chromium_profiles(root)
        if not profiles:
            continue
        info(f"{browser}:")
        any_found = True
        for profile in profiles:
            hist_db = os.path.join(profile, "History")
            if not os.path.exists(hist_db):
                continue
            try:
                tmp = _chromium_db_copy(hist_db)
                conn = sqlite3.connect(tmp)
                cur  = conn.cursor()
                cur.execute("""
                    SELECT target_path, tab_url, total_bytes, received_bytes,
                           datetime(start_time/1000000-11644473600, 'unixepoch', 'localtime'),
                           state, danger_type
                    FROM downloads
                    ORDER BY start_time DESC
                    LIMIT 100
                """)
                rows = cur.fetchall()
                conn.close()
                os.remove(tmp)
                print(f"    Profile: {os.path.basename(profile)}  ({len(rows)} downloads)")
                for target, tab_url, total, received, ts, state, danger in rows:
                    fname    = os.path.basename(target or "?")
                    size_kb  = (total or 0) // 1024
                    still_on = os.path.exists(target or "")
                    exists   = "\033[92m[ON DISK]\033[0m" if still_on else "\033[91m[DELETED]\033[0m"

                    ext = os.path.splitext(fname)[1].lower()
                    flagged = ext in [".jar", ".exe", ".dll", ".bat", ".ps1", ".vbs", ".zip"]
                    flag_str = " \033[93m<< SUSPICIOUS EXT\033[0m" if flagged else ""

                    print(f"      [{ts}] {exists} {fname} ({size_kb} KB){flag_str}")
                    print(f"               From: {(tab_url or '')[:100]}")
                    if not still_on:
                        print(f"               Path was: {target}")
                    # Offer path inspection for flagged files that still exist
                    if flagged and still_on and target:
                        show_path_options(fname, target)
            except Exception as e:
                warn(f"    Could not read {browser} downloads ({os.path.basename(profile)}): {e}")

    if not any_found:
        info("No browser profile folders found.")
    pause()


def check_browser_cache_cleared():
    clear()
    header("Browser Cache / History Wipe Detection")
    print()
    info("Checking for signs of deliberate browser data clearing...")
    print()

    suspicious_found = False

    for browser, root in BROWSER_PROFILES.items():
        profiles = _chromium_profiles(root)
        if not profiles:
            continue
        for profile in profiles:
            hist_db = os.path.join(profile, "History")
            if not os.path.exists(hist_db):
                warn(f"{browser} [{os.path.basename(profile)}]: History file MISSING — likely wiped!")
                suspicious_found = True
                continue

            size = os.path.getsize(hist_db)
            if size < 40960:
                warn(f"{browser} [{os.path.basename(profile)}]: History DB is very small ({size} bytes) — possibly cleared recently")
                suspicious_found = True

            try:
                tmp  = _chromium_db_copy(hist_db)
                conn = sqlite3.connect(tmp)
                cur  = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM urls")
                url_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM downloads")
                dl_count = cur.fetchone()[0]
                conn.close()
                os.remove(tmp)
                print(f"  {browser} [{os.path.basename(profile)}]:  {url_count} history entries,  {dl_count} download entries")
                if url_count == 0:
                    warn(f"  → Zero history entries — history was cleared!")
                    suspicious_found = True
                if dl_count == 0:
                    warn(f"  → Zero download entries — downloads were cleared!")
                    suspicious_found = True
            except Exception as e:
                warn(f"  Could not read {browser} DB: {e}")

    info("\nChecking for known wipe tools...")
    wipe_tools = ["CCleaner", "BleachBit", "Eraser", "PrivaZer", "Wise Disk Cleaner"]
    for tool in wipe_tools:
        for base in [APPDATA, LOCALAPPDATA,
                     os.environ.get("PROGRAMFILES","C:\\Program Files"),
                     os.environ.get("PROGRAMFILES(X86)","C:\\Program Files (x86)")]:
            path = os.path.join(base, tool)
            if os.path.exists(path):
                warn(f"Wipe tool found: {tool} in {base}")
                suspicious_found = True
                show_path_options(tool, path)

    pf_out = run("dir C:\\Windows\\Prefetch /b *.pf 2>nul").lower()
    for tool in ["ccleaner", "bleachbit", "privazer", "eraser"]:
        if tool in pf_out:
            warn(f"Prefetch entry for wipe tool: {tool} — was recently run!")
            suspicious_found = True

    info("\nChecking Windows Event Log for manual log clears (ID 1102)...")
    ev = run('wevtutil qe Security /q:"*[System[EventID=1102]]" /f:text /c:5')
    if ev.strip():
        warn("Security event log was manually CLEARED recently:")
        print(ev[:800])
        suspicious_found = True
    else:
        info("No event log clear events found.")

    print()
    if not suspicious_found:
        info("No obvious signs of browser data wiping detected.")
    pause()


def check_browser_cookies_search():
    clear()
    header("Browser Recently Visited Sites (Cookies)")
    info("Reading cookie domains as evidence of visited sites...")
    print()

    for browser, root in BROWSER_PROFILES.items():
        profiles = _chromium_profiles(root)
        if not profiles:
            continue
        info(f"{browser}:")
        for profile in profiles:
            cookie_db = os.path.join(profile, "Network", "Cookies")
            if not os.path.exists(cookie_db):
                cookie_db = os.path.join(profile, "Cookies")
            if not os.path.exists(cookie_db):
                continue
            try:
                tmp  = _chromium_db_copy(cookie_db)
                conn = sqlite3.connect(tmp)
                cur  = conn.cursor()
                cur.execute("""
                    SELECT host_key,
                           datetime(last_access_utc/1000000-11644473600, 'unixepoch', 'localtime')
                    FROM cookies
                    GROUP BY host_key
                    ORDER BY MAX(last_access_utc) DESC
                    LIMIT 60
                """)
                rows = cur.fetchall()
                conn.close()
                os.remove(tmp)
                print(f"    Profile: {os.path.basename(profile)}  ({len(rows)} unique domains)")
                for host, ts in rows:
                    flagged = any(k in host.lower() for k in [
                        "crack", "cheat", "hack", "warez", "nulled", "skid",
                        "vape", "sigma", "future", "meteor", "wurst", "ghost",
                        "leaked", "free", "bypass", "inject"
                    ])
                    flag_str = "  \033[91m<< SUSPICIOUS DOMAIN\033[0m" if flagged else ""
                    print(f"      [{ts}]  {host}{flag_str}")
            except Exception as e:
                warn(f"    Could not read {browser} cookies ({os.path.basename(profile)}): {e}")
    pause()


CHEAT_SITE_KEYWORDS = [
    "cheat", "hack", "inject", "ghost", "crack", "nulled", "warez",
    "leaked", "bypass", "skid", "payload", "exploit", "trainer","client", "prestige", "reflex", "exodus", "zenith", "ketamine", "http://prestigeclient.vip/", "cyemer", "velaris", "bleach", "vapor", "dusk", "azura", "vertex", "nexus", "rise", "lucid"
    "Wurst", "Impact", "Meteor", "Aristois", "Liquidbounce", "Sigma",
    "Ares", "Future", "Vape", "Astolfo", "Drip", "Salhack", "Entropy",
    "Inertia", "Raven", "Novoline", "Wolfram", "PyroHax", "Rekt",
    "Remix", "XRay", "Horion", "Phi", "Hybrid", "Rusher", "cyemer",
    "Prestige", "velaris", "bleach", "vapor", "dusk", "azura", "vertex",
    "nexus", "rise", "lucid", "ketamine", "reflex", "exodus", "zenith"
    "blackspigot", "spigotunlocked", "mcleaks", "tlauncher", "cracked",
    "freemc", "freeminecraft", "altening", "thealtening", "easymc",
    "minecraftalt", "skyclient",
    "free-download", "crack-download", "keygen",
]

SAFE_DOMAINS = [
    "google.com", "youtube.com", "discord.com", "reddit.com", "microsoft.com",
    "minecraft.net", "mojang.com", "curseforge.com", "modrinth.com",
    "fabricmc.net", "minecraftforge.net", "optifine.net", "github.com",
    "twitch.tv", "wikipedia.org", "cloudflare.com", "gstatic.com",
    "googleapis.com", "badlion.net", "lunarclient.com",
]


def check_website_cheat_scanner():
    clear()
    header("Website Cheat / Client Scanner")
    info("Scanning browser history and downloads for cheat-related websites...")
    print()

    results = []

    def is_safe(url):
        for safe in SAFE_DOMAINS:
            if safe in url.lower():
                return True
        return False

    def is_suspicious(text):
        t = text.lower()
        return any(k in t for k in CHEAT_SITE_KEYWORDS)

    for browser, root in BROWSER_PROFILES.items():
        profiles = _chromium_profiles(root)
        for profile in profiles:
            pname = os.path.basename(profile)
            hist_db = os.path.join(profile, "History")
            if not os.path.exists(hist_db):
                continue

            try:
                tmp = _chromium_db_copy(hist_db)
                conn = sqlite3.connect(tmp)
                cur = conn.cursor()
                cur.execute("""
                    SELECT url, title,
                           datetime(last_visit_time/1000000-11644473600,'unixepoch','localtime')
                    FROM urls ORDER BY last_visit_time DESC
                """)
                for url, title, ts in cur.fetchall():
                    if not is_safe(url) and (is_suspicious(url) or is_suspicious(title or "")):
                        results.append((browser, pname, "HISTORY", url, title or "", ts))
                conn.close()
                os.remove(tmp)
            except Exception as e:
                warn(f"Could not read {browser} history ({pname}): {e}")

            try:
                tmp = _chromium_db_copy(hist_db)
                conn = sqlite3.connect(tmp)
                cur = conn.cursor()
                cur.execute("""
                    SELECT target_path, tab_url,
                           datetime(start_time/1000000-11644473600,'unixepoch','localtime')
                    FROM downloads ORDER BY start_time DESC
                """)
                for target, tab_url, ts in cur.fetchall():
                    check_str = (target or "") + (tab_url or "")
                    if not is_safe(check_str) and is_suspicious(check_str):
                        fname = os.path.basename(target or "?")
                        still_on = os.path.exists(target or "")
                        label = "DOWNLOAD" + ("" if still_on else " [DELETED]")
                        results.append((browser, pname, label, tab_url or target, fname, ts))
                conn.close()
                os.remove(tmp)
            except Exception:
                pass

    if os.path.isdir(FIREFOX_ROOT):
        for profile in os.listdir(FIREFOX_ROOT):
            places = os.path.join(FIREFOX_ROOT, profile, "places.sqlite")
            if not os.path.exists(places):
                continue
            try:
                tmp = _chromium_db_copy(places)
                conn = sqlite3.connect(tmp)
                cur = conn.cursor()
                cur.execute("""
                    SELECT p.url, p.title,
                           datetime(h.visit_date/1000000,'unixepoch','localtime')
                    FROM moz_places p
                    JOIN moz_historyvisits h ON h.place_id = p.id
                    ORDER BY h.visit_date DESC
                """)
                for url, title, ts in cur.fetchall():
                    if not is_safe(url) and (is_suspicious(url) or is_suspicious(title or "")):
                        results.append(("Firefox", profile, "HISTORY", url, title or "", ts))
                conn.close()
                os.remove(tmp)
            except Exception as e:
                warn(f"Could not read Firefox history ({profile}): {e}")

    if not results:
        info("No cheat-related websites or downloads found in browser history.")
        pause()
        return

    history_hits  = [r for r in results if "HISTORY"  in r[2]]
    download_hits = [r for r in results if "DOWNLOAD" in r[2]]

    if history_hits:
        print(f"  \033[91m[!!] SUSPICIOUS VISITED SITES ({len(history_hits)} found)\033[0m")
        print("  " + "─" * 90)
        for browser, pname, rtype, url, title, ts in history_hits:
            print(f"  \033[93m[{ts}]\033[0m  {browser} / {pname}")
            if title:
                print(f"    Title : {title[:80]}")
            print(f"    URL   : {url[:100]}")
            print()

    if download_hits:
        print(f"  \033[91m[!!] SUSPICIOUS DOWNLOADS ({len(download_hits)} found)\033[0m")
        print("  " + "─" * 90)
        for browser, pname, rtype, url, fname, ts in download_hits:
            deleted = " \033[91m[FILE DELETED]\033[0m" if "DELETED" in rtype else ""
            print(f"  \033[93m[{ts}]\033[0m  {browser} / {pname}{deleted}")
            print(f"    File  : {fname[:80]}")
            print(f"    From  : {url[:100]}")
            print()

    info(f"Total flagged: {len(results)}  ({len(history_hits)} visited, {len(download_hits)} downloaded)")
    pause()


def menu_browser_forensics():
    while True:
        clear()
        header("Browser Forensics")
        print("  [1]  History Viewer            — last 50 visited URLs per browser")
        print("  [2]  Downloads Viewer          — all downloads, flags deleted files")
        print("  [3]  Cache / History Wipe Check — detect if they cleared their browser")
        print("  [4]  Cookie Domain Viewer      — sites visited (even if history cleared)")
        print("  [5]  Browser history paths     — open raw folder locations")
        print("  [6]  Cheat Site Scanner        — flag cheat/client sites in history & downloads")
        print("  [0]  Back to main menu")
        print()
        choice = input("  Choice: ").strip()
        if choice == "0":
            break
        elif choice == "1":
            check_browser_history()
        elif choice == "2":
            check_browser_downloads()
        elif choice == "3":
            check_browser_cache_cleared()
        elif choice == "4":
            check_browser_cookies_search()
        elif choice == "5":
            check_browser()
        elif choice == "6":
            check_website_cheat_scanner()
        else:
            warn("Invalid choice.")
            input("  Press Enter to continue...")


# ── Standard checks ───────────────────────────────────────────────────────────

def check_startup():
    clear()
    header("Startup Programs")
    info("Registry - Current User:")
    print(run("reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"))
    info("Registry - Local Machine:")
    print(run("reg query HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"))
    info("Startup folder:")
    path = os.path.join(APPDATA, r"Microsoft\Windows\Start Menu\Programs\Startup")
    if os.path.exists(path):
        files = os.listdir(path)
        print("    " + "\n    ".join(files) if files else "    Empty.")
    pause()

def check_recent():
    clear()
    header("Recently Opened Files")
    path = os.path.join(APPDATA, r"Microsoft\Windows\Recent")
    if os.path.exists(path):
        files = sorted(
            [f for f in os.listdir(path)],
            key=lambda f: os.path.getmtime(os.path.join(path, f)),
            reverse=True
        )
        for f in files[:40]:
            print(f"  {f}")
    pause()

def check_temp():
    clear()
    header("Temp Folder Check")
    for ext in ["*.exe", "*.jar", "*.dll", "*.bat", "*.ps1"]:
        out = run(f'dir "{TEMP}" /b {ext} 2>nul')
        if out:
            warn(f"{ext} files in Temp:")
            for line in out.splitlines():
                full_path = os.path.join(TEMP, line.strip())
                print(f"  {line.strip()}")
                if os.path.exists(full_path):
                    show_path_options(line.strip(), full_path)
    info("Full temp listing:")
    print(run(f'dir "{TEMP}" /b'))
    pause()

def check_hosts():
    clear()
    header("Hosts File")
    hosts = r"C:\Windows\System32\drivers\etc\hosts"
    if os.path.exists(hosts):
        with open(hosts, "r") as f:
            print(f.read())
    pause()

def check_programs():
    clear()
    header("Installed Programs")
    out = run('reg query HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall /s /v DisplayName')
    for line in out.splitlines():
        if "DisplayName" in line:
            print(" ", line.split("DisplayName")[-1].strip().lstrip("REG_SZ").strip())
    pause()

def check_browser():
    clear()
    header("Browser History Paths")
    paths = {
        "Chrome":  os.path.join(LOCALAPPDATA, r"Google\Chrome\User Data\Default\History"),
        "Edge":    os.path.join(LOCALAPPDATA, r"Microsoft\Edge\User Data\Default\History"),
        "Firefox": os.path.join(APPDATA, r"Mozilla\Firefox\Profiles"),
        "Opera":   os.path.join(APPDATA, r"Opera Software\Opera Stable\History"),
        "Brave":   os.path.join(LOCALAPPDATA, r"BraveSoftware\Brave-Browser\User Data\Default\History"),
    }
    for browser, path in paths.items():
        if os.path.exists(path):
            found(f"{browser}: {path}")
        else:
            info(f"{browser}: not found")
    pause()

def check_prefetch():
    clear()
    header("Windows Prefetch (Recently Run Programs)")
    out = run("dir C:\\Windows\\Prefetch /od /b *.pf")
    keywords = ["java","cheat","inject","hack","wurst","sigma","vape","rat",
                "bleach","vapor","dusk","ccleaner","bleachbit","prestige","rat"]
    info("Flagged prefetch entries:")
    flagged = False
    for line in out.splitlines():
        if any(k in line.lower() for k in keywords):
            found(line)
            flagged = True
    if not flagged:
        info("Nothing suspicious flagged.")
    info("All prefetch entries:")
    print(out)
    pause()

def check_tasks():
    clear()
    header("Scheduled Tasks")
    print(run("schtasks /query /fo LIST"))
    pause()

def check_envvars():
    clear()
    header("Environment Variables")
    for k, v in os.environ.items():
        print(f"  {k} = {v}")
    pause()

def check_vpn():
    clear()
    header("Network Adapters / VPN Detection")
    out = run("ipconfig /all")
    info("All adapter descriptions:")
    for line in out.splitlines():
        if "description" in line.lower():
            print(f"  {line.strip()}")
    info("Flagged (virtual/vpn/tap):")
    flagged = False
    for line in out.splitlines():
        if "description" in line.lower():
            if any(k in line.lower() for k in ["virtual","vpn","tap","tunnel","hyper-v","hamachi"]):
                found(line.strip())
                flagged = True
    if not flagged:
        info("No VPN/virtual adapters detected.")
    pause()

def check_shadow():
    clear()
    header("Shadow Copies / Restore Points")
    print(run("vssadmin list shadows"))
    print(run("wmic shadowcopy list brief"))
    pause()

def check_modified():
    clear()
    header("Files Modified in Last 24h")
    info("Desktop:")
    print(run(f'forfiles /p "{USERPROFILE}\\Desktop" /s /d 0 /c "cmd /c echo @path" 2>nul'))
    info("AppData:")
    print(run(f'forfiles /p "{APPDATA}" /s /d 0 /c "cmd /c echo @path" 2>nul'))
    pause()

def check_netstat():
    clear()
    header("Active Network Connections")
    print(run("netstat -ano"))
    pause()

def check_drivers():
    clear()
    header("Installed Drivers")
    print(run("driverquery"))
    pause()

def full_scan():
    clear()
    header("Full Auto Scan")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info(f"Scan started at {now}")
    print()
    info("[1/11] AppData cheat folders...")
    for client in CHEAT_CLIENTS:
        for base in [APPDATA, LOCALAPPDATA]:
            path = os.path.join(base, client)
            if os.path.exists(path):
                found(f"{client} in {base}")
                show_path_options(client, path)
                send_to_webhook("N/A (Full Auto Scan)", {
                    "result": f"Cheat Folder Found: {client}",
                    "game": "Full Auto Scan",
                    "detects": [path],
                    "country": "N/A",
                    "scantime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
    info("[2/11] Java processes...")
    print(run("tasklist /fi \"imagename eq javaw.exe\""))
    info("[2a/11] Java injection module scan...")
    scan_java_injection()
    info("[3/11] Suspicious processes...")
    all_procs = run("tasklist").lower()
    for s in SUSPICIOUS_PROCS:
        if s in all_procs:
            found(f"Process: {s}")
            send_to_webhook("N/A (Full Auto Scan)", {
                "result": "Suspicious Process Detected",
                "game": "Full Auto Scan",
                "detects": [s],
                "country": "N/A",
                "scantime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
    info("[3a] Scanning for cheat executables...")
    for line in run("tasklist /fo csv /nh").splitlines():
        exe = line.split(",")[0].strip('"').lower()
        for client in CHEAT_CLIENTS:
            if client.lower() in exe:
                found(f"Cheat process running: {exe}")
                send_to_webhook("N/A (Full Auto Scan)", {
                    "result": f"Cheat EXE Detected: {exe}",
                    "game": "Full Auto Scan",
                    "detects": [exe],
                    "country": "N/A",
                    "scantime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
    info("[4/11] .minecraft mods...")
    mods = os.path.join(MINECRAFT, "mods")
    if os.path.exists(mods):
        files = os.listdir(mods)
        print("  " + "\n  ".join(files) if files else "  Empty.")
    else:
        info("No mods folder.")
    info("[5/11] Startup entries...")
    print(run("reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"))
    info("[6/11] Temp executables...")
    for ext in ["*.exe", "*.jar"]:
        out = run(f'dir "{TEMP}" /b {ext} 2>nul')
        if out:
            warn(f"{ext} in temp: {out}")
            for line in out.splitlines():
                full_path = os.path.join(TEMP, line.strip())
                if os.path.exists(full_path):
                    show_path_options(line.strip(), full_path)
            send_to_webhook("N/A (Full Auto Scan)", {
                "result": f"Suspicious File in Temp: {ext}",
                "game": "Full Auto Scan",
                "detects": out.splitlines(),
                "country": "N/A",
                "scantime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
    info("[7/11] Hosts file...")
    hosts = r"C:\Windows\System32\drivers\etc\hosts"
    if os.path.exists(hosts):
        with open(hosts) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    print(f"  {line.strip()}")
    info("[8/11] Prefetch suspicious names...")
    out = run("dir C:\\Windows\\Prefetch /od /b *.pf")
    for line in out.splitlines():
        if any(k in line.lower() for k in ["cheat","inject","wurst","sigma","vape","ccleaner","bleachbit","prestige","rat"]):
            found(f"Prefetch: {line}")
            send_to_webhook("N/A (Full Auto Scan)", {
                "result": f"Suspicious Prefetch Entry: {line}",
                "game": "Full Auto Scan",
                "detects": [line],
                "country": "N/A",
                "scantime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
    info("[9/11] Scheduled tasks...")
    out = run("schtasks /query /fo LIST")
    for line in out.splitlines():
        if "Task Name:" in line:
            print(f"  {line.strip()}")
    info("[10/11] VPN/virtual adapters...")
    out = run("ipconfig /all")
    for line in out.splitlines():
        if "description" in line.lower():
            if any(k in line.lower() for k in ["virtual","vpn","tap","tunnel","hamachi"]):
                found(line.strip())
    info("[11/11] Browser wipe check...")
    for browser, root in BROWSER_PROFILES.items():
        profiles = _chromium_profiles(root)
        for profile in profiles:
            hist_db = os.path.join(profile, "History")
            if not os.path.exists(hist_db):
                warn(f"{browser} history file MISSING — possibly wiped!")
                send_to_webhook("N/A (Full Auto Scan)", {
                    "result": f"{browser} History Wiped",
                    "game": "Full Auto Scan",
                    "detects": [f"{browser} history file missing: {profile}"],
                    "country": "N/A",
                    "scantime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
            elif os.path.getsize(hist_db) < 40960:
                warn(f"{browser} history DB suspiciously small — possibly cleared!")
                send_to_webhook("N/A (Full Auto Scan)", {
                    "result": f"{browser} History Suspiciously Small",
                    "game": "Full Auto Scan",
                    "detects": [f"{browser} history DB under 40KB: {profile}"],
                    "country": "N/A",
                    "scantime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
    print()
    info(f"Scan complete — {datetime.now().strftime('%H:%M:%S')}")
    pause()

def save_full_scan_report():
    clear()
    header("Save Full Scan Report")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "SS HELPER REPORT",
        f"Scan started at {now}",
        "",
        "[1] AppData cheat folders",
    ]

    for client in CHEAT_CLIENTS:
        for base in [APPDATA, LOCALAPPDATA]:
            path = os.path.join(base, client)
            if os.path.exists(path):
                lines.append(f"FOUND: {client} in {path}")

    lines.extend([
        "",
        "[2] Java processes",
        run("tasklist /fi \"imagename eq javaw.exe\""),
        run("tasklist /fi \"imagename eq java.exe\""),
        "",
        "[2a] Java injection modules",
        run("tasklist /m /fi \"imagename eq javaw.exe\""),
        run("tasklist /m /fi \"imagename eq java.exe\""),
        "",
        "[3] Suspicious processes",
    ])
    all_procs = run("tasklist").lower()
    for s in SUSPICIOUS_PROCS:
        if s in all_procs:
            lines.append(f"FOUND: {s}")

    lines.extend(["", "[4] .minecraft mods"])
    mods = os.path.join(MINECRAFT, "mods")
    if os.path.exists(mods):
        files = os.listdir(mods)
        lines.extend(files if files else ["Empty"])
    else:
        lines.append("No mods folder.")

    lines.extend([
        "",
        "[5] Startup entries",
        run("reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
        run("reg query HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
        "",
        "[6] Temp executables",
    ])
    for ext in ["*.exe", "*.jar"]:
        out = run(f'dir "{TEMP}" /b {ext} 2>nul')
        if out:
            lines.append(f"{ext}: {out.replace(chr(10), chr(10) + '    ')}")

    lines.extend(["", "[7] Hosts file (non-comment lines)"])
    hosts = r"C:\Windows\System32\drivers\etc\hosts"
    if os.path.exists(hosts):
        with open(hosts, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    lines.append(line)
    else:
        lines.append("Hosts file not found.")

    lines.extend(["", "[8] Prefetch suspicious names"])
    out = run("dir C:\\Windows\\Prefetch /od /b *.pf")
    for line in out.splitlines():
        if any(k in line.lower() for k in ["cheat","inject","wurst","sigma","vape","prestige","rat"]):
            lines.append(line)

    lines.extend([
        "",
        "[9] Scheduled tasks",
        run("schtasks /query /fo LIST"),
        "",
        "[10] VPN/virtual adapters",
        run("ipconfig /all"),
    ])

    filename = f"OceanSS_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    dump_to_desktop(filename, "\n".join(lines))
    pause()

# ── Manual openers ────────────────────────────────────────────────────────────

def open_path(path):
    if os.path.exists(path):
        os.startfile(path)
    else:
        warn(f"Path not found: {path}")

def dump_to_desktop(filename, content):
    path = os.path.join(USERPROFILE, "Desktop", filename)
    with open(path, "w") as f:
        f.write(content)
    info(f"Saved to Desktop: {filename}")
    pause()

def dump_to_downloads(filename, content):
    os.makedirs(DOWNLOADS, exist_ok=True)
    path = os.path.join(DOWNLOADS, filename)
    with open(path, "w") as f:
        f.write(content)
    info(f"Saved to: {path}")
    pause()

def file_search():
    clear()
    header("File Search")
    term = input("  Enter filename to search for: ").strip()
    info(f"Searching C:\\ for {term}...")
    print(run(f'dir C:\\ /s /b 2>nul | findstr /i "{term}"'))
    pause()

def reg_search():
    clear()
    header("Registry Search")
    term = input("  Enter registry key/value to search for: ").strip()
    info(f"Searching registry for {term}...")
    print(run(f'reg query HKCU /f "{term}" /s'))
    print(run(f'reg query HKLM /f "{term}" /s'))
    pause()

# ── HWID Extractor ────────────────────────────────────────────────────────────

def hwid_extractor():
    clear()
    header("HWID Extractor")
    os.makedirs(DOWNLOADS, exist_ok=True)
    out_file = os.path.join(DOWNLOADS, "HWID.txt")
    lines = []
    lines.append(f"User Name      : {os.environ.get('USERNAME','')}")
    lines.append(f"Computer Name  : {os.environ.get('COMPUTERNAME','')}")
    lines.append(f"User Domain    : {os.environ.get('USERDOMAIN','')}")
    for label, cmd in [
        ("UUID",           "wmic path win32_computersystemproduct get uuid"),
        ("MAC Address",    "getmac"),
        ("CPU ID",         "wmic cpu get ProcessorId"),
        ("Disk Serial",    "wmic diskdrive get serialnumber"),
        ("RAM Serial",     "wmic memorychip get serialnumber"),
        ("Baseboard S/N",  "wmic baseboard get serialnumber"),
        ("CPU Name",       "wmic cpu get name"),
    ]:
        lines.append(f"\n--- {label} ---")
        lines.append(run(cmd))
    content = "\n".join(lines)
    with open(out_file, "w") as f:
        f.write(content)
    print(content)
    info(f"Saved to: {out_file}")
    os.startfile(out_file)
    pause()

# ── Manual Tools ──────────────────────────────────────────────────────────────

def menu_manual_tools():
    while True:
        clear()
        header("Manual Tools  (download & open forensic utilities)")
        items = [
            ("PH2",   "Process Hacker 2"),
            ("LAV",   "LastActivityView"),
            ("WPV",   "WinPrefetchView"),
            ("LYT",   "Luyten (JAR decompiler)"),
            ("ERT",   "Everything (file search)"),
            ("ASV",   "AlternateStreamView"),
            ("RGS",   "RegScanner"),
            ("EPF",   "ExecutedProgramsList"),
            ("MCV",   "MUICacheView"),
            ("SBV",   "ShellBagsView"),
            ("BDV",   "Browser Downloads View"),
            ("BHV",   "BrowsingHistoryView"),
            ("OFV",   "OpenSaveFilesView"),
            ("RFV",   "RecentFilesView"),
            ("LDV",   "LoadedDLLsView"),
            ("HV",    "HistoryViewer"),
            ("CPL",   "CachedProgramsList"),
            ("WF",    "WizFile"),
            ("PSFE",  "PcaSvc FileExplorer"),
            ("NUV",   "NetworkUsageView"),
            ("MLS",   "MyLastSearch"),
            ("UDL",   "USBDriveLog"),
            ("WDTV",  "WinDefender ThreatsView"),
            ("KBSV",  "KeyboardStateView"),
            ("JLV",   "JumpListsView"),
            ("ADS",   "AlternateDataStream viewer"),
            ("FELV",  "FullEventLogView"),
            ("AMP",   "Amcache Parser (EZ Tools)"),
            ("TLE",   "Timeline Explorer (EZ Tools)"),
            ("RYE",   "Registry Explorer (EZ Tools)"),
            ("PEC",   "PECmd (EZ Tools)"),
            ("EEC",   "EvtxECmd (EZ Tools)"),
            ("WTC",   "WxTCmd (EZ Tools)"),
            ("MFTE",  "MFTECmd (EZ Tools)"),
            ("USBDV", "USBDeview"),
            ("PFR",   "Previous Files Recovery"),
        ]
        for code, name in items:
            print(f"  [{code}]  {name}")
        print("\n  [0]  Back to main menu")
        choice = input("\n  Choice: ").strip().upper()

        urls = {
            "PH2":   ("https://github.com/processhacker/processhacker/releases/download/v2.39/processhacker-2.39-setup.exe", "ProcessHacker2-Setup.exe"),
            "LAV":   ("https://www.nirsoft.net/utils/lastactivityview.zip",            "LastActivityView.zip"),
            "WPV":   ("https://www.nirsoft.net/utils/winprefetchview-x64.zip",         "WinPrefetchView.zip"),
            "LYT":   ("https://github.com/deathmarine/Luyten/releases/download/v0.5.4_Rebuilt_with_Latest_depenencies/luyten-0.5.4.exe", "Luyten.exe"),
            "ERT":   ("https://www.voidtools.com/Everything-1.4.1.1005.x64.zip",       "Everything.zip"),
            "ASV":   ("https://www.nirsoft.net/utils/alternatestreamview-x64.zip",     "AlternateStreamView.zip"),
            "RGS":   ("https://www.nirsoft.net/utils/regscanner-x64.zip",              "RegScanner.zip"),
            "EPF":   ("https://www.nirsoft.net/utils/executedprogramslist.zip",        "ExecutedProgramsList.zip"),
            "MCV":   ("http://www.nirsoft.net/utils/muicacheview.zip",                 "MUICacheView.zip"),
            "SBV":   ("https://www.nirsoft.net/utils/shellbagsview.zip",               "ShellBagsView.zip"),
            "BDV":   ("https://www.nirsoft.net/utils/browserdownloadsview-x64.zip",   "BrowserDownloadsView.zip"),
            "BHV":   ("https://www.nirsoft.net/utils/browsinghistoryview-x64.zip",    "BrowsingHistoryView.zip"),
            "OFV":   ("https://www.nirsoft.net/utils/opensavefilesview-x64.zip",      "OpenSaveFilesView.zip"),
            "RFV":   ("https://www.nirsoft.net/utils/recentfilesview.zip",             "RecentFilesView.zip"),
            "LDV":   ("https://www.nirsoft.net/utils/loadeddllsview-x64.zip",         "LoadedDLLsView.zip"),
            "HV":    ("https://chicho.lol/downloads/hvsetup.exe",                     "HistoryViewer-Setup.exe"),
            "CPL":   ("https://github.com/ponei/CachedProgramsList/releases/download/1.1/CachedProgramsList.exe", "CachedProgramsList.exe"),
            "WF":    ("https://antibody-software.com/files/wizfile_3_07_setup.exe",   "WizFile-Setup.exe"),
            "PSFE":  ("https://github.com/Zack-src/Service-Execution/releases/download/1.0/PcaSvc.FileExplorer.exe", "PcaSvc.FileExplorer.exe"),
            "NUV":   ("https://www.nirsoft.net/utils/networkusageview-x64.zip",       "NetworkUsageView.zip"),
            "MLS":   ("https://www.nirsoft.net/utils/mylastsearch.zip",               "MyLastSearch.zip"),
            "UDL":   ("https://www.nirsoft.net/utils/usbdrivelog.zip",                "USBDriveLog.zip"),
            "WDTV":  ("https://www.nirsoft.net/utils/wdthreatsview.zip",              "WinDefThreatsView.zip"),
            "KBSV":  ("https://www.nirsoft.net/utils/keyboardstatesview.zip",         "KeyboardStateView.zip"),
            "JLV":   ("https://www.nirsoft.net/utils/jumplistsview.zip",              "JumpListsView.zip"),
            "ADS":   ("https://www.nirsoft.net/utils/alternatestreamview-x64.zip",    "ADS-View.zip"),
            "FELV":  ("https://www.nirsoft.net/utils/fulleventlogview-x64.zip",       "FullEventLogView.zip"),
            "AMP":   ("https://github.com/EricZimmerman/AmcacheParser/releases/latest/download/AmcacheParser.zip", "AmcacheParser.zip"),
            "TLE":   ("https://github.com/EricZimmerman/Timeline-Explorer/releases/latest/download/TimelineExplorer.zip", "TimelineExplorer.zip"),
            "RYE":   ("https://github.com/EricZimmerman/RegistryExplorer/releases/latest/download/RegistryExplorer.zip", "RegistryExplorer.zip"),
            "PEC":   ("https://github.com/EricZimmerman/PECmd/releases/latest/download/PECmd.zip",   "PECmd.zip"),
            "EEC":   ("https://github.com/EricZimmerman/evtx/releases/latest/download/EvtxECmd.zip", "EvtxECmd.zip"),
            "WTC":   ("https://github.com/EricZimmerman/WxTCmd/releases/latest/download/WxTCmd.zip", "WxTCmd.zip"),
            "MFTE":  ("https://github.com/EricZimmerman/MFTECmd/releases/latest/download/MFTECmd.zip","MFTECmd.zip"),
            "USBDV": ("https://www.nirsoft.net/utils/usbdeview-x64.zip",              "USBDeview.zip"),
            "PFR":   ("https://www.nirsoft.net/utils/previousfilesrecovery-x64.zip",  "PreviousFilesRecovery.zip"),
        }

        if choice == "0":
            break
        elif choice in urls:
            url, fname = urls[choice]
            download_and_open(url, fname)
        else:
            warn("Invalid choice.")
            input("  Press Enter to continue...")

# ── Recovery Tools ────────────────────────────────────────────────────────────

def menu_recovery_tools():
    while True:
        clear()
        header("Recovery File Tools")
        items = [
            ("Recuva",    "Recuva",               "https://www.ccleaner.com/recuva/download/standard",        "RecuvaSetup.exe"),
            ("EaseUS",    "EaseUS Data Recovery",  "https://down.easeus.com/product/drw_trial",               "EaseUS-DR-Setup.exe"),
            ("Glarysoft", "Glarysoft File Recovery","https://www.glarysoft.com/file-recovery/download/",      "GlarysoftFileRecovery.exe"),
            ("KickAss",   "KickAssUndelete",       "https://www.kickassundelete.com/download/KickAssUndelete.exe","KickAssUndelete.exe"),
        ]
        for code, name, _, _ in items:
            print(f"  [{code}]  {name}")
        print("\n  [0]  Back to main menu")
        choice = input("\n  Choice: ").strip()
        if choice == "0":
            break
        match = next((i for i in items if i[0].lower() == choice.lower()), None)
        if match:
            download_and_open(match[2], match[3])
        else:
            warn("Invalid choice.")
            input("  Press Enter to continue...")

# ── Explorer Paths ────────────────────────────────────────────────────────────

def menu_explorer():
    while True:
        clear()
        header("Explorer Paths")
        paths = {
            "PRE":  ("Prefetch",            r"C:\Windows\Prefetch"),
            "TEMP": ("Temp",                TEMP),
            "MC":   (".minecraft",          MINECRAFT),
            "RB":   ("Recycle Bin",         r"shell:RecycleBinFolder"),
            "RN":   ("Recent",              os.path.join(APPDATA, r"Microsoft\Windows\Recent")),
            "HIS":  ("History",             os.path.join(LOCALAPPDATA, r"Microsoft\Windows\History")),
            "UL":   ("Usage Logs",          os.path.join(LOCALAPPDATA, r"Microsoft\Windows\UsageLogs")),
            "CD":   ("Crash Dumps",         os.path.join(LOCALAPPDATA, r"CrashDumps")),
            "RA":   ("Report Archive",      os.path.join(PROGRAMDATA, r"Microsoft\Windows\WER\ReportArchive")),
            "CF":   ("Control Panel",       "control"),
            "FW":   ("Firewall",            "wf.msc"),
            "NP":   ("Netplwiz",            "netplwiz"),
            "SRV":  ("Services",            "services.msc"),
            "DM":   ("Disk Management",     "diskmgmt.msc"),
            "GPE":  ("Group Policy Editor", "gpedit.msc"),
            "DRS":  ("Nvidia DRS folder",   os.path.join(PROGRAMDATA, r"NVIDIA Corporation\Drs")),
            "CHR":  ("Chrome User Data",    os.path.join(LOCALAPPDATA, r"Google\Chrome\User Data")),
            "EDG":  ("Edge User Data",      os.path.join(LOCALAPPDATA, r"Microsoft\Edge\User Data")),
            "BRV":  ("Brave User Data",     os.path.join(LOCALAPPDATA, r"BraveSoftware\Brave-Browser\User Data")),
            "FFX":  ("Firefox Profiles",    FIREFOX_ROOT),
        }
        for code, (name, _) in paths.items():
            print(f"  [{code}]  {name}")
        print("\n  [0]  Back to main menu")
        choice = input("\n  Choice: ").strip().upper()
        if choice == "0":
            break
        elif choice in paths:
            name, target = paths[choice]
            info(f"Opening {name}...")
            if target.endswith(".msc") or target in ("control", "netplwiz", "gpedit.msc"):
                subprocess.Popen(target, shell=True)
            elif target.startswith("shell:"):
                subprocess.Popen(f"explorer {target}", shell=True)
            else:
                open_path(target)
        else:
            warn("Invalid choice.")
        input("  Press Enter to continue...")

# ── USN Journal ───────────────────────────────────────────────────────────────

def menu_usn_journal():
    while True:
        clear()
        header("USN Journal Queries  (requires fsutil / admin)")
        options = {
            "JDF":  ("Deleted files",        'fsutil usn readjournal C: csv | findstr /i "0x80000200"'),
            "JRF":  ("Renamed files",        'fsutil usn readjournal C: csv | findstr /i "0x00001000\\|0x00002000"'),
            "JFT":  ("By file type (.jar)",  'fsutil usn readjournal C: csv | findstr /i ".jar"'),
            "JFS":  ("File streams",         'fsutil usn readjournal C: csv | findstr /i ":$DATA"'),
            "JRP":  ("Process restarts",     'fsutil usn readjournal C: csv | findstr /i "javaw"'),
            "JJC":  ("Jarcache entries",     'fsutil usn readjournal C: csv | findstr /i "jarcache"'),
            "JSC":  ("Security changes",     'fsutil usn readjournal C: csv | findstr /i "0x00000800"'),
            "JEC":  ("Empty/hidden chars",   'fsutil usn readjournal C: csv | findstr /i "  "'),
            "HL":   ("Hard links",           'fsutil hardlink list C:\\Windows\\System32\\ntdll.dll'),
        }
        for code, (desc, _) in options.items():
            print(f"  [{code}]  {desc}")
        print("\n  [0]  Back to main menu")
        choice = input("\n  Choice: ").strip().upper()
        if choice == "0":
            break
        elif choice in options:
            desc, cmd = options[choice]
            clear()
            header(f"USN: {desc}")
            info(f"Running: {cmd}")
            print(run(cmd) or "  (no output or fsutil not available)")
            pause()
        else:
            warn("Invalid choice.")
            input("  Press Enter to continue...")

# ── Commands ──────────────────────────────────────────────────────────────────

def menu_commands():
    while True:
        clear()
        header("CMD / PowerShell Commands")
        options = {
            "TL":   ("TaskList (verbose)",         "tasklist /v"),
            "CH":   ("Console Host history",       f'type "{APPDATA}\\Microsoft\\Windows\\PowerShell\\PSReadLine\\ConsoleHost_history.txt"'),
            "IC":   ("IPConfig /all",              "ipconfig /all"),
            "TRE":  ("Tree C:\\Users (2 levels)",  f'tree "{USERPROFILE}" /f 2>nul'),
            "SC":   ("Shadow copies list",         "vssadmin list shadows"),
            "NS":   ("NTFS USN journal state",     "fsutil usn queryjournal C:"),
            "MMA":  ("MMAgent settings",           "powershell Get-MMAgent"),
            "TNC":  ("Test network (8.8.8.8)",     "powershell Test-NetConnection 8.8.8.8"),
            "SCM":  ("Service control manager",    'sc query type= all state= all'),
            "DPS":  ("Query DPS service",          "sc queryex dps"),
            "PCA":  ("Query PcaSvc service",       "sc queryex PcaSvc"),
            "EVL":  ("Query Eventlog service",     "sc queryex eventlog"),
            "SYS":  ("Query SysMain service",      "sc queryex SysMain"),
            "DIA":  ("Query DiagTrack service",    "sc queryex DiagTrack"),
            "APPI": ("Query AppInfo service",      "sc queryex Appinfo"),
            "DIRA": ("Folder modification dates",  f'dir "{USERPROFILE}" /ad /tc'),
            "GETP": ("Get-Process (PowerShell)",   "powershell Get-Process | Sort-Object CPU -Descending | Select-Object -First 30"),
        }
        for code, (desc, _) in options.items():
            print(f"  [{code}]  {desc}")
        print("\n  [0]  Back to main menu")
        choice = input("\n  Choice: ").strip().upper()
        if choice == "0":
            break
        elif choice in options:
            desc, cmd = options[choice]
            clear()
            header(desc)
            print(run(cmd) or "  (no output)")
            pause()
        else:
            warn("Invalid choice.")
            input("  Press Enter to continue...")

# ── Registry ──────────────────────────────────────────────────────────────────

def menu_regedit():
    while True:
        clear()
        header("Registry Paths  (query / view reg keys)")
        paths = {
            "EF":   ("Executable files ran",          r"HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Compatibility Assistant\Store"),
            "DR":   ("Disallow Run",                  r"HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\DisallowRun"),
            "MCC":  ("MUICache",                      r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"),
            "AH":   ("Arc History",                   r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"),
            "APPS": ("AppSwitched",                   r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FeatureUsage\AppSwitched"),
            "UA":   ("UserAssist",                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"),
            "EP":   ("Executed programs (BAM)",       r"SYSTEM\CurrentControlSet\Services\bam\State\UserSettings"),
            "FA":   ("File type associations",        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts"),
            "OS":   ("Open/Save dialog files",        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU"),
            "MV":   ("Mounted volumes",               r"HKLM\SYSTEM\MountedDevices"),
            "PF":   ("Prefetch parameters",           r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"),
            "OP":   ("OpenWithList",                  r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts"),
            "RD":   ("RecentDocs",                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs"),
            "SJV":  ("ShowJumpView",                  r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"),
            "LVP":  ("LastVisitedPidlMRU",            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU"),
            "EN":   ("Environment variables",         r"HKCU\Environment"),
            "FR":   ("Firewall rules",                r"HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\FirewallRules"),
            "UN":   ("Uninstall list",                r"HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            "DI":   ("DirectInput devices",           r"HKCU\System\CurrentControlSet\Control\MediaProperties\PrivateProperties\DirectInput"),
            "CSM":  ("CIDsizeMRU",                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\CIDSizeMRU"),
            "TPS":  ("TypedPaths",                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths"),
            "SMI":  ("StartMenuInternet",             r"HKLM\Software\Clients\StartMenuInternet"),
            "CP":   ("Command Processor",             r"HKCU\Software\Microsoft\Command Processor"),
            "VIC":  ("VolumeInfoCache",               r"HKLM\Software\Microsoft\Windows Search\VolumeInfoCache"),
            "USBS": ("USB Storage devices",           r"HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR"),
            "RMRU": ("Run MRU",                       r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"),
            "TRA":  ("Tracing",                       r"HKLM\Software\Microsoft\Tracing"),
        }
        for code, (desc, _) in paths.items():
            print(f"  [{code}]  {desc}")
        print("\n  [0]  Back to main menu")
        choice = input("\n  Choice: ").strip().upper()
        if choice == "0":
            break
        elif choice in paths:
            desc, reg_path = paths[choice]
            info(f"Querying: {reg_path}")
            print(run(f'reg query "{reg_path}"') or "  (key not found or access denied)")
            pause()
        else:
            warn("Invalid choice.")
            input("  Press Enter to continue...")

# ── EventViewer ───────────────────────────────────────────────────────────────

def menu_eventviewer():
    while True:
        clear()
        header("EventViewer Log Queries")
        options = {
            "TC":  ("Time change events (ID 4616)",          'wevtutil qe Security /q:"*[System[EventID=4616]]" /f:text /c:20'),
            "UC":  ("User account changes (ID 4738)",        'wevtutil qe Security /q:"*[System[EventID=4738]]" /f:text /c:20'),
            "EE":  ("System unexpected shutdowns (ID 41)",   'wevtutil qe System /q:"*[System[EventID=41]]" /f:text /c:20'),
            "LS":  ("Logout sessions (ID 4634)",             'wevtutil qe Security /q:"*[System[EventID=4634]]" /f:text /c:20'),
            "LSS": ("Login sessions (ID 4624)",              'wevtutil qe Security /q:"*[System[EventID=4624]]" /f:text /c:20'),
            "LC":  ("Log cleared (ID 1102 / 104)",           'wevtutil qe Security /q:"*[System[EventID=1102]]" /f:text /c:10'),
            "AJ":  ("App log — deleted journal",             'wevtutil qe Application /q:"*[System[EventID=45]]" /f:text /c:20'),
            "NJ":  ("NTFS — deleted journal (ID 98)",        'wevtutil qe System /q:"*[System[EventID=98]]" /f:text /c:20'),
            "USB": ("USB connected (ID 2003/2004)",          'wevtutil qe Microsoft-Windows-DriverFrameworks-UserMode/Operational /q:"*[System[(EventID=2003 or EventID=2004)]]" /f:text /c:20'),
        }
        for code, (desc, _) in options.items():
            print(f"  [{code}]  {desc}")
        print("\n  [0]  Back to main menu")
        choice = input("\n  Choice: ").strip().upper()
        if choice == "0":
            break
        elif choice in options:
            desc, cmd = options[choice]
            clear()
            header(f"EventViewer: {desc}")
            print(run(cmd) or "  (no matching events found or access denied)")
            pause()
        else:
            warn("Invalid choice.")
            input("  Press Enter to continue...")

# ── Macro scanner ─────────────────────────────────────────────────────────────

def check_macros():
    clear()
    header("Macro Software Scanner")
    macros = [
        "AutoHotkey", "Logitech Gaming Software", "G HUB",
        "Razer Synapse", "Corsair iCUE", "SteelSeries GG",
        "JoyToKey", "Xpadder", "AntiMicro", "Pulover",
        "TinyTask", "GS Auto Clicker", "OP Auto Clicker",
        "MacroGamer", "MacroToolworks", "Perfect Keyboard",
    ]
    info("Scanning AppData and Program Files for macro software...")
    found_any = False
    search_bases = [APPDATA, LOCALAPPDATA,
                    os.environ.get("PROGRAMFILES","C:\\Program Files"),
                    os.environ.get("PROGRAMFILES(X86)","C:\\Program Files (x86)")]
    for macro in macros:
        for base in search_bases:
            path = os.path.join(base, macro)
            if os.path.exists(path):
                found(f"{macro} → {path}")
                found_any = True
                show_path_options(macro, path)
    all_procs = run("tasklist").lower()
    for m in ["ahk", "autohotkey", "ghub", "synapse", "icue", "joytokey", "tinytask"]:
        if m in all_procs:
            found(f"Running process contains: {m}")
            found_any = True
    if not found_any:
        info("No macro software detected.")
    pause()

def check_bam():
    clear()
    header("BAM (Background Activity Moderator) — Execution History")
    info("Reading BAM registry for recently executed programs...")
    info("Credit: spokwn (BAM Parser) / RedLotus-Development (RedLotusBam.ps1)")
    print()

    bam_keys = [
        r"HKLM\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings",
        r"HKLM\SYSTEM\CurrentControlSet\Services\bam\UserSettings",
    ]

    entries = []
    for base_key in bam_keys:
        out = run(f'reg query "{base_key}" /s 2>nul')
        if not out:
            continue
        current_sid = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("HKEY_"):
                current_sid = line
                continue
            if not line or "REG_" not in line:
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            exe_path = parts[0]
            if not exe_path.lower().endswith(".exe") and "\\" not in exe_path:
                continue
            exe_path = exe_path.replace("\\Device\\HarddiskVolume3", "C:") \
                               .replace("\\Device\\HarddiskVolume2", "C:") \
                               .replace("\\Device\\HarddiskVolume1", "C:")
            entries.append((current_sid or "?", exe_path))
        if entries:
            break

    if not entries:
        warn("No BAM entries found, or BAM key is inaccessible.")
        info("Try running: spokwn's BAM Parser or RedLotusBam.ps1 for deeper parsing.")
        info("RedLotusBam.ps1 command:")
        print()
        print("  iex(New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/PureIntent/ScreenShare/main/RedLotusBam.ps1')")
        print()
        pause()
        return

    cheat_keywords = [k.lower() for k in CHEAT_CLIENTS] + [
        "inject", "hack", "cheat", "rat", "payload", "ghost",
        "ccleaner", "bleachbit", "privazer"
    ]

    flagged_count = 0
    clean_count   = 0

    info("Checking digital signatures and flagging suspicious entries...")
    print()
    print(f"  {'EXE':<55} {'SIG STATUS':<18} {'NOTE'}")
    print("  " + "─" * 95)

    seen = set()
    for sid, exe_path in entries:
        if exe_path in seen:
            continue
        seen.add(exe_path)

        sig = "Unknown"
        if os.path.exists(exe_path):
            ps_out = run(
                f'powershell -NoProfile -Command "(Get-AuthenticodeSignature \'{exe_path}\').Status"'
            ).strip()
            if ps_out:
                sig = ps_out
        else:
            sig = "File Deleted"

        name = os.path.basename(exe_path)
        is_suspicious = any(k in exe_path.lower() for k in cheat_keywords)
        is_unsigned    = sig.lower() in ["notsiged", "notsigned", "unknownerror", "hashmismatch", "nottrusteddomain"]
        is_deleted     = sig == "File Deleted"

        if is_suspicious or is_unsigned or is_deleted:
            colour = "\033[91m"
            note   = []
            if is_suspicious: note.append("SUSPICIOUS NAME")
            if is_unsigned:   note.append("UNSIGNED")
            if is_deleted:    note.append("FILE DELETED")
            note_str = " | ".join(note)
            print(f"  {colour}{name:<55} {sig:<18} ⚠  {note_str}\033[0m")
            flagged_count += 1
            if os.path.exists(exe_path):
                show_path_options(name, exe_path)
        else:
            print(f"  {name:<55} {sig:<18}")
            clean_count += 1

    print()
    info(f"Total unique entries: {len(seen)}  |  Flagged: {flagged_count}  |  Clean: {clean_count}")
    print()
    info("For deeper BAM analysis, use:")
    print("  → spokwn's BAM Parser : https://github.com/spokwn")
    print("  → RedLotusBam.ps1     : iex(New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/PureIntent/ScreenShare/main/RedLotusBam.ps1')")
    print("  → RedLotus Guide      : https://itzicehere.gitbook.io/redlotusguide")
    pause()


def check_recording_software():
    clear()
    header("Recording Software Scanner")
    recorders = [
        "OBS", "obs-studio", "Bandicam", "Fraps", "Shadowplay",
        "Medal", "Plays.tv", "Action!", "Mirillis", "XSplit",
        "Nvidia Share", "AMD ReLive", "GeForce Experience",
        "Streamlabs", "Loom", "Camtasia", "Screencast-O-Matic",
    ]
    info("Scanning for recording software installations and processes...")
    found_any = False
    search_bases = [APPDATA, LOCALAPPDATA,
                    os.environ.get("PROGRAMFILES","C:\\Program Files"),
                    os.environ.get("PROGRAMFILES(X86)","C:\\Program Files (x86)")]
    for rec in recorders:
        for base in search_bases:
            path = os.path.join(base, rec)
            if os.path.exists(path):
                found(f"{rec} → {path}")
                found_any = True
    all_procs = run("tasklist").lower()
    for r in ["obs", "bandicam", "fraps", "medal", "xsplit", "streamlabs", "camtasia", "loom"]:
        if r in all_procs:
            found(f"Running process contains: {r}")
            found_any = True
    if not found_any:
        info("No recording software detected.")
    pause()

# ── JAR PARSER ────────────────────────────────────────────────────────────────

JAR_PARSER_DIR  = os.path.join(TEMP, "JARParserTool")
JAR_PARSER_EXE  = os.path.join(JAR_PARSER_DIR, "JARParser.exe")
JAR_INSPECTOR   = os.path.join(JAR_PARSER_DIR, "JarInspector.class")

JAR_PARSER_URL  = "https://github.com/Orbdiff/jar-parser/releases/download/v1.2/JARParser.exe"
JAR_INSPECTOR_URL = "https://github.com/Orbdiff/jar-parser/releases/download/v1.1/JarInspector.class"

CHEAT_JAR_KEYWORDS = [
    "wurst", "impact", "meteor", "sigma", "vape", "future", "aristois",
    "liquidbounce", "salhack", "entropy", "inertia", "raven", "novoline",
    "wolfram", "pyrohax", "rekt", "remix", "xray", "phi", "hybrid",
    "prestige", "velaris", "bleach", "vapor", "dusk", "azura", "vertex",
    "nexus", "rise", "lucid", "ketamine", "reflex", "exodus", "zenith",
    "cyemer", "drip", "ares", "astolfo", "cheat", "hack", "inject",
    "novoware", "doomsday", "ghost", "payload",
]


def _download_file(url, dest, label=""):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = min(downloaded * 100 // total, 100)
                        bar = ("█" * (pct // 5)).ljust(20)
                        print(f"\r  [{bar}] {pct}%  ({downloaded // 1024} KB)  {label}", end="", flush=True)
        print()
        return True
    except Exception as e:
        print()
        warn(f"Download failed ({label}): {e}")
        if os.path.exists(dest):
            os.remove(dest)
        return False


def _ensure_jar_parser():
    os.makedirs(JAR_PARSER_DIR, exist_ok=True)
    ok = True
    if not os.path.exists(JAR_PARSER_EXE) or os.path.getsize(JAR_PARSER_EXE) < 1024:
        info("Downloading JARParser.exe ...")
        ok = _download_file(JAR_PARSER_URL, JAR_PARSER_EXE, "JARParser.exe") and ok
    if not os.path.exists(JAR_INSPECTOR) or os.path.getsize(JAR_INSPECTOR) < 64:
        info("Downloading JarInspector.class ...")
        ok = _download_file(JAR_INSPECTOR_URL, JAR_INSPECTOR, "JarInspector.class") and ok
    return ok


def _scan_prefetch_for_jars():
    found_any = False
    pf_dir = r"C:\Windows\Prefetch"
    if not os.path.isdir(pf_dir):
        warn("Prefetch folder inaccessible.")
        return
    for fname in os.listdir(pf_dir):
        if not fname.lower().endswith(".pf"):
            continue
        full = os.path.join(pf_dir, fname)
        try:
            with open(full, "rb") as f:
                raw = f.read()
            text = raw.decode("utf-16-le", errors="ignore")
            for match in re.findall(r'[A-Za-z]:\\[^\x00\r\n"<>|?*]{5,200}\.jar', text, re.IGNORECASE):
                kw_hit = any(k in match.lower() for k in CHEAT_JAR_KEYWORDS)
                tag = "  \033[91m<< SUSPICIOUS\033[0m" if kw_hit else ""
                print(f"  \033[93m[PF]\033[0m  {os.path.basename(fname)}")
                print(f"         JAR ref: {match}{tag}")
                if kw_hit and os.path.exists(match):
                    show_path_options(os.path.basename(match), match)
                found_any = True
        except Exception:
            pass
    if not found_any:
        info("No .jar references found in Prefetch files.")


def check_jar_parser():
    clear()
    header("JAR Parser — Prefetch Forensics & Bytecode Inspection")
    print()
    print("  This function uses two components:")
    print("  • JARParser.exe  — parses Windows Prefetch for .jar execution history")
    print("  • JarInspector.class — decompiles and inspects Java bytecode signatures")
    print()

    print("  ── Built-in Prefetch JAR scan ──────────────────────────────────────")
    _scan_prefetch_for_jars()
    print()

    print("  ── Quick .jar file scan (AppData + Desktop + Temp) ─────────────────")
    scan_roots = [APPDATA, LOCALAPPDATA, TEMP,
                  os.path.join(USERPROFILE, "Desktop"),
                  os.path.join(USERPROFILE, "Downloads")]
    jar_hits = []
    for root in scan_roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            for fn in files:
                if fn.lower().endswith(".jar"):
                    full = os.path.join(dirpath, fn)
                    kw = any(k in fn.lower() for k in CHEAT_JAR_KEYWORDS)
                    jar_hits.append((full, kw))

    if jar_hits:
        for path, suspicious in jar_hits:
            if suspicious:
                print(f"  \033[91m[!!]\033[0m {path}  \033[91m<< SUSPICIOUS NAME\033[0m")
                show_path_options(os.path.basename(path), path)
            else:
                info(path)
    else:
        info("No .jar files found outside .minecraft in scanned locations.")
    print()

    print("  ── External JARParser (full bytecode analysis) ──────────────────────")
    choice = input("  Download and launch JARParser.exe for deep analysis? [y/N]: ").strip().lower()
    if choice != "y":
        pause()
        return

    if not _ensure_jar_parser():
        warn("Could not download JARParser components. Check your internet connection.")
        pause()
        return

    info(f"Saved to: {JAR_PARSER_DIR}")
    info("Launching JARParser with elevated privileges...")
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", JAR_PARSER_EXE, None, JAR_PARSER_DIR, 1
        )
        info("JARParser launched — check the new window for results.")
    except Exception as e:
        warn(f"Launch failed: {e}")
        info("Try opening manually:")
        print(f"  {JAR_PARSER_EXE}")

    pause()


# ── ANTI-FORENSIC BYPASS DETECTOR ─────────────────────────────────────────────

BYPASS_TOOL_NAMES = [
    "SSBypass", "BypassSS", "SSCleaner", "ClearSS", "SSEvade",
    "ScreenShareBypass", "AntiSS", "bypass", "cleaner", "eraser",
    "CCleaner", "BleachBit", "Privazer", "PrivaZer", "Glary",
    "WiseCleaner", "WiseRegistryCleaner", "WiseDiskCleaner",
    "CleanMyPC", "PCCleaner", "RegistryCleaner", "PrivacyEraser",
    "Eraser", "FileShredder", "HardWipePortable",
    "ADSCleaner", "AlternateStreamRemover",
    "MRUBlaster", "Evidence Eliminator", "WindowWasher",
    "novoware_bypass", "doomsday_bypass", "cheat_cleaner",
    "log_cleaner", "mc_bypass", "mc_cleaner",
]

BYPASS_REGISTRY_ARTIFACTS = [
    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU",
    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs",
    r"HKCU\Software\Piriform\CCleaner",
    r"HKLM\Software\Piriform\CCleaner",
    r"HKCU\Software\BleachBit",
    r"HKCU\Software\Wise\Wise Registry Cleaner",
    r"HKCU\Software\Glarysoft\Glary Utilities",
    r"HKCU\Software\PrivaZer",
    r"HKCU\Software\PrivacyEraser",
    r"HKCU\Software\File Shredder",
]

BYPASS_PROCESS_NAMES = [
    "ccleaner", "ccleaner64", "bleachbit", "privazer",
    "wisecleaner", "glaryutilities", "privacyeraser",
    "eraser", "hardwipe", "ssbypass", "bypass",
]


def _check_bypass_registry():
    hits = []
    for reg_key in BYPASS_REGISTRY_ARTIFACTS:
        out = run(f'reg query "{reg_key}" 2>nul')
        if out.strip():
            hits.append(reg_key)
    return hits


def _check_bypass_files():
    hits = []
    search_bases = [
        APPDATA, LOCALAPPDATA, TEMP,
        os.path.join(USERPROFILE, "Desktop"),
        os.path.join(USERPROFILE, "Downloads"),
        os.environ.get("PROGRAMFILES", "C:\\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
    ]
    for base in search_bases:
        if not os.path.isdir(base):
            continue
        for name in BYPASS_TOOL_NAMES:
            p = os.path.join(base, name)
            if os.path.exists(p):
                hits.append(p)
            p2 = os.path.join(base, name + ".exe")
            if os.path.exists(p2):
                hits.append(p2)
    return hits


def _check_bypass_prefetch():
    hits = []
    pf_out = run("dir C:\\Windows\\Prefetch /b *.pf 2>nul").lower()
    for name in BYPASS_TOOL_NAMES:
        n = name.lower()
        for line in pf_out.splitlines():
            if n in line:
                hits.append(line.strip())
    return list(set(hits))


def _check_event_log_tamper():
    results = []
    for eid, log, desc in [
        ("1102", "Security",    "Security log manually CLEARED"),
        ("104",  "System",      "System log manually CLEARED"),
        ("104",  "Application", "Application log manually CLEARED"),
    ]:
        out = run(f'wevtutil qe {log} /q:"*[System[EventID={eid}]]" /f:text /c:5 2>nul')
        if out.strip():
            results.append((desc, out.strip()[:400]))

    out = run('wevtutil qe System /q:"*[System[EventID=98]]" /f:text /c:5 2>nul')
    if out.strip():
        results.append(("NTFS USN Journal DELETED (ID 98)", out.strip()[:400]))

    usn_check = run("fsutil usn queryjournal C: 2>&1")
    if "error" in usn_check.lower() or "not" in usn_check.lower():
        results.append(("USN Journal appears DISABLED/DELETED on C:", usn_check[:200]))

    return results


def _check_bypass_processes():
    hits = []
    all_procs = run("tasklist").lower()
    for name in BYPASS_PROCESS_NAMES:
        if name in all_procs:
            hits.append(name)
    return hits


def check_bypass_detector():
    clear()
    header("Anti-Forensic Bypass Detector")
    print()
    info("Scanning for SS bypass tools, evidence wipers, and anti-forensic tampering...")
    print()

    total_flags = 0

    print("  ── [1/5] Running bypass processes ─────────────────────────────────")
    procs = _check_bypass_processes()
    if procs:
        for p in procs:
            found(f"ACTIVE PROCESS: {p}")
            total_flags += 1
    else:
        info("No bypass processes currently running.")
    print()

    print("  ── [2/5] Bypass tool files on disk ─────────────────────────────────")
    files = _check_bypass_files()
    if files:
        for f in files:
            found(f"FILE/FOLDER: {f}")
            total_flags += 1
            show_path_options(os.path.basename(f), f)
    else:
        info("No bypass tool files found in common locations.")
    print()

    print("  ── [3/5] Registry traces (bypass/cleaner tools) ────────────────────")
    reg_hits = _check_bypass_registry()
    if reg_hits:
        for r in reg_hits:
            found(f"REGISTRY KEY EXISTS: {r}")
            total_flags += 1
    else:
        info("No bypass tool registry keys found.")
    print()

    print("  ── [4/5] Prefetch execution history ────────────────────────────────")
    pf = _check_bypass_prefetch()
    if pf:
        for entry in pf:
            found(f"PREFETCH ENTRY: {entry}")
            total_flags += 1
    else:
        info("No bypass tools found in prefetch history.")
    print()

    print("  ── [5/5] Event log & USN journal tampering ─────────────────────────")
    ev_hits = _check_event_log_tamper()
    if ev_hits:
        for desc, detail in ev_hits:
            found(f"{desc}")
            print(f"    {detail[:300]}")
            total_flags += 1
    else:
        info("No event log clearing or USN journal deletion detected.")
    print()

    print("  ── [+] Windows Defender real-time protection status ────────────────")
    defender = run(
        'powershell -NoProfile -Command "(Get-MpPreference).DisableRealtimeMonitoring" 2>nul'
    ).strip()
    if defender.lower() == "true":
        found("Windows Defender REAL-TIME PROTECTION IS DISABLED")
        total_flags += 1
    elif defender.lower() == "false":
        info("Windows Defender real-time protection is enabled.")
    else:
        warn(f"Could not determine Defender status: {defender or '(no output)'}")
    print()

    fw_out = run('netsh advfirewall show allprofiles state 2>nul')
    if "off" in fw_out.lower():
        found("Windows Firewall appears to be DISABLED (possible bypass)")
        total_flags += 1
    print()

    print("  " + "═" * 68)
    if total_flags == 0:
        info(f"Bypass scan complete — \033[92mNO bypass artifacts detected.\033[0m")
    else:
        red(f"Bypass scan complete — \033[91m{total_flags} suspicious artifact(s) found!\033[0m")

    if files:
        print()
        warn("Bypass tool files were detected on disk.")
        print("  The following files/folders can be removed:")
        for i, f in enumerate(files, 1):
            print(f"  [{i}] {f}")
        print()
        choice = input(
            "  Remove detected bypass tool files? [y/N] (ONLY non-system files will be touched): "
        ).strip().lower()
        if choice == "y":
            removed = 0
            for fpath in files:
                skip_patterns = [
                    "windows\\system32", "windows\\syswow64",
                    "program files", "programdata\\microsoft",
                ]
                if any(s in fpath.lower() for s in skip_patterns):
                    warn(f"Skipping system path: {fpath}")
                    continue
                try:
                    if os.path.isdir(fpath):
                        shutil.rmtree(fpath)
                    else:
                        os.remove(fpath)
                    info(f"Removed: {fpath}")
                    removed += 1
                except Exception as e:
                    warn(f"Could not remove {fpath}: {e}")
            info(f"Removed {removed} item(s).")
        else:
            info("No files removed.")

    pause()


# ── FILE FORENSIC SCANNER + VIRUSTOTAL ────────────────────────────────────────

VT_API_KEY_FILE = os.path.join(DOWNLOADS, "vt_api_key.txt")

CHEAT_STRING_PATTERNS = [
    b"com/wurst", b"net/wurst", b"me/sigma", b"me/vape", b"com/future",
    b"me/baritone", b"com/meteor", b"me/astolfo", b"net/liquidbounce",
    b"com/salhack", b"me/prestige", b"net/exodus", b"com/novoline",
    b"me/reflex", b"com/aristois", b"me/inertia", b"me/entropy",
    b"com/velaris", b"me/lucid", b"com/dusk", b"me/bleach",
    b"novoware", b"doomsday", b"ghostclient",
    b"KillAura", b"killaura", b"AutoCrystal", b"Reach", b"Velocity",
    b"Aimbot", b"ESP", b"Wallhack", b"Freecam", b"ChestStealer",
    b"AntiKnockback", b"ClickGUI", b"Scaffold",
    b"ClassLoader", b"Inject", b"HookMethod", b"transformClass",
    b"LaunchWrapper",
]

SUSPICIOUS_PE_IMPORTS = [
    "WriteProcessMemory", "VirtualAllocEx", "CreateRemoteThread",
    "NtWriteVirtualMemory", "ZwWriteVirtualMemory", "RtlCreateUserThread",
    "LoadLibraryA", "LoadLibraryW", "GetProcAddress",
    "OpenProcess", "VirtualProtectEx", "SetWindowsHookEx",
    "NtOpenProcess", "NtAllocateVirtualMemory",
]

OBFUSCATION_INDICATORS = [
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
]


def _compute_hashes(filepath):
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                md5.update(chunk)
                sha1.update(chunk)
                sha256.update(chunk)
        return md5.hexdigest(), sha1.hexdigest(), sha256.hexdigest()
    except Exception as e:
        return None, None, None


def _vt_lookup(sha256, api_key):
    url = f"https://www.virustotal.com/api/v3/files/{sha256}"
    try:
        req = urllib.request.Request(
            url,
            headers={"x-apikey": api_key, "User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        total = sum(stats.values())
        permalink = f"https://www.virustotal.com/gui/file/{sha256}"
        return malicious + suspicious, total, permalink, None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return 0, 0, None, "NOT FOUND in VirusTotal database"
        return None, None, None, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return None, None, None, str(e)


def _scan_strings(filepath):
    hits = []
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        for pattern in CHEAT_STRING_PATTERNS:
            if pattern.lower() in data.lower():
                hits.append(pattern.decode("utf-8", errors="replace"))
    except Exception:
        pass
    return hits


def _scan_pe_imports(filepath):
    suspicious = []
    try:
        with open(filepath, "rb") as f:
            raw = f.read()
        if raw[:2] != b"MZ":
            return suspicious
        e_lfanew = struct.unpack_from("<I", raw, 0x3C)[0]
        pe_sig = raw[e_lfanew: e_lfanew + 4]
        if pe_sig != b"PE\x00\x00":
            return suspicious
        machine = struct.unpack_from("<H", raw, e_lfanew + 4)[0]
        is64 = (machine == 0x8664)
        opt_offset = e_lfanew + 24
        if is64:
            import_dir_offset = opt_offset + 104
        else:
            import_dir_offset = opt_offset + 96
        import_rva  = struct.unpack_from("<I", raw, import_dir_offset)[0]
        import_size = struct.unpack_from("<I", raw, import_dir_offset + 4)[0]
        if import_rva == 0 or import_size == 0:
            return suspicious
        num_sections = struct.unpack_from("<H", raw, e_lfanew + 6)[0]
        sec_offset = opt_offset + (240 if is64 else 224)
        sections = []
        for i in range(num_sections):
            off = sec_offset + i * 40
            vaddr = struct.unpack_from("<I", raw, off + 12)[0]
            vsize = struct.unpack_from("<I", raw, off + 16)[0]
            raddr = struct.unpack_from("<I", raw, off + 20)[0]
            sections.append((vaddr, vsize, raddr))

        def rva_to_offset(rva):
            for vaddr, vsize, raddr in sections:
                if vaddr <= rva < vaddr + vsize:
                    return raddr + (rva - vaddr)
            return None

        desc_off = rva_to_offset(import_rva)
        if desc_off is None:
            return suspicious
        while desc_off + 20 <= len(raw):
            orig_thunk = struct.unpack_from("<I", raw, desc_off)[0]
            name_rva   = struct.unpack_from("<I", raw, desc_off + 12)[0]
            first_thunk = struct.unpack_from("<I", raw, desc_off + 16)[0]
            if name_rva == 0 and orig_thunk == 0:
                break
            dll_off = rva_to_offset(name_rva)
            dll_name = ""
            if dll_off:
                end = raw.find(b"\x00", dll_off)
                dll_name = raw[dll_off:end].decode("ascii", errors="replace")
            thunk_rva = orig_thunk if orig_thunk else first_thunk
            thunk_off = rva_to_offset(thunk_rva)
            if thunk_off:
                while thunk_off + (8 if is64 else 4) <= len(raw):
                    if is64:
                        val = struct.unpack_from("<Q", raw, thunk_off)[0]
                    else:
                        val = struct.unpack_from("<I", raw, thunk_off)[0]
                    if val == 0:
                        break
                    ord_flag = 0x8000000000000000 if is64 else 0x80000000
                    if not (val & ord_flag):
                        fn_off = rva_to_offset(val & 0x7FFFFFFFFFFFFFFF)
                        if fn_off and fn_off + 2 < len(raw):
                            fn_end = raw.find(b"\x00", fn_off + 2)
                            fn_name = raw[fn_off + 2: fn_end].decode("ascii", errors="replace")
                            if fn_name in SUSPICIOUS_PE_IMPORTS:
                                suspicious.append(f"{dll_name}!{fn_name}")
                    thunk_off += 8 if is64 else 4
            desc_off += 20
    except Exception:
        pass
    return suspicious


def _detect_obfuscation(filepath):
    flags = []
    try:
        with open(filepath, "rb") as f:
            data = f.read(65536)
        zero_ratio = data.count(b"\x00") / max(len(data), 1)
        if zero_ratio > 0.6:
            flags.append(f"High null-byte density ({zero_ratio:.0%}) — possible packer/obfuscator")
        if filepath.lower().endswith(".jar"):
            class_count = data.count(b"\xca\xfe\xba\xbe")
            if class_count > 0:
                flags.append(f"Contains {class_count} compiled .class file(s)")
        b64_matches = re.findall(rb"[A-Za-z0-9+/]{80,}={0,2}", data)
        if len(b64_matches) > 5:
            flags.append(f"{len(b64_matches)} long base64-like strings found (possible encoded payload)")
    except Exception:
        pass
    return flags


def _print_forensic_report(filepath, api_key=None):
    if not os.path.exists(filepath):
        warn(f"File not found: {filepath}")
        return

    size_kb = os.path.getsize(filepath) // 1024
    ext = os.path.splitext(filepath)[1].lower()
    mtime = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n  {'─'*70}")
    print(f"  File   : {filepath}")
    print(f"  Size   : {size_kb} KB    Ext: {ext}    Modified: {mtime}")

    md5, sha1, sha256 = _compute_hashes(filepath)
    if sha256:
        print(f"  MD5    : {md5}")
        print(f"  SHA1   : {sha1}")
        print(f"  SHA256 : {sha256}")

    if ext in [".exe", ".dll", ".sys"]:
        sig = run(
            f'powershell -NoProfile -Command "(Get-AuthenticodeSignature \'{filepath}\').Status"'
        ).strip()
        color = "\033[92m" if "Valid" in sig else "\033[91m"
        print(f"  Sig    : {color}{sig}\033[0m")

    str_hits = _scan_strings(filepath)
    if str_hits:
        print(f"\n  \033[91m[STRINGS] Cheat pattern matches ({len(str_hits)}):\033[0m")
        for h in str_hits[:20]:
            print(f"    • {h}")
        show_path_options(os.path.basename(filepath), filepath)
    else:
        print(f"\n  [STRINGS] No cheat string patterns detected.")

    if ext in [".exe", ".dll", ".sys"]:
        pe_hits = _scan_pe_imports(filepath)
        if pe_hits:
            print(f"\n  \033[91m[PE IMPORTS] Suspicious imports ({len(pe_hits)}):\033[0m")
            for h in pe_hits[:20]:
                print(f"    • {h}")
            show_path_options(os.path.basename(filepath), filepath)
        else:
            print(f"\n  [PE IMPORTS] No suspicious imports detected.")

    obf = _detect_obfuscation(filepath)
    if obf:
        print(f"\n  \033[93m[OBFUSCATION] Indicators detected:\033[0m")
        for f in obf:
            print(f"    • {f}")

    if api_key and sha256:
        print(f"\n  [VT] Querying VirusTotal...")
        detections, total, link, err = _vt_lookup(sha256, api_key)
        if err:
            warn(f"[VT] {err}")
        elif total == 0:
            info("[VT] File not found in VirusTotal database (never scanned).")
        else:
            if detections == 0:
                print(f"  \033[92m[VT] CLEAN  — 0/{total} engines detected\033[0m")
            elif detections <= 3:
                print(f"  \033[93m[VT] SUSPICIOUS — {detections}/{total} engines detected\033[0m")
                show_path_options(os.path.basename(filepath), filepath)
            else:
                print(f"  \033[91m[VT] MALICIOUS — {detections}/{total} engines detected\033[0m")
                show_path_options(os.path.basename(filepath), filepath)
            if link:
                print(f"       Report: {link}")
    elif not api_key:
        info("[VT] No API key set — VirusTotal lookup skipped.")


def _load_vt_key():
    if os.path.exists(VT_API_KEY_FILE):
        try:
            with open(VT_API_KEY_FILE, "r") as f:
                k = f.read().strip()
            if k:
                return k
        except Exception:
            pass
    return None


def check_file_forensics():
    clear()
    header("File Forensic Scanner + VirusTotal")

    os.makedirs(DOWNLOADS, exist_ok=True)
    api_key = _load_vt_key()

    while True:
        clear()
        header("File Forensic Scanner + VirusTotal")
        vt_status = f"\033[92m[KEY SET]\033[0m" if api_key else "\033[93m[NO KEY]\033[0m"
        print(f"  VirusTotal API Key: {vt_status}")
        print()
        print("  [1]  Scan a single file")
        print("  [2]  Scan a directory (non-recursive)")
        print("  [3]  Scan AppData for suspicious .jar / .exe / .dll files")
        print("  [4]  Set VirusTotal API key")
        print("  [0]  Back to main menu")
        print()
        choice = input("  Choice: ").strip()

        if choice == "0":
            break
        elif choice == "4":
            clear()
            header("Set VirusTotal API Key")
            print("  Get a free API key at https://www.virustotal.com/gui/my-apikey")
            print()
            new_key = input("  Paste your VT API key (or Enter to cancel): ").strip()
            if new_key:
                with open(VT_API_KEY_FILE, "w") as f:
                    f.write(new_key)
                api_key = new_key
                info("API key saved.")
            pause()
        elif choice == "1":
            clear()
            header("Scan Single File")
            path = input("  File path to scan: ").strip().strip('"')
            if not path:
                continue
            _print_forensic_report(path, api_key)
            pause()
        elif choice == "2":
            clear()
            header("Scan Directory")
            dirpath = input("  Directory path: ").strip().strip('"')
            if not os.path.isdir(dirpath):
                warn("Not a valid directory.")
                pause()
                continue
            exts = [".jar", ".exe", ".dll", ".bat", ".ps1", ".vbs", ".zip"]
            files = [
                os.path.join(dirpath, f)
                for f in os.listdir(dirpath)
                if os.path.splitext(f)[1].lower() in exts
            ]
            if not files:
                info("No scannable files found.")
                pause()
                continue
            info(f"Scanning {len(files)} file(s)...")
            for fp in files:
                _print_forensic_report(fp, api_key)
                if api_key:
                    time.sleep(0.5)
            pause()
        elif choice == "3":
            clear()
            header("Auto-scan AppData for suspicious files")
            scan_dirs = [APPDATA, LOCALAPPDATA, TEMP,
                         os.path.join(USERPROFILE, "Downloads")]
            suspicious_exts = [".jar", ".exe", ".dll"]
            hits = []
            info("Walking AppData directories for cheat-related files...")
            for base in scan_dirs:
                if not os.path.isdir(base):
                    continue
                for dirpath, _, fnames in os.walk(base):
                    if ".minecraft" in dirpath.lower():
                        continue
                    for fn in fnames:
                        ext = os.path.splitext(fn)[1].lower()
                        if ext not in suspicious_exts:
                            continue
                        kw = any(k in fn.lower() for k in CHEAT_JAR_KEYWORDS)
                        if kw or ext == ".jar":
                            hits.append(os.path.join(dirpath, fn))
            if not hits:
                info("No suspicious files found.")
                pause()
                continue
            info(f"Found {len(hits)} suspect file(s).")
            scan_all = input("  Scan all with forensics + VT? [y/N]: ").strip().lower()
            if scan_all != "y":
                continue
            for fp in hits:
                _print_forensic_report(fp, api_key)
                if api_key:
                    time.sleep(0.5)
            pause()


# ── NOVOWARE RAM + NTFS JOURNAL SCANNER ──────────────────────────────────────

NOVOWARE_SIGNATURES: list[bytes] = [
    # << INSERT PRIVATE NOVOWARE SIGNATURES HERE >>
]

NOVOWARE_FS_KEYWORDS = [
    "novoware", "novo_", "novo-", "novomod", "novobypass",
    "novojar", "nv_loader", "nvware",
]

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress",       ctypes.c_void_p),
        ("AllocationBase",    ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize",        ctypes.c_size_t),
        ("State",             ctypes.c_ulong),
        ("Protect",           ctypes.c_ulong),
        ("Type",              ctypes.c_ulong),
    ]

MEM_COMMIT  = 0x1000
PAGE_GUARD  = 0x100
PAGE_NOACCESS = 0x01
READABLE_PROTECTIONS = {0x02, 0x04, 0x20, 0x40}
PROCESS_VM_READ           = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MAX_REGION_MB = 100


def _get_java_pids():
    pids = []
    out = run("tasklist /fo csv /nh")
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 2:
            name = parts[0].lower()
            if name in ("java.exe", "javaw.exe"):
                try:
                    pids.append((int(parts[1]), parts[0]))
                except ValueError:
                    pass
    return pids


def _scan_pid_for_sigs(pid, signatures):
    hits = []
    k32 = ctypes.windll.kernel32
    handle = k32.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid
    )
    if not handle:
        return hits
    try:
        mbi = MEMORY_BASIC_INFORMATION()
        addr = 0
        chunk_size = 50 * 1024 * 1024
        while True:
            ret = k32.VirtualQueryEx(
                handle,
                ctypes.c_void_p(addr),
                ctypes.byref(mbi),
                ctypes.sizeof(mbi),
            )
            if ret == 0:
                break
            region_end = addr + mbi.RegionSize
            if (
                mbi.State == MEM_COMMIT
                and (mbi.Protect & PAGE_GUARD) == 0
                and mbi.Protect != PAGE_NOACCESS
                and (mbi.Protect & 0xFF) in READABLE_PROTECTIONS
                and mbi.RegionSize <= MAX_REGION_MB * 1024 * 1024
            ):
                offset = 0
                while offset < mbi.RegionSize:
                    read_sz = min(chunk_size, mbi.RegionSize - offset)
                    buf     = (ctypes.c_char * read_sz)()
                    bytes_read = ctypes.c_size_t(0)
                    ok = k32.ReadProcessMemory(
                        handle,
                        ctypes.c_void_p(addr + offset),
                        buf,
                        read_sz,
                        ctypes.byref(bytes_read),
                    )
                    if ok and bytes_read.value > 0:
                        data = bytes(buf[: bytes_read.value])
                        for i, sig in enumerate(signatures):
                            if sig in data:
                                hits.append((i, addr + offset))
                    offset += chunk_size
            if region_end <= addr:
                break
            addr = region_end
    finally:
        k32.CloseHandle(handle)
    return hits


def _novoware_ntfs_journal_scan():
    hits = []
    tmp_journal = os.path.join(TEMP, "_usn_dump_novo.txt")
    run(f'fsutil usn readdata C: 0 2048 > "{tmp_journal}" 2>nul')
    ev_out = run(
        'wevtutil qe Security '
        '/q:"*[System[EventID=4663]]" '
        '/f:text /c:500 2>nul'
    )
    if ev_out:
        for line in ev_out.splitlines():
            ll = line.lower()
            if any(k in ll for k in NOVOWARE_FS_KEYWORDS):
                hits.append(f"[EventLog 4663] {line.strip()}")
    if os.path.exists(tmp_journal):
        try:
            with open(tmp_journal, "r", errors="ignore") as f:
                for line in f:
                    ll = line.lower()
                    if any(k in ll for k in NOVOWARE_FS_KEYWORDS):
                        hits.append(f"[USN Journal] {line.strip()}")
        except Exception:
            pass
        try:
            os.remove(tmp_journal)
        except Exception:
            pass
    pf_out = run("dir C:\\Windows\\Prefetch /b *.pf 2>nul").lower()
    for line in pf_out.splitlines():
        if any(k in line for k in NOVOWARE_FS_KEYWORDS):
            hits.append(f"[Prefetch] {line.strip()}")
    for base in [APPDATA, LOCALAPPDATA, TEMP]:
        if not os.path.isdir(base):
            continue
        for dirpath, _, files in os.walk(base):
            for fn in files:
                if any(k in fn.lower() for k in NOVOWARE_FS_KEYWORDS):
                    full_path = os.path.join(dirpath, fn)
                    hits.append(f"[File Trace] {full_path}")
    return hits


def check_novoware():
    clear()
    header("Novoware Cheat Client — RAM + NTFS Journal Scanner")
    print()
    print("  \033[93mForensic analysis tool for detecting the Novoware cheat client\033[0m")
    print("  Phase 1 → NTFS journal & filesystem traces")
    print("  Phase 2 → RAM memory scan of active Java processes")
    print()

    print("  " + "═" * 68)
    info("[Phase 1] NTFS Journal & Filesystem Analysis")
    print("  " + "═" * 68)

    fs_hits = _novoware_ntfs_journal_scan()
    if fs_hits:
        found(f"{len(fs_hits)} Novoware filesystem trace(s) detected!")
        for h in fs_hits:
            print(f"  \033[91m[FS]\033[0m {h}")
            # Extract path from file trace hits and offer inspection
            if h.startswith("[File Trace]"):
                fpath = h.replace("[File Trace] ", "").strip()
                if os.path.exists(fpath):
                    show_path_options(os.path.basename(fpath), fpath)
    else:
        info("No Novoware filesystem traces found.")

    print()
    print("  " + "═" * 68)
    info("[Phase 2] RAM Memory Scan — Java Process Analysis")
    print("  " + "═" * 68)

    if not NOVOWARE_SIGNATURES:
        warn("No Novoware signatures loaded.")
        warn("Add private byte signatures to NOVOWARE_SIGNATURES list in ss.py.")
        print()
        info("Infrastructure is ready — signatures redacted to prevent bypass.")
        print()
    else:
        pids = _get_java_pids()
        if not pids:
            info("No Java processes found running.")
        else:
            info(f"Found {len(pids)} Java process(es). Beginning memory scan...")
            print()
            overall_result = "CLEAN"
            for pid, pname in pids:
                print(f"  Scanning PID {pid} ({pname})...", end="", flush=True)
                hits = _scan_pid_for_sigs(pid, NOVOWARE_SIGNATURES)
                if hits:
                    print(f"\r  \033[91m[!!] PID {pid} ({pname}) — NOVOWARE DETECTED ({len(hits)} signature hit(s))\033[0m")
                    overall_result = "DETECTED"
                else:
                    print(f"\r  \033[92m[OK] PID {pid} ({pname}) — CLEAN\033[0m                    ")
            print()
            if overall_result == "DETECTED":
                red("VERDICT: NOVOWARE ACTIVE IN MEMORY — FUCKED")
            else:
                info("VERDICT: No Novoware signatures found in RAM — CLEAN")

    print()
    info("[+] BAM history check for Novoware traces...")
    bam_keys = [
        r"HKLM\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings",
        r"HKLM\SYSTEM\CurrentControlSet\Services\bam\UserSettings",
    ]
    bam_found = False
    for key in bam_keys:
        out = run(f'reg query "{key}" /s 2>nul')
        for line in out.splitlines():
            if any(k in line.lower() for k in NOVOWARE_FS_KEYWORDS):
                found(f"BAM entry: {line.strip()}")
                bam_found = True
    if not bam_found:
        info("No Novoware entries in BAM execution history.")

    pause()


# ── EXTERNAL POWERSHELL TOOLS ─────────────────────────────────────────────────

EXTERNAL_PS_TOOLS = {
    "MeowModAnalyzer": {
        "desc":    "Forensic mod scanner — scans files for cheat signatures, PE imports, obfuscation",
        "url":     "https://raw.githubusercontent.com/MeowTonynoh/MeowModAnalyzer/main/MeowModAnalyzer.ps1",
        "cmd":     'powershell -ExecutionPolicy Bypass -Command "Invoke-Expression (Invoke-RestMethod \'https://raw.githubusercontent.com/MeowTonynoh/MeowModAnalyzer/main/MeowModAnalyzer.ps1\')"',
    },
    "ShadowClicker": {
        "desc":    "AutoClicker / macro detection forensic tool",
        "url":     "https://raw.githubusercontent.com/MeowTonynoh/Shadowclicker/main/ShadowClicker.ps1",
        "cmd":     'powershell -ExecutionPolicy Bypass -Command "Invoke-Expression (Invoke-RestMethod \'https://raw.githubusercontent.com/MeowTonynoh/Shadowclicker/main/ShadowClicker.ps1\')"',
    },
}


def _preview_ps_script(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
        lines = content.splitlines()
        print()
        print("  ── Script Preview (first 60 lines) ───────────────────────────────")
        for i, line in enumerate(lines[:60], 1):
            print(f"  {i:3}  {line}")
        if len(lines) > 60:
            info(f"  ... ({len(lines) - 60} more lines) — full URL: {url}")
    except Exception as e:
        warn(f"Could not preview script: {e}")


def _launch_ps_tool(name, tool_info):
    clear()
    header(f"Launching: {name}")
    print(f"  {tool_info['desc']}")
    print()
    warn("This will download and execute an external PowerShell script.")
    warn(f"Source: {tool_info['url']}")
    print()

    print("  [P] Preview script source before running")
    print("  [R] Run now")
    print("  [0] Cancel")
    choice = input("\n  Choice: ").strip().upper()

    if choice == "P":
        _preview_ps_script(tool_info["url"])
        print()
        run_after = input("  Run the script now? [y/N]: ").strip().lower()
        if run_after != "y":
            pause()
            return

    if choice in ("R",) or (choice == "P" and run_after == "y"):
        info(f"Launching {name} in new window...")
        try:
            subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass",
                 "-Command", f"Invoke-Expression (Invoke-RestMethod '{tool_info['url']}')"],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            info("Script launched in separate window.")
        except Exception as e:
            warn(f"Launch failed: {e}")
            info("Manual command:")
            print(f"  {tool_info['cmd']}")
    else:
        info("Cancelled.")

    pause()


def menu_external_tools():
    while True:
        clear()
        header("External PowerShell Tools")
        print()
        print("  These are community screenshare tools fetched directly from GitHub.")
        print("  You can preview the source before running each one.")
        print()
        print("  ── MEOW TOOLS (MeowTonynoh) ─────────────────────────────────────")
        print("  [1]  MeowModAnalyzer — cheat signature & PE forensic scanner")
        print("  [2]  ShadowClicker   — AutoClicker / macro detection tool")
        print()
        print("  ── JAR / BYTECODE ────────────────────────────────────────────────")
        print("  [3]  JAR Parser      — Prefetch + bytecode analysis (JARParser.exe)")
        print()
        print("  ── NOVOWARE ──────────────────────────────────────────────────────")
        print("  [4]  Novoware Scanner — RAM memory + NTFS journal detection")
        print()
        print("  [0]  Back to main menu")
        print()
        choice = input("  Choice: ").strip()

        if choice == "0":
            break
        elif choice == "1":
            _launch_ps_tool("MeowModAnalyzer", EXTERNAL_PS_TOOLS["MeowModAnalyzer"])
        elif choice == "2":
            _launch_ps_tool("ShadowClicker", EXTERNAL_PS_TOOLS["ShadowClicker"])
        elif choice == "3":
            check_jar_parser()
        elif choice == "4":
            check_novoware()
        else:
            warn("Invalid choice.")
            input("  Press Enter to continue...")


def open_path_safe(path):
    if os.path.exists(path):
        os.startfile(path)
    else:
        warn(f"Path not found: {path}")

# ── Main Menu ─────────────────────────────────────────────────────────────────

def menu():
    while True:
        clear()
        print("""
  ╔══════════════════════════════════════════════════════════════════════╗
  ║              SS HELPER — Minecraft Screenshare Tool                  ║
  ╚══════════════════════════════════════════════════════════════════════╝
        """)

        print("  ── AUTOMATIC CHECKS ─────────────────────────────────────────────")
        print("  [1]  AppData cheat client folders  [2]  Running processes")
        print("  [3]  .minecraft folder              [4]  Startup programs")
        print("  [5]  Recently opened files          [6]  Temp folder")
        print("  [7]  Hosts file                     [8]  Installed programs")
        print("  [9]  Browser history paths          [10] Windows Prefetch")
        print("  [11] Scheduled tasks                [12] Environment variables")
        print("  [13] VPN / virtual adapters         [14] Shadow copies")
        print("  [15] Files modified in last 24h     [16] Active network connections")
        print("  [17] Installed drivers              [18] Full auto scan (all checks)")
        print("  [O]  Ocean Anti-Cheat PIN lookup")
        print("  [R]  Save full scan report to Desktop")
        print("  [K]  Launcher/Profile Scanner")
        print("  [M]  Java Argument Scanner")
        print("  [S]  Suspicious Cheat Folders")
        print("  [L]  Launcher / Mods Reader")
        print()
        print("  ── BROWSER FORENSICS ────────────────────────────────────────────")
        print("  [BF] Browser Forensics Menu")
        print("       History · Downloads · Wipe Detection · Cookie Domains")
        print()
        print("  ── CHICHO SS HELPER SECTIONS ────────────────────────────────────")
        print("  [A]  Manual Tools     (NirSoft / forensic download & launch)")
        print("  [B]  Recovery Tools   (file recovery software)")
        print("  [C]  Explorer Paths   (open system folders)")
        print("  [D]  USN Journal      (NTFS journal queries)")
        print("  [E]  Commands         (CMD / PowerShell checks)")
        print("  [F]  Registry Paths   (query / view reg keys)")
        print("  [G]  EventViewer      (query event logs)")
        print("  [H]  Macro Scanner    (detect macro software)")
        print("  [I]  Recording Scanner(detect screen recorders)")
        print("  [BAM] BAM Checker     (execution history + signature check)")
        print("  [J]  HWID Extractor   (dump hardware IDs to file)")
        print()
        print("  ── ADVANCED FORENSICS ───────────────────────────────────────────")
        print("  [JP]  JAR Parser       (Prefetch JAR forensics + bytecode scan)")
        print("  [BYP] Bypass Detector  (anti-forensic tool & registry artifact scan)")
        print("  [FF]  File Forensics   (string/PE/obfuscation scan + VirusTotal)")
        print("  [NW]  Novoware Scanner (RAM memory + NTFS journal detection)")
        print("  [EXT] External Tools   (MeowModAnalyzer / ShadowClicker / PS tools)")
        print()
        print("  ── MANUAL OPENERS ───────────────────────────────────────────────")
        print("  [19] Task Manager      [20] Registry Editor   [21] AppData folder")
        print("  [22] .minecraft folder [23] Temp folder       [24] Startup folder")
        print("  [25] Recent files      [26] Program Files     [27] Hosts in Notepad")
        print("  [28] Event Viewer      [29] Resource Monitor  [30] System Info (msinfo32)")
        print("  [31] Services          [32] Device Manager    [33] Network Connections")
        print("  [34] Autoruns          [35] Dump processes    [36] Dump startup")
        print("  [37] Dump network      [38] Search for a file [39] Search registry")
        print("  [40] Disk Cleanup")
        print()
        print("  [0]  Exit")
        print()

        choice = input("  Choice: ").strip().upper()

        num_actions = {
            "1":  check_appdata,
            "2":  check_processes,
            "3":  check_minecraft,
            "4":  check_startup,
            "5":  check_recent,
            "6":  check_temp,
            "7":  check_hosts,
            "8":  check_programs,
            "9":  check_browser,
            "10": check_prefetch,
            "11": check_tasks,
            "12": check_envvars,
            "13": check_vpn,
            "14": check_shadow,
            "15": check_modified,
            "16": check_netstat,
            "17": check_drivers,
            "18": full_scan,
            "O":  check_ocean_api,
            "R":  save_full_scan_report,
            "K":  check_minecraft_launchers,
            "M":  check_java_arguments,
            "S":  check_suspicious_folders,
            "L":  scan_launcher_mods,
            "BF": menu_browser_forensics,
            "A":  menu_manual_tools,
            "B":  menu_recovery_tools,
            "C":  menu_explorer,
            "D":  menu_usn_journal,
            "E":  menu_commands,
            "F":  menu_regedit,
            "G":  menu_eventviewer,
            "H":  check_macros,
            "I":  check_recording_software,
            "BAM": check_bam,
            "J":  hwid_extractor,
            "JP":  check_jar_parser,
            "BYP": check_bypass_detector,
            "FF":  check_file_forensics,
            "NW":  check_novoware,
            "EXT": menu_external_tools,
            "19": lambda: subprocess.Popen("taskmgr"),
            "20": lambda: subprocess.Popen("regedit"),
            "21": lambda: open_path_safe(APPDATA),
            "22": lambda: open_path_safe(MINECRAFT),
            "23": lambda: open_path_safe(TEMP),
            "24": lambda: open_path_safe(os.path.join(APPDATA, r"Microsoft\Windows\Start Menu\Programs\Startup")),
            "25": lambda: open_path_safe(os.path.join(APPDATA, r"Microsoft\Windows\Recent")),
            "26": lambda: open_path_safe(os.environ.get("PROGRAMFILES", "C:\\Program Files")),
            "27": lambda: subprocess.Popen(["notepad", r"C:\Windows\System32\drivers\etc\hosts"]),
            "28": lambda: subprocess.Popen("eventvwr"),
            "29": lambda: subprocess.Popen("resmon"),
            "30": lambda: subprocess.Popen("msinfo32"),
            "31": lambda: subprocess.Popen("services.msc", shell=True),
            "32": lambda: subprocess.Popen("devmgmt.msc", shell=True),
            "33": lambda: subprocess.Popen("ncpa.cpl",     shell=True),
            "34": lambda: subprocess.Popen("autoruns",     shell=True),
            "35": lambda: dump_to_desktop("processes.txt", run("tasklist /v")),
            "36": lambda: dump_to_desktop("startup.txt",
                              run("reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run") + "\n" +
                              run("reg query HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run")),
            "37": lambda: dump_to_desktop("network.txt", run("netstat -ano")),
            "38": file_search,
            "39": reg_search,
            "40": lambda: subprocess.Popen("cleanmgr"),
            "0":  sys.exit,
        }

        action = num_actions.get(choice)
        if action:
            action()
        else:
            warn("Invalid choice.")
            input("  Press Enter to continue...")

# ── Entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not is_admin():
        relaunch_as_admin()
    menu()
