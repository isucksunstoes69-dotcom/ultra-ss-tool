import os
import sys
import subprocess
import ctypes
import urllib.request
import zipfile
import shutil
import json
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
DOWNLOADS    = os.path.join(USERPROFILE, "AppData", "Local", "SSHelper")
OCEAN_API_BASE = "https://anticheat.ac/api/pins"

CHEAT_CLIENTS = [
    "Wurst", "Impact", "Meteor", "Aristois", "Liquidbounce", "Sigma",
    "Ares", "Future", "Vape", "Astolfo", "Drip", "Salhack", "Entropy",
    "Inertia", "Raven", "Novoline", "Wolfram", "PyroHax", "Rekt",
    "Remix", "XRay", "Horion", "Phi", "Hybrid", "Rusher", "cyemer",
    "Prestige", "velaris",
    # Extended
    "Reflex", "Atomic", "Dimension", "Vertex", "Flux", "Tenacity",
    "Crypt", "Praxis", "Hexed", "Emerald", "Autumn", "Serenity",
    "XCarbon", "3arthh4ck", "Quantic", "Oringo", "ForgeHax",
    "Omikron", "Zenith", "BleachHack", "GhostClient", "Skidware",
    "killaura", "autoclick", "ScaffoldBot", "AntiAFK",
    "Stealhack", "Kami", "Rusherhack", "Novoline", "ErisClient",
    "Rise", "Moon", "SquadHack", "Zenia", "Polar", "Abyss",
]

SUSPICIOUS_PROCS = [
    "cheat", "hack", "inject", "ghost", "vape", "sigma",
    "future", "meteor", "wurst", "aristois", "payload", "rat",
    "keylog", "prestige", "flux", "tenacity", "reflex", "crypt",
    "anydesk", "teamviewer", "ammyy", "supremo", "ultraviewer",
    "remotedesktop", "rustdesk", "dwservice", "connectwise",
    "autoclick", "killaura", "scaffoldbot", "parsec",
]

SUSPICIOUS_INJECTION_MODULES = [
    "inject", "hook", "cheat", "vape", "sigma",
    "future", "meteor", "wurst", "aristois", "payload",
]

REMOTE_ACCESS_TOOLS = [
    ("AnyDesk",        ["AnyDesk"],                       ["anydesk.exe"]),
    ("TeamViewer",     ["TeamViewer"],                    ["TeamViewer.exe", "TeamViewer_Service.exe"]),
    ("Ammyy Admin",    ["Ammyy"],                         ["AA_v3.exe"]),
    ("Supremo",        ["Supremo"],                       ["Supremo.exe"]),
    ("UltraViewer",    ["UltraViewer"],                   ["UltraViewer_Desktop.exe"]),
    ("RustDesk",       ["RustDesk"],                      ["rustdesk.exe"]),
    ("DWService",      ["dwagent", "DWAgent"],            ["dwagent.exe"]),
    ("Parsec",         ["Parsec"],                        ["parsecd.exe"]),
    ("NoMachine",      ["NoMachine"],                     ["nxd.exe"]),
    ("ConnectWise",    ["ConnectWise", "ScreenConnect"],  ["ScreenConnect.ClientService.exe"]),
    ("Splashtop",      ["Splashtop"],                     ["SRService.exe"]),
    ("Chrome Remote",  ["Chrome Remote Desktop"],         ["remoting_host.exe"]),
    ("Zoho Assist",    ["ZohoAssist"],                    ["ZohoMeeting.exe"]),
    ("AeroAdmin",      ["AeroAdmin"],                     ["AeroAdmin.exe"]),
    ("ISL Online",     ["ISL Online"],                    ["ISLLight.exe"]),
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
        if any(s in line.lower() for s in ["inject", "hook", "cheat"]):
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
    info("Checking latest.log for suspicious keywords...")
    log = os.path.join(MINECRAFT, "logs", "latest.log")
    if os.path.exists(log):
        with open(log, "r", errors="ignore") as f:
            for line in f:
                if any(k in line.lower() for k in ["cheat", "inject", "wurst", "sigma", "vape"]):
                    warn(f"Suspicious log entry: {line.strip()}")
    else:
        info("No latest.log found.")
    pause()


def find_launcher_paths(name):
    candidates = []
    if name == "norisk":
        candidates = [os.path.join(LOCALAPPDATA, "norisk"), os.path.join(APPDATA, "norisk")]
    elif name == "prism":
        candidates = [os.path.join(APPDATA, "prism-launcher"), os.path.join(APPDATA, "Prism Launcher"),
                      os.path.join(LOCALAPPDATA, "Programs", "Prism Launcher")]
    elif name == "lunar":
        candidates = [os.path.join(USERPROFILE, ".lunarclient", "profiles"),
                      os.path.join(USERPROFILE, ".lunarclient"), os.path.join(APPDATA, "LunarClient"),
                      os.path.join(LOCALAPPDATA, "Programs", "Lunar Client")]
    elif name == "feather":
        candidates = [os.path.join(APPDATA, "feather"), os.path.join(APPDATA, "FeatherClient"),
                      os.path.join(LOCALAPPDATA, "Programs", "Feather")]
    elif name == "modrinth":
        candidates = [os.path.join(APPDATA, "ModrinthApp", "profiles"), os.path.join(APPDATA, "ModrinthApp"),
                      os.path.join(LOCALAPPDATA, "ModrinthApp"), os.path.join(LOCALAPPDATA, "Programs", "Modrinth")]
    elif name == "curseforge":
        candidates = [os.path.join(APPDATA, "CurseForge"), os.path.join(LOCALAPPDATA, "CurseForge"),
                      os.path.join(APPDATA, "Overwolf", "CurseForge")]
    elif name == ".minecraft":
        candidates = [os.path.join(MINECRAFT, "mods")]
    return [p for p in candidates if os.path.exists(p)]


def scan_launcher_mods():
    clear()
    header("Minecraft Launcher / Mods Reader")
    print("  [1] norisk")
    print("  [2] prism")
    print("  [3] lunar")
    print("  [4] feather")
    print("  [5] modrinth")
    print("  [6] curseforge")
    print("  [7] .minecraft mods")
    print("  [0] Return to menu")
    print()
    choice = input("  Launcher choice: ").strip()
    mapping = {"1": "norisk", "2": "prism", "3": "lunar", "4": "feather",
               "5": "modrinth", "6": "curseforge", "7": ".minecraft"}
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
    lines = [f"Launcher scan: {launcher}", f"Path: {selected_path}",
             f"Found {len(matches)} mod / metadata files", ""]
    lines.extend(matches if matches else ["No mod or launcher metadata files found."])
    filename = f"launcher_mods_{launcher}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    dump_to_downloads(filename, "\n".join(lines))


def check_minecraft_launchers():
    clear()
    header("Minecraft Launcher / Profile Scanner")
    launchers = ["norisk", "prism", "lunar", "feather", "modrinth", "curseforge", ".minecraft"]
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
    flagged = False
    for line in out.splitlines():
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
        APPDATA, LOCALAPPDATA,
        os.path.join(USERPROFILE, "Downloads"),
        os.path.join(USERPROFILE, "Desktop"),
        os.environ.get("PROGRAMFILES", "C:\\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
        os.path.join(USERPROFILE, ".minecraft"),
    ]
    extra_names = ["badlion", "impact", "salhack", "liquidbounce", "disabler",
                   "meteor", "exploit", "payload", "reflex", "flux", "tenacity",
                   "crypt", "praxis", "hexed", "rise", "moon", "zenith"]
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


def check_ocean_api():
    clear()
    header("Ocean Anti-Cheat API Lookup")
    pin = input("  Enter Ocean pin: ").strip()
    if not pin:
        warn("No pin entered.")
        pause()
        return
    url = f"{OCEAN_API_BASE}/{pin}"
    info(f"Querying Ocean API for pin {pin}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            data = json.loads(raw)
    except Exception as e:
        warn(f"Ocean API request failed: {e}")
        pause()
        return
    if not isinstance(data, dict) or "result" not in data:
        warn("Ocean API returned invalid data.")
        pause()
        return
    print()
    print(f"  Game: {data.get('pin_type','N/A')}")
    print(f"  Scan Time: {data.get('scantime','N/A')}")
    print(f"  Pin: {data.get('pin','N/A')}")
    print(f"  Country: {data.get('country','N/A')}")
    print(f"  Sentence: {data.get('result','N/A')}")

    def _print_list(field_name, label):
        print(f"\n{label}:")
        raw_value = data.get(field_name, "[]")
        if isinstance(raw_value, str):
            try:
                entries = json.loads(raw_value.replace("'", '"'))
            except:
                entries = [raw_value]
        else:
            entries = raw_value
        if not entries:
            print("    None")
            return
        for item in entries:
            print(f"    {item}")

    _print_list("detects", "Detections")
    _print_list("warnings", "Warnings")
    _print_list("suspicious", "Suspicious Files")
    _print_list("execlist", "Exec List")
    pause()

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
    keywords = ["java", "cheat", "inject", "hack", "wurst", "sigma", "vape", "rat",
                "anydesk", "teamviewer", "reflex", "flux", "tenacity", "luyten", "recaf"]
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
            if any(k in line.lower() for k in ["virtual", "vpn", "tap", "tunnel", "hyper-v", "hamachi"]):
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

# ── NEW CHECKS ────────────────────────────────────────────────────────────────

def check_remote_access():
    clear()
    header("Remote Access / Cheat-Assist Tool Detection")
    all_procs = run("tasklist").lower()
    found_any = False

    for name, folders, procs in REMOTE_ACCESS_TOOLS:
        folder_hit = any(
            os.path.exists(os.path.join(base, f))
            for f in folders
            for base in [APPDATA, LOCALAPPDATA,
                         os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                         os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")]
        )
        proc_hit = any(p.lower() in all_procs for p in procs)
        if folder_hit or proc_hit:
            status = []
            if folder_hit: status.append("installed")
            if proc_hit:   status.append("RUNNING")
            found(f"{name}  →  {', '.join(status)}")
            found_any = True
        else:
            info(f"{name}: not found")

    pause()


def check_bam():
    clear()
    header("BAM — Background Activity Monitor (Recently Executed Programs)")
    info("BAM tracks recently run executables — survives deletion and reboots.")
    bam_base = r"SYSTEM\CurrentControlSet\Services\bam\State\UserSettings"
    out = run(f'reg query "HKLM\\{bam_base}" /s')
    if not out:
        warn("BAM key not found or access denied (requires admin).")
        pause()
        return

    keywords = [
        "cheat", "hack", "inject", "wurst", "sigma", "vape", "future",
        "meteor", "aristois", "payload", "rat", "anydesk", "teamviewer",
        "reflex", "flux", "killaura", "autoclick", "ghost", "prestige",
        "luyten", "recaf", "jd-gui", "bytecode",
    ]

    info("Flagged BAM entries:")
    flagged = False
    for line in out.splitlines():
        lower = line.lower()
        if r"\device\harddiskvolume" in lower:
            if any(k in lower for k in keywords):
                found(line.strip())
                flagged = True
    if not flagged:
        info("No suspicious BAM entries found.")

    info("\nAll BAM executable entries:")
    for line in out.splitlines():
        if r"\device\harddiskvolume" in line.lower():
            print(f"  {line.strip()}")
    pause()


def check_shellbags():
    clear()
    header("ShellBags — Explorer Folder History")
    info("ShellBags record folders a user opened in Explorer — even renamed/deleted ones.")
    info("Text-scanning registry for suspicious folder name clues...")

    sb_keys = [
        r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\BagMRU",
        r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\Bags",
        r"HKCU\Software\Microsoft\Windows\Shell\BagMRU",
        r"HKCU\Software\Microsoft\Windows\Shell\Bags",
    ]
    keywords = [
        "cheat", "hack", "inject", "wurst", "sigma", "vape", "future",
        "meteor", "aristois", "payload", "rat", "reflex", "flux", "ghost",
        "killaura", "autoclick", "luyten", "recaf",
    ]
    found_any = False
    for key in sb_keys:
        out = run(f'reg query "{key}" /s')
        for line in out.splitlines():
            if any(k in line.lower() for k in keywords):
                found(line.strip())
                found_any = True
    if not found_any:
        info("No suspicious folder names found in ShellBags (text pass).")
    info("For full ShellBags analysis: use SBV in Manual Tools to launch ShellBagsView.")
    pause()


def check_muicache():
    clear()
    header("MUICache — Programs Run (by display name, survives uninstall)")
    info("MUICache stores the display name of every EXE ever run on this account.")
    key = r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"
    out = run(f'reg query "{key}"')
    keywords = [
        "cheat", "hack", "inject", "wurst", "sigma", "vape", "future",
        "meteor", "aristois", "payload", "rat", "anydesk", "teamviewer",
        "reflex", "flux", "killaura", "autoclick", "ghost", "prestige",
        "luyten", "recaf", "decompil", "jd-gui", "bytecode",
    ]
    info("Flagged MUICache entries:")
    flagged = False
    for line in out.splitlines():
        if any(k in line.lower() for k in keywords):
            found(line.strip())
            flagged = True
    if not flagged:
        info("No suspicious MUICache entries.")
    info("\nAll MUICache entries:")
    print(out)
    pause()


def check_ps_history():
    clear()
    header("PowerShell Command History")
    hist_path = os.path.join(APPDATA,
        r"Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt")
    if not os.path.exists(hist_path):
        info("No PowerShell history file found.")
        pause()
        return
    info(f"Reading: {hist_path}")
    keywords = [
        "cheat", "inject", "wurst", "sigma", "vape", "del ", "rd /", "rmdir",
        "format", "clear-", "bypass", "download", "invoke-webrequest", "iwr ",
        "curl ", "wget ", "base64", "anydesk", "teamviewer", "remove-item",
    ]
    with open(hist_path, "r", errors="ignore") as f:
        lines = f.readlines()
    info("Flagged commands:")
    flagged = False
    for line in lines:
        if any(k in line.lower() for k in keywords):
            found(line.strip())
            flagged = True
    if not flagged:
        info("Nothing suspicious flagged.")
    info("\nFull history:")
    print("".join(lines))
    pause()


def check_clipboard():
    clear()
    header("Clipboard History Artifacts")
    clip_base = os.path.join(LOCALAPPDATA, "Microsoft", "Windows", "Clipboard")
    if os.path.exists(clip_base):
        info(f"Clipboard folder found: {clip_base}")
        for root, dirs, files in os.walk(clip_base):
            for f in files:
                full = os.path.join(root, f)
                info(f"  {full}  ({os.path.getsize(full)} bytes)")
        info("Opening clipboard folder in Explorer...")
        subprocess.Popen(f'explorer "{clip_base}"')
    else:
        info("No Clipboard history folder found (feature may be disabled or cleared).")
    pause()


def check_decompilers():
    clear()
    header("JAR Decompiler / Bytecode Tool Detection")
    info("These tools suggest the player may have been inspecting or modifying JAR files.")
    decompilers = [
        ("Luyten",          ["luyten", "Luyten"]),
        ("Recaf",           ["recaf", "Recaf"]),
        ("JD-GUI",          ["jd-gui", "JD-GUI"]),
        ("Bytecode Viewer", ["BytecodeViewer", "bytecode-viewer"]),
        ("CFR",             ["cfr"]),
        ("Fernflower",      ["fernflower"]),
        ("Vineflower",      ["vineflower"]),
        ("jadx",            ["jadx"]),
    ]
    search_bases = [
        APPDATA, LOCALAPPDATA,
        os.path.join(USERPROFILE, "Downloads"),
        os.path.join(USERPROFILE, "Desktop"),
        os.path.join(USERPROFILE, "Documents"),
        os.environ.get("PROGRAMFILES", "C:\\Program Files"),
    ]
    found_any = False
    for name, folders in decompilers:
        for f in folders:
            for base in search_bases:
                path = os.path.join(base, f)
                if os.path.exists(path):
                    found(f"{name}  →  {path}")
                    found_any = True

    info("Scanning AppData for decompiler JARs...")
    decompiler_jar_keys = ["recaf", "jd-gui", "bytecodeviewer", "fernflower",
                           "vineflower", "cfr", "jadx", "luyten"]
    for base in [APPDATA, LOCALAPPDATA]:
        jar_scan = run(f'dir "{base}" /s /b *.jar 2>nul')
        for line in jar_scan.splitlines():
            if any(k in line.lower() for k in decompiler_jar_keys):
                found(f"Decompiler JAR: {line}")
                found_any = True

    if not found_any:
        info("No decompiler tools detected.")
    pause()


def check_ghost_artifacts():
    clear()
    header("Ghost Client & Injection Artifact Scanner")
    ghost_paths = [
        os.path.join(APPDATA, ".vape"),
        os.path.join(APPDATA, "Vape"),
        os.path.join(APPDATA, ".vape.encrypted"),
        os.path.join(APPDATA, "ghost"),
        os.path.join(APPDATA, ".ghost"),
        os.path.join(APPDATA, "Flux"),
        os.path.join(APPDATA, ".flux"),
        os.path.join(APPDATA, "Reflex"),
        os.path.join(APPDATA, "Tenacity"),
        os.path.join(APPDATA, "Rise"),
        os.path.join(APPDATA, ".rise"),
        os.path.join(APPDATA, "Moon"),
        os.path.join(APPDATA, "Crypt"),
        os.path.join(APPDATA, "Praxis"),
        os.path.join(APPDATA, "Hexed"),
        os.path.join(APPDATA, "Zenith"),
        os.path.join(LOCALAPPDATA, "Temp", "inject"),
        os.path.join(LOCALAPPDATA, "Temp", "payload"),
        os.path.join(USERPROFILE, ".crypt"),
        os.path.join(USERPROFILE, ".praxis"),
        os.path.join(USERPROFILE, ".hexed"),
    ]
    found_any = False
    for path in ghost_paths:
        if os.path.exists(path):
            found(f"Ghost artifact: {path}")
            found_any = True

    info("Scanning Temp for injection artifacts...")
    inject_keys = ["inject", "hook", "payload", "ghost", "vape", "cheat", "sigma", "flux"]
    for ext in ["*.dll", "*.exe", "*.jar", "*.bat", "*.vbs", "*.ps1"]:
        out = run(f'dir "{TEMP}" /s /b {ext} 2>nul')
        for line in out.splitlines():
            if any(k in line.lower() for k in inject_keys):
                found(f"Suspicious temp file: {line}")
                found_any = True

    info("Scanning for .agent / javaagent files...")
    for base in [APPDATA, LOCALAPPDATA, MINECRAFT, TEMP]:
        if not os.path.exists(base):
            continue
        out = run(f'dir "{base}" /s /b *.agent 2>nul')
        for line in out.splitlines():
            found(f"Agent file: {line}")
            found_any = True

    if not found_any:
        info("No ghost client artifacts found.")
    pause()


def check_discord():
    clear()
    header("Discord Artifact & Inject Check")
    discord_base = os.path.join(APPDATA, "discord")
    if os.path.exists(discord_base):
        found(f"Discord AppData: {discord_base}")
        inject_keywords = ["inject", "cheat", "hook", "vape", "sigma"]
        for root, _, files in os.walk(discord_base):
            for f in files:
                if any(k in f.lower() for k in inject_keywords):
                    found(f"Suspicious Discord file: {os.path.join(root, f)}")
    else:
        info("Discord AppData folder not found.")

    bd_path = os.path.join(APPDATA, "BetterDiscord")
    if os.path.exists(bd_path):
        warn(f"BetterDiscord found: {bd_path}")
        plugins = os.path.join(bd_path, "data", "stable", "plugins")
        if os.path.exists(plugins):
            for f in os.listdir(plugins):
                print(f"  Plugin: {f}")
    else:
        info("BetterDiscord: not found")

    info("Checking Discord process for injected modules...")
    out = run('tasklist /m /fi "imagename eq Discord.exe"')
    for line in out.splitlines():
        if any(k in line.lower() for k in ["inject", "hook", "cheat", "payload"]):
            found(f"Suspicious module in Discord: {line.strip()}")
    pause()


def check_autorun_enhanced():
    clear()
    header("Enhanced Autorun / Persistence Check")
    persistence_keys = [
        (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",          "HKCU Run"),
        (r"HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce",      "HKCU RunOnce"),
        (r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",          "HKLM Run"),
        (r"HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce",      "HKLM RunOnce"),
        (r"HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon",  "Winlogon"),
        (r"HKCU\Software\Microsoft\Windows NT\CurrentVersion\Windows",   "HKCU Windows Load"),
        (r"HKCU\Environment",                                            "User Environment"),
    ]
    cheat_keywords = ["inject", "cheat", "wurst", "sigma", "vape", "rat",
                      "anydesk", "teamviewer", "payload", "hook", "ghost"]
    for key, label in persistence_keys:
        out = run(f'reg query "{key}"')
        flagged_lines = [l.strip() for l in out.splitlines()
                         if any(k in l.lower() for k in cheat_keywords)]
        if flagged_lines:
            for fl in flagged_lines:
                found(f"[{label}] {fl}")
        else:
            info(f"{label}: clean")

    startup = os.path.join(APPDATA, r"Microsoft\Windows\Start Menu\Programs\Startup")
    info(f"\nStartup folder: {startup}")
    if os.path.exists(startup):
        files = os.listdir(startup)
        if files:
            for f in files:
                print(f"  {f}")
        else:
            print("  Empty.")
    pause()


def check_userassist():
    clear()
    header("UserAssist — GUI Programs Launched (with timestamps)")
    info("UserAssist records every GUI program run via Explorer, with run count and last run time.")
    info("Values are ROT-13 encoded — use UserAssistView (NirSoft) for decoded output.")
    key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"
    out = run(f'reg query "{key}" /s')

    keywords = [
        "cheat", "hack", "inject", "wurst", "sigma", "vape", "future",
        "meteor", "aristois", "payload", "rat", "anydesk", "teamviewer",
        "reflex", "flux", "killaura", "autoclick", "ghost", "prestige",
        "luyten", "recaf", "jd-gui", "bytecode",
    ]
    info("Flagged UserAssist entries (ROT-13 decoded inline):")
    import codecs
    flagged = False
    for line in out.splitlines():
        try:
            decoded = codecs.decode(line, "rot_13")
        except:
            decoded = line
        if any(k in decoded.lower() for k in keywords):
            found(f"{line.strip()}  →  {decoded.strip()}")
            flagged = True
    if not flagged:
        info("No suspicious entries found (ROT-13 pass).")
    info("\nRaw UserAssist output:")
    print(out)
    pause()


def check_typed_paths():
    clear()
    header("TypedPaths — Paths Typed into Explorer Address Bar")
    key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths"
    out = run(f'reg query "{key}"')
    info("All typed paths:")
    print(out if out else "  (none found)")
    pause()


def check_run_mru():
    clear()
    header("RunMRU — Commands Run via Win+R")
    key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"
    out = run(f'reg query "{key}"')
    info("All Win+R commands:")
    print(out if out else "  (none found)")
    pause()


def check_deleted_recently():
    clear()
    header("Recycle Bin Contents")
    info("Checking Recycle Bin on all drives...")
    for drive in ["C", "D", "E"]:
        rb = f"{drive}:\\$Recycle.Bin"
        if os.path.exists(rb):
            info(f"Drive {drive}: Recycle Bin found")
            try:
                out = run(f'dir "{rb}" /s /b /a 2>nul')
                if out:
                    for line in out.splitlines()[:50]:
                        print(f"  {line}")
                else:
                    print("  (empty or access denied)")
            except:
                print("  (access denied)")
    pause()


def check_event_log_cleared():
    clear()
    header("Event Log Cleared / Tampered Check")
    info("Checking if security/system logs were recently cleared (a red flag)...")
    cmds = [
        ("Security log cleared (1102)", 'wevtutil qe Security /q:"*[System[EventID=1102]]" /f:text /c:10'),
        ("System log cleared (104)",    'wevtutil qe System /q:"*[System[EventID=104]]" /f:text /c:10'),
        ("Audit policy changed (4719)", 'wevtutil qe Security /q:"*[System[EventID=4719]]" /f:text /c:10'),
    ]
    found_any = False
    for label, cmd in cmds:
        out = run(cmd)
        if out and "Event[" in out:
            found(f"{label}:\n{out}")
            found_any = True
        else:
            info(f"{label}: no events found")
    if not found_any:
        info("No log-clearing events detected.")
    pause()


# ── Full scan ─────────────────────────────────────────────────────────────────

def full_scan():
    clear()
    header("Full Auto Scan")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info(f"Scan started at {now}")
    print()
    info("[1/15] AppData cheat folders...")
    for client in CHEAT_CLIENTS:
        for base in [APPDATA, LOCALAPPDATA]:
            if os.path.exists(os.path.join(base, client)):
                found(f"{client} in {base}")
    info("[2/15] Java processes...")
    print(run("tasklist /fi \"imagename eq javaw.exe\""))
    info("[2a/15] Java injection module scan...")
    scan_java_injection()
    info("[3/15] Suspicious processes...")
    all_procs = run("tasklist").lower()
    for s in SUSPICIOUS_PROCS:
        if s in all_procs:
            found(f"Process: {s}")
    info("[4/15] .minecraft mods...")
    mods = os.path.join(MINECRAFT, "mods")
    if os.path.exists(mods):
        files = os.listdir(mods)
        print("  " + "\n  ".join(files) if files else "  Empty.")
    else:
        info("No mods folder.")
    info("[5/15] Startup entries...")
    print(run("reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"))
    info("[6/15] Temp executables...")
    for ext in ["*.exe", "*.jar"]:
        out = run(f'dir "{TEMP}" /b {ext} 2>nul')
        if out:
            warn(f"{ext} in temp: {out}")
    info("[7/15] Hosts file...")
    hosts = r"C:\Windows\System32\drivers\etc\hosts"
    if os.path.exists(hosts):
        with open(hosts) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    print(f"  {line.strip()}")
    info("[8/15] Prefetch suspicious names...")
    out = run("dir C:\\Windows\\Prefetch /od /b *.pf")
    for line in out.splitlines():
        if any(k in line.lower() for k in ["cheat", "inject", "wurst", "sigma", "vape",
                                            "anydesk", "teamviewer", "reflex", "luyten"]):
            found(f"Prefetch: {line}")
    info("[9/15] Scheduled tasks...")
    out = run("schtasks /query /fo LIST")
    for line in out.splitlines():
        if "Task Name:" in line:
            print(f"  {line.strip()}")
    info("[10/15] VPN/virtual adapters...")
    out = run("ipconfig /all")
    for line in out.splitlines():
        if "description" in line.lower():
            if any(k in line.lower() for k in ["virtual", "vpn", "tap", "tunnel", "hamachi"]):
                found(line.strip())
    info("[11/15] Remote access tools...")
    all_procs2 = run("tasklist").lower()
    for name, folders, procs in REMOTE_ACCESS_TOOLS:
        folder_hit = any(os.path.exists(os.path.join(base, f))
                         for f in folders
                         for base in [APPDATA, LOCALAPPDATA,
                                      os.environ.get("PROGRAMFILES", "C:\\Program Files")])
        proc_hit = any(p.lower() in all_procs2 for p in procs)
        if folder_hit or proc_hit:
            found(f"Remote access: {name} ({'installed' if folder_hit else ''} {'RUNNING' if proc_hit else ''})")
    info("[12/15] BAM recently executed programs...")
    bam_out = run(r'reg query "HKLM\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings" /s')
    bam_keys = ["cheat", "vape", "sigma", "inject", "anydesk", "teamviewer", "luyten", "ghost"]
    for line in bam_out.splitlines():
        if r"\device\harddiskvolume" in line.lower():
            if any(k in line.lower() for k in bam_keys):
                found(f"BAM: {line.strip()}")
    info("[13/15] MUICache programs run...")
    mui_out = run(r'reg query "HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"')
    mui_keys = ["cheat", "inject", "vape", "sigma", "anydesk", "teamviewer", "luyten", "recaf"]
    for line in mui_out.splitlines():
        if any(k in line.lower() for k in mui_keys):
            found(f"MUICache: {line.strip()}")
    info("[14/15] Ghost client artifacts...")
    ghost_paths_quick = [
        os.path.join(APPDATA, ".vape"), os.path.join(APPDATA, "Vape"),
        os.path.join(APPDATA, "Flux"), os.path.join(APPDATA, "Reflex"),
        os.path.join(APPDATA, "Tenacity"), os.path.join(APPDATA, "ghost"),
    ]
    for gp in ghost_paths_quick:
        if os.path.exists(gp):
            found(f"Ghost artifact: {gp}")
    info("[15/15] PowerShell history...")
    hist = os.path.join(APPDATA, r"Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt")
    if os.path.exists(hist):
        with open(hist, "r", errors="ignore") as f:
            for line in f:
                if any(k in line.lower() for k in ["anydesk", "inject", "cheat", "base64", "bypass"]):
                    found(f"PS History: {line.strip()}")
    print()
    info(f"Scan complete — {datetime.now().strftime('%H:%M:%S')}")
    pause()


def save_full_scan_report():
    clear()
    header("Save Full Scan Report")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = ["SS HELPER REPORT", f"Scan started at {now}", "", "[1] AppData cheat folders"]
    for client in CHEAT_CLIENTS:
        for base in [APPDATA, LOCALAPPDATA]:
            path = os.path.join(base, client)
            if os.path.exists(path):
                lines.append(f"FOUND: {client} in {path}")
    lines.extend(["", "[2] Java processes",
                  run("tasklist /fi \"imagename eq javaw.exe\""),
                  run("tasklist /fi \"imagename eq java.exe\""),
                  "", "[2a] Java injection modules",
                  run("tasklist /m /fi \"imagename eq javaw.exe\""),
                  run("tasklist /m /fi \"imagename eq java.exe\""),
                  "", "[3] Suspicious processes"])
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
    lines.extend(["", "[5] Startup entries",
                  run("reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
                  run("reg query HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
                  "", "[6] Temp executables"])
    for ext in ["*.exe", "*.jar"]:
        out = run(f'dir "{TEMP}" /b {ext} 2>nul')
        if out:
            lines.append(f"{ext}: {out}")
    lines.extend(["", "[7] Hosts file"])
    hosts = r"C:\Windows\System32\drivers\etc\hosts"
    if os.path.exists(hosts):
        with open(hosts, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    lines.append(line)
    lines.extend(["", "[8] Prefetch suspicious names"])
    out = run("dir C:\\Windows\\Prefetch /od /b *.pf")
    for line in out.splitlines():
        if any(k in line.lower() for k in ["cheat", "inject", "wurst", "sigma", "vape",
                                            "anydesk", "teamviewer", "luyten"]):
            lines.append(line)
    lines.extend(["", "[9] Scheduled tasks", run("schtasks /query /fo LIST"),
                  "", "[10] VPN/virtual adapters", run("ipconfig /all"),
                  "", "[11] Remote access tools"])
    all_procs2 = run("tasklist").lower()
    for name, folders, procs in REMOTE_ACCESS_TOOLS:
        folder_hit = any(os.path.exists(os.path.join(base, f))
                         for f in folders
                         for base in [APPDATA, LOCALAPPDATA,
                                      os.environ.get("PROGRAMFILES", "C:\\Program Files")])
        proc_hit = any(p.lower() in all_procs2 for p in procs)
        if folder_hit or proc_hit:
            lines.append(f"FOUND: {name} ({'installed' if folder_hit else ''} {'RUNNING' if proc_hit else ''})")
    lines.extend(["", "[12] BAM recently executed",
                  run(r'reg query "HKLM\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings" /s'),
                  "", "[13] MUICache",
                  run(r'reg query "HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"'),
                  "", "[14] UserAssist",
                  run(r'reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist" /s'),
                  "", "[15] PowerShell history"])
    hist = os.path.join(APPDATA, r"Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt")
    if os.path.exists(hist):
        with open(hist, "r", errors="ignore") as f:
            lines.extend(f.readlines())

    filename = f"SSHelper_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
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
        ("UUID",          "wmic path win32_computersystemproduct get uuid"),
        ("MAC Address",   "getmac"),
        ("CPU ID",        "wmic cpu get ProcessorId"),
        ("Disk Serial",   "wmic diskdrive get serialnumber"),
        ("RAM Serial",    "wmic memorychip get serialnumber"),
        ("Baseboard S/N", "wmic baseboard get serialnumber"),
        ("CPU Name",      "wmic cpu get name"),
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
            ("UAV",   "UserAssistView"),
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
            ("OFV2",  "OpenedFilesView (live open files)"),
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
            ("FELV",  "FullEventLogView"),
            ("SMF",   "SearchMyFiles"),
            ("WIN",   "WinLogonView"),
            ("PSV",   "ProcessActivityView"),
            ("SAV",   "StartupRunView"),
            ("FCV",   "FolderChangesView"),
            ("DNV",   "DNSQuerySniffer"),
            ("USBDV", "USBDeview"),
            ("PFR",   "Previous Files Recovery"),
            ("AMP",   "Amcache Parser (EZ Tools)"),
            ("TLE",   "Timeline Explorer (EZ Tools)"),
            ("RYE",   "Registry Explorer (EZ Tools)"),
            ("PEC",   "PECmd (EZ Tools)"),
            ("EEC",   "EvtxECmd (EZ Tools)"),
            ("WTC",   "WxTCmd (EZ Tools)"),
            ("MFTE",  "MFTECmd (EZ Tools)"),
        ]
        for code, name in items:
            print(f"  [{code}]  {name}")
        print("\n  [0]  Back to main menu")
        choice = input("\n  Choice: ").strip().upper()

        urls = {
            "PH2":   ("https://github.com/processhacker/processhacker/releases/download/v2.39/processhacker-2.39-setup.exe", "ProcessHacker2-Setup.exe"),
            "LAV":   ("https://www.nirsoft.net/utils/lastactivityview.zip",            "LastActivityView.zip"),
            "UAV":   ("https://www.nirsoft.net/utils/userassist_view.zip",             "UserAssistView.zip"),
            "WPV":   ("https://www.nirsoft.net/utils/winprefetchview-x64.zip",         "WinPrefetchView.zip"),
            "LYT":   ("https://github.com/deathmarine/Luyten/releases/download/v0.5.4_Rebuilt_with_Latest_depenencies/luyten-0.5.4.exe", "Luyten.exe"),
            "ERT":   ("https://www.voidtools.com/Everything-1.4.1.1005.x64.zip",       "Everything.zip"),
            "ASV":   ("https://www.nirsoft.net/utils/alternatestreamview-x64.zip",     "AlternateStreamView.zip"),
            "RGS":   ("https://www.nirsoft.net/utils/regscanner-x64.zip",              "RegScanner.zip"),
            "EPF":   ("https://www.nirsoft.net/utils/executedprogramslist.zip",        "ExecutedProgramsList.zip"),
            "MCV":   ("https://www.nirsoft.net/utils/muicacheview.zip",                "MUICacheView.zip"),
            "SBV":   ("https://www.nirsoft.net/utils/shellbagsview.zip",               "ShellBagsView.zip"),
            "BDV":   ("https://www.nirsoft.net/utils/browserdownloadsview-x64.zip",   "BrowserDownloadsView.zip"),
            "BHV":   ("https://www.nirsoft.net/utils/browsinghistoryview-x64.zip",    "BrowsingHistoryView.zip"),
            "OFV":   ("https://www.nirsoft.net/utils/opensavefilesview-x64.zip",      "OpenSaveFilesView.zip"),
            "OFV2":  ("https://www.nirsoft.net/utils/openedfilesview-x64.zip",        "OpenedFilesView.zip"),
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
            "FELV":  ("https://www.nirsoft.net/utils/fulleventlogview-x64.zip",       "FullEventLogView.zip"),
            "SMF":   ("https://www.nirsoft.net/utils/searchmyfiles.zip",              "SearchMyFiles.zip"),
            "WIN":   ("https://www.nirsoft.net/utils/winlogonview.zip",               "WinLogonView.zip"),
            "PSV":   ("https://www.nirsoft.net/utils/processactivityview.zip",        "ProcessActivityView.zip"),
            "SAV":   ("https://www.nirsoft.net/utils/startuprunview.zip",             "StartupRunView.zip"),
            "FCV":   ("https://www.nirsoft.net/utils/folderchangesview.zip",          "FolderChangesView.zip"),
            "DNV":   ("https://www.nirsoft.net/utils/dns_query_sniffer.zip",          "DNSQuerySniffer.zip"),
            "USBDV": ("https://www.nirsoft.net/utils/usbdeview-x64.zip",              "USBDeview.zip"),
            "PFR":   ("https://www.nirsoft.net/utils/previousfilesrecovery-x64.zip",  "PreviousFilesRecovery.zip"),
            "AMP":   ("https://github.com/EricZimmerman/AmcacheParser/releases/latest/download/AmcacheParser.zip", "AmcacheParser.zip"),
            "TLE":   ("https://github.com/EricZimmerman/Timeline-Explorer/releases/latest/download/TimelineExplorer.zip", "TimelineExplorer.zip"),
            "RYE":   ("https://github.com/EricZimmerman/RegistryExplorer/releases/latest/download/RegistryExplorer.zip", "RegistryExplorer.zip"),
            "PEC":   ("https://github.com/EricZimmerman/PECmd/releases/latest/download/PECmd.zip",   "PECmd.zip"),
            "EEC":   ("https://github.com/EricZimmerman/evtx/releases/latest/download/EvtxECmd.zip", "EvtxECmd.zip"),
            "WTC":   ("https://github.com/EricZimmerman/WxTCmd/releases/latest/download/WxTCmd.zip", "WxTCmd.zip"),
            "MFTE":  ("https://github.com/EricZimmerman/MFTECmd/releases/latest/download/MFTECmd.zip","MFTECmd.zip"),
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
            ("Recuva",    "Recuva",               "https://www.ccleaner.com/recuva/download/standard",              "RecuvaSetup.exe"),
            ("EaseUS",    "EaseUS Data Recovery",  "https://down.easeus.com/product/drw_trial",                     "EaseUS-DR-Setup.exe"),
            ("Glarysoft", "Glarysoft File Recovery","https://www.glarysoft.com/file-recovery/download/",             "GlarysoftFileRecovery.exe"),
            ("KickAss",   "KickAssUndelete",       "https://www.kickassundelete.com/download/KickAssUndelete.exe",   "KickAssUndelete.exe"),
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

# ── Explorer paths ────────────────────────────────────────────────────────────

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
            "RA":   ("Report Archive",      os.path.join(os.environ.get("PROGRAMDATA","C:\\ProgramData"), r"Microsoft\Windows\WER\ReportArchive")),
            "CB":   ("Clipboard Cache",     os.path.join(LOCALAPPDATA, r"Microsoft\Windows\Clipboard")),
            "CF":   ("Control Panel",       "control"),
            "FW":   ("Firewall",            "wf.msc"),
            "NP":   ("Netplwiz",            "netplwiz"),
            "SRV":  ("Services",            "services.msc"),
            "DM":   ("Disk Management",     "diskmgmt.msc"),
            "GPE":  ("Group Policy Editor", "gpedit.msc"),
            "DRS":  ("Nvidia DRS folder",   os.path.join(os.environ.get("PROGRAMDATA","C:\\ProgramData"), r"NVIDIA Corporation\Drs")),
            "DL":   ("SSHelper Downloads",  DOWNLOADS),
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
            if target.endswith(".msc") or target in ("control", "netplwiz"):
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
            "SCM":  ("Service control manager",    "sc query type= all state= all"),
            "DPS":  ("Query DPS service",          "sc queryex dps"),
            "PCA":  ("Query PcaSvc service",       "sc queryex PcaSvc"),
            "EVL":  ("Query Eventlog service",     "sc queryex eventlog"),
            "SYS":  ("Query SysMain service",      "sc queryex SysMain"),
            "DIA":  ("Query DiagTrack service",    "sc queryex DiagTrack"),
            "APPI": ("Query AppInfo service",      "sc queryex Appinfo"),
            "DIRA": ("Folder modification dates",  f'dir "{USERPROFILE}" /ad /tc'),
            "GETP": ("Get-Process (PowerShell)",   "powershell Get-Process | Sort-Object CPU -Descending | Select-Object -First 30"),
            "ARP":  ("ARP table (LAN devices)",    "arp -a"),
            "DNS":  ("DNS cache",                  "ipconfig /displaydns"),
            "FW":   ("Firewall rules (outbound)",  "netsh advfirewall firewall show rule name=all dir=out"),
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

# ── Registry paths ────────────────────────────────────────────────────────────

def menu_regedit():
    while True:
        clear()
        header("Registry Paths  (query reg keys)")
        paths = {
            "EF":   ("Executable files ran",          r"HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Compatibility Assistant\Store"),
            "DR":   ("Disallow Run",                  r"HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\DisallowRun"),
            "MCC":  ("MUICache",                      r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"),
            "AH":   ("Run MRU (Win+R history)",       r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"),
            "APPS": ("AppSwitched",                   r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FeatureUsage\AppSwitched"),
            "UA":   ("UserAssist",                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"),
            "EP":   ("Executed programs (BAM)",       r"SYSTEM\CurrentControlSet\Services\bam\State\UserSettings"),
            "FA":   ("File type associations",        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts"),
            "OS":   ("Open/Save dialog files",        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU"),
            "MV":   ("Mounted volumes",               r"HKLM\SYSTEM\MountedDevices"),
            "PF":   ("Prefetch parameters",           r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"),
            "RD":   ("RecentDocs",                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs"),
            "LVP":  ("LastVisitedPidlMRU",            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU"),
            "EN":   ("Environment variables",         r"HKCU\Environment"),
            "FR":   ("Firewall rules",                r"HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\FirewallRules"),
            "UN":   ("Uninstall list",                r"HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            "DI":   ("DirectInput devices",           r"HKCU\System\CurrentControlSet\Control\MediaProperties\PrivateProperties\DirectInput"),
            "TPS":  ("TypedPaths",                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths"),
            "CP":   ("Command Processor",             r"HKCU\Software\Microsoft\Command Processor"),
            "USBS": ("USB Storage devices",           r"HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR"),
            "TRA":  ("Tracing",                       r"HKLM\Software\Microsoft\Tracing"),
            "AMC":  ("Amcache (recent programs)",     r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Appraiser\Amcache"),
            "WIM":  ("Windows Image (install info)",  r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion"),
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
            "AU":  ("Audit policy changed (4719)",           'wevtutil qe Security /q:"*[System[EventID=4719]]" /f:text /c:10'),
            "FW":  ("Firewall rule changed (4946/4947)",     'wevtutil qe Security /q:"*[System[(EventID=4946 or EventID=4947)]]" /f:text /c:10'),
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

# ── Macro / recording scanners ────────────────────────────────────────────────

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
    found_any = False
    search_bases = [APPDATA, LOCALAPPDATA,
                    os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                    os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")]
    for macro in macros:
        for base in search_bases:
            if os.path.exists(os.path.join(base, macro)):
                found(f"{macro} → {os.path.join(base, macro)}")
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
    found_any = False
    search_bases = [APPDATA, LOCALAPPDATA,
                    os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                    os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")]
    for rec in recorders:
        for base in search_bases:
            if os.path.exists(os.path.join(base, rec)):
                found(f"{rec} → {os.path.join(base, rec)}")
                found_any = True
    all_procs = run("tasklist").lower()
    for r in ["obs", "bandicam", "fraps", "medal", "xsplit", "streamlabs", "camtasia", "loom"]:
        if r in all_procs:
            found(f"Running process contains: {r}")
            found_any = True
    if not found_any:
        info("No recording software detected.")
    pause()

# ── Download History Check ────────────────────────────────────────────────────

def check_download_history():
    """
    1. Copy browser Download SQLite DBs to temp (avoids browser file-lock).
    2. Query them with the built-in sqlite3 module — no external deps needed.
    3. If the table is empty or missing, flag it as CLEARED and show when.
    4. Cross-reference five other Windows artifacts for download traces that
       survive a browser history wipe: DNS cache, MUICache, BAM, Prefetch,
       and the Windows Downloads folder on disk.
    """
    import sqlite3, shutil, tempfile

    clear()
    header("Download History — Cleared Detection & Recovery")

    # ── Browser DB definitions ─────────────────────────────────────────────
    # Each entry: (display name, db path, sql to fetch rows, sql to count rows)
    CHROM_SQL_ROWS  = "SELECT target_path, tab_url, total_bytes, start_time FROM downloads ORDER BY start_time DESC LIMIT 200"
    CHROM_SQL_COUNT = "SELECT COUNT(*) FROM downloads"
    FF_SQL_ROWS     = "SELECT place_id, content, dateAdded FROM moz_annos WHERE anno_attribute_id=(SELECT id FROM moz_anno_attributes WHERE name='downloads/destinationFileURI') ORDER BY dateAdded DESC LIMIT 200"
    FF_SQL_COUNT    = "SELECT COUNT(*) FROM moz_annos WHERE anno_attribute_id=(SELECT id FROM moz_anno_attributes WHERE name='downloads/destinationFileURI')"

    browsers = {
        "Chrome": {
            "db":    os.path.join(LOCALAPPDATA, r"Google\Chrome\User Data\Default\History"),
            "rows":  CHROM_SQL_ROWS,
            "count": CHROM_SQL_COUNT,
            "type":  "chromium",
        },
        "Edge": {
            "db":    os.path.join(LOCALAPPDATA, r"Microsoft\Edge\User Data\Default\History"),
            "rows":  CHROM_SQL_ROWS,
            "count": CHROM_SQL_COUNT,
            "type":  "chromium",
        },
        "Brave": {
            "db":    os.path.join(LOCALAPPDATA, r"BraveSoftware\Brave-Browser\User Data\Default\History"),
            "rows":  CHROM_SQL_ROWS,
            "count": CHROM_SQL_COUNT,
            "type":  "chromium",
        },
        "Opera": {
            "db":    os.path.join(APPDATA, r"Opera Software\Opera Stable\History"),
            "rows":  CHROM_SQL_ROWS,
            "count": CHROM_SQL_COUNT,
            "type":  "chromium",
        },
        "OperaGX": {
            "db":    os.path.join(APPDATA, r"Opera Software\Opera GX Stable\History"),
            "rows":  CHROM_SQL_ROWS,
            "count": CHROM_SQL_COUNT,
            "type":  "chromium",
        },
        "Vivaldi": {
            "db":    os.path.join(LOCALAPPDATA, r"Vivaldi\User Data\Default\History"),
            "rows":  CHROM_SQL_ROWS,
            "count": CHROM_SQL_COUNT,
            "type":  "chromium",
        },
    }

    # Firefox: scan all profiles
    ff_profiles_root = os.path.join(APPDATA, r"Mozilla\Firefox\Profiles")
    if os.path.exists(ff_profiles_root):
        for prof in os.listdir(ff_profiles_root):
            db = os.path.join(ff_profiles_root, prof, "places.sqlite")
            if os.path.exists(db):
                browsers[f"Firefox ({prof[:20]})"] = {
                    "db":    db,
                    "rows":  FF_SQL_ROWS,
                    "count": FF_SQL_COUNT,
                    "type":  "firefox",
                }

    tmp_dir = tempfile.mkdtemp(prefix="sshelper_dl_")
    any_browser_found = False

    for browser, cfg in browsers.items():
        db_path = cfg["db"]
        if not os.path.exists(db_path):
            continue

        any_browser_found = True
        print()
        print(f"  {'─'*64}")
        print(f"  Browser : {browser}")
        print(f"  DB path : {db_path}")

        # Copy DB + WAL/SHM so SQLite can open it even while browser runs
        tmp_db = os.path.join(tmp_dir, f"{browser.replace(' ','_')}.db")
        try:
            shutil.copy2(db_path, tmp_db)
            for ext in ["-wal", "-shm"]:
                src = db_path + ext
                if os.path.exists(src):
                    shutil.copy2(src, tmp_db + ext)
        except Exception as e:
            warn(f"  Could not copy DB: {e}")
            continue

        try:
            con = sqlite3.connect(tmp_db)
            con.row_factory = sqlite3.Row

            # ── Row count (cleared = 0 rows but DB exists) ──────────────
            try:
                count = con.execute(cfg["count"]).fetchone()[0]
            except sqlite3.OperationalError:
                count = None   # table missing entirely

            if count is None:
                warn(f"  Downloads table missing — DB may be wiped/recreated")
            elif count == 0:
                warn(f"  CLEARED — downloads table exists but is EMPTY (0 rows)")
                warn(f"  History was cleared after the last download session.")
            else:
                info(f"  {count} download record(s) found:")

                rows = con.execute(cfg["rows"]).fetchall()
                for r in rows:
                    if cfg["type"] == "chromium":
                        # start_time is microseconds since 1601-01-01
                        try:
                            from datetime import timezone
                            epoch_delta = 11644473600  # seconds between 1601 and 1970
                            ts = datetime.fromtimestamp(
                                r["start_time"] / 1_000_000 - epoch_delta,
                                tz=timezone.utc
                            ).strftime("%Y-%m-%d %H:%M:%S UTC")
                        except:
                            ts = "?"
                        path = r["target_path"] or "(no path)"
                        url  = r["tab_url"]     or "(no url)"
                        size = r["total_bytes"] or 0
                        print(f"    [{ts}]  {os.path.basename(path)}  ({size//1024} KB)")
                        print(f"      URL : {url}")
                        print(f"      Path: {path}")
                    else:
                        # Firefox: content is the local file URI
                        content = r["content"] or ""
                        try:
                            from datetime import timezone
                            ts = datetime.fromtimestamp(
                                r["dateAdded"] / 1_000_000,
                                tz=timezone.utc
                            ).strftime("%Y-%m-%d %H:%M:%S UTC")
                        except:
                            ts = "?"
                        print(f"    [{ts}]  {content}")

            con.close()

        except Exception as e:
            warn(f"  SQLite error: {e}")

        # ── Check DB metadata: last modified time of the DB file itself ──
        try:
            db_mtime = datetime.fromtimestamp(os.path.getmtime(db_path))
            db_size  = os.path.getsize(db_path)
            info(f"  DB last modified : {db_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            info(f"  DB size          : {db_size} bytes")
            if db_size < 40960 and count == 0:
                warn(f"  DB is suspiciously small ({db_size}B) AND empty — likely wiped and rebuilt.")
        except:
            pass

    # Clean up temp copies
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except:
        pass

    if not any_browser_found:
        info("No browser history databases found.")

    # ═══════════════════════════════════════════════════════════════════════
    # FORENSIC CROSS-REFERENCE — traces that survive a history clear
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print(f"  {'═'*64}")
    print("   FORENSIC TRACES — survive browser history clear")
    print(f"  {'═'*64}")

    # 1. Actual Downloads folder on disk
    print()
    info("[1/5] Files currently in Downloads folder:")
    dl_folder = os.path.join(USERPROFILE, "Downloads")
    if os.path.exists(dl_folder):
        entries = []
        for f in os.listdir(dl_folder):
            full = os.path.join(dl_folder, f)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(full))
                size  = os.path.getsize(full) if os.path.isfile(full) else 0
                entries.append((mtime, f, size))
            except:
                entries.append((datetime.min, f, 0))
        entries.sort(reverse=True)
        if entries:
            for mtime, fname, size in entries[:40]:
                ext = os.path.splitext(fname)[1].lower()
                flag = " ◄ SUSPICIOUS" if ext in [".exe", ".jar", ".dll", ".bat",
                                                   ".ps1", ".vbs", ".zip", ".rar"] else ""
                print(f"    [{mtime.strftime('%Y-%m-%d %H:%M')}]  {fname}  ({size//1024} KB){flag}")
        else:
            warn("Downloads folder is EMPTY — may have been cleared before SS.")
    else:
        warn("Downloads folder not found.")

    # 2. Windows DNS cache — reveals domains visited (including download CDNs)
    print()
    info("[2/5] DNS cache — download-related domains:")
    dns_out = run("ipconfig /displaydns")
    download_domains = []
    current_record   = []
    dl_keywords = [
        "download", "cdn", "mediafire", "mega.nz", "gofile", "anonfiles",
        "dropbox", "drive.google", "github", "githubusercontent", "discord",
        "1fichier", "uploadhaven", "zippyshare", "workupload", "pixeldrain",
        "cheat", "hack", "inject", "vape", "sigma", "flux",
    ]
    for line in dns_out.splitlines():
        stripped = line.strip()
        if stripped.startswith("Record Name"):
            current_record = [stripped]
        elif current_record:
            current_record.append(stripped)
            if any(k in stripped.lower() for k in dl_keywords) or \
               any(k in current_record[0].lower() for k in dl_keywords):
                download_domains.extend(current_record)
                download_domains.append("")
                current_record = []
    if download_domains:
        for line in download_domains:
            print(f"    {line}")
    else:
        info("No download-related domains in DNS cache (may be flushed).")

    # 3. Prefetch — shows if a downloaded EXE was ever run
    print()
    info("[3/5] Prefetch — downloaded executables that were RUN:")
    pf_out = run("dir C:\\Windows\\Prefetch /od /b *.pf")
    dl_exec_keywords = [
        "cheat", "inject", "hack", "vape", "sigma", "wurst", "meteor",
        "anydesk", "teamviewer", "luyten", "recaf", "jd-gui",
        "setup", "install", "loader", "injector", "rat", "ghost",
        "flux", "reflex", "tenacity", "prestige",
    ]
    pf_hits = [l for l in pf_out.splitlines()
               if any(k in l.lower() for k in dl_exec_keywords)]
    if pf_hits:
        for h in pf_hits:
            found(f"  {h}")
    else:
        info("No suspicious downloaded executables found in Prefetch.")

    # 4. MUICache — display names of run programs (survives uninstall + history clear)
    print()
    info("[4/5] MUICache — programs run that match download/cheat keywords:")
    mui_out = run(r'reg query "HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"')
    mui_dl_keys = [
        "cheat", "inject", "hack", "vape", "sigma", "wurst", "anydesk",
        "teamviewer", "luyten", "recaf", "loader", "injector", "rat",
        "flux", "reflex", "tenacity", "download", "setup", "install",
    ]
    mui_hits = [l.strip() for l in mui_out.splitlines()
                if any(k in l.lower() for k in mui_dl_keys)]
    if mui_hits:
        for h in mui_hits:
            found(f"  {h}")
    else:
        info("No suspicious MUICache entries.")

    # 5. BAM — background activity monitor, records EXE execution with timestamp
    print()
    info("[5/5] BAM — recently executed files matching download/cheat keywords:")
    bam_out = run(r'reg query "HKLM\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings" /s')
    bam_dl_keys = [
        "cheat", "inject", "hack", "vape", "sigma", "wurst", "anydesk",
        "teamviewer", "luyten", "recaf", "loader", "injector",
        "flux", "reflex", "tenacity", "downloads", "rat", "ghost",
    ]
    bam_hits = [l.strip() for l in bam_out.splitlines()
                if r"\device\harddiskvolume" in l.lower()
                and any(k in l.lower() for k in bam_dl_keys)]
    if bam_hits:
        for h in bam_hits:
            found(f"  {h}")
    else:
        info("No suspicious BAM entries.")

    print()
    info("Tip: even with history cleared, Prefetch + BAM + MUICache show what was RUN.")
    info("     DNS cache shows what sites were visited. Downloads folder shows what remains.")
    pause()


# ── Menu ──────────────────────────────────────────────────────────────────────

def open_path_safe(path):
    if os.path.exists(path):
        os.startfile(path)
    else:
        warn(f"Path not found: {path}")

def menu():
    while True:
        clear()
        print("""
  ╔══════════════════════════════════════════════════════════════════════╗
  ║              SS HELPER — Minecraft Screenshare Tool                  ║
  ╚══════════════════════════════════════════════════════════════════════╝
        """)

        print("  ── AUTOMATIC CHECKS ─────────────────────────────────────────────")
        print("  [1]  AppData cheat folders      [2]  Running processes")
        print("  [3]  .minecraft folder           [4]  Startup programs")
        print("  [5]  Recently opened files       [6]  Temp folder")
        print("  [7]  Hosts file                  [8]  Installed programs")
        print("  [9]  Browser history paths       [10] Windows Prefetch")
        print("  [11] Scheduled tasks             [12] Environment variables")
        print("  [13] VPN / virtual adapters      [14] Shadow copies")
        print("  [15] Files modified in last 24h  [16] Active network connections")
        print("  [17] Installed drivers           [18] Full auto scan (all checks)")
        print("  [O]  Ocean Anti-Cheat PIN lookup")
        print("  [R]  Save full scan report to Desktop")
        print("  [K]  Launcher/Profile Scanner")
        print("  [M]  Java Argument Scanner")
        print("  [S]  Suspicious Cheat Folders")
        print("  [L]  Launcher / Mods Reader")
        print()
        print("  ── NEW CHECKS ───────────────────────────────────────────────────")
        print("  [N]  Remote Access Tools         [P]  BAM Executed Programs")
        print("  [Q]  ShellBags Explorer History  [T]  MUICache Programs Run")
        print("  [U]  PowerShell History          [V]  Clipboard Artifacts")
        print("  [W]  JAR Decompiler Detection    [X]  Ghost Client Artifacts")
        print("  [Y]  Discord Inject Check        [Z]  Enhanced Autorun Check")
        print("  [AA] UserAssist (GUI Programs)   [AB] TypedPaths (Explorer bar)")
        print("  [AC] RunMRU (Win+R history)      [AD] Recycle Bin Contents")
        print("  [AE] Event Log Cleared Check")
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
        print("  [28] Event Viewer      [29] Resource Monitor  [30] System Info")
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
            # New checks
            "N":  check_remote_access,
            "P":  check_bam,
            "Q":  check_shellbags,
            "T":  check_muicache,
            "U":  check_ps_history,
            "V":  check_clipboard,
            "W":  check_decompilers,
            "X":  check_ghost_artifacts,
            "Y":  check_discord,
            "Z":  check_autorun_enhanced,
            "AA": check_userassist,
            "AB": check_typed_paths,
            "AC": check_run_mru,
            "AD": check_deleted_recently,
            "AE": check_event_log_cleared,
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
