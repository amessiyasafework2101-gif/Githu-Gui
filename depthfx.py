#!/usr/bin/env python3

import os
import sys
import time
import math
import subprocess
import threading

import cv2
import numpy as np


# ============================================================
# DEPTH3D TERMUX GUI
# AI-FREE
# Python + OpenCV + NumPy + FFmpeg
# ============================================================


# ------------------------------------------------------------
# COLORS
# ------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
WHITE = "\033[97m"
GRAY = "\033[90m"


# ------------------------------------------------------------
# GLOBAL SETTINGS
# ------------------------------------------------------------

input_file = None

strength = 18
movement = "horizontal"
resolution = 480

processing = False
stop_requested = False


# ============================================================
# TERMINAL FUNCTIONS
# ============================================================

def clear():
    os.system("clear")


def pause():
    input(
        f"\n{GRAY}Press ENTER to continue...{RESET}"
    )


def header():

    print(
        f"{CYAN}{BOLD}"
        "╔══════════════════════════════════════════╗\n"
        "║          DEPTH 3D • TERMUX GUI          ║\n"
        "║        AI-FREE PARALLAX EFFECT          ║\n"
        "╚══════════════════════════════════════════╝"
        f"{RESET}\n"
    )


def bar(value, maximum=100, width=30):

    value = max(
        0,
        min(
            value,
            maximum
        )
    )

    filled = int(
        width * value / maximum
    )

    return (
        "█" * filled +
        "░" * (width - filled)
    )


# ============================================================
# VIDEO FILE PICKER
# ============================================================

def find_videos():

    folders = [
        "/storage/emulated/0/Download",
        "/storage/emulated/0/DCIM",
        "/storage/emulated/0/Movies",
        "/storage/emulated/0/Pictures",
        "/storage/emulated/0"
    ]

    videos = []

    extensions = (
        ".mp4",
        ".mov",
        ".mkv",
        ".avi",
        ".webm",
        ".m4v"
    )

    for folder in folders:

        if not os.path.exists(folder):
            continue

        try:

            for name in os.listdir(folder):

                path = os.path.join(
                    folder,
                    name
                )

                if (
                    os.path.isfile(path)
                    and
                    name.lower().endswith(
                        extensions
                    )
                ):

                    if path not in videos:
                        videos.append(path)

        except PermissionError:
            pass

    return sorted(videos)


def select_video():

    global input_file

    clear()
    header()

    print(
        f"{BOLD}VIDEO FILES{RESET}\n"
    )

    videos = find_videos()

    if not videos:

        print(
            f"{RED}"
            "No videos found.\n\n"
            "Put a video in:\n"
            "/storage/emulated/0/Download/"
            f"{RESET}"
        )

        pause()
        return

    for i, video in enumerate(
        videos,
        1
    ):

        print(
            f"{YELLOW}{i:2}{RESET}. "
            f"{os.path.basename(video)}"
        )

    print()
    print(
        "0. Cancel"
    )

    try:

        choice = int(
            input("\nSelect video: ")
        )

    except ValueError:
        return

    if choice == 0:
        return

    if 1 <= choice <= len(videos):

        input_file = videos[
            choice - 1
        ]

        print(
            f"\n{GREEN}"
            "Selected:"
            f"{RESET} "
            f"{input_file}"
        )

        time.sleep(1)


# ============================================================
# SETTINGS
# ============================================================

def choose_strength():

    global strength

    clear()
    header()

    print(
        f"{BOLD}3D STRENGTH{RESET}\n"
    )

    print("1. Low       8")
    print("2. Medium   18")
    print("3. High     30")
    print("4. Extreme  45")
    print()

    choice = input(
        "Choose: "
    )

    values = {
        "1": 8,
        "2": 18,
        "3": 30,
        "4": 45
    }

    if choice in values:
        strength = values[choice]


def choose_movement():

    global movement

    clear()
    header()

    print(
        f"{BOLD}CAMERA MOVEMENT{RESET}\n"
    )

    print(
        "1. Horizontal"
    )

    print(
        "2. Vertical"
    )

    print(
        "3. Diagonal"
    )

    print()

    choice = input(
        "Choose: "
    )

    values = {
        "1": "horizontal",
        "2": "vertical",
        "3": "diagonal"
    }

    if choice in values:
        movement = values[choice]


def choose_resolution():

    global resolution

    clear()
    header()

    print(
        f"{BOLD}PROCESSING RESOLUTION{RESET}\n"
    )

    print(
        "1. 360p   (fast)"
    )

    print(
        "2. 480p   (recommended)"
    )

    print(
        "3. 640p   (better)"
    )

    print(
        "4. 720p   (slow)"
    )

    print()

    choice = input(
        "Choose: "
    )

    values = {
        "1": 360,
        "2": 480,
        "3": 640,
        "4": 720
    }

    if choice in values:
        resolution = values[choice]


# ============================================================
# DEPTH GENERATION
# ============================================================

def create_depth_map(frame):

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    brightness = (
        gray.astype(np.float32)
        / 255.0
    )

    local_blur = cv2.GaussianBlur(
        gray,
        (0, 0),
        9
    )

    contrast = cv2.absdiff(
        gray,
        local_blur
    ).astype(
        np.float32
    ) / 255.0

    edges = cv2.Canny(
        gray,
        50,
        150
    )

    edges = (
        edges.astype(np.float32)
        / 255.0
    )

    edges = cv2.GaussianBlur(
        edges,
        (0, 0),
        5
    )

    h, w = gray.shape

    vertical = np.linspace(
        0,
        1,
        h,
        dtype=np.float32
    )

    vertical = np.repeat(
        vertical[:, None],
        w,
        axis=1
    )

    depth = (
        brightness * 0.30 +
        contrast * 0.20 +
        edges * 0.10 +
        vertical * 0.40
    )

    depth = cv2.GaussianBlur(
        depth,
        (0, 0),
        5
    )

    mn = depth.min()
    mx = depth.max()

    if mx > mn:

        depth = (
            depth - mn
        ) / (
            mx - mn
        )

    return depth


# ============================================================
# PARALLAX
# ============================================================

def parallax(
    frame,
    depth,
    frame_number,
    fps
):

    h, w = depth.shape

    x, y = np.meshgrid(
        np.arange(
            w,
            dtype=np.float32
        ),
        np.arange(
            h,
            dtype=np.float32
        )
    )

    depth_centered = (
        depth - 0.5
    )

    t = frame_number / fps

    if movement == "horizontal":

        camera_x = (
            math.sin(
                t * 0.75
            ) * 10
        )

        camera_y = (
            math.sin(
                t * 0.5
            ) * 2
        )

    elif movement == "vertical":

        camera_x = (
            math.sin(
                t * 0.5
            ) * 2
        )

        camera_y = (
            math.sin(
                t * 0.75
            ) * 8
        )

    else:

        camera_x = (
            math.sin(
                t * 0.7
            ) * 8
        )

        camera_y = (
            math.sin(
                t * 0.6
            ) * 5
        )

    map_x = (
        x +
        depth_centered * strength +
        camera_x
    )

    map_y = (
        y +
        depth_centered *
        strength *
        0.45 +
        camera_y
    )

    result = cv2.remap(
        frame,
        map_x,
        map_y,
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT
    )

    return result


# ============================================================
# PROCESS VIDEO
# ============================================================

def process():

    global processing
    global stop_requested

    if not input_file:

        print(
            f"\n{RED}"
            "Please select a video first."
            f"{RESET}"
        )

        pause()
        return

    processing = True
    stop_requested = False

    base = os.path.splitext(
        input_file
    )[0]

    output_file = (
        base +
        "_3D.mp4"
    )

    depth_file = (
        base +
        "_DEPTH.mp4"
    )

    temp_file = (
        base +
        "_TEMP.mp4"
    )

    cap = cv2.VideoCapture(
        input_file
    )

    if not cap.isOpened():

        print(
            f"{RED}"
            "Could not open video."
            f"{RESET}"
        )

        processing = False
        pause()
        return

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps <= 0:
        fps = 30

    total = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    original_w = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    original_h = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    scale = min(
        1.0,
        resolution /
        float(original_w)
    )

    w = int(
        original_w * scale
    )

    h = int(
        original_h * scale
    )

    w -= w % 2
    h -= h % 2

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    out = cv2.VideoWriter(
        temp_file,
        fourcc,
        fps,
        (w, h)
    )

    depth_out = cv2.VideoWriter(
        depth_file,
        fourcc,
        fps,
        (w, h)
    )

    clear()
    header()

    print(
        f"{BOLD}PROCESSING{RESET}\n"
    )

    print(
        "Resolution:",
        f"{w}x{h}"
    )

    print(
        "Strength:",
        strength
    )

    print(
        "Movement:",
        movement
    )

    print()

    frame_number = 0

    previous_depth = None

    while True:

        if stop_requested:
            break

        ret, frame = cap.read()

        if not ret:
            break

        frame_number += 1

        frame = cv2.resize(
            frame,
            (w, h),
            interpolation=cv2.INTER_AREA
        )

        depth = create_depth_map(
            frame
        )

        # Temporal smoothing
        if previous_depth is not None:

            depth = (
                previous_depth * 0.80 +
                depth * 0.20
            )

        previous_depth = depth

        result = parallax(
            frame,
            depth,
            frame_number,
            fps
        )

        out.write(
            result
        )

        depth8 = np.clip(
            depth * 255,
            0,
            255
        ).astype(
            np.uint8
        )

        depth_frame = cv2.cvtColor(
            depth8,
            cv2.COLOR_GRAY2BGR
        )

        depth_out.write(
            depth_frame
        )

        if (
            frame_number % 5 == 0
            or frame_number == total
        ):

            percent = (
                frame_number /
                total *
                100
            )

            print(
                "\r"
                + f"{CYAN}"
                + bar(percent)
                + f"{RESET} "
                + f"{percent:6.1f}%",
                end="",
                flush=True
            )

    cap.release()
    out.release()
    depth_out.release()

    print()

    processing = False

    if stop_requested:

        print(
            f"\n{YELLOW}"
            "Processing stopped."
            f"{RESET}"
        )

        pause()
        return

    print(
        f"\n{GREEN}"
        "Creating final MP4..."
        f"{RESET}"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i",
        temp_file,

        "-i",
        input_file,

        "-map",
        "0:v:0",

        "-map",
        "1:a?",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "20",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-shortest",

        output_file
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    try:
        os.remove(
            temp_file
        )
    except OSError:
        pass

    if result.returncode == 0:

        print(
            f"\n{GREEN}"
            "╔══════════════════════════════════════╗\n"
            "║              COMPLETE!               ║\n"
            "╚══════════════════════════════════════╝"
            f"{RESET}\n"
        )

        print(
            "3D video:"
        )

        print(
            output_file
        )

        print()

        print(
            "Depth map:"
        )

        print(
            depth_file
        )

    else:

        print(
            f"\n{RED}"
            "FFmpeg encoding failed."
            f"{RESET}"
        )

    pause()


# ============================================================
# PREVIEW DEPTH MAP
# ============================================================

def preview_depth():

    if not input_file:

        print(
            f"\n{RED}"
            "Select a video first."
            f"{RESET}"
        )

        pause()
        return

    cap = cv2.VideoCapture(
        input_file
    )

    ret, frame = cap.read()

    cap.release()

    if not ret:

        print(
            f"\n{RED}"
            "Could not read video."
            f"{RESET}"
        )

        pause()
        return

    depth = create_depth_map(
        frame
    )

    depth8 = np.clip(
        depth * 255,
        0,
        255
    ).astype(
        np.uint8
    )

    preview_file = (
        "/storage/emulated/0/"
        "Download/depth_preview.png"
    )

    cv2.imwrite(
        preview_file,
        depth8
    )

    clear()
    header()

    print(
        f"{GREEN}"
        "Depth map created!"
        f"{RESET}\n"
    )

    print(
        preview_file
    )

    print(
        "\nWhite = closer"
    )

    print(
        "Black = farther"
    )

    pause()


# ============================================================
# MAIN GUI
# ============================================================

def main():

    global stop_requested

    while True:

        clear()
        header()

        if input_file:

            filename = os.path.basename(
                input_file
            )

            print(
                f"{GREEN}"
                "Input:"
                f"{RESET} "
                f"{filename}"
            )

        else:

            print(
                f"{YELLOW}"
                "Input: No video selected"
                f"{RESET}"
            )

        print()

        print(
            f"[1] 📁 Select Video"
        )

        print(
            f"[2] 🎚️  3D Strength "
            f"({strength})"
        )

        print(
            f"[3] 🎥 Movement "
            f"({movement})"
        )

        print(
            f"[4] 🖼️  Resolution "
            f"({resolution}px)"
        )

        print(
            f"[5] 🔍 Preview Depth Map"
        )

        print(
            f"[6] ▶️  START 3D"
        )

        print(
            f"[7] ⏹️  STOP"
        )

        print(
            f"[8] 📂 Output Folder"
        )

        print(
            f"[9] ❌ Exit"
        )

        print()

        choice = input(
            "Choose: "
        ).strip()

        if choice == "1":

            select_video()

        elif choice == "2":

            choose_strength()

        elif choice == "3":

            choose_movement()

        elif choice == "4":

            choose_resolution()

        elif choice == "5":

            preview_depth()

        elif choice == "6":

            process()

        elif choice == "7":

            stop_requested = True

            print(
                f"\n{YELLOW}"
                "Stop requested..."
                f"{RESET}"
            )

            time.sleep(1)

        elif choice == "8":

            folder = os.path.dirname(
                input_file
            ) if input_file else \
                "/storage/emulated/0/Download"

            print(
                f"\nOutput files are in:\n"
                f"{folder}"
            )

            pause()

        elif choice == "9":

            clear()

            print(
                "Goodbye!"
            )

            break


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\n\nExiting..."
        )