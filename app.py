from flask import Flask, render_template, request, flash, redirect, url_for
from datamanager.models import db, User, DailyPlan, WeeklyPlan
from datamanager.sqlite_data_manager import SQLiteDataManager
from validation import validate_user_data
from datetime import datetime,timezone ,date
import json
from ai.openai_service import generate_daily_plan, generate_weekly_plan, generate_daily_meals, generate_daily_workouts
from flask_migrate import Migrate
import requests
from functools import lru_cache
from ai.openai_img import generate_meal_image, generate_workout_image
# Use threading (optional for dev)
# If you still want to fill missing images on the fly but not freeze the page, use a background thread or task queue.
# For a quick Flask-only approach:
import threading


app = Flask(__name__)
db_path = 'fitness_app.db'

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'  # Required for session

db.init_app(app)
data_manager = SQLiteDataManager(db_path, app)  # Use the appropriate path to your Database


migrate = Migrate(app, db)


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    users = User.query.all()
    return render_template('home.html', today=date.today(), users=users)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form.get('user_name', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        height = request.form.get('height', '').strip()
        weight = request.form.get('weight', '').strip()
        dietary_pref = request.form.get('dietary_pref', '').strip()
        fitness_goal = request.form.get('fitness_goal', '').strip()
        activity_level = request.form.get('activity_level', '').strip()

        missing_fields = validate_user_data(
            name=name, age=age, gender=gender, height=height, weight=weight,
            dietary_pref=dietary_pref, fitness_goal=fitness_goal, activity_level=activity_level
        )

        # validation of existence
        existing_user = User.query.filter_by(user_name=name).first()
        if existing_user:
            flash(f"User '{name}' already exists.", "error")
            return render_template('add_user.html', today=date.today())

        if missing_fields:
            flash(f"Missing fields: {', '.join(missing_fields)}")
            return render_template('add_user.html', today=date.today())

        try:
            # Convert numeric fields
            age = int(age)
            height = float(height)
            weight = float(weight)

            # Add user via SQLiteDataManager
            new_user = data_manager.add_user(
                user_name=name,
                gender=gender,
                age=age,
                height=height,
                weight=weight,
                dietary_pref=dietary_pref,
                fitness_goal=fitness_goal,
                activity_level=activity_level
            )

            flash("User added successfully!", "success")
            # Render a result page showing the user immediately
            return render_template('user_result.html', user=new_user)

        except Exception as e:
            flash(f"Error adding user: {str(e)}", "error")
            return render_template('add_user.html', today=date.today())

    return render_template('add_user.html', today=date.today())


@app.context_processor
def time_now():
    return {
        "now": datetime.now(timezone.utc),
        "today": date.today()
    }


@app.context_processor
def inject_date_info():
    """This function injects global date info into all templates."""
    today = datetime.today()
    return {
        "month_name": today.strftime("%B"),  # e.g., "October"
        "weekday_name": today.strftime("%A"),  # e.g., "Tuesday"
        "today": today
    }


@app.route('/daily_plan/<int:user_id>')
def daily_plan(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found")
        return redirect(url_for("home"))

    # Generate a new plan or get the latest
    plan = generate_daily_plan(user)
    daily_plan = DailyPlan(user_id=user.id, plan_json=json.dumps(plan))
    db.session.add(daily_plan)
    db.session.commit()

    for plan in user.daily_plans:
        plan.plan_json = json.loads(plan.plan_json)

    return render_template("daily_plan.html", user=user)


@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    # old
    # user = User.query.get(user_id)
    # new
    user = db.session.get(User, user_id)
    print(user, "UUUUUUUUUUU")
    if not user:
        flash("User not found")
        return redirect(url_for('home'))

    # Parse JSON strings into Python dicts for daily plans
    for plan in user.daily_plans:
        raw = plan.plan_json
    #     try:
    #         if isinstance(plan.plan_json, str):
    #             plan.data = json.loads(plan.plan_json)
    #         else:
    #             plan.data = plan.plan_json
    #     except Exception as e:
    #         print("Error parsing daily plan:", e)
    #         plan.data = {} # fallback if broken JSON

        try:
            data = plan.plan_json
            #
            # # 🛡️ Skip parsing when empty or None
            # if not data:
            #     plan.data = {"meals": [], "workouts": []}
            #     continue
            #
            # 1️⃣ Parse JSON strings until we actually get a dict
            if isinstance(raw, str):
                data = json.loads(raw)
            else:
                data = raw
            #     # Sometimes data is a stringified dict nested once more
            #     while isinstance(data, str):
            #         data = json.loads(data)
            #
            # 2️⃣ Guarantee fallback
            if not isinstance(data, dict):
                 raise ValueError("Data is not a dictionary after parsing")
            #
            # # 3️⃣ Attach missing pictures
            # for meal in data.get("meals", []):
            #     if isinstance(meal, dict):
            #         name = meal.get("name")
            #         if name and not meal.get("image_url"):
            #             meal["image_url"] = get_meal_image(name)
            # print(vars(plan), "test")    # plan before transforming and to print the result on the dashboard
            plan.data = data
            # {"meals": [], "workouts": []}  # plan = data
            # print(vars(plan))            # plan after transforming to print the result on the dashboard
        except Exception as e:
            print("[Dashboard parse error]", e)
            # plan.data = {}
            plan.data = {"meals": [], "workouts": []}

    # Parse JSON for weekly plans
    for plan in user.weekly_plans:
        raw = plan.plan_json
        try:

            if isinstance(raw, str):
                plan.data = json.loads(raw)
            else:
                plan.data = raw or {}
        except Exception as e:
                print("Error parsing weekly plan:", e)
                plan.data = {}

    return render_template("dashboard.html", user=user)


# --- 🌐 Meal Image Fetcher with Caching ---
@lru_cache(maxsize=200)
def get_meal_image(meal_name: str) -> str:
    """
    Fetches a meal image from TheMealDB API by meal name.
    Uses an in-memory cache to reduce repeated API calls.
    """
    try:
    #     meal_name = meal_name.strip().title
    #     response = requests.get(
    #         f"https://www.themealdb.com/api/json/v1/1/search.php?s={meal_name}"
    #     )
    #     data = response.json()
    #     meals = data.get("meals")
    #     if meals and meals[0].get("strMealThumb"):
    #         return meals[0]["strMealThumb"]
    # except Exception as e:
    #     print(f"Error fetching image for {meal_name}: {e}")
    #
    # # fallback placeholder if not found
    # return url_for("static", filename="default_meal.jpg")

        clean = meal_name.strip().title()  # normalize casing
        response = requests.get(
            f"https://www.themealdb.com/api/json/v1/1/search.php?s={clean}",
            timeout=5,
        )
        data = response.json()
        meals = data.get("meals")
        if meals and meals[0].get("strMealThumb"):
            return meals[0]["strMealThumb"]

        # --- fallback: retry using only the first keyword (e.g. 'Chicken' from 'Chicken Salad Bowl')
        # first_word = clean.split()[0]
        # response = requests.get(
        #     f"https://www.themealdb.com/api/json/v1/1/search.php?s={first_word}",
        #     timeout=5,
        # )
        # data = response.json()
        # meals = data.get("meals")
        # if meals and meals[0].get("strMealThumb"):
        #     return meals[0]["strMealThumb"]

        # else generate a meal pic:
        else:
            generated_image_path = generate_meal_image(meal_name)
            return generated_image_path


    except Exception as e:
        print(f"[Meal image fetch error] {meal_name!r}: {e}")
        return generate_meal_image(meal_name)
    # still nothing → static placeholder

    # return url_for("static", filename="default_meal.jpg")

# @app.route('/generate_plan/<int:user_id>')
# def generate_plan(user_id):
#     user = User.query.get(user_id)
#     if not user:
#         flash("User not found", "error")
#         return redirect(url_for("home"))
#
#     try:
#         db.session.commit()  # commit any pending changes
#
#         # Call your AI service for daily plan
#         plan_data = generate_daily_plan(user)
#
#         # ✅ Attach meal images
#         for meal in plan_data.get("meals", []):
#             meal_name = meal.get("name")
#             if meal_name:
#                 meal["image_url"] = get_meal_image(meal_name)
#
#         # Save to DB
#         daily_plan = DailyPlan(
#             user_id=user.id,
#             plan_json=json.dumps(plan_data.model_dump()) # Convert Pydantic → dict → JSON string by adding .model_dump()
#         )
#         db.session.add(daily_plan)
#         db.session.commit()
#
#         flash("Daily plan generated successfully!", "success")
#     except Exception as e:
#         db.session.rollback()
#         flash(f"Error generating plan: {str(e)}", "error")
#
#     return redirect(url_for('dashboard', user_id=user.id))


# --- 🌐 Meal Image Fetcher with Caching ---
@lru_cache(maxsize=200)
def get_workout_image(workout_name: str) -> str:
    try:
        generated_image_path = generate_workout_image(workout_name)
        return generated_image_path

    except Exception as e:
        print(f"[Workout image fetch error] {workout_name!r}: {e}")
        return generate_workout_image(workout_name)



@app.route('/generate_plan/<int:user_id>')
def generate_plan(user_id):
    # user = User.query.get(user_id)
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("home"))

    try:
        db.session.commit()

        plan_data = generate_daily_plan(user)  # returns DailyPlan (Pydantic model)
        plan_dict = plan_data.model_dump()            # ← convert to Python dict

        # --- ✨ attach meal images here ---
        for meal in plan_dict.get("meals", []):
            meal_name = meal.get("name")
            if meal_name:
                meal["image_url"] = get_meal_image(meal_name)

        # Save to DB
        daily_plan = DailyPlan(
            user_id=user.id,
            plan_json=json.dumps(plan_dict, indent=2)
        )
        db.session.add(daily_plan)
        db.session.commit()

        flash("Daily plan generated successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error generating plan: {str(e)}", "error")

    return redirect(url_for('dashboard', user_id=user.id))


@app.route('/generate_weekly_plan/<int:user_id>')
def generate_weekly_plan_route(user_id):
    # user = User.query.get(user_id)
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("home"))

    try:
        db.session.commit()  # commit any pending changes

        # Call your AI service for weekly plan
        plan_data = generate_weekly_plan(user)

        # ✅ Add images for each meal in each day
        for day in plan_data.get("days", []):
            for meal in day.get("meals", []):
                meal_name = meal.get("name")
                if meal_name:
                    meal["image_url"] = get_meal_image(meal_name)

        weekly_plan = WeeklyPlan(
            user_id=user.id,
            plan_json=json.dumps(plan_data.model_dump()) # Convert Pydantic → dict → JSON string by adding .model_dump()
        )
        db.session.add(weekly_plan)
        db.session.commit()

        flash("Weekly plan generated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error generating weekly plan: {str(e)}", "error")

    return redirect(url_for('dashboard', user_id=user.id))


# Fill missing images on the fly, but do not freeze the page; use a background thread or task queue.
def async_get_meal_image(meal, workout):
    if meal:
        meal_name = meal.get("name")
        meal["image_url"] = get_meal_image(meal_name)

    else:
    
        workout_name = workout.get("name")
        workout["image_url"] = get_workout_image(workout_name)

    # in dashboard parsing loop
    threading.Thread(target=async_get_meal_image, args=(meal, workout)).start()



# --- Generate only daily meals ---
@app.route("/generate_daily_meals/<int:user_id>")
def generate_daily_meals(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for('home'))
    try:
        # 🔹 Call AI but only request meals
        from ai.openai_service import generate_daily_meals
        plan_data = generate_daily_meals(user)
        plan_dict = plan_data.model_dump()

        for meal in plan_dict.get("meals", []):
            meal_name = meal.get("name")
            if meal_name:
                meal["image_url"] = get_meal_image(meal_name)

        # ✅ save to DB as a partial plan (just meals)
        daily_plan = DailyPlan(user_id=user.id, plan_json=json.dumps(plan_dict))
        db.session.add(daily_plan)
        db.session.commit()
        flash("Daily meals generated successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error generating meals: {str(e)}", "error")

    return redirect(url_for('dashboard', user_id=user.id))

# --- Generate only daily workouts ---
@app.route("/generate_daily_workouts/<int:user_id>")
def generate_daily_workouts(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for('home'))

    try:
        from ai.openai_service import generate_daily_workouts
        plan_data = generate_daily_workouts(user)
        plan_dict = plan_data.model_dump()

        for workout in plan_dict.get("workouts", []):
            workout_name = workout.get("name")
            if workout_name:
                workout["image_url"] = get_workout_image(workout_name)

        daily_plan = DailyPlan(user_id=user.id, plan_json=json.dumps(plan_dict))
        db.session.add(daily_plan)
        db.session.commit()
        flash("Daily workouts generated successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error generating workouts: {str(e)}", "error")

    return redirect(url_for('dashboard', user_id=user.id))


@app.route("/daily_meals/<int:user_id>")
def daily_meals(user_id):
    user = db.session.get(User, user_id)
    plans = DailyPlan.query.filter_by(user_id=user_id).all()
    parsed = [json.loads(p.plan_json) | {"id": p.id} for p in plans]
    return render_template("daily_meals.html", user=user, plans=parsed)

@app.route("/daily_workouts/<int:user_id>")
def daily_workouts(user_id):
    # user = db.session.get(User, user_id)
    plans = DailyPlan.query.filter_by(user_id=user_id).all()
    parsed = [json.loads(p.plan_json) | {"id": p.id} for p in plans]
    return render_template("daily_workouts.html", user=user, plans=parsed)

@app.route("/item/<string:item_type>/<int:plan_id>/<int:item_index>")
def item_details(item_type, plan_id, item_index):
    plan = db.session.get(DailyPlan, plan_id)
    if not plan:
        flash("Plan not found", "error")
        return redirect(url_for("home"))

    data = json.loads(plan.plan_json)
    item = None
    if item_type == "meal":
        item = data.get("meals index", [])[item_index]
        print("test (meal)"[item_index])
    elif item_type == "workout":
        item = data.get("workouts", [])[item_index]
        print("test (workout index)"[item_index])
    else:
        flash("Invalid item type", "error")
        return redirect(url_for("dashboard", user_id=plan.user_id))

    return render_template("item_details.html",
                           item=item,
                           item_type=item_type,
                           user_id=plan.user_id)


if __name__ == '__main__':
    app.run(debug=True, port=5001) # uvicorn to run the server