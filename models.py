from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Electeur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    has_voted = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.mot_de_passe = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe, password)


class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)

    candidats = db.relationship('Candidat', backref='election', lazy=True)


class Candidat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'))


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    electeur_id = db.Column(db.Integer, db.ForeignKey('electeur.id'))
    candidat_id = db.Column(db.Integer, db.ForeignKey('candidat.id'))

    electeur = db.relationship('Electeur')
    candidat = db.relationship('Candidat')