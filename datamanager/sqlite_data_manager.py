from abc import ABC

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .data_manager_interface import DataManagerInterface
from .models import db, User, Workout, WorkoutPlan, Meal, Log

class SQLiteDataManager(DataManagerInterface, ABC):
    """
    SQLiteDataManager implements the DataManagerInterface using SQLAlchemy ORM.
    Provides CRUD operations for the User model (can be extended to others).
    """
    def __init__(self, db_file_name, app):
        self.app = app
        self.db_file_name = db_file_name

    # def __int__(self, db_file_name, app: Flask):
    #     self.app = app
    #     app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file_name}'
    #     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    #     app.secret_key = 'your_secret_key_here'  # Required for session
    #
    #     db.init_app(app)

    def add_user(self, user_name, gender, age, height, weight, dietary_pref, fitness_goal, activity_level):
        """Add a new user to the database."""
        new_user = User(
            user_name=user_name,
            age=age,
            gender=gender,
            height=height,
            weight=weight,
            dietary_pref=dietary_pref,
            fitness_goal=fitness_goal,
            activity_level=activity_level
        )

        db.session.add(new_user)
        db.session.commit()
        db.session.refresh(new_user)
        return new_user

    def get_user_by_id(self, user_id):
        """Retrieve a user by their ID."""
        return User.query.get(user_id)

    def get_user_by_name(self, user_name):
        """Retrieve a user by their name."""
        return User.query.filter_by(user_name=user_name).first()

    def delete_user(self, user_id):
        """Delete a user by their ID."""
        user = User.query.get(user_id )
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False

    def get_all_users(self):
        """Retrieve a list for all users."""
        return User.query.all()

    def update_user(self, user_id, updated_data):
        user = User.query.get(user_id)
        if not user:
            return None
        for key, value in updated_data.items():
            setattr(user, key, value)
        db.session.commit()
        return user