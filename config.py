class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Breejeada2007#@localhost/evoting_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "evoting_secret_2025"
    JWT_SECRET_KEY = "evoting_jwt_secret_2025"
    