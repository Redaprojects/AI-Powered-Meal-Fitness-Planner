from abc import ABC, abstractmethod

class DataManagerInterface(ABC):
    """
    Abstract base class for data manager implementations.
    Provides a standard interface for interacting with the database layer.
    """

    @abstractmethod
    def add_user(self, user_name, gender, age, height, weight, dietary_pref, fitness_goal, activity_level):
        pass

    @abstractmethod
    def get_user_by_id(self, user_id):
        pass

    @abstractmethod
    def get_user_by_name(self, user_name):
        pass

    @abstractmethod
    def delete_user(self, user_id):
        pass

    @abstractmethod
    def get_all_users(self):
        pass

    def update_user(self, user_id, updated_data):
        pass


