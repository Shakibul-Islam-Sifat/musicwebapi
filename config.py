class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///music_database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "music-app-secret-key"