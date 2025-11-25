from dotenv import load_dotenv
from openai import OpenAI
import json, os
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid #random

load_dotenv()


client = OpenAI()

class Meal(BaseModel):
    name: str
    ingredients: str
    description: str
    calories: float
    protein: float
    carbs: float
    fats: float
    Rest_between_meals: str

class Meals(BaseModel):
    meals: List[Meal]


class Exercise(BaseModel):
    name: str
    type: str
    duration: str
    intensity: str
    sets: str
    reps: str
    rest_between_sets: str
    instructions: str


class Exercises(BaseModel):
    exercises: List[Exercise]

class DailyPlan(BaseModel):
    meals: List[Meal]
    workouts: List[Exercise]

class DailyMealsOnly(BaseModel):
    meals: List[Meal]

class DailyWorkoutsOnly(BaseModel):
    workouts: List[Exercise]

def generate_daily_meals(user):
    """Generate only meals/snacks for one day."""
    random_key = uuid.uuid4().hex[:8]
    # seed = random.randint(0, 99999)
    # and reference it inside the prompt.
    # The effect is the same: each plan request now carries a tiny random fingerprint.

    prompt = f"""
    You are a certified nutrition coach.
    Create a unique personalized one-day MEAL plan for today for today (Random key: {random_key})for a client of the age: {user.age}-year-old, gender: {user.gender},
    weight: {user.weight} kg, and height: {user.height} cm tall.
    Based on Goal: {user.fitness_goal}, Activity level: {user.activity_level},
    Dietary preference: {user.dietary_pref}.

    *Requirements*
    - Return ONLY valid JSON.
    - Output: 3 main meals + 2 snacks.
    - Each entry must contain:
      name, ingredients, description, calories, protein, carbs, fats,
      and rest_between_meals.
    - Respect dietary preference ({user.dietary_pref}) and fitness goal.
    - Keep it realistic, tasty, and easy to prepare.

    Example output:
    {{
      "meals": [
        {{
          "name": "Breakfast Oats Bowl",
          "ingredients": "Oats, almond milk, banana, chia",
          "description": "Blend oats with almond milk and top with fruits.",
          "calories": 350,
          "protein": 15,
          "carbs": 50,
          "fats": 8,
          "Rest_between_meals": "2 h"
        }},
        ...
      ]
    }}
    """

    completion = client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional nutrition coach."},
            {"role": "user", "content": prompt},
        ],
        response_format=DailyMealsOnly,
        temperature=0.8,
        max_completion_tokens=800,

    )
    plan = completion.choices[0].message.parsed
    return plan


def generate_daily_workouts(user):
    """Generate only workouts for one day."""
    # choose reps style

    if user.activity_level.lower() in ["sedentary", "light"]:
        sets = "2 sets per exercise"
        reps = "from 8 to 10 reps per exercise"
    elif user.activity_level.lower() == "moderate":
        sets = "3 sets per exercise"
        reps = "from 10 to 12 reps per exercise"
    else:
        sets = "4 sets per exercise"
        reps = "from 10 to 15 reps per exercise"

    random_key = uuid.uuid4().hex[:8]

    prompt = f"""
    You are a certified personal trainer.
    Create a realistic full-body photo for a person one‑day unique WORKOUT plan for today (Random key: {random_key}) for a client of the age: {user.age}-year-old, gender: {user.gender},
    weight: {user.weight} kg, and height: {user.height} cm tall.
    Based on Goal: {user.fitness_goal}, Activity: {user.activity_level}.

    *Requirements*
    - Return ONLY JSON.
    - Include exactly 3 workouts (name, type, duration, intensity, sets, reps,
      rest_between_sets, and short instructions).
    - Provide {sets}
    - Provide {reps}.
    - Adapt difficulty to the activity level.

    Example output:
    {{
      "workouts": [
        {{
          "name": "Push‑Ups",
          "type": "Strength",
          "duration": "10 min",
          "intensity": "Moderate",
          "sets": "3",
          "reps": "12",
          "rest_between_sets": "60 sec",
          "instructions": "Keep core tight and full range of motion."
        }},
        ...
      ]
    }}
    """

    completion = client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional fitness coach."},
            {"role": "user", "content": prompt},
        ],
        response_format=DailyWorkoutsOnly,
        temperature=0.8,
        max_completion_tokens=800,
    )
    plan = completion.choices[0].message.parsed
    return plan


def generate_daily_plan(user):
    # Decide reps based on activity level
    if user.activity_level.lower() in ["sedentary", "light"]:
        reps = "2 sets per exercise"
    elif user.activity_level.lower() == "moderate":
        reps = "3 sets per exercise"
    else:
        reps = "4 sets per exercise"

    random_key = uuid.uuid4().hex[:8]

    prompt = f"""
        You are a certified fitness and nutrition coach. Create a unique personalized one-day plan for today (Random key: {random_key})
        by adding duration for each workout and rest time between sets.
        Make sure that the plan is suitable for a client of the age: {user.age}-year-old, gender: {user.gender}, who weights: {user.weight}kg and height: {user.height}cm tall.

        Based on this these infos about the user:
        - Fitness goal: {user.fitness_goal}
        - Activity level: {user.activity_level}
        - Dietary preference: {user.dietary_pref}
        
        * General Rules:
            - Always return ONLY valid JSON.
            - Each day (Monday–Sunday) must include:
              (a) 3 meals + 2 snacks (with calories, protein, carbs, fats) 
              AND 3 structured workouts, OR
              (b) meals + rest_day = true with recovery notes.
            - Respect dietary preferences and fitness goal.
            - Provide for each meal short instructions as possible.
            - Provide workouts with: name, type (Strength/Cardio/Flexibility), duration, sets, reps, rest_between_sets, intensity, short description, and short notes.

        Guidelines:
        1. Nutrition:
           - If goal = "lose weight": keep meals moderate in calories, high in protein, controlled carbs and fats.
           - If goal = "gain muscle": increase calories, protein-rich meals, complex carbs, healthy fats.
           - If goal = "maintain": keep calories balanced with moderate macros.
           - Respect dietary preference ({user.dietary_pref}) and avoid restricted foods.
           - Provide {"5 meals (3 main + 2 snacks)" if user.fitness_goal.lower() == "lose weight" else "6 meals (3 main + 3 snacks)"}.
           - Provide a snack after each meal but put a time until to make the meal consumed before the snack.
           - Each meal must include: name, calories, protein, carbs, fat.
           

        2. Training:
           - Sedentary/light activity → beginner-friendly workouts (walking, yoga, light bodyweight).
           - Moderate activity → balanced strength + cardio.
           - Active/very active → higher intensity (strength, HIT, endurance).
           - Provide 3 structured workouts: name, type (strength/cardio/flexibility), duration, and intensity.
           - Provide {reps}
           - Have at least 1 or 2 days of rest. 

        3. Output:
           Return ONLY valid JSON in this format:

           {{
             "meals": [
               {{
                 "Meal 1": ".....",
                 "Name": ".....",
                 "Description": "Bread, Eggs, Milk",
                 "Ingredients": ".....",
                 "Instructions": ".....",
                 "Calories": 400,
                 "Protein": 25,
                 "Carbs": 45,
                 "Fats": 12,
                 "Rest between meals": "1h - 1:30h"
               }},
                 "Snack 1": ".....",
                 "Name": ".....",
                 "Description": "Bread, Eggs, Milk",
                 "Ingredients": ".....",
                 "Instructions": ".....",
                 "Calories": ,
                 "Protein": ,
                 "Carbs": ,
                 "Fats": ,
                 "Rest between meals": "2h - 3h"
                 }},
                 
                 .....
             ],
             "workouts": [
               {{
                 "Name": "Push-ups",
                 "Sets": "2",
                 "Reps" "8 - 10",
                 "Type": "Strength",
                 "Duration": "15 min",
                 "Intensity": "Medium",
                 "Instructions": "...."
               }}
             ]
           }}

        Make the plan realistic, motivating, and personalized to the user,
        """

    # completion = client.chat.completions.create       # Create without using structured data.
    completion = client.chat.completions.parse(        # parse by using structured data.

    model="gpt-4o-mini",
    messages=[
    {"role": "developer", "content": "You are a professional coach."},
    {"role": "user", "content": prompt}
    ],
    response_format=DailyPlan, # key part
    max_completion_tokens=1000,
    temperature=0.8
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
#
#
# def generate_weekly_plan(user):
#     # Decide reps based on activity level
#     if user.activity_level.lower() in ["sedentary", "light"]:
#         reps = "2 sets per exercise"
#         rest_days = 2
#         last_day_weekly = "complete body workout"
#     elif user.activity_level.lower() == "moderate":
#         reps = "3 sets per exercise"
#         rest_days = 2
#     else:
#         reps = "4 sets per exercise"
#         rest_days = 1
#     prompt = f"""
#     Create a structured 7-day weekly plan
#     for a {user.age}-year-old {user.gender}, {user.weight}kg, {user.height}cm tall.
#     Goal: {user.fitness_goal}, Activity level: {user.activity_level}, Dietary preference: {user.dietary_pref}.
#
#     Requirements:
#     - 7 days (Monday–Sunday).
#     - Each day must include either:
#       (a) 3 meals + 2 snacks (with calories, protein, carbs, fats) + 3 workouts, OR
#       (b) 3 meals + 2 snacks (with calories, protein, carbs, fats) and a rest day (clearly marked).
#     - Provide {rest_days}
#     - Workouts must include:
#       * Before a rest day, the user should have a complete full-body workout.
#       * Provide {{last_day_weekly} if "rest_day == Day 6" else "there was a rest day then it must generate the  after a rest day"}}
#       * name
#       * type (Strength / Cardio / Flexibility)
#       * duration
#       * sets & {reps} (if strength)
#       * rest_between_sets {("in seconds" if user.activity_level.lower() in ["sedentary", "light"] else "minutes")}
#       * intensity (Low, Moderate, High)
#       * notes (short tips for execution)
#
#     - Meals must include:
#       * name
#       * calories
#       * protein (g), carbs (g), fats (g)
#
#     Output only valid JSON structured like:
#     {{
#       "Day 1": {{
#         "meals": [...],
#         "workouts": [...]
#       }},
#       "Day 2: {{
#         "rest_day": true,
#         "notes": "Full body recovery"
#       }},
#       ...
#       "Day 7": {{ ... }}
#     }}
#     """
#
#     # completion = client.chat.completions.create(
#     completion = client.chat.completions.parse(
#       model="gpt-4o-mini",
#       messages=[
#         {"role": "system", "content": "You are a professional coach generating structured weekly fitness plans."},
#         {"role": "user", "content": prompt}
#       ],
#         response_format=WeeklyPlan,
#     max_completion_tokens=10000
#     )
#
#     # plan_text = completion.choices[0].message.content
#     # print(plan_text)
#     # return json.loads(plan_text)
#
#     plan_text = completion.choices[0].message.parsed
#     print(plan_text)
#     return plan_text


def generate_weekly_plan(user):
    today = datetime.today()
    weekday_name = today.strftime("%A")
    month_name = today.strftime("%B")

    random_key = uuid.uuid4().hex[:8]

    prompt = f"""
    You are a certified professional fitness and nutrition coach.
    Create a personalized unique 7-day weekly workout and meal plan for a week (Random key: {random_key})
    for a client age {user.age}-year-old, gender {user.gender}, weight {user.weight}kg, height {user.height}cm tall. 
    Based on Goal: {user.fitness_goal}, Activity level: {user.activity_level}, Dietary preference: {user.dietary_pref}.

    * General Rules:
    - Always return ONLY valid JSON.
    - Today is {weekday_name} in the month of {month_name}.
      That means the plan should start from **{weekday_name}** and continue in sequence
      until the next {weekday_name} (7 full days total).

      Example:
      If today is Tuesday → generate days: Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday, Monday.
      
    - each day must include:
      (a) 3 meals + 2 snacks (with calories, protein, carbs, fats) 
      AND 3 structured workouts, OR
      (b) meals + rest_day = true with recovery notes.
    - Respect dietary preferences and fitness goal.
    - Provide for each meal short instructions as possible.
    - Provide workouts with: name, type (Strength/Cardio/Flexibility), duration, sets, reps, rest_between_sets, intensity, short description, and short notes.

    * Training Logic:
    
    - For Sedentary/Light levels (3 training days): prefer lower session frequency, lower intensity, mobility and functional work.
      * Workouts alternate Upper Body, Lower Body, and Full Body.
      * The last day should always end with a **Full Body Strength** session.

    - Moderate Activity (4 training days):
      * 2 rest days per week.
      * Workouts alternate Upper Body, Lower Body, and Full Body.
      * Before each rest day → include a **Full Body Workout**.
      * Day 5 should always end with a **Full Body Strength** session.

    - Active (5 training days):
      * 2 rest days.
      * Split into Upper Body, Lower Body, Cardio/HIIT, Hypertrophy, and Full Body.
      * Rest days follow after heavy workouts.
      * Always finish the week with a **Full Body workout**.

    - Very Active (6 training days):
      * 1 rest day.
      * Push/Pull/Legs + Full Body Functional + Upper Body Pull + Lower Body Power.
      * Rest day is midweek or at the end (Day 3 or 7).
      * Always have a **Full Body workout before or after the rest day**.
      * Day 6 (final session) should be a **Full Body Power workout**.

    * Nutrition Logic:
    - Lose weight → Calorie deficit, high protein, moderate carbs, low fats.
    - Gain muscle → Calorie surplus, protein-rich meals, complex carbs, healthy fats.
    - Maintain → Balanced macros.
    - Always respect dietary preference (e.g., vegan, vegetarian, keto, halal).
    - Moderate activity: 5 meals/day (3 main + 2 snacks).
    - Active/Very Active: 6 meals/day (3 main + 3 snacks).

    * Output Format (JSON only):
    {{
      "{weekday_name}": {{
        "meals": [
          {{
            "name": "Breakfast",
            "Ingredients": ".....",
            "description": ".....",
            "calories": 400,
            "protein": 25,
            "carbs": 45,
            "fats": 12,
            "Rest time": "1h - 1:30h"
          }},
            "Snack 1": "......",
            "Name": ".....",
            "Description": "Bread, Eggs, Milk",
            "Ingredients": ".....",
            "Instructions": ".....",
            "Calories": ,
            "Protein": ,
            "Carbs": ,
            "Fats": ,
            "Rest between meals": "2h - 3h"
            }}
        ]
        
        "workouts": [
          {{
            "name": "Bench Press",
            "type": "Strength",
            "duration": "20 min",
            "sets": "4",
            "reps": "8–10",
            "rest_between_sets": "90 sec",
            "intensity": "Moderate",
            "instructions": ".....",
            "notes": "Focus on form, controlled movement"
          }}
        ]
      }},
      ...
      "{weekday_name}": {{ ... }}
    }}
    """

    completion = client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional coach generating structured weekly fitness and meal plans."},
            {"role": "user", "content": prompt}
        ],
        response_format=WeeklyPlan,
        # max_completion_tokens=20000,
        temperature=0.8,
        # verbosity="medium"    # low, medium or high only with gpt 5
    )

    plan = completion.choices[0].message.parsed

    # Track tokens
    usage = completion.usage
    print("\n Token Usage:")
    print(f"- Prompt tokens: {usage.prompt_tokens}")
    print(f"- Completion tokens: {usage.completion_tokens}")
    print(f"- Total tokens: {usage.total_tokens}")

    return plan


class User:
    age = 30
    gender = "male"
    weight = 70
    height = 160
    fitness_goal = "gain weight"
    activity_level = "active"
    dietary_pref = "vegan"


if __name__ == "__main__":
    # For local testing only
    # user = User(30, "male", 70, 160, "gain weight", "active", "vegan")
    user = User()

    # generate_daily_plan(user)
    # daily = generate_daily_plan(user)
    # print(daily.model_dump())  # Pydantic → dict

    # For testing daily plan
    # daily = generate_daily_plan(user)
    # print(daily.model_dump())  # Pydantic → dict

    # For testing weekly plan

    # generate_weekly_plan(user)
    weekly = generate_weekly_plan(user)


    file_path = "tempfix.json"
    if os.path.exists(file_path):
        with open (file_path, 'r') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    # Make a new Plan to add instead of overwriting
    if isinstance(existing_data, list):
        existing_data.append(weekly.model_dump())
    else:
        existing_data = [existing_data, weekly.model_dump()]

    # Add new data to the existing one.
    with open(file_path, "w") as file:
        json.dump(existing_data, file, indent=4)
    # json.dump(weekly.model_dump(), open(existing_data, file_path, "w"), indent=4)
    print(weekly)
