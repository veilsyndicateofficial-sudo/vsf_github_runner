#!/data/data/com.termux/files/usr/bin/python
import datetime
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.parse
import urllib.request


class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    CYAN = "\033[38;5;45m"
    TEAL = "\033[38;5;43m"
    BLUE = "\033[38;5;39m"
    GREEN = "\033[38;5;46m"
    YELLOW = "\033[38;5;220m"
    ORANGE = "\033[38;5;208m"
    RED = "\033[38;5;196m"
    MAGENTA = "\033[38;5;177m"
    VIOLET = "\033[38;5;141m"
    WHITE = "\033[38;5;255m"
    GRAY = "\033[38;5;244m"


SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
PULSE = ["▁", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(BASE_DIR, "vsf_github_tools")
HISTORY_FILE = os.path.join(BASE_DIR, "vsf_github_history.log")
os.makedirs(WORKSPACE_DIR, exist_ok=True)


def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def animate_bar(label, duration=1.5, accent=Style.CYAN):
    hide_cursor()
    start = time.time()
    idx = 0
    bar_len = 26
    try:
        while time.time() - start < duration:
            pct = min(100, int(((time.time() - start) / duration) * 100))
            filled = int((pct / 100) * bar_len)
            bar = f"{accent}{'━' * filled}{Style.GRAY}{'┄' * (bar_len - filled)}{Style.RESET}"
            spin = SPINNER[idx % len(SPINNER)]
            wave = "".join(
                f"{accent if (i + idx) % 3 == 0 else Style.DIM}{PULSE[(i + idx) % len(PULSE)]}{Style.RESET}"
                for i in range(6)
            )
            sys.stdout.write(
                f"\r  {accent}{spin}{Style.RESET} {wave} {Style.BOLD}{label}{Style.RESET} "
                f"[{bar}] {Style.WHITE}{pct:3d}%{Style.RESET}"
            )
            sys.stdout.flush()
            time.sleep(0.07)
            idx += 1
        done_bar = f"{Style.GREEN}{'━' * bar_len}{Style.RESET}"
        sys.stdout.write(
            f"\r  {Style.GREEN}✔{Style.RESET} {Style.GREEN}━━━━━━{Style.RESET} {Style.BOLD}{label}{Style.RESET} "
            f"[{done_bar}] {Style.GREEN}100%{Style.RESET}\n"
        )
        sys.stdout.flush()
    finally:
        show_cursor()


def boot_animation():
    clear_screen()
    stages = [
        ("Booting V.S.F GitHub Intelligence Engine", 0.5, Style.CYAN),
        ("Checking git & Python runtime in Termux", 0.45, Style.MAGENTA),
        ("Preparing V.S.F local tool workspace", 0.4, Style.TEAL),
    ]
    print()
    for text, dur, col in stages:
        animate_bar(text, duration=dur, accent=col)
    time.sleep(0.2)


def log_action(action, detail):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, "a", encoding="utf-8") as fh:
        fh.write(f"[{ts}] {action:<14} | {detail}\n")


def list_installed_repos():
    if not os.path.isdir(WORKSPACE_DIR):
        return []
    repos = []
    for name in sorted(os.listdir(WORKSPACE_DIR)):
        full = os.path.join(WORKSPACE_DIR, name)
        if os.path.isdir(full):
            repos.append(name)
    return repos


def github_search_repos(query, limit=6):
    q = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={limit}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "V.S.F-Termux-GitHub-Runner",
            "Accept": "application/vnd.github+json",
        },
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    rtt = int((time.time() - t0) * 1000)
    data = json.loads(raw)
    items = data.get("items", [])
    results = []
    for it in items:
        results.append(
            {
                "full_name": it.get("full_name", "unknown/repo"),
                "name": it.get("name", "repo"),
                "desc": (it.get("description") or "No description provided.").strip(),
                "stars": it.get("stargazers_count", 0),
                "lang": it.get("language") or "Misc",
                "clone_url": it.get("clone_url", ""),
                "html_url": it.get("html_url", ""),
            }
        )
    return results, rtt


def render_banner():
    w = 60
    print(f"{Style.CYAN}┏{'━' * w}┓{Style.RESET}")
    print(
        f"{Style.CYAN}┃{Style.RESET}"
        f"{Style.BOLD}{Style.MAGENTA}{'V.S.F'.center(w)}{Style.RESET}"
        f"{Style.CYAN}┃{Style.RESET}"
    )
    print(
        f"{Style.CYAN}┃{Style.RESET}"
        f"{Style.BOLD}{Style.WHITE}{'V.S.F GITHUB TOOL FINDER & TERMUX RUNNER'.center(w)}{Style.RESET}"
        f"{Style.CYAN}┃{Style.RESET}"
    )
    print(
        f"{Style.CYAN}┃{Style.RESET}"
        f"{Style.DIM}{Style.TEAL}{'Fast Search  •  Inspect  •  Clone  •  Run in Termux'.center(w)}{Style.RESET}"
        f"{Style.CYAN}┃{Style.RESET}"
    )
    print(f"{Style.CYAN}┗{'━' * w}┛{Style.RESET}")


def render_status():
    git_ok = shutil.which("git") is not None
    py_ok = shutil.which("python") is not None or shutil.which("python3") is not None
    repos_count = len(list_installed_repos())
    badge = (
        f"{Style.GREEN}● READY{Style.RESET}"
        if (git_ok and py_ok)
        else f"{Style.RED}⚠ MISSING RUNTIME{Style.RESET}"
    )
    print(
        f"\n  {Style.BOLD}ENGINE:{Style.RESET} {badge}  "
        f"{Style.DIM}git:{'OK' if git_ok else 'NO'}  Installed:{repos_count}  Dir:vsf_github_tools{Style.RESET}"
    )
    print(f"  {Style.GRAY}{'─' * 58}{Style.RESET}")


def render_menu():
    options = [
        ("1", "Search GitHub Tools", "Find top repos by keyword & quick-clone", Style.CYAN),
        ("2", "Clone by Repo URL/Name", "Clone any owner/repo or .git URL directly", Style.GREEN),
        ("3", "Run Installed Tool", "Pick a cloned repo, inspect & run safely", Style.MAGENTA),
        ("4", "Manage Installed Tools", "View README/files or delete a repo folder", Style.YELLOW),
        ("5", "View Activity History", "Inspect recent search, clone & run logs", Style.BLUE),
        ("6", "Safety & Execution Guide", "Safe review checklist before running code", Style.TEAL),
        ("0", "Exit V.S.F Runner", "Return cleanly to Termux prompt", Style.GRAY),
    ]
    print()
    for key, title, desc, col in options:
        print(
            f"  {col}{Style.BOLD}[{key}]{Style.RESET} "
            f"{Style.WHITE}{Style.BOLD}{title:<24}{Style.RESET} "
            f"{Style.DIM}{desc}{Style.RESET}"
        )


def render_footer():
    w = 60
    print(f"\n{Style.CYAN}┏{'─' * w}┓{Style.RESET}")
    print(
        f"{Style.CYAN}┃{Style.RESET}"
        f"{Style.BOLD}{Style.WHITE}{'© V.S.F All Rights Reserved'.center(w)}{Style.RESET}"
        f"{Style.CYAN}┃{Style.RESET}"
    )
    print(f"{Style.CYAN}┗{'─' * w}┛{Style.RESET}")


def do_clone(clone_url, folder_name=None):
    if not shutil.which("git"):
        print(f"\n  {Style.RED}✘ 'git' not installed. Run: pkg install git{Style.RESET}")
        return None

    clean_url = clone_url.strip()
    if not clean_url.startswith(("https://", "http://", "git@")):
        if "/" in clean_url and not clean_url.endswith(".git"):
            clean_url = f"https://github.com/{clean_url}.git"
        else:
            print(f"\n  {Style.RED}✘ Invalid repository URL or owner/repo format.{Style.RESET}")
            return None

    if not folder_name:
        base = clean_url.rstrip("/").split("/")[-1]
        folder_name = base[:-4] if base.endswith(".git") else base
    folder_name = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in folder_name)
    dest = os.path.join(WORKSPACE_DIR, folder_name)

    if os.path.exists(dest):
        print(f"\n  {Style.YELLOW}⚠ Already cloned at:{Style.RESET} {Style.DIM}{dest}{Style.RESET}")
        return dest

    animate_bar(f"Cloning {folder_name}", duration=1.4, accent=Style.GREEN)
    proc = subprocess.run(["git", "clone", "--depth", "1", clean_url, dest], capture_output=True, text=True)
    if proc.returncode == 0:
        print(f"\n  {Style.GREEN}✔ Cloned successfully:{Style.RESET} {Style.WHITE}{dest}{Style.RESET}")
        log_action("CLONE", f"{clean_url} -> {folder_name}")
        return dest
    else:
        print(f"\n  {Style.RED}✘ Git clone failed:{Style.RESET} {Style.DIM}{proc.stderr.strip()[:160]}{Style.RESET}")
        return None


def action_search_github():
    print()
    query = input(f"  {Style.CYAN}{Style.BOLD}Search GitHub Keyword > {Style.RESET}").strip()
    if not query:
        print(f"  {Style.YELLOW}⚠ Search cancelled.{Style.RESET}")
        return

    animate_bar("Querying GitHub repositories API", duration=1.2, accent=Style.CYAN)
    try:
        results, rtt = github_search_repos(query, limit=6)
    except Exception as exc:
        print(f"\n  {Style.RED}✘ GitHub search failed:{Style.RESET} {Style.DIM}{str(exc)[:140]}{Style.RESET}")
        return

    log_action("SEARCH", f"Query='{query}' Matches={len(results)}")
    print(f"\n  {Style.GREEN}✔ {len(results)} Repositories Found{Style.RESET} {Style.DIM}({rtt} ms){Style.RESET}")
    print(f"  {Style.GRAY}{'─' * 58}{Style.RESET}")

    if not results:
        print(f"  {Style.YELLOW}No matching repositories found.{Style.RESET}")
        return

    for idx, item in enumerate(results, 1):
        print(
            f"  {Style.CYAN}{Style.BOLD}[{idx}] {item['full_name']}{Style.RESET} "
            f"{Style.YELLOW}★ {item['stars']}{Style.RESET}  {Style.TEAL}[{item['lang']}]{Style.RESET}"
        )
        print(f"      {Style.WHITE}{item['desc'][:115]}{Style.RESET}")
        print(f"      {Style.DIM}{item['html_url']}{Style.RESET}\n")

    pick = input(f"  {Style.GREEN}{Style.BOLD}Enter # to Clone (or Enter to skip) > {Style.RESET}").strip()
    if pick.isdigit():
        num = int(pick)
        if 1 <= num <= len(results):
            chosen = results[num - 1]
            cloned_path = do_clone(chosen["clone_url"], chosen["name"])
            if cloned_path:
                run_now = input(f"  {Style.MAGENTA}Run this tool now? (y/N) > {Style.RESET}").strip().lower()
                if run_now == "y":
                    run_repo_interactive(cloned_path)


def action_clone_direct():
    print()
    raw = input(f"  {Style.GREEN}{Style.BOLD}Enter GitHub URL or owner/repo > {Style.RESET}").strip()
    if not raw:
        print(f"  {Style.YELLOW}⚠ Cancelled.{Style.RESET}")
        return
    do_clone(raw)


def find_entry_candidates(repo_dir):
    candidates = []
    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules", ".git")]
        for fn in sorted(files):
            if fn.endswith((".py", ".sh", ".bash")):
                rel = os.path.relpath(os.path.join(root, fn), repo_dir)
                candidates.append(rel)
    return candidates[:15]


def run_repo_interactive(repo_dir):
    repo_name = os.path.basename(repo_dir)
    print(f"\n  {Style.MAGENTA}{Style.BOLD}LAUNCHPAD: {repo_name}{Style.RESET}")
    print(f"  {Style.DIM}Path: {repo_dir}{Style.RESET}")
    print(f"  {Style.GRAY}{'─' * 58}{Style.RESET}")

    candidates = find_entry_candidates(repo_dir)
    if candidates:
        print(f"  {Style.BOLD}Detected Scripts:{Style.RESET}")
        for idx, rel in enumerate(candidates, 1):
            print(f"    {Style.CYAN}[{idx}]{Style.RESET} {Style.WHITE}{rel}{Style.RESET}")
    else:
        print(f"  {Style.YELLOW}No .py or .sh scripts auto-detected. You can still enter a custom command.{Style.RESET}")

    print(f"    {Style.YELLOW}[C]{Style.RESET} Enter custom run command inside {repo_name}")
    print(f"    {Style.GRAY}[0]{Style.RESET} Cancel")

    choice = input(f"\n  {Style.MAGENTA}{Style.BOLD}Select Script or [C] > {Style.RESET}").strip().upper()
    if choice == "0" or not choice:
        return

    cmd_str = ""
    if choice == "C":
        cmd_str = input(f"  {Style.WHITE}Command to run > {Style.RESET}").strip()
    elif choice.isdigit() and 1 <= int(choice) <= len(candidates):
        target_rel = candidates[int(choice) - 1]
        args = input(f"  {Style.DIM}Optional CLI arguments (or Enter) > {Style.RESET}").strip()
        if target_rel.endswith(".py"):
            cmd_str = f"python {target_rel} {args}".strip()
        else:
            cmd_str = f"bash {target_rel} {args}".strip()
    else:
        print(f"  {Style.RED}✘ Invalid selection.{Style.RESET}")
        return

    if not cmd_str:
        return

    print(f"\n  {Style.YELLOW}⚠ Review Command Before Execution:{Style.RESET} {Style.BOLD}{cmd_str}{Style.RESET}")
    confirm = input(f"  {Style.GREEN}Execute inside {repo_name}? (yes/no) > {Style.RESET}").strip().lower()
    if confirm != "yes":
        print(f"  {Style.DIM}Execution cancelled.{Style.RESET}")
        return

    log_action("RUN", f"{repo_name}: {cmd_str}")
    print(f"\n  {Style.CYAN}{'═' * 58}{Style.RESET}")
    subprocess.run(cmd_str, shell=True, cwd=repo_dir)
    print(f"  {Style.CYAN}{'═' * 58}{Style.RESET}")


def action_run_installed():
    print()
    repos = list_installed_repos()
    if not repos:
        print(f"  {Style.YELLOW}⚠ No tools cloned yet. Use [1] Search GitHub Tools or [2] Clone.{Style.RESET}")
        return

    print(f"  {Style.MAGENTA}{Style.BOLD}INSTALLED GITHUB TOOLS{Style.RESET}")
    print(f"  {Style.GRAY}{'─' * 58}{Style.RESET}")
    for idx, name in enumerate(repos, 1):
        print(f"  {Style.CYAN}[{idx}]{Style.RESET} {Style.WHITE}{Style.BOLD}{name}{Style.RESET}")

    sel = input(f"\n  {Style.MAGENTA}{Style.BOLD}Choose Tool # to Run > {Style.RESET}").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(repos):
        run_repo_interactive(os.path.join(WORKSPACE_DIR, repos[int(sel) - 1]))
    else:
        print(f"  {Style.RED}✘ Invalid choice.{Style.RESET}")


def action_manage_tools():
    print()
    repos = list_installed_repos()
    if not repos:
        print(f"  {Style.YELLOW}⚠ No installed tools found.{Style.RESET}")
        return

    for idx, name in enumerate(repos, 1):
        print(f"  {Style.CYAN}[{idx}]{Style.RESET} {Style.WHITE}{name}{Style.RESET}")

    sel = input(f"\n  {Style.YELLOW}Select Tool # to Inspect/Delete > {Style.RESET}").strip()
    if not sel.isdigit() or not (1 <= int(sel) <= len(repos)):
        return

    name = repos[int(sel) - 1]
    repo_path = os.path.join(WORKSPACE_DIR, name)
    print(f"\n  {Style.BOLD}Selected:{Style.RESET} {Style.CYAN}{name}{Style.RESET}")
    print(f"  {Style.TEAL}[R]{Style.RESET} View README snippet")
    print(f"  {Style.RED}[D]{Style.RESET} Delete tool folder")
    act = input(f"  {Style.YELLOW}Action > {Style.RESET}").strip().upper()

    if act == "R":
        readme_path = None
        for cand in ("README.md", "README.rst", "README", "readme.md"):
            p = os.path.join(repo_path, cand)
            if os.path.isfile(p):
                readme_path = p
                break
        if readme_path:
            with open(readme_path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()[:35]
            print(f"\n  {Style.GRAY}{'─' * 58}{Style.RESET}")
            for ln in lines:
                print(f"  {Style.WHITE}{ln[:90]}{Style.RESET}")
        else:
            print(f"\n  {Style.YELLOW}No README file found in {name}.{Style.RESET}")
    elif act == "D":
        confirm = input(f"  {Style.RED}Delete '{name}' permanently? (yes/no) > {Style.RESET}").strip().lower()
        if confirm == "yes":
            shutil.rmtree(repo_path, ignore_errors=True)
            log_action("DELETE", name)
            print(f"\n  {Style.GREEN}✔ Removed {name}.{Style.RESET}")


def action_history():
    print()
    print(f"  {Style.BLUE}{Style.BOLD}V.S.F GITHUB ACTIVITY LOG{Style.RESET}")
    print(f"  {Style.GRAY}{'─' * 58}{Style.RESET}")
    if not os.path.exists(HISTORY_FILE) or os.path.getsize(HISTORY_FILE) == 0:
        print(f"  {Style.YELLOW}⚠ No activity recorded yet.{Style.RESET}")
        return
    with open(HISTORY_FILE, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()[-25:]
    for ln in lines:
        print(f"  {Style.WHITE}{ln}{Style.RESET}")


def action_safety():
    print()
    print(f"  {Style.TEAL}{Style.BOLD}V.S.F SAFE EXECUTION & OPSEC GUIDE{Style.RESET}")
    print(f"  {Style.GRAY}{'─' * 58}{Style.RESET}")
    tips = [
        ("Inspect Before Run", "Check repository owner, stars, and scripts before executing code."),
        ("Dependency Isolation", "Check requirements.txt before installing packages; avoid unknown binaries."),
        ("Protect Credentials", "Never paste real passwords, tokens, or personal data into untrusted tools."),
        ("Lawful Usage", "Use open-source tools strictly for lawful, ethical, and permitted tasks."),
    ]
    for title, note in tips:
        print(f"  {Style.CYAN}▸ {Style.BOLD}{title}:{Style.RESET} {Style.WHITE}{note}{Style.RESET}")


def handle_interrupt(signum, frame):
    show_cursor()
    print(f"\n\n  {Style.YELLOW}Interrupted. Closing V.S.F GitHub Runner...{Style.RESET}")
    render_footer()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, handle_interrupt)
    boot_animation()
    while True:
        clear_screen()
        render_banner()
        render_status()
        render_menu()
        render_footer()

        try:
            choice = input(f"\n  {Style.CYAN}{Style.BOLD}V.S.F > {Style.RESET}").strip().upper()
        except EOFError:
            handle_interrupt(None, None)

        if choice == "1":
            action_search_github()
        elif choice == "2":
            action_clone_direct()
        elif choice == "3":
            action_run_installed()
        elif choice == "4":
            action_manage_tools()
        elif choice == "5":
            action_history()
        elif choice == "6":
            action_safety()
        elif choice == "0":
            print(f"\n  {Style.MAGENTA}{Style.BOLD}Exiting V.S.F GitHub Runner. Stay sharp!{Style.RESET}")
            render_footer()
            break
        else:
            print(f"\n  {Style.RED}✘ Invalid option '{choice}'.{Style.RESET}")

        input(f"\n  {Style.DIM}Press Enter to continue...{Style.RESET}")


if __name__ == "__main__":
    main()

