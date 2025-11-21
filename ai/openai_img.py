import base64
from openai import OpenAI
from dotenv import load_dotenv
import os
from flask import current_app

load_dotenv()

client = OpenAI()

# def generate_img():
#     prompt="Generate a nice white table and put on it at the center a black dish as a background for each meal",
#
#
#     img = client.images.generate(
#         model="gpt-image-1",
#         n=1,
#         size="256x256",
#         quality="medium",
#         background="transparent",
#
#     )
#
#     image_bytes = base64.b64decode(img.data[0].b64_json)
#     with open("output.png", "wb") as f:
#         f.write(image_bytes)



def generate_meal_image(meal_name: str) -> str:
    """Generate a realistic meal image using OpenAI and save it in static folder."""
    try:
        prompt = f"""
        Create a professional, realistic photo of the meal '{meal_name}'.
        Show it on a white plate, on a clean wooden table, well-lit,
        healthy-looking and delicious.
        """

        response = client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            n=1,
            size="256x256",
            response_format="b64_json"  # 👈 this makes .b64_json exist

        )

        # Decode image
        image_data = base64.b64decode(response.data[0].b64_json)

        # Define save path (Flask static folder)
        # save_dir = os.path.join("static", "meal_images") old not absolute
        save_dir = os.path.join(current_app.static_folder, "meal_images")

        os.makedirs(save_dir, exist_ok=True)

        image_filename = f"{meal_name.replace(' ', '_').lower()}.png"
        image_path = os.path.join(save_dir, image_filename)
        # Add a tiny print to confirm the save:
        print("Image saved to:", image_path)

        # To avoid regenerating the same PNG every time:
        if os.path.exists(image_path):
            return f"/static/meal_images/{image_filename}"

        with open(image_path, "wb") as f:
            f.write(image_data)

        return f"/static/meal_images/{image_filename}"

    except Exception as e:
        print(f"Error generating image for {meal_name}: {e}")
        return "/static/default_meal.jpg"


def generate_workout_image(workout_name: str, user) -> str:
    """Generate a realistic meal image using OpenAI and save it in static folder."""
    try:
        prompt = f"""
            Create a high-quality, realistic full‑body photo of a person performing
            the exercise '{workout_name}'should be perform correctly in a modern gym.
            Show the entire person from head to feet with clear technique,
            natural lighting, sharp focus, and no text overlay, 
            Generate the suitable and proper image based on {user.activity_level} and {workout_name}.
            Output only the image in a photorealistic style.

        """

        response = client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            n=1,
            size="256x256",
            response_format="b64_json"  # 👈 this makes .b64_json exist

        )

        # Decode image
        image_data = base64.b64decode(response.data[0].b64_json)

        # Define save path (Flask static folder)
        # save_dir = os.path.join("static", "meal_images") old not absolute
        save_dir = os.path.join(current_app.static_folder, "workout_images")

        os.makedirs(save_dir, exist_ok=True)

        image_filename = f"{workout_name.replace(' ', '_').lower()}.png"
        image_path = os.path.join(save_dir, image_filename)
        # Add a tiny print to confirm the save:
        print("Image saved to:", image_path)

        # To avoid regenerating the same PNG every time:
        if os.path.exists(image_path):
            return f"/static/workout_images/{image_filename}"

        with open(image_path, "wb") as f:
            f.write(image_data)

        return f"/static/workout_images/{image_filename}"

    except Exception as e:
        print(f"Error generating image for {workout_name}: {e}")
        return "/static/default_workout.jpg"


if __name__ == "__main__":
    generate_meal_image("pizza")
    generate_workout_image("dumbbell curls")