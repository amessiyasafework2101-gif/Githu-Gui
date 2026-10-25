import os
import subprocess
import sys
import termuxgui as tg


HOME = os.path.expanduser("~")

CUSTOM_COMMANDS = {
    "List Files": "ls -lah",
    "Python Version": "python --version",
    "Disk Usage": "df -h",
    "Who Am I": "whoami",
}


def run_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=HOME,
            capture_output=True,
            text=True,
            timeout=60
        )

        return result.stdout + result.stderr

    except Exception as e:
        return f"Error: {e}"


with tg.Connection() as c:

    # Create the Android Activity
    a = tg.Activity(c)

    # Main vertical layout
    root = tg.LinearLayout(a)

    # Title
    title = tg.TextView(
        a,
        "TERMUX CONTROL CENTER",
        root
    )
    title.settextsize(24)

    # Output area
    output = tg.TextView(
        a,
        "Ready.",
        root
    )

    # File Manager
    file_button = tg.Button(
        a,
        "📁 File Manager",
        root
    )

    # Git buttons
    status_button = tg.Button(
        a,
        "📊 Git Status",
        root
    )

    pull_button = tg.Button(
        a,
        "⬇️ Git Pull",
        root
    )

    push_button = tg.Button(
        a,
        "⬆️ Git Push",
        root
    )

    # Terminal
    terminal_button = tg.Button(
        a,
        "💻 Open Terminal",
        root
    )

    # Custom commands title
    custom_title = tg.TextView(
        a,
        "CUSTOM COMMANDS",
        root
    )

    custom_buttons = {}

    for name, command in CUSTOM_COMMANDS.items():

        custom_buttons[name] = tg.Button(
            a,
            f"▶ {name}",
            root
        )

    # Wait for button events
    for ev in c.events():

        # Close program when Activity is closed
        if ev.type == tg.Event.destroy:
            if ev.value["finishing"]:
                sys.exit()

        # Button clicked
        if ev.type == tg.Event.click:

            # File Manager
            if ev.value["id"] == file_button:

                try:
                    subprocess.Popen(
                        ["termux-gui-files", HOME]
                    )

                    output.settext(
                        "File manager opened."
                    )

                except Exception as e:

                    output.settext(
                        f"File manager error:\n{e}"
                    )

            # Git Status
            elif ev.value["id"] == status_button:

                result = run_command("git status")

                output.settext(
                    "GIT STATUS\n\n" + result
                )

            # Git Pull
            elif ev.value["id"] == pull_button:

                output.settext(
                    "Running git pull..."
                )

                result = run_command("git pull")

                output.settext(
                    "GIT PULL\n\n" + result
                )

            # Git Push
            elif ev.value["id"] == push_button:

                output.settext(
                    "Running git push..."
                )

                result = run_command("git push")

                output.settext(
                    "GIT PUSH\n\n" + result
                )

            # Open Termux
            elif ev.value["id"] == terminal_button:

                try:

                    subprocess.Popen(
                        [
                            "am",
                            "start",
                            "-n",
                            "com.termux/.app.TermuxActivity"
                        ]
                    )

                    output.settext(
                        "Termux terminal opened."
                    )

                except Exception as e:

                    output.settext(
                        f"Terminal error:\n{e}"
                    )

            # Custom commands
            else:

                for name, button in custom_buttons.items():

                    if ev.value["id"] == button:

                        command = CUSTOM_COMMANDS[name]

                        output.settext(
                            f"Running:\n{command}\n"
                        )

                        result = run_command(command)

                        output.settext(
                            f"{name}\n\n{result}"
                        )