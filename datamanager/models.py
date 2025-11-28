from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    activity_level = db.Column(db.String(20), nullable=True)
    dietary_pref = db.Column(db.String, nullable=False)
    fitness_goal = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    workout = db.relationship('Workout', backref='user', cascade="all, delete", lazy=True )
    workout_plan = db.relationship('WorkoutPlan', backref='user', cascade="all, delete", lazy=True)
    meal = db.relationship('Meal', backref='user', cascade="all, delete", lazy=True)
    log = db.relationship('Log', backref='user', cascade="all, delete", lazy=True)
    daily_plans = db.relationship('DailyPlan', back_populates='user', cascade="all, delete", lazy=True,
                                  order_by="desc(DailyPlan.created_at)") # newest first
    weekly_plans = db.relationship("WeeklyPlan", back_populates="user", cascade="all, delete-orphan",
                                  order_by="desc(WeeklyPlan.created_at)") # newest first


class Workout(db.Model):

    __tablename__ = 'workouts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(120), nullable=False)
    duration = db.Column(db.Integer)
    intensity = db.Column(db.String)
    description = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workout_plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.id'), nullable=False)


class WorkoutPlan(db.Model):

    __tablename__ = 'workout_plans'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=True, nullable=False)
    active = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workouts = db.relationship('Workout', backref='plan', cascade="all, delete", lazy=True)


class DailyPlan(db.Model):

    __tablename__ = 'daily_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, default=lambda: datetime.utcnow().date())
    plan_json = db.Column(db.Text, nullable=False)  # Save JSON as string
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='daily_plans')

    @property
    def plan(self):
        """Returns plan_json as a Python dict"""
        try:
            return json.loads(self.plan_json)
        except:
            return {}


class WeeklyPlan(db.Model):

    __tablename__ = 'weekly_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_json = db.Column(db.JSON)  # Full Monday–Sunday JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="weekly_plans")


class Meal(db.Model):

    __tablename__ = 'meals'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=True)
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat =  db.Column(db.Float)
    ingredients = db.Column(db.String)
    instructions = db.Column(db.String)
    rest_time = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class DailyMeal(db.Model):

    __tablename__ = 'daily_meals'

    id = db.Column(db.Integer, primary_key=True)
    daily_plan_id = db.Column(db.Integer, db.ForeignKey('daily_plans.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), nullable=False)
    user = db.relationship('DailyPlan', backref='daily_meals')
    meal = db.relationship('Meal')


class Log(db.Model):

    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=True)
    meals_completed = db.Column(db.Integer)
    workouts_completed = db.Column(db.Integer)
    mood = db.Column(db.String)
    notes = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
