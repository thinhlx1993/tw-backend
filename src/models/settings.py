from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column, ForeignKey, String
from src import db


class Settings(db.Model):
    """
    Model for settings Table
    Attributes:
    'user_id' : User ID linked to the settings(UUID)
    'device_id' : Device ID linked to the settings(UUID)
    'settings' : Settings data stored in JSON format(JSON)
    """

    __tablename__ = "settings"

    user_id = Column(
        String(128), ForeignKey("user.user_id"), primary_key=True, nullable=False
    )
    device_id = Column(String(128), primary_key=True, nullable=False)
    settings = Column(JSON)

    # Constructor initializing values
    def __init__(self, user_id, device_id, settings):
        self.user_id = user_id
        self.device_id = device_id
        self.settings = settings

    # String representation of the model
    def __repr__(self):
        return f"<Settings(user_id={self.user_id}, device_id={self.device_id}, settings={self.settings})>"

    def repr_name(self):
        """
        browserPath: '',
        browserType: 'HideMyAcc',
        browserVersion: '',
        hideMyAccAccount: '',
        hideMyAccPassword: '',
        chatGptKey: '',
        defaultCaptchaResolve: '',
        antiCaptchaKey: '',
        textSolveKey: ''
        """
        return {
            "user_id": self.user_id,
            "device_id": self.device_id,
            "settings": self.settings,
        }
