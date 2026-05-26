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
from datetime import datetime

# ── Admin check ───────────────────────────────────────────────────────────────

def is_admin():
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

APPDATA      = os.environ.get("APPDATA", "")
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
TEMP         = os.environ.get("TEMP", "")
USERPROFILE  = os.environ.get("USERPROFILE", "")
MINECRAFT    = os.path.join(APPDATA, ".minecraft")
PROGRAMDATA  = os.environ.get("PROGRAMDATA", "C:\\ProgramData")
DOWNLOADS    = os.path.join(LOCALAPPDATA, "ChichoSSHelper")

OCEAN_API_BASE = "https://anticheat.ac/api/pins"

CHEAT_CLIENTS = [
    "Wurst", "Impact", "Meteor", "Aristois", "Liquidbounce", "Sigma",
    "Ares", "Future", "Vape", "Astolfo", "Drip", "Salhack", "Entropy",
    "Inertia", "Raven", "Novoline", "Wolfram", "PyroHax", "Rekt",
    "Remix", "XRay", "Horion", "Phi", "Hybrid", "Rusher", "cyemer",
    "Prestige", "velaris", "bleach", "vapor", "dusk", "azura", "vertex",
    "nexus", "rise", "lucid", "ketamine", "reflex", "exodus"
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
    if not found_any:
        info("No known cheat client folders found.")
    info("Scanning for .jar files in AppData...")
    out = run(f'dir "{APPDATA}" /s /b *.jar 2>nul')
    for line in out.splitlines():
        if ".minecraft" not in line.lower():
            warn(f"JAR outside .minecraft: {line}")
    info("Scanning for .dll files with suspicious names...")
    out = run(f'dir "{APPDATA}" /s /b *.dll 2>nul')
    for line in out.splitlines():
        if any(s in line.lower() for s in ["inject","hook","cheat"]):
            warn(f"Suspicious DLL: {line}")
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
                # Flag if java path is not in Program Files
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

    if not found_any:
        info("No suspicious cheat folders found in common locations.")
    pause()


# ── Ocean API (fixed) ─────────────────────────────────────────────────────────

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

    # ── Summary ──────────────────────────────────────────────────────────────
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


# ── Browser Forensics (new) ───────────────────────────────────────────────────

BROWSER_PROFILES = {
    "Chrome":  os.path.join(LOCALAPPDATA, r"Google\Chrome\User Data"),
    "Edge":    os.path.join(LOCALAPPDATA, r"Microsoft\Edge\User Data"),
    "Brave":   os.path.join(LOCALAPPDATA, r"BraveSoftware\Brave-Browser\User Data"),
    "Opera":   os.path.join(APPDATA,      r"Opera Software\Opera Stable"),
    "Vivaldi": os.path.join(LOCALAPPDATA, r"Vivaldi\User Data"),
}

FIREFOX_ROOT = os.path.join(APPDATA, r"Mozilla\Firefox\Profiles")


def _chromium_db_copy(db_path):
    """Copy a locked Chromium SQLite db to temp so we can read it."""
    tmp = tempfile.mktemp(suffix=".db")
    shutil.copy2(db_path, tmp)
    return tmp


def _chromium_profiles(browser_root):
    """Return list of profile folders inside a Chromium user data dir."""
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

    # Firefox
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

                    # Flag suspicious extensions
                    ext = os.path.splitext(fname)[1].lower()
                    flagged = ext in [".jar", ".exe", ".dll", ".bat", ".ps1", ".vbs", ".zip"]
                    flag_str = " \033[93m<< SUSPICIOUS EXT\033[0m" if flagged else ""

                    print(f"      [{ts}] {exists} {fname} ({size_kb} KB){flag_str}")
                    print(f"               From: {(tab_url or '')[:100]}")
                    if not still_on:
                        print(f"               Path was: {target}")
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
                # Profile folder exists but no History file — wiped
                warn(f"{browser} [{os.path.basename(profile)}]: History file MISSING — likely wiped!")
                suspicious_found = True
                continue

            # Check if history DB is suspiciously small or empty
            size = os.path.getsize(hist_db)
            if size < 40960:  # under 40 KB is almost certainly freshly cleared
                warn(f"{browser} [{os.path.basename(profile)}]: History DB is very small ({size} bytes) — possibly cleared recently")
                suspicious_found = True

            # Check row count
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

    # Check for CCleaner / BleachBit which are commonly used to wipe
    info("\nChecking for known wipe tools...")
    wipe_tools = ["CCleaner", "BleachBit", "Eraser", "PrivaZer", "Wise Disk Cleaner"]
    for tool in wipe_tools:
        for base in [APPDATA, LOCALAPPDATA,
                     os.environ.get("PROGRAMFILES","C:\\Program Files"),
                     os.environ.get("PROGRAMFILES(X86)","C:\\Program Files (x86)")]:
            if os.path.exists(os.path.join(base, tool)):
                warn(f"Wipe tool found: {tool} in {base}")
                suspicious_found = True

    # Check prefetch for wipe tools
    pf_out = run("dir C:\\Windows\\Prefetch /b *.pf 2>nul").lower()
    for tool in ["ccleaner", "bleachbit", "privazer", "eraser"]:
        if tool in pf_out:
            warn(f"Prefetch entry for wipe tool: {tool} — was recently run!")
            suspicious_found = True

    # Check event log for cleared history (Event ID 4663 file delete on history paths is complex,
    # simpler: just check if Windows.old or shadow copies exist and were deleted)
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
                    # Flag known cheat/crack sites
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


def menu_browser_forensics():
    while True:
        clear()
        header("Browser Forensics")
        print("  [1]  History Viewer            — last 50 visited URLs per browser")
        print("  [2]  Downloads Viewer          — all downloads, flags deleted files")
        print("  [3]  Cache / History Wipe Check — detect if they cleared their browser")
        print("  [4]  Cookie Domain Viewer      — sites visited (even if history cleared)")
        print("  [5]  Browser history paths     — open raw folder locations")
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
            print("  " + out.replace("\n", "\n  "))
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
                "bleach","vapor","dusk","ccleaner","bleachbit"]
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
            if os.path.exists(os.path.join(base, client)):
                found(f"{client} in {base}")
    info("[2/11] Java processes...")
    print(run("tasklist /fi \"imagename eq javaw.exe\""))
    info("[2a/11] Java injection module scan...")
    scan_java_injection()
    info("[3/11] Suspicious processes...")
    all_procs = run("tasklist").lower()
    for s in SUSPICIOUS_PROCS:
        if s in all_procs:
            found(f"Process: {s}")
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
        if any(k in line.lower() for k in ["cheat","inject","wurst","sigma","vape","ccleaner","bleachbit"]):
            found(f"Prefetch: {line}")
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
            elif os.path.getsize(hist_db) < 40960:
                warn(f"{browser} history DB suspiciously small — possibly cleared!")
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
        if any(k in line.lower() for k in ["cheat","inject","wurst","sigma","vape"]):
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
    all_procs = run("tasklist").lower()
    for m in ["ahk", "autohotkey", "ghub", "synapse", "icue", "joytokey", "tinytask"]:
        if m in all_procs:
            found(f"Running process contains: {m}")
            found_any = True
    if not found_any:
        info("No macro software detected.")
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

# ── helpers ───────────────────────────────────────────────────────────────────

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
        print("  [J]  HWID Extractor   (dump hardware IDs to file)")
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
            # Browser forensics
            "BF": menu_browser_forensics,
            # Chicho sections
            "A":  menu_manual_tools,
            "B":  menu_recovery_tools,
            "C":  menu_explorer,
            "D":  menu_usn_journal,
            "E":  menu_commands,
            "F":  menu_regedit,
            "G":  menu_eventviewer,
            "H":  check_macros,
            "I":  check_recording_software,
            "J":  hwid_extractor,
            # Manual openers
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
