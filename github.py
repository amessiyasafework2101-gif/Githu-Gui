import os
import re
import sys
import json
import shutil
import tempfile
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

import termuxgui as tg


# ============================================================
# GitHub Manager for Termux:GUI
# ============================================================

API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

def clean_repo_name(name):
    """
    Convert a friendly repository name into a safe GitHub
    repository name.

    Example:
        "Hoji App"       -> "Hoji-App"
        "My Python App"  -> "My-Python-App"
        "hello_world"    -> "hello_world"
    """
    name = name.strip()

    # Replace spaces and whitespace with -
    name = re.sub(r"\s+", "-", name)

    # Remove characters that are troublesome in URLs
    name = re.sub(r"[^A-Za-z0-9._-]", "-", name)

    # Collapse multiple -
    name = re.sub(r"-+", "-", name)

    # Remove leading/trailing dots and dashes
    name = name.strip(".-")

    if not name:
        name = "my-project"

    return name


def run_git(folder, args, env=None):
    """
    Run a git command and return:
        success, output
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=folder,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            timeout=300,
        )

        output = result.stdout.strip()

        return result.returncode == 0, output

    except subprocess.TimeoutExpired:
        return False, "Git command timed out."

    except Exception as e:
        return False, str(e)


def api_request(token, method, path, data=None):
    """
    GitHub REST API request.
    """

    url = API_URL + path

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "Termux-GitHub-Manager",
    }

    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")

            if not raw:
                return True, {}

            try:
                return True, json.loads(raw)
            except Exception:
                return True, raw

    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8")
            data = json.loads(raw)
        except Exception:
            data = {"message": str(e)}

        return False, {
            "status": e.code,
            "data": data,
        }

    except Exception as e:
        return False, {
            "status": 0,
            "data": {
                "message": str(e)
            },
        }


def safe_text(value):
    return str(value).replace("\n", " ")


# ------------------------------------------------------------
# GUI
# ------------------------------------------------------------

with tg.Connection() as connection:

    activity = tg.Activity(connection)

    # Scrollable screen
    scroll = tg.NestedScrollView(activity)

    root = tg.LinearLayout(activity, scroll)

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title = tg.TextView(
        activity,
        "🐙 GITHUB MANAGER",
        root
    )
    title.settextsize(28)
    title.setmargin(8)

    subtitle = tg.TextView(
        activity,
        "Simple GitHub manager for Termux",
        root
    )
    subtitle.settextsize(16)
    subtitle.setmargin(5)

    # --------------------------------------------------------
    # GitHub connection
    # --------------------------------------------------------

    connection_title = tg.TextView(
        activity,
        "\n🔐 GitHub Connection",
        root
    )
    connection_title.settextsize(22)
    connection_title.setmargin(5)

    username_label = tg.TextView(
        activity,
        "GitHub Username",
        root
    )

    username_box = tg.EditText(
        activity,
        "",
        root,
        singleline=True
    )

    token_label = tg.TextView(
        activity,
        "Personal Access Token",
        root
    )

    token_box = tg.EditText(
        activity,
        "",
        root,
        singleline=True,
        inputtype="textPassword"
    )

    connect_button = tg.Button(
        activity,
        "🔐 Connect",
        root
    )

    disconnect_button = tg.Button(
        activity,
        "🔓 Disconnect",
        root
    )

    connection_status = tg.TextView(
        activity,
        "🔴 Not connected",
        root
    )

    # --------------------------------------------------------
    # Project
    # --------------------------------------------------------

    project_title = tg.TextView(
        activity,
        "\n📁 Project Folder",
        root
    )
    project_title.settextsize(22)
    project_title.setmargin(5)

    project_box = tg.EditText(
        activity,
        str(Path.home()),
        root,
        singleline=True
    )

    use_project_button = tg.Button(
        activity,
        "📁 Use Project",
        root
    )

    project_status = tg.TextView(
        activity,
        "No project selected.",
        root
    )

    # --------------------------------------------------------
    # Create GitHub repository
    # --------------------------------------------------------

    create_title = tg.TextView(
        activity,
        "\n☁️ Create GitHub Repository",
        root
    )
    create_title.settextsize(22)
    create_title.setmargin(5)

    repo_label = tg.TextView(
        activity,
        "Repository name",
        root
    )

    repo_box = tg.EditText(
        activity,
        "Hoji-App",
        root,
        singleline=True
    )

    description_label = tg.TextView(
        activity,
        "Description",
        root
    )

    description_box = tg.EditText(
        activity,
        "",
        root,
        singleline=True
    )

    private_box = tg.Checkbox(
        activity,
        "🔒 Private repository",
        root,
        True
    )

    create_button = tg.Button(
        activity,
        "➕ Create & Connect Repository",
        root
    )

    # --------------------------------------------------------
    # Repository information
    # --------------------------------------------------------

    repo_status = tg.TextView(
        activity,
        "🌿 Branch: unknown\n☁️ Remote: not connected",
        root
    )

    # --------------------------------------------------------
    # Sync buttons
    # --------------------------------------------------------

    sync_title = tg.TextView(
        activity,
        "\n📤 SYNC",
        root
    )
    sync_title.settextsize(22)
    sync_title.setmargin(5)

    upload_button = tg.Button(
        activity,
        "⬆️ Upload Changes",
        root
    )

    download_button = tg.Button(
        activity,
        "⬇️ Download Changes",
        root
    )

    sync_button = tg.Button(
        activity,
        "🔄 Sync Both Ways",
        root
    )

    # --------------------------------------------------------
    # Project actions
    # --------------------------------------------------------

    project_actions_title = tg.TextView(
        activity,
        "\n📊 PROJECT",
        root
    )
    project_actions_title.settextsize(22)
    project_actions_title.setmargin(5)

    changes_button = tg.Button(
        activity,
        "📋 Changes",
        root
    )

    history_button = tg.Button(
        activity,
        "📜 History",
        root
    )

    branches_button = tg.Button(
        activity,
        "🌿 Branches",
        root
    )

    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

    commit_label = tg.TextView(
        activity,
        "\n💾 Commit Message",
        root
    )
    commit_label.settextsize(18)

    commit_box = tg.EditText(
        activity,
        "",
        root,
        singleline=True
    )

    add_all_button = tg.Button(
        activity,
        "➕ Add All",
        root
    )

    commit_push_button = tg.Button(
        activity,
        "💾 Commit & Push",
        root
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    output_title = tg.TextView(
        activity,
        "\n📋 OUTPUT",
        root
    )
    output_title.settextsize(22)
    output_title.setmargin(5)

    output = tg.TextView(
        activity,
        "Ready.",
        root
    )
    output.setmargin(5)

    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    current_folder = ""
    current_repo = ""
    current_owner = ""

    # --------------------------------------------------------
    # Output helper
    # --------------------------------------------------------

    def show(message):
        try:
            output.settext(str(message))
        except Exception:
            pass

    # --------------------------------------------------------
    # Credentials
    # --------------------------------------------------------

    def get_credentials():
        username = username_box.gettext().strip()
        token = token_box.gettext().strip()

        if not username:
            show("❌ Enter your GitHub username.")
            return None, None

        if not token:
            show("❌ Enter your GitHub Personal Access Token.")
            return None, None

        return username, token

    # --------------------------------------------------------
    # Temporary Git authentication
    # --------------------------------------------------------

    def git_environment():
        """
        GitHub HTTPS authentication.

        The token is NOT placed inside:
            https://username:token@github.com/...

        Instead GIT_ASKPASS supplies it only while Git runs.
        """

        username, token = get_credentials()

        if not username or not token:
            return None, None, None

        askpass_dir = tempfile.mkdtemp(prefix="github_askpass_")
        askpass_file = os.path.join(askpass_dir, "askpass.sh")

        script = """#!/data/data/com.termux/files/usr/bin/sh
case "$1" in
    *Username*) printf '%s\\n' "$GITHUB_GUI_USERNAME" ;;
    *Password*) printf '%s\\n' "$GITHUB_GUI_TOKEN" ;;
    *) printf '\\n' ;;
esac
"""

        with open(askpass_file, "w") as f:
            f.write(script)

        os.chmod(askpass_file, 0o700)

        env = os.environ.copy()

        env["GIT_ASKPASS"] = askpass_file
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GITHUB_GUI_USERNAME"] = username
        env["GITHUB_GUI_TOKEN"] = token

        return env, askpass_dir, token

    # --------------------------------------------------------
    # Refresh repository information
    # --------------------------------------------------------

    def refresh_repo_info():
        nonlocal_current = None

        if not current_folder:
            repo_status.settext(
                "🌿 Branch: unknown\n"
                "☁️ Remote: not connected"
            )
            return

        ok, branch = run_git(
            current_folder,
            ["branch", "--show-current"]
        )

        if not ok or not branch:
            branch = "unknown"

        ok2, remote = run_git(
            current_folder,
            ["remote", "get-url", "origin"]
        )

        if not ok2:
            remote = "not connected"

        repo_status.settext(
            "🌿 Branch: " + safe_text(branch) +
            "\n☁️ Remote: " + safe_text(remote)
        )

    # --------------------------------------------------------
    # Use project
    # --------------------------------------------------------

    def use_project():
        nonlocal_placeholder = None

        global current_folder

        folder = project_box.gettext().strip()

        if not folder:
            show("❌ Enter a project folder.")
            return

        folder = os.path.expanduser(folder)

        if not os.path.isdir(folder):
            show("❌ Folder does not exist:\n" + folder)
            return

        current_folder = os.path.abspath(folder)

        project_status.settext(
            "📁 Project:\n" + current_folder
        )

        ok, out = run_git(
            current_folder,
            ["rev-parse", "--is-inside-work-tree"]
        )

        if ok:
            show(
                "✅ Git repository loaded.\n\n"
                + current_folder
            )
        else:
            show(
                "ℹ️ This folder is not a Git repository yet.\n"
                "Create & Connect Repository will initialize it."
            )

        refresh_repo_info()

    # --------------------------------------------------------
    # Connect
    # --------------------------------------------------------

    def connect_github():
        username, token = get_credentials()

        if not username or not token:
            return

        ok, data = api_request(
            token,
            "GET",
            "/user"
        )

        if not ok:
            msg = data.get("data", {}).get(
                "message",
                "Authentication failed."
            )

            connection_status.settext(
                "🔴 Connection failed"
            )

            show(
                "❌ GitHub connection failed.\n\n"
                + str(msg)
            )

            return

        actual_username = data.get("login", username)

        username_box.settext(actual_username)

        connection_status.settext(
            "🟢 Connected as @" + actual_username
        )

        show(
            "✅ GitHub connected.\n\n"
            "Account: @" + actual_username
        )

    # --------------------------------------------------------
    # Disconnect
    # --------------------------------------------------------

    def disconnect_github():
        token_box.settext("")

        connection_status.settext(
            "🔴 Not connected"
        )

        show("🔓 GitHub disconnected.")

    # --------------------------------------------------------
    # Initialize Git repository
    # --------------------------------------------------------

    def ensure_git_repository(folder):
        git_folder = os.path.join(folder, ".git")

        if not os.path.isdir(git_folder):

            ok, out = run_git(
                folder,
                ["init"]
            )

            if not ok:
                return False, out

        # Always use main
        ok, out = run_git(
            folder,
            ["checkout", "-B", "main"]
        )

        if not ok:
            return False, out

        # Configure default identity only if Git has none.
        ok_name, name = run_git(
            folder,
            ["config", "user.name"]
        )

        ok_email, email = run_git(
            folder,
            ["config", "user.email"]
        )

        if not ok_name or not name.strip():
            run_git(
                folder,
                ["config", "user.name", "Termux GitHub User"]
            )

        if not ok_email or not email.strip():
            run_git(
                folder,
                ["config", "user.email", "termux@localhost"]
            )

        return True, "Git repository ready."

    # --------------------------------------------------------
    # Set remote
    # --------------------------------------------------------

    def set_remote(folder, owner, repo):
        # IMPORTANT:
        # The remote contains only the normal HTTPS URL.
        # No token is placed inside it.
        remote_url = (
            "https://github.com/"
            + owner
            + "/"
            + repo
            + ".git"
        )

        ok, existing = run_git(
            folder,
            ["remote", "get-url", "origin"]
        )

        if ok:
            ok2, out = run_git(
                folder,
                ["remote", "set-url", "origin", remote_url]
            )
        else:
            ok2, out = run_git(
                folder,
                ["remote", "add", "origin", remote_url]
            )

        if not ok2:
            return False, out

        return True, remote_url

    # --------------------------------------------------------
    # Create GitHub repository
    # --------------------------------------------------------

    def create_repository():
        global current_folder
        global current_repo
        global current_owner

        username, token = get_credentials()

        if not username or not token:
            return

        folder = project_box.gettext().strip()

        if not folder:
            show("❌ Enter your project folder first.")
            return

        folder = os.path.abspath(
            os.path.expanduser(folder)
        )

        if not os.path.isdir(folder):
            show(
                "❌ Project folder does not exist:\n"
                + folder
            )
            return

        raw_name = repo_box.gettext().strip()

        if not raw_name:
            show("❌ Enter a repository name.")
            return

        # THE IMPORTANT FIX
        repo_name = clean_repo_name(raw_name)

        if repo_name != raw_name:
            repo_box.settext(repo_name)

        description = description_box.gettext().strip()

        private = False

        try:
            private = private_box.ischecked()
        except Exception:
            pass

        show(
            "⏳ Creating GitHub repository:\n\n"
            + username
            + "/"
            + repo_name
        )

        data = {
            "name": repo_name,
            "description": description,
            "private": private,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": True
        }

        ok, result = api_request(
            token,
            "POST",
            "/user/repos",
            data
        )

        if not ok:

            status = result.get("status", 0)

            details = result.get(
                "data",
                {}
            )

            message = details.get(
                "message",
                "Unknown GitHub error."
            )

            # If repository already exists, offer to connect it.
            if status == 422:

                show(
                    "⚠️ GitHub did not create a new repository.\n\n"
                    + str(message)
                    + "\n\n"
                    "Trying to connect the existing repository..."
                )

                ok_get, existing = api_request(
                    token,
                    "GET",
                    "/repos/"
                    + username
                    + "/"
                    + repo_name
                )

                if not ok_get:
                    show(
                        "❌ Repository creation failed.\n\n"
                        + str(message)
                    )
                    return

                # Existing repo is accessible.
                pass

            else:
                show(
                    "❌ GitHub repository creation failed.\n\n"
                    "HTTP: "
                    + str(status)
                    + "\n\n"
                    + str(message)
                )

                return

        current_folder = folder
        current_owner = username
        current_repo = repo_name

        project_box.settext(folder)

        project_status.settext(
            "📁 Project:\n" + folder
        )

        ok_git, git_message = ensure_git_repository(
            folder
        )

        if not ok_git:
            show(
                "❌ Git initialization failed:\n\n"
                + git_message
            )
            return

        ok_remote, remote_result = set_remote(
            folder,
            username,
            repo_name
        )

        if not ok_remote:
            show(
                "❌ Could not set GitHub remote:\n\n"
                + remote_result
            )
            return

        refresh_repo_info()

        show(
            "✅ Repository connected!\n\n"
            "GitHub:\n"
            "https://github.com/"
            + username
            + "/"
            + repo_name
            + "\n\n"
            "Local:\n"
            + folder
            + "\n\n"
            "Branch: main"
        )

    # --------------------------------------------------------
    # Add all
    # --------------------------------------------------------

    def add_all():
        if not current_folder:
            show("❌ Select a project first.")
            return

        ok, out = run_git(
            current_folder,
            ["add", "-A"]
        )

        if ok:
            show("✅ All changes added to Git.\n\n" + out)
        else:
            show("❌ git add failed:\n\n" + out)

    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

    def commit_only():
        if not current_folder:
            show("❌ Select a project first.")
            return False

        message = commit_box.gettext().strip()

        if not message:
            show("❌ Enter a commit message.")
            return False

        ok, out = run_git(
            current_folder,
            ["add", "-A"]
        )

        if not ok:
            show("❌ git add failed:\n\n" + out)
            return False

        ok, out = run_git(
            current_folder,
            ["commit", "-m", message]
        )

        if not ok:
            show(
                "❌ Commit failed.\n\n"
                + out
            )
            return False

        return True

    # --------------------------------------------------------
    # Push
    # --------------------------------------------------------

    def push_changes():
        if not current_folder:
            show("❌ Select a project first.")
            return

        env, temp_dir, token = git_environment()

        if env is None:
            return

        try:

            # Make sure origin exists
            ok, remote = run_git(
                current_folder,
                ["remote", "get-url", "origin"]
            )

            if not ok:
                show(
                    "❌ No GitHub remote configured.\n\n"
                    "Use Create & Connect Repository first."
                )
                return

            ok, branch = run_git(
                current_folder,
                ["branch", "--show-current"]
            )

            if not ok or not branch:
                branch = "main"

            show(
                "⏳ Pushing to GitHub..."
            )

            ok, out = run_git(
                current_folder,
                [
                    "push",
                    "-u",
                    "origin",
                    branch
                ],
                env
            )

            if ok:
                show(
                    "✅ Push successful!\n\n"
                    + out
                )
            else:
                show(
                    "❌ Push failed.\n\n"
                    + out
                )

            refresh_repo_info()

        finally:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

    # --------------------------------------------------------
    # Commit & Push
    # --------------------------------------------------------

    def commit_and_push():
        if not commit_only():
            return

        push_changes()

    # --------------------------------------------------------
    # Pull
    # --------------------------------------------------------

    def pull_changes():
        if not current_folder:
            show("❌ Select a project first.")
            return

        env, temp_dir, token = git_environment()

        if env is None:
            return

        try:

            show(
                "⏳ Downloading changes from GitHub..."
            )

            ok, out = run_git(
                current_folder,
                [
                    "pull",
                    "--rebase",
                    "origin",
                    "main"
                ],
                env
            )

            if ok:
                show(
                    "✅ Download successful!\n\n"
                    + out
                )
            else:
                show(
                    "❌ Download failed.\n\n"
                    + out
                )

            refresh_repo_info()

        finally:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

    # --------------------------------------------------------
    # Sync both ways
    # --------------------------------------------------------

    def sync_both():
        if not current_folder:
            show("❌ Select a project first.")
            return

        env, temp_dir, token = git_environment()

        if env is None:
            return

        try:

            show("⏳ Syncing with GitHub...")

            # Fetch first
            ok, out = run_git(
                current_folder,
                ["fetch", "origin"],
                env
            )

            if not ok:
                show(
                    "❌ Fetch failed.\n\n"
                    + out
                )
                return

            # Pull/rebase
            ok, out = run_git(
                current_folder,
                [
                    "pull",
                    "--rebase",
                    "origin",
                    "main"
                ],
                env
            )

            if not ok:
                show(
                    "❌ Pull/rebase failed.\n\n"
                    + out
                )
                return

            # Push local commits
            ok, out = run_git(
                current_folder,
                [
                    "push",
                    "-u",
                    "origin",
                    "main"
                ],
                env
            )

            if ok:
                show(
                    "✅ Sync completed!\n\n"
                    + out
                )
            else:
                show(
                    "❌ Push during sync failed.\n\n"
                    + out
                )

            refresh_repo_info()

        finally:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

    # --------------------------------------------------------
    # Changes
    # --------------------------------------------------------

    def show_changes():
        if not current_folder:
            show("❌ Select a project first.")
            return

        ok, out = run_git(
            current_folder,
            [
                "status",
                "--short"
            ]
        )

        if ok:

            if not out:
                out = "Working tree is clean."

            show(
                "📋 CHANGES\n\n"
                + out
            )

        else:
            show(
                "❌ Status failed:\n\n"
                + out
            )

    # --------------------------------------------------------
    # History
    # --------------------------------------------------------

    def show_history():
        if not current_folder:
            show("❌ Select a project first.")
            return

        ok, out = run_git(
            current_folder,
            [
                "log",
                "--oneline",
                "--decorate",
                "-20"
            ]
        )

        if ok:
            show(
                "📜 HISTORY\n\n"
                + (out or "No commits yet.")
            )
        else:
            show(
                "❌ History failed:\n\n"
                + out
            )

    # --------------------------------------------------------
    # Branches
    # --------------------------------------------------------

    def show_branches():
        if not current_folder:
            show("❌ Select a project first.")
            return

        ok, out = run_git(
            current_folder,
            [
                "branch",
                "-a"
            ]
        )

        if ok:
            show(
                "🌿 BRANCHES\n\n"
                + (out or "No branches.")
            )
        else:
            show(
                "❌ Branch command failed:\n\n"
                + out
            )

    # --------------------------------------------------------
    # Event loop
    # --------------------------------------------------------

    try:

        for event in connection.events():

            if (
                event.type == tg.Event.destroy
                and event.value.get("finishing", False)
            ):
                sys.exit()

            if event.type != tg.Event.click:
                continue

            clicked = event.value["id"]

            # --------------------------------------------
            # Connection
            # --------------------------------------------

            if clicked == connect_button:
                connect_github()

            elif clicked == disconnect_button:
                disconnect_github()

            # --------------------------------------------
            # Project
            # --------------------------------------------

            elif clicked == use_project_button:
                use_project()

            # --------------------------------------------
            # Create repository
            # --------------------------------------------

            elif clicked == create_button:
                create_repository()

            # --------------------------------------------
            # Sync
            # --------------------------------------------

            elif clicked == upload_button:
                add_all()

                if current_folder:
                    push_changes()

            elif clicked == download_button:
                pull_changes()

            elif clicked == sync_button:
                sync_both()

            # --------------------------------------------
            # Project
            # --------------------------------------------

            elif clicked == changes_button:
                show_changes()

            elif clicked == history_button:
                show_history()

            elif clicked == branches_button:
                show_branches()

            # --------------------------------------------
            # Commit
            # --------------------------------------------

            elif clicked == add_all_button:
                add_all()

            elif clicked == commit_push_button:
                commit_and_push()

    except KeyboardInterrupt:
        try:
            activity.finish()
        except Exception:
            pass