import os
import sys
import shutil
import subprocess
import termuxgui as tg


# ============================================================
# SETTINGS
# ============================================================

SHARED = os.path.expanduser("~/storage/shared")

if not os.path.isdir(SHARED):
    SHARED = os.path.expanduser("~")

current_path = SHARED
search_text = ""


# ============================================================
# HELPERS
# ============================================================

def format_size(size):
    if size < 1024:
        return f"{size} B"

    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"

    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"

    return f"{size / (1024 * 1024 * 1024):.1f} GB"


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


def open_file(path):

    try:

        subprocess.Popen(
            ["termux-open", path]
        )

        status.settext(
            "Opening..."
        )

    except Exception as e:

        status.settext(
            f"Cannot open file: {e}"
        )


def show_message(title_text, message):

    dialog = tg.Activity(
        c,
        dialog=True
    )

    layout = tg.LinearLayout(
        dialog
    )

    title = tg.TextView(
        dialog,
        title_text,
        layout
    )

    title.settextsize(22)
    title.setmargin(8)

    text = tg.TextView(
        dialog,
        message,
        layout
    )

    text.setmargin(8)

    ok = tg.Button(
        dialog,
        "OK",
        layout
    )

    for ev in c.events():

        if ev.type == tg.Event.destroy:

            if ev.value["finishing"]:
                return

        if ev.type == tg.Event.click:

            if ev.value["id"] == ok:

                dialog.finish()
                return


def input_dialog(title_text, default_text=""):

    dialog = tg.Activity(
        c,
        dialog=True
    )

    layout = tg.LinearLayout(
        dialog
    )

    title = tg.TextView(
        dialog,
        title_text,
        layout
    )

    title.settextsize(22)
    title.setmargin(8)

    edit = tg.EditText(
        dialog,
        default_text,
        layout
    )

    buttons = tg.LinearLayout(
        dialog,
        layout,
        False
    )

    ok = tg.Button(
        dialog,
        "OK",
        buttons
    )

    cancel = tg.Button(
        dialog,
        "Cancel",
        buttons
    )

    for ev in c.events():

        if ev.type == tg.Event.destroy:

            if ev.value["finishing"]:
                return None

        if ev.type == tg.Event.click:

            clicked = ev.value["id"]

            if clicked == ok:

                value = edit.gettext()

                dialog.finish()

                return value

            if clicked == cancel:

                dialog.finish()

                return None


def confirm_dialog(title_text, message):

    dialog = tg.Activity(
        c,
        dialog=True
    )

    layout = tg.LinearLayout(
        dialog
    )

    title = tg.TextView(
        dialog,
        title_text,
        layout
    )

    title.settextsize(22)
    title.setmargin(8)

    text = tg.TextView(
        dialog,
        message,
        layout
    )

    text.setmargin(8)

    buttons = tg.LinearLayout(
        dialog,
        layout,
        False
    )

    yes = tg.Button(
        dialog,
        "Yes",
        buttons
    )

    no = tg.Button(
        dialog,
        "Cancel",
        buttons
    )

    for ev in c.events():

        if ev.type == tg.Event.destroy:

            if ev.value["finishing"]:
                return False

        if ev.type == tg.Event.click:

            clicked = ev.value["id"]

            if clicked == yes:

                dialog.finish()

                return True

            if clicked == no:

                dialog.finish()

                return False


def choose_destination():

    default = display_path(
        current_path
    )

    return input_dialog(
        "Destination folder",
        default
    )


# ============================================================
# FILE OPERATIONS
# ============================================================

def create_folder():

    name = input_dialog(
        "New folder name"
    )

    if not name:
        return

    name = name.strip()

    if not name:
        return

    destination = os.path.join(
        current_path,
        name
    )

    if os.path.exists(destination):

        show_message(
            "Already exists",
            "A file or folder with that name already exists."
        )

        return

    try:

        os.makedirs(destination)

        status.settext(
            f"Created folder: {name}"
        )

        load_directory(
            current_path
        )

    except Exception as e:

        show_message(
            "Error",
            str(e)
        )


def rename_item(path):

    old_name = os.path.basename(
        path
    )

    new_name = input_dialog(
        "Rename",
        old_name
    )

    if not new_name:
        return

    new_name = new_name.strip()

    if not new_name:
        return

    new_path = os.path.join(
        os.path.dirname(path),
        new_name
    )

    if os.path.exists(new_path):

        show_message(
            "Already exists",
            "Another file or folder already has that name."
        )

        return

    try:

        os.rename(
            path,
            new_path
        )

        status.settext(
            f"Renamed to {new_name}"
        )

        load_directory(
            current_path
        )

    except Exception as e:

        show_message(
            "Rename failed",
            str(e)
        )


def delete_item(path):

    name = os.path.basename(
        path
    )

    answer = confirm_dialog(
        "Delete",
        f"Delete '{name}'?"
    )

    if not answer:
        return

    try:

        if os.path.isdir(path):

            shutil.rmtree(
                path
            )

        else:

            os.remove(
                path
            )

        status.settext(
            f"Deleted: {name}"
        )

        load_directory(
            current_path
        )

    except Exception as e:

        show_message(
            "Delete failed",
            str(e)
        )


def copy_item(path):

    destination = choose_destination()

    if not destination:
        return

    destination = os.path.expanduser(
        destination
    )

    # Convert Android shared-storage path
    if destination.startswith(
        "/storage/emulated/0"
    ):

        destination = destination.replace(
            "/storage/emulated/0",
            os.path.expanduser(
                "~/storage/shared"
            ),
            1
        )

    if not os.path.isdir(destination):

        show_message(
            "Invalid destination",
            "The destination folder does not exist."
        )

        return

    name = os.path.basename(
        path
    )

    target = os.path.join(
        destination,
        name
    )

    if os.path.exists(target):

        show_message(
            "Already exists",
            f"{name} already exists there."
        )

        return

    try:

        if os.path.isdir(path):

            shutil.copytree(
                path,
                target
            )

        else:

            shutil.copy2(
                path,
                target
            )

        status.settext(
            f"Copied: {name}"
        )

    except Exception as e:

        show_message(
            "Copy failed",
            str(e)
        )


def move_item(path):

    destination = choose_destination()

    if not destination:
        return

    destination = os.path.expanduser(
        destination
    )

    if destination.startswith(
        "/storage/emulated/0"
    ):

        destination = destination.replace(
            "/storage/emulated/0",
            os.path.expanduser(
                "~/storage/shared"
            ),
            1
        )

    if not os.path.isdir(destination):

        show_message(
            "Invalid destination",
            "The destination folder does not exist."
        )

        return

    name = os.path.basename(
        path
    )

    target = os.path.join(
        destination,
        name
    )

    if os.path.exists(target):

        show_message(
            "Already exists",
            f"{name} already exists there."
        )

        return

    try:

        shutil.move(
            path,
            target
        )

        status.settext(
            f"Moved: {name}"
        )

        load_directory(
            current_path
        )

    except Exception as e:

        show_message(
            "Move failed",
            str(e)
        )


def share_item(path):

    try:

        subprocess.Popen(
            ["termux-share", path]
        )

        status.settext(
            "Opening share menu..."
        )

    except Exception as e:

        show_message(
            "Share unavailable",
            "termux-share could not be started.\n\n"
            "Install Termux:API if necessary."
        )


# ============================================================
# LONG-PRESS MENU
# ============================================================

def item_menu(path):

    name = os.path.basename(
        path
    )

    dialog = tg.Activity(
        c,
        dialog=True
    )

    layout = tg.LinearLayout(
        dialog
    )

    title = tg.TextView(
        dialog,
        f"📁 {name}",
        layout
    )

    title.settextsize(20)
    title.setmargin(8)

    rename = tg.Button(
        dialog,
        "✏️ Rename",
        layout
    )

    copy = tg.Button(
        dialog,
        "📋 Copy",
        layout
    )

    move = tg.Button(
        dialog,
        "📦 Move",
        layout
    )

    share = tg.Button(
        dialog,
        "📤 Share",
        layout
    )

    delete = tg.Button(
        dialog,
        "🗑️ Delete",
        layout
    )

    cancel = tg.Button(
        dialog,
        "Cancel",
        layout
    )

    for ev in c.events():

        if ev.type == tg.Event.destroy:

            if ev.value["finishing"]:
                return

        if ev.type == tg.Event.click:

            clicked = ev.value["id"]

            if clicked == rename:

                dialog.finish()

                rename_item(
                    path
                )

                return

            if clicked == copy:

                dialog.finish()

                copy_item(
                    path
                )

                return

            if clicked == move:

                dialog.finish()

                move_item(
                    path
                )

                return

            if clicked == share:

                dialog.finish()

                share_item(
                    path
                )

                return

            if clicked == delete:

                dialog.finish()

                delete_item(
                    path
                )

                return

            if clicked == cancel:

                dialog.finish()

                return


# ============================================================
# SEARCH
# ============================================================

def perform_search():

    global search_text

    search_text = search_box.gettext().strip().lower()

    load_directory(
        current_path
    )


def clear_search():

    global search_text

    search_text = ""

    search_box.settext("")

    load_directory(
        current_path
    )


# ============================================================
# MAIN GUI
# ============================================================

with tg.Connection() as c:

    a = tg.Activity(c)

    root = tg.LinearLayout(a)


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
    # PATH
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
    # NAVIGATION
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


    # ========================================================
    # ACTIONS
    # ========================================================

    actions = tg.LinearLayout(
        a,
        root,
        False
    )

    actions.setlinearlayoutparams(0)
    actions.setheight(
        tg.View.WRAP_CONTENT
    )

    new_folder = tg.Button(
        a,
        "📁+ New",
        actions
    )

    search_button = tg.Button(
        a,
        "🔎 Search",
        actions
    )


    # ========================================================
    # SEARCH BAR
    # ========================================================

    search_row = tg.LinearLayout(
        a,
        root,
        False
    )

    search_row.setlinearlayoutparams(0)
    search_row.setheight(
        tg.View.WRAP_CONTENT
    )

    search_box = tg.EditText(
        a,
        "",
        search_row
    )

    clear_button = tg.Button(
        a,
        "✖",
        search_row
    )


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
    # SCROLL AREA
    # ========================================================

    scroll = tg.NestedScrollView(
        a,
        root
    )

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

        # Enable long press
        button.sendlongclickevent(True)

        file_buttons.append(
            button
        )


    # ========================================================
    # DIRECTORY LOADER
    # ========================================================

    def load_directory(path):

        global current_path

        try:

            path = os.path.abspath(
                path
            )

            if not os.path.isdir(path):

                status.settext(
                    "Folder does not exist."
                )

                return

            current_path = path

            path_view.settext(
                display_path(
                    current_path
                )
            )


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
            # SEARCH FILTER
            # =================================================

            if search_text:

                entries = [
                    x for x in entries
                    if search_text in x.lower()
                ]


            # =================================================
            # SORT
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
            # DISPLAY
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


                    if os.path.isdir(
                        full_path
                    ):

                        button.settext(
                            f"📁  {name}"
                        )

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


                    button.file_path = full_path


                else:

                    button.settext("")

                    button.file_path = None


            if search_text:

                status.settext(
                    f"Search: {search_text} • "
                    f"{len(entries)} result(s)"
                )

            else:

                status.settext(
                    f"{len(entries)} items"
                )


        except Exception as e:

            status.settext(
                f"Error: {e}"
            )


    # ========================================================
    # INITIAL LOAD
    # ========================================================

    load_directory(
        SHARED
    )


    # ========================================================
    # EVENT LOOP
    # ========================================================

    for ev in c.events():

        # ====================================================
        # CLOSE
        # ====================================================

        if ev.type == tg.Event.destroy:

            if ev.value["finishing"]:

                sys.exit()


        # ====================================================
        # NORMAL CLICK
        # ====================================================

        if ev.type == tg.Event.click:

            clicked = ev.value["id"]


            # Back
            if clicked == back_button:

                parent = os.path.dirname(
                    current_path
                )

                if parent != current_path:

                    load_directory(
                        parent
                    )


            # Home
            elif clicked == home_button:

                load_directory(
                    SHARED
                )


            # Refresh
            elif clicked == refresh_button:

                load_directory(
                    current_path
                )


            # New folder
            elif clicked == new_folder:

                create_folder()


            # Search
            elif clicked == search_button:

                perform_search()


            # Clear search
            elif clicked == clear_button:

                clear_search()


            # File/folder button
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

                    if os.path.isdir(
                        selected
                    ):

                        # Opening a folder clears
                        # the search filter.
                        search_text = ""

                        search_box.settext("")

                        load_directory(
                            selected
                        )

                    else:

                        open_file(
                            selected
                        )


        # ====================================================
        # LONG PRESS
        # ====================================================

        if ev.type == tg.Event.longClick:

            clicked = ev.value["id"]

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

                item_menu(
                    selected
                )