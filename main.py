import cv2
import mediapipe as mp
import pyautogui
import math
import time
from pathlib import Path

# ----------------------------
# SETTINGS
# ----------------------------

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# ----------------------------
# CAMERA
# ----------------------------

cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# ----------------------------
# SCREEN SIZE
# ----------------------------

screen_width, screen_height = pyautogui.size()

# ----------------------------
# MEDIAPIPE
# ----------------------------

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

mp_draw = mp.solutions.drawing_utils

# ----------------------------
# VARIABLES
# ----------------------------

prev_x = 0
prev_y = 0

smoothening = 5
margin = 100

last_click = 0
last_right_click = 0
last_scroll = 0
last_screenshot = 0
last_volume = 0

click_delay = 1
right_click_delay = 1
scroll_delay = 0.2
screenshot_delay = 2
volume_delay = 0.6

prev_scroll_y = 0

is_dragging = False

gesture_text = ""
gesture_time = 0

# ----------------------------
# GESTURE DISPLAY
# ----------------------------

def show_gesture(frame):

    global gesture_text
    global gesture_time

    if time.time() - gesture_time < 1.2:

        cv2.rectangle(
            frame,
            (120, 20),
            (560, 100),
            (20, 20, 20),
            -1
        )

        cv2.putText(
            frame,
            gesture_text,
            (145, 75),
            cv2.FONT_HERSHEY_DUPLEX,
            1.2,
            (0, 255, 255),
            3
        )

# ----------------------------
# MAIN LOOP
# ----------------------------

while True:

    start_time = time.time()

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    result = hands.process(rgb)

    frame_height, frame_width, _ = frame.shape

    # ----------------------------
    # CONTROL AREA
    # ----------------------------

    cv2.rectangle(
        frame,
        (margin, margin),
        (frame_width - margin, frame_height - margin),
        (255, 255, 255),
        2
    )

    if result.multi_hand_landmarks:

        for hand_landmarks in result.multi_hand_landmarks:

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # ----------------------------
            # LANDMARKS
            # ----------------------------

            index_tip = hand_landmarks.landmark[8]
            middle_tip = hand_landmarks.landmark[12]
            ring_tip = hand_landmarks.landmark[16]
            pinky_tip = hand_landmarks.landmark[20]
            thumb_tip = hand_landmarks.landmark[4]

            index_down = hand_landmarks.landmark[6]
            middle_down = hand_landmarks.landmark[10]
            ring_down = hand_landmarks.landmark[14]
            pinky_down = hand_landmarks.landmark[18]

            # ----------------------------
            # PAUSE
            # ----------------------------

            if (
                index_tip.y < index_down.y and
                middle_tip.y < middle_down.y and
                ring_tip.y < ring_down.y and
                pinky_tip.y < pinky_down.y
            ):

                gesture_text = "PAUSED ✋"
                gesture_time = time.time()

                show_gesture(frame)

                cv2.imshow("AI Virtual Mouse", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                continue

            # ----------------------------
            # POSITIONS
            # ----------------------------

            x = int(index_tip.x * frame_width)
            y = int(index_tip.y * frame_height)

            middle_x = int(middle_tip.x * frame_width)
            middle_y = int(middle_tip.y * frame_height)

            thumb_x = int(thumb_tip.x * frame_width)
            thumb_y = int(thumb_tip.y * frame_height)

            # Draw finger points
            cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)
            cv2.circle(frame, (thumb_x, thumb_y), 10, (255, 0, 0), -1)

            # ----------------------------
            # SAFE AREA
            # ----------------------------

            x = max(margin, min(x, frame_width - margin))
            y = max(margin, min(y, frame_height - margin))

            # ----------------------------
            # SCREEN MAPPING
            # ----------------------------

            screen_x = (
                (x - margin)
                / (frame_width - 2 * margin)
            ) * screen_width

            screen_y = (
                (y - margin)
                / (frame_height - 2 * margin)
            ) * screen_height

            # ----------------------------
            # SMOOTH CURSOR
            # ----------------------------

            curr_x = prev_x + (
                screen_x - prev_x
            ) / smoothening

            curr_y = prev_y + (
                screen_y - prev_y
            ) / smoothening

            pyautogui.moveTo(curr_x, curr_y)

            prev_x = curr_x
            prev_y = curr_y

            # ----------------------------
            # LEFT CLICK
            # ----------------------------

            left_distance = math.hypot(
                x - thumb_x,
                y - thumb_y
            )

            current_time = time.time()

            if left_distance < 35:

                if current_time - last_click > click_delay:

                    pyautogui.click()

                    last_click = current_time

                    gesture_text = "LEFT CLICK 👆"
                    gesture_time = time.time()

            # ----------------------------
            # DRAG
            # ----------------------------

            if left_distance < 20:

                if not is_dragging:

                    pyautogui.mouseDown()

                    is_dragging = True

                    gesture_text = "DRAG MODE 🖱️"
                    gesture_time = time.time()

            else:

                if is_dragging:

                    pyautogui.mouseUp()

                    is_dragging = False

            # ----------------------------
            # RIGHT CLICK
            # ----------------------------

            right_distance = math.hypot(
                middle_x - thumb_x,
                middle_y - thumb_y
            )

            current_right_time = time.time()

            if right_distance < 25:

                if current_right_time - last_right_click > right_click_delay:

                    pyautogui.rightClick()

                    last_right_click = current_right_time

                    gesture_text = "RIGHT CLICK 👉"
                    gesture_time = time.time()

            # ----------------------------
            # SCROLL
            # ----------------------------

            finger_gap = abs(y - middle_y)

            if finger_gap < 30:

                current_scroll_time = time.time()

                if prev_scroll_y != 0:

                    # Scroll Up
                    if y < prev_scroll_y - 25:

                        if current_scroll_time - last_scroll > scroll_delay:

                            pyautogui.scroll(40)

                            gesture_text = "SCROLL UP ⬆️"
                            gesture_time = time.time()

                            last_scroll = current_scroll_time

                    # Scroll Down
                    elif y > prev_scroll_y + 25:

                        if current_scroll_time - last_scroll > scroll_delay:

                            pyautogui.scroll(-40)

                            gesture_text = "SCROLL DOWN ⬇️"
                            gesture_time = time.time()

                            last_scroll = current_scroll_time

                prev_scroll_y = y

            # ----------------------------
            # SCREENSHOT
            # ----------------------------

            v_distance = math.hypot(
                x - middle_x,
                y - middle_y
            )

            current_screenshot_time = time.time()

            ring_folded = ring_tip.y > ring_down.y
            pinky_folded = pinky_tip.y > pinky_down.y

            if (
                v_distance > 120 and
                ring_folded and
                pinky_folded
            ):

                if current_screenshot_time - last_screenshot > screenshot_delay:

                    try:

                        screenshot = pyautogui.screenshot()

                        desktop_path = Path.home() / "Desktop"

                        filename = desktop_path / (
                            f"screenshot_{int(time.time())}.png"
                        )

                        screenshot.save(str(filename))

                        last_screenshot = current_screenshot_time

                        gesture_text = "SCREENSHOT 📸"
                        gesture_time = time.time()

                    except Exception as e:

                        print(e)

            # ----------------------------
            # VOLUME CONTROL
            # ----------------------------

            volume_distance = math.hypot(
                thumb_x - middle_x,
                thumb_y - middle_y
            )

            current_volume_time = time.time()

            # ----------------------------
            # VOLUME BAR UI
            # ----------------------------

            bar_x = 40
            bar_y = 120
            bar_width = 35
            bar_height = 250

            vol_percent = int(
                min(max(volume_distance, 40), 200)
            )

            vol_bar = int(
                ((vol_percent - 40) / (200 - 40))
                * bar_height
            )

            # Background Bar
            cv2.rectangle(
                frame,
                (bar_x, bar_y),
                (bar_x + bar_width, bar_y + bar_height),
                (80, 80, 80),
                3
            )

            # Filled Bar
            cv2.rectangle(
                frame,
                (bar_x, bar_y + bar_height - vol_bar),
                (bar_x + bar_width, bar_y + bar_height),
                (0, 255, 0),
                -1
            )

            # Percentage
            cv2.putText(
                frame,
                f"{vol_percent}%",
                (25, 400),
                cv2.FONT_HERSHEY_DUPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            # Distance
            cv2.putText(
                frame,
                f"VOL DIST: {int(volume_distance)}",
                (20, 90),
                cv2.FONT_HERSHEY_DUPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            # ----------------------------
            # VOLUME UP / DOWN
            # ----------------------------

            if current_volume_time - last_volume > volume_delay:

                # Volume Up
                if volume_distance > 170:

                    for _ in range(3):
                        pyautogui.press("volumeup")

                    gesture_text = "VOLUME UP 🔊"
                    gesture_time = time.time()

                    last_volume = current_volume_time

                # Volume Down
                elif volume_distance < 55:

                    for _ in range(3):
                        pyautogui.press("volumedown")

                    gesture_text = "VOLUME DOWN 🔉"
                    gesture_time = time.time()

                    last_volume = current_volume_time

    # ----------------------------
    # FPS
    # ----------------------------

    fps = int(
        1 / (time.time() - start_time)
    )

    cv2.putText(
        frame,
        f"FPS: {fps}",
        (20, 40),
        cv2.FONT_HERSHEY_DUPLEX,
        1,
        (0, 255, 0),
        2
    )

    # ----------------------------
    # SHOW POPUP
    # ----------------------------

    show_gesture(frame)

    # ----------------------------
    # SHOW WINDOW
    # ----------------------------

    cv2.imshow(
        "AI Virtual Mouse",
        frame
    )

    # ----------------------------
    # EXIT
    # ----------------------------

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ----------------------------
# RELEASE
# ----------------------------

cap.release()
cv2.destroyAllWindows()