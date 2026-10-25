import os
import subprocess
import sys
import termuxgui as tg


# ============================================================
# SETTINGS
# ============================================================

SHARED = os.path.expanduser("~/storage/shared")

# If Android shared storage is unavailable,
# use the Termux home directory.
if not os.path.isdir(SHARED):
    SHARED = os.path.expanduser("~")

current_path = SHARED


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_size(size):
    if size < 1024:
        return f"{size} B"

    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"

    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"

    return f"{size / (1024 * 1024 * 1024):.1f} GB"


def open_file(path):
    try:
        subprocess.Popen(
            ["termux-open", path]
        )

        status.settext("Opening file...")

    except Exception as e:
        status.settext(
            f"Cannot open file:\n{e}"
        )


def display_path(path):

    shared = os.path.expanduser(
        "~/storage/shared"
    )

    if path.startswith(shared):

        result = path.replace(
            shared,
            "/storage/emulated/0",
            1
        )

        if result == "":
            return "/storage/emulated/0"

        return result

    return path


# ============================================================
# GUI
# ============================================================

with tg.Connection() as c:

    a = tg.Activity(c)

    # ========================================================
    # MAIN LAYOUT
    # ========================================================

    root = tg.LinearLayout(a)

    root.setheight(
        tg.View.MATCH_PARENT
    )


    # ========================================================
    # TITLE
    # ========================================================

    title = tg.TextView(
        a,
        "📁  FILE MANAGER",
        root
    )

    title.settextsize(22)

    title.setlinearlayoutparams(0)

    title.setheight(
        tg.View.WRAP_CONTENT
    )

    title.setmargin(5)


    # ========================================================
    # CURRENT PATH
    # ========================================================

    path_view = tg.TextView(
        a,
        display_path(current_path),
        root
    )

    path_view.settextsize(12)

    path_view.setlinearlayoutparams(0)

    path_view.setheight(
        tg.View.WRAP_CONTENT
    )

    path_view.setmargin(5)


    # ========================================================
    # NAVIGATION BUTTONS
    # ========================================================

    nav = tg.LinearLayout(
        a,
        root,
        False
    )

    nav.setlinearlayoutparams(0)

    nav.setheight(
        tg.View.WRAP_CONTENT
    )


    back_button = tg.Button(
        a,
        "⬅ Back",
        nav
    )


    home_button = tg.Button(
        a,
        "🏠 Home",
        nav
    )


    refresh_button = tg.Button(
        a,
        "🔄 Refresh",
        nav
    )


    # Try to keep navigation buttons compact.
    back_button.setwidth(120)
    home_button.setwidth(120)
    refresh_button.setwidth(120)


    # ========================================================
    # STATUS
    # ========================================================

    status = tg.TextView(
        a,
        "Ready",
        root
    )

    status.settextsize(12)

    status.setlinearlayoutparams(0)

    status.setheight(
        tg.View.WRAP_CONTENT
    )

    status.setmargin(5)


    # ========================================================
    # SCROLLABLE FILE LIST
    # ========================================================

    scroll = tg.NestedScrollView(
        a,
        root
    )

    # Give the file area all remaining space.
    scroll.setlinearlayoutparams(1)


    file_list = tg.LinearLayout(
        a,
        scroll
    )


    # ========================================================
    # FILE BUTTONS
    # ========================================================

    file_buttons = []

    for i in range(100):

        button = tg.Button(
            a,
            "",
            file_list
        )

        button.setlinearlayoutparams(0)

        button.setheight(
            tg.View.WRAP_CONTENT
        )

        file_buttons.append(button)


    # ========================================================
    # LOAD DIRECTORY
    # ========================================================

    def load_directory(path):

        global current_path

        try:

            path = os.path.abspath(path)


            # Make sure it exists
            if not os.path.isdir(path):

                status.settext(
                    "Folder does not exist."
                )

                return


            current_path = path


            # Update path display
            path_view.settext(
                display_path(current_path)
            )


            # Read directory
            try:

                entries = os.listdir(
                    current_path
                )

            except PermissionError:

                status.settext(
                    "Permission denied."
                )

                return


            # =================================================
            # SORT
            # FOLDERS FIRST
            # =================================================

            entries.sort(
                key=lambda name: (
                    not os.path.isdir(
                        os.path.join(
                            current_path,
                            name
                        )
                    ),
                    name.lower()
                )
            )


            # =================================================
            # UPDATE FILE BUTTONS
            # =================================================

            for i, button in enumerate(
                file_buttons
            ):

                if i < len(entries):

                    name = entries[i]

                    full_path = os.path.join(
                        current_path,
                        name
                    )


                    # Folder
                    if os.path.isdir(
                        full_path
                    ):

                        button.settext(
                            f"📁  {name}"
                        )


                    # File
                    else:

                        try:

                            size = format_size(
                                os.path.getsize(
                                    full_path
                                )
                            )

                            button.settext(
                                f"📄  {name}  •  {size}"
                            )

                        except:

                            button.settext(
                                f"📄  {name}"
                            )


                    # Store path
                    button.file_path = full_path


                else:

                    # Hide unused buttons
                    button.settext("")

                    button.file_path = None


            status.settext(
                f"{len(entries)} items"
            )


        except Exception as e:

            status.settext(
                f"Error:\n{e}"
            )


    # ========================================================
    # START IN ANDROID SHARED STORAGE
    # ========================================================

    load_directory(
        SHARED
    )


    # ========================================================
    # EVENT LOOP
    # ========================================================

    for ev in c.events():


        # ====================================================
        # APP CLOSED
        # ====================================================

        if ev.type == tg.Event.destroy:

            if ev.value["finishing"]:

                sys.exit()


        # ====================================================
        # BUTTON CLICK
        # ====================================================

        if ev.type == tg.Event.click:

            clicked = ev.value["id"]


            # =================================================
            # BACK
            # =================================================

            if clicked == back_button:

                parent = os.path.dirname(
                    current_path
                )

                if parent != current_path:

                    load_directory(
                        parent
                    )


            # =================================================
            # HOME
            # =================================================

            elif clicked == home_button:

                load_directory(
                    SHARED
                )


            # =================================================
            # REFRESH
            # =================================================

            elif clicked == refresh_button:

                load_directory(
                    current_path
                )


            # =================================================
            # FILE / FOLDER
            # =================================================

            else:

                selected = None


                for button in file_buttons:

                    if clicked == button:

                        selected = getattr(
                            button,
                            "file_path",
                            None
                        )

                        break


                if selected:

                    # Folder
                    if os.path.isdir(
                        selected
                    ):

                        load_directory(
                            selected
                        )


                    # File
                    else:

                        open_file(
                            selected
                        )