from flask import Flask, render_template, request, flash, redirect, url_for
from datamanager.models import db, User, Workout, WorkoutPlan, Meal, Log, DailyPlan, WeeklyPlan
from datamanager.sqlite_data_manager import SQLiteDataManager
from validation import validate_user_data
from datetime import datetime, date
import json
from ai.openai_service import generate_daily_plan, generate_weekly_plan
from flask_migrate import Migrate


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
        "now": datetime.utcnow(),
        "today": date.today()
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
    user = User.query.get(user_id)
    if not user:
        flash("User not found")
        return redirect(url_for('home'))

    # Parse JSON strings into Python dicts for daily plans
    for plan in user.daily_plans:
        try:
            plan.data = json.loads(plan.plan_json)
        except Exception:
            plan.data = {} # fallback if broken JSON

    # Parse JSON for weekly plans
    for plan in user.weekly_plans:
        if isinstance(plan.plan_json, str):
            try:
                plan.data = json.loads(plan.plan_json)
            except Exception:
                plan.data = {}

    return render_template("dashboard.html", user=user)


@app.route('/generate_plan/<int:user_id>')
def generate_plan(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("home"))

    try:
        plan_data = generate_daily_plan(user)

        # Save to DB
        daily_plan = DailyPlan(
            user_id=user.id,
            plan_json=json.dumps(plan_data)
        )
        db.session.add(daily_plan)
        db.session.commit()

        flash("Daily plan generated successfully!", "success")
    except Exception as e:
        flash(f"Error generating plan: {str(e)}", "error")

    return redirect(url_for('dashboard', user_id=user.id))


@app.route('/generate_weekly_plan/<int:user_id>')
def generate_weekly_plan_route(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("home"))

    try:
        # Call your AI service for weekly plan
        plan_data = generate_weekly_plan(user)

        weekly_plan = WeeklyPlan(
            user_id=user.id,
            plan_json=json.dumps(plan_data)
        )
        db.session.add(weekly_plan)
        db.session.commit()

        flash("Weekly plan generated successfully!", "success")
    except Exception as e:
        flash(f"Error generating weekly plan: {str(e)}", "error")

    return redirect(url_for('dashboard', user_id=user.id))


if __name__ == '__main__':
    app.run(debug=True, port=5000)