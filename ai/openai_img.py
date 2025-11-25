import base64
import os
import time
from flask import current_app
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# from app import app

load_dotenv()
client = OpenAI()


def generate_meal_images(meal_name: str) -> str:
    """Generate a realistic meal image with OpenAI and save it inside /static/meal_images."""
    try:
        # with app.app_context():
        img_dir = os.path.join(current_app.static_folder, "meal_images")
        os.makedirs(img_dir, exist_ok=True)
        timestamp = str(int(time.time()))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        image_filename = f"{meal_name.replace(' ', '_').lower()}_{timestamp}.png"
        image_path = os.path.join(img_dir, image_filename)

        # Add a tiny print to confirm the save:
        print("Image saved to:", image_path)

        # To avoid regenerating the same PNG every time:
        # ✅ File already exists
        if os.path.exists(image_path):
            return f"/static/meal_images/{image_filename}"

        prompt = f"""
        Create a professional, realistic photo of the meal '{meal_name}'.
        Show it on a white plate, on a clean wooden table, well-lit,
        healthy-looking and delicious.
        """

        response = client.images.generate(
            model="gpt-image-1",
            # model="dall-e-2",
            prompt = prompt,
            # size="512x512",
            # size = "256x256",
            n=1,
            # response_format="b64_json",
        )

        image_data = base64.b64decode(response.data[0].b64_json)
        with open(image_path, "wb") as f:
            f.write(image_data)
        print(f"[Meal image] saved: {image_path}")
        return f"/static/meal_images/{image_filename}"

    except Exception as e:
        print(f"[Meal image error] {meal_name}: {e}")
        return "/static/default_meal.jpg"


def generate_workout_images(workout_item: dict, user) -> str:
    """Generate a photorealistic workout image and save it in /static/workout_images."""
    try:
        # make sure workout_item is a dictionary‑like object
        if isinstance(workout_item, dict):
            workout_name = workout_item.get("name", "exercise")
            timestamp = workout_item.get("created_at", str(time.time()))
            timestamp = workout_item.get("created_at", str(datetime.now().strftime("%Y%m%d_%H%M")))
        else:
            # it's just a text word
            workout_name = str(workout_item)
            w_type = intensity = duration = sets = reps = ""

        # with app.app_context():
        img_dir = os.path.join(current_app.static_folder, "workout_images")
        os.makedirs(img_dir, exist_ok=True)

        image_filename = f"{workout_name.replace(' ', '_').lower()}_{timestamp}.png"
        image_path = os.path.join(img_dir, image_filename)
        if os.path.exists(image_path):
            return f"/static/workout_images/{image_filename}"


        print("---\n\n", image_path, "---")
        prompt = f"""
        Create a photorealistic full‑body image of a fit {user.gender} performing the exercise
        '{workout_name}' in a modern gym environment. Camera framing shows the entire person head‑to‑toe, equipment visible if relevant.
        Lighting should be bright, cinematic.
        """


        response = client.images.generate(
            model="gpt-image-1",
            # model="dall-e-2",
            prompt=prompt,
            # size="512x512",
            # size = "256x256",
            n=1,
            # response_format="b64_json"  # 👈 this makes .b64_json exist
        )

        image_data = base64.b64decode(response.data[0].b64_json)
        with open(image_path, "wb") as f:
            f.write(image_data)
        print(f"[Workout image] saved: {image_path}")
        return f"/static/workout_images/{image_filename}"

    except Exception as e:
        print(f"[Workout image error] {workout_item.get('name')}: {e}")
        return "/static/default_workout.jpg"

class User:
    age = int
    gender = str
    weight = float
    height = float
    fitness_goal = str
    activity_level = str
    dietary_pref = str

user = User()

# Usage examples inside Flask
if __name__ == "__main__":

    img_path = generate_meal_images("Quinoa Salad")
    workout_path = generate_workout_images({"name": "Dumbbell Curls"}, user)

# Outside a Flask app (without current_app):
# if __name__ == "__main__":
#     from types import SimpleNamespace
#     os.environ["OPENAI_API_KEY"] = "your-key"
#     dummy_user = SimpleNamespace(activity_level="moderate")
#     os.makedirs("static/meal_images", exist_ok=True)
#     os.makedirs("static/workout_images", exist_ok=True)
#     print(generate_workout_image({"name": "Dumbbell Curls"}, dummy_user))
