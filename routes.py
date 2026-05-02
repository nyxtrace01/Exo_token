from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from app import db
from models import Electeur, Candidat, Vote, Election

main = Blueprint('main', __name__)


# ── Accueil : liste des candidats (point 11) ─────────────────────────────────
@main.route('/')
def index():
    candidats  = Candidat.query.all()
    elections  = Election.query.all()
    # Exercice 13.4 : compter les votes par candidat
    resultats = []
    for c in candidats:
        nb = Vote.query.filter_by(candidat_id=c.id).count()
        resultats.append({'candidat': c, 'votes': nb})
    return render_template('index.html', candidats=candidats,
                           elections=elections, resultats=resultats)


# ── Inscription ───────────────────────────────────────────────────────────────
@main.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        nom      = request.form['nom'].strip()
        email    = request.form['email'].strip()
        password = request.form['mot_de_passe']

        if Electeur.query.filter_by(email=email).first():
            flash("Cet email est déjà utilisé.", "danger")
            return redirect(url_for('main.inscription'))

        e = Electeur(nom=nom, email=email)
        e.set_password(password)   # 12.1 — hash
        db.session.add(e)
        db.session.commit()
        flash("Compte créé avec succès !", "success")
        return redirect(url_for('main.connexion'))

    return render_template('inscription.html')


# ── Connexion ─────────────────────────────────────────────────────────────────
@main.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email    = request.form['email'].strip()
        password = request.form['mot_de_passe']
        e = Electeur.query.filter_by(email=email).first()

        if e and e.check_password(password):   # 12.1 — vérification hash
            session['electeur_id']  = e.id
            session['electeur_nom'] = e.nom
            flash(f"Bienvenue {e.nom} !", "success")
            return redirect(url_for('main.voter'))
        flash("Email ou mot de passe incorrect.", "danger")

    return render_template('connexion.html')


@main.route('/deconnexion')
def deconnexion():
    session.clear()
    flash("Déconnecté.", "info")
    return redirect(url_for('main.connexion'))


@main.route('/voter', methods=['GET', 'POST'])
def voter():
    if 'electeur_id' not in session:
        flash("Connectez-vous pour voter.", "warning")
        return redirect(url_for('main.connexion'))

    electeur = Electeur.query.get(session['electeur_id'])

    if request.method == 'POST':
        # Exercice 13.1 — empêcher de voter deux fois
        if electeur.has_voted:
            flash("Vous avez déjà voté !", "danger")
            return redirect(url_for('main.resultats'))

        candidat_id = request.form.get('candidat_id')
        if not candidat_id:
            flash("Sélectionnez un candidat.", "warning")
            return redirect(url_for('main.voter'))

        vote = Vote(electeur_id=electeur.id, candidat_id=int(candidat_id))
        db.session.add(vote)
        electeur.has_voted = True   # Exercice 13.5
        db.session.commit()
        flash("✅ Vote enregistré !", "success")
        return redirect(url_for('main.resultats'))

    candidats = Candidat.query.all()
    return render_template('voter.html', electeur=electeur, candidats=candidats)


# ── Résultats (exercice 13.4) ─────────────────────────────────────────────────
@main.route('/resultats')
def resultats():
    candidats    = Candidat.query.all()
    total_votes  = Vote.query.count()
    resultats    = []
    for c in candidats:
        nb  = Vote.query.filter_by(candidat_id=c.id).count()
        pct = round(nb / total_votes * 100, 1) if total_votes else 0
        resultats.append({'nom': c.nom, 'votes': nb, 'pct': pct,
                          'election': c.election.titre if c.election else '—'})
    resultats.sort(key=lambda x: x['votes'], reverse=True)
    return render_template('resultats.html', resultats=resultats, total=total_votes)


# ── Admin : candidats ─────────────────────────────────────────────────────────
@main.route('/admin/candidat', methods=['GET', 'POST'])
def admin_candidat():
    if request.method == 'POST':
        nom         = request.form['nom'].strip()
        election_id = request.form.get('election_id') or None
        db.session.add(Candidat(nom=nom, election_id=election_id))
        db.session.commit()
        flash(f"Candidat « {nom} » ajouté.", "success")
        return redirect(url_for('main.admin_candidat'))

    candidats = Candidat.query.all()
    elections = Election.query.all()
    # ajouter comptage votes pour affichage
    data = []
    for c in candidats:
        nb = Vote.query.filter_by(candidat_id=c.id).count()
        data.append({'candidat': c, 'votes': nb})
    return render_template('admin_candidat.html', data=data, elections=elections)


# ── Admin : élections (exercice 13.2) ────────────────────────────────────────
@main.route('/admin/election', methods=['GET', 'POST'])
def admin_election():
    if request.method == 'POST':
        titre = request.form['titre'].strip()
        db.session.add(Election(titre=titre))
        db.session.commit()
        flash(f"Élection « {titre} » créée.", "success")
        return redirect(url_for('main.admin_election'))

    elections = Election.query.all()
    return render_template('admin_election.html', elections=elections)


# ── Login JWT ─────────────────────────────────────────────────────────────────
@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({
            'success': False,
            'message': 'Email et mot de passe requis.'
        }), 400

    electeur = Electeur.query.filter_by(email=data['email']).first()

    if not electeur or not electeur.check_password(data['password']):
        return jsonify({
            'success': False,
            'message': 'Email ou mot de passe incorrect.'
        }), 401

    access_token = create_access_token(
        identity=str(electeur.id),
        additional_claims={
            'email': electeur.email,
            'nom':   electeur.nom,
        },
        expires_delta=timedelta(hours=1)
    )

    return jsonify({
        'success':      True,
        'message':      f'Bienvenue {electeur.nom} !',
        'access_token': access_token,
        'electeur': {
            'id':    electeur.id,
            'email': electeur.email,
            'nom':   electeur.nom,
        }
    }), 200


# ── Profil — route protégée par JWT ──────────────────────────────────────────
@main.route('/profil', methods=['GET'])
@jwt_required()
def profil():
    electeur_id = get_jwt_identity()
    electeur    = Electeur.query.get(int(electeur_id))
    return jsonify({
        'id':        electeur.id,
        'nom':       electeur.nom,
        'email':     electeur.email,
        'has_voted': electeur.has_voted
    }), 200