import random

import cv2
import flet as ft
import base64
import threading
import time
import numpy as np

def extract_dominant_color(image):
    # Convert the image to HSV (Hue, Saturation, Value) color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define ranges for colors in HSV space (these can be adjusted)
    color_ranges = {
        "red": ((0, 50, 50), (10, 255, 255)),  # Red color range
        "yellow": ((20, 50, 50), (40, 255, 255)),  # Yellow color range
        "grey": ((0, 0, 50), (180, 50, 200)),  # Grey color range
        "green": ((40, 50, 50), (80, 255, 255)),  # Green color range
        "pink": ((140, 50, 50), (170, 255, 255))  # Pink color range
    }

    # Create a mask for each color range and calculate the percentage of each color in the image
    color_scores = {}
    for color, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(hsv, lower, upper)
        color_area = cv2.countNonZero(mask)
        total_area = image.size / 3  # Total number of pixels (3 channels)
        color_percentage = color_area / total_area * 100
        color_scores[color] = color_percentage

    # Determine the dominant color based on the highest percentage
    dominant_color = max(color_scores, key=color_scores.get)
    return dominant_color


# Function to map the dominant color to a score
def map_color_to_score(dominant_color):
    score_map = {
        "red": "zenach_pro_max.png",  # Highest score for red
        "yellow": "zenach_pro.png",  # High score for yellow
        "green": "zenach_max.png",  # Medium score for green
        "pink": "zenach_pro_max.png",  # High score for pink
        "grey": "zenach.png",  # Low score for grey
    }
    _ = score_map.get(dominant_color, 0)  # Default to 0 if no color detected
    if _ == "zenach.png":
        return random.choice(list(score_map.values()))
    return _


class VideoStreamApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.window_full_screen = True
        self.camera_id = 0  # Default camera ID
        self.cap = None  # VideoCapture object

        # UI components
        self.video_image = ft.Image(
        )
        self.capture_button = ft.Button(
            text="Capture Photo",
            on_click=self.capture_photo
        )

        self.camera_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(str(i)) for i in range(5)],  # Assuming up to 5 cameras
            label="Select Camera",
            on_change=self.update_camera,
        )

        # Initialize the UI layout
        self.page.title = "Video Stream with Watermark"
        self.page.bgcolor = ft.colors.BLACK

        # Set watermark image as the background of the app and fit it to the entire screen
        # self.page.add(
        #     ft.Image(src=r"C:\Users\Abel\Desktop\mela\assets\frame_2.png", fit=ft.ImageFit.COVER,  opacity=1)
        # )

        # self.page.add(
        #     ft.Stack(
        #         controls=[
        #
        #         ]
        #     )
        # )

        # Add video stream and other UI components on top of the background
        self.page.add(
            ft.Stack(
                controls=[
                    ft.Image(src=r"C:\Users\Abel\Desktop\mela\assets\frame_2.png", fit=ft.ImageFit.COVER, opacity=1),
                    self.video_image,
                ],
                alignment=ft.alignment.top_center,
            )
        )

        self.cap_b = ft.Container(
            on_click=self.capture_photo,
            content=ft.Image(src="assets\\capture.png", height=100)
        )


        self.page.add(
            ft.Column(
                controls=[
                    self.cap_b,
                    self.camera_dropdown,
                ]
            )
        )

        # Start the video stream in a separate thread
        threading.Thread(target=self.video_stream, daemon=True).start()

    def capture_photo(self, e):
        """Capture a photo from the selected camera and save it."""
        frame = self.get_video_frame(just_the_frame=True)
        if frame is not None:
            # Save the captured photo
            cv2.imwrite(f"captured_photo_{self.camera_id}.jpg", frame)
            self.cap.release()

        print_button = ft.Container(
            on_click=self.capture_photo,
            content=ft.Image(src="assets\\print.png", height=100)
        )
        self.page.add(print_button)

    def update_camera(self, e):
        """Update the selected camera ID and restart the capture device."""
        self.camera_id = int(e.control.value)
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.camera_id)

    def get_video_frame(self, just_the_frame=False):
        """Capture a video frame and resize it for portrait mode (4:5 aspect ratio) with a watermark."""
        ret, frame = self.cap.read()
        if ret:
            # Resize the frame to the required dimensions (1000x1225)
            resized_frame = cv2.resize(frame, (1000, 1225))
            dominant_color = extract_dominant_color(resized_frame)
            score = map_color_to_score(dominant_color)
            print(score)

            # Load the watermark image (ensure it's a PNG with transparency if needed)
            watermark = cv2.imread(fr"C:\Users\Abel\Desktop\mela\assets\{score}", cv2.IMREAD_UNCHANGED)
            wm_height, wm_width = watermark.shape[:2]

            # Resize the watermark to fit in the bottom center
            max_width = 1000  # Max width available for watermark (frame width)
            scale_factor = max_width / wm_width  # Scale factor to fit watermark into frame width
            new_width = int(wm_width * scale_factor)
            new_height = int(wm_height * scale_factor)

            # Resize the watermark
            watermark_resized = cv2.resize(watermark, (new_width, new_height))

            # Calculate position to place the watermark (bottom center)
            x_offset = (resized_frame.shape[1] - new_width) // 2  # Center horizontally
            y_offset = resized_frame.shape[0] - new_height  # Place at the bottom

            # Overlay the watermark on the video frame
            if watermark_resized.shape[2] == 4:  # If watermark has an alpha channel (transparency)
                alpha_channel = watermark_resized[:, :, 3] / 255.0
                for c in range(0, 3):  # Apply to R, G, B channels
                    resized_frame[y_offset:y_offset+new_height, x_offset:x_offset+new_width, c] = (
                        alpha_channel * watermark_resized[:, :, c] +
                        (1 - alpha_channel) * resized_frame[y_offset:y_offset+new_height, x_offset:x_offset+new_width, c]
                    )
            else:
                resized_frame[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = watermark_resized

            # Convert the frame to RGB for further processing
            frame_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

            if just_the_frame:
                return resized_frame

            # Convert the frame to base64 to display in the UI
            _, buffer = cv2.imencode('.png', resized_frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            return frame_base64
        return None

    def video_stream(self):
        """Continuously capture and display video frames."""
        self.cap = cv2.VideoCapture(self.camera_id)  # Initialize the camera capture once

        while True:
            frame_base64 = self.get_video_frame()
            if frame_base64:
                self.video_image.src_base64 = frame_base64
                self.page.update()
            time.sleep(0.1)  # Sleep for a short time to prevent excessive CPU usage

# Run the Flet app
def main(page: ft.Page):
    VideoStreamApp(page)

ft.app(target=main)
