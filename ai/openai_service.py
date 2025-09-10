from dotenv import load_dotenv
from openai import OpenAI
import json
from pydantic import BaseModel
from typing import List, Optional

load_dotenv()


client = OpenAI()

class Meal(BaseModel):
    name = str
    description: Optional[str] = None
    calories: float
    protein: float
    carbs: float
    fats: float

class Meals(BaseModel):
    meals = List[Meal]


class Exercise(BaseModel):
    name: str
    type: str
    duration: str
    intensity: str
    sets: Optional[str] = None
    reps: Optional[str] = None
    rest_between_sets: Optional[str] = None

class Exercises(BaseModel):
    exercises = list[Exercise]

class DailyPlan(BaseModel):
    meals: List[Meal]
    workouts: List[Exercise]

def generate_daily_plan(user):
    prompt = f"""
        You are a certified fitness and nutrition coach. Create a personalized one-day plan
        by adding duration for each workout and rest time between sets.
        Make sure that the plan is suitable for a {user.age}-year-old {user.gender} who weighs {user.weight}kg and is {user.height}cm tall.

        Context about the user:
        - Fitness goal: {user.fitness_goal}
        - Activity level: {user.activity_level}
        - Dietary preference: {user.dietary_pref}

        Guidelines:
        1. Nutrition:
           - If goal = "lose weight": keep meals moderate in calories, high in protein, controlled carbs and fats.
           - If goal = "gain muscle": increase calories, protein-rich meals, complex carbs, healthy fats.
           - If goal = "maintain": keep calories balanced with moderate macros.
           - Respect dietary preference ({user.dietary_pref}) and avoid restricted foods.
           - Provide {"5 meals (3 main + 2 snacks)" if user.fitness_goal.lower() == "lose weight" else "6 meals (3 main + 3 snacks)"}.
           - Each meal must include: name, calories, protein, carbs, fat.

        2. Training:
           - Sedentary/light activity → beginner-friendly workouts (walking, yoga, light bodyweight).
           - Moderate activity → balanced strength + cardio.
           - Active/very active → higher intensity (strength, HIIT, endurance).
           - Provide 3 structured workouts: name, type (strength/cardio/flexibility), duration, and intensity.


        3. Output:
           Return ONLY valid JSON in this format:

           {{
             "meals": [
               {{
                 "Name": "Breakfast",
                 "Description": "Bread, Eggs, Milk",
                 "Calories": 400,
                 "Protein": 25,
                 "Carbs": 45,
                 "Fats": 12
               }}
             ],
             "workouts": [
               {{
                 "name": "Push-ups",
                 "sets": "2",
                 "reps" "8 - 10",
                 "type": "Strength",
                 "duration": "15 min",
                 "intensity": "Medium"
               }}
             ]
           }}

        Make the plan realistic, motivating, and personalized to the user,
        """

    # completion = client.chat.completions.create       # Create without using structured data.
    completion = client.chat.completions.parse(        # parse by using structured data.

    model="gpt-4o-mini"
      messages=[
        {"role": "developer", "content": "You are a professional coach."},
        {"role": "user", "content": prompt}
      ],
      response_formate=DailyPlan # key part
    max_completion_tokens=1000
    )

    # plan_text = completion.choices[0].message.content
    plan_text = completion.choices[0].message.parsed
    text_format=DailyPlan
    print(plan_text)
    # return json.loads(plan_text)  # Parse JSON to Python dict
    return plan_text


class DayPlan(BaseModel):
    meals: Optional[List[Meal]] = None
    workouts: Optional[List[Exercise]] = None
    rest_day: Optional[bool] = None
    notes: Optional[str] = None

class WeeklyPlan(BaseModel):
    Monday: DayPlan
    Tuesday: DayPlan
    Wednesday: DayPlan
    Thursday: DayPlan
    Friday: DayPlan
    Saturday: DayPlan
    Sunday: DayPlan


def generate_weekly_plan(user):
    prompt = f"""
    Create a structured 7-day weekly plan
    for a {user.age}-year-old {user.gender}, {user.weight}kg, {user.height}cm tall.
    Goal: {user.fitness_goal}, Activity level: {user.activity_level}, Dietary preference: {user.dietary_pref}.

    Requirements:
    - 7 days (Monday–Sunday).
    - Each day must include either:
      (a) 3 meals + 2 snacks (with calories, protein, carbs, fats) + 3 workouts, OR
      (b) a rest day (clearly marked).
    - Workouts must include:
      * name
      * type (Strength / Cardio / Flexibility)
      * duration
      * sets & reps (if strength)
      * rest_between_sets (in seconds or minutes)
      * intensity (Low, Moderate, High)
      * notes (short tips for execution)
    - Meals must include:
      * name
      * calories
      * protein (g), carbs (g), fats (g)

    Output only valid JSON structured like:
    {{
      "Monday": {{
        "meals": [...],
        "workouts": [...]
      }},
      "Tuesday": {{
        "rest_day": true,
        "notes": "Full body recovery"
      }},
      ...
      "Sunday": {{ ... }}
    }}
    """

    # completion = client.chat.completions.create(
    completion = client.chat.completions.parse(
      model="gpt-4o-mini",
      messages=[
        {"role": "system", "content": "You are a professional coach generating structured weekly fitness plans."},
        {"role": "user", "content": prompt}
      ],
    max_completion_tokens=1000
    )

    # plan_text = completion.choices[0].message.content
    print(plan_text)
    # return json.loads(plan_text)

    plan_text = completion.choices[0].message.parsed
    return plan_text


class User:
    age = 30
    gender = "male"
    weight = 70
    height = 160
    fitness_goal = "gain weight"
    activity_level = "active"
    dietary_pref = "vegan"

user = User()

# generate_daily_plan(user)
daily = generate_daily_plan(user)
print(daily.model_dump())  # Pydantic → dict


# generate_weekly_plan(user)
weekly = generate_weekly_plan(user)
print(weekly.model_dump())