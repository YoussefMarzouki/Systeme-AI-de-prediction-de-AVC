import sys
import os
from datetime import datetime
import bcrypt

# Adjust Python path if run from root
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.core.db import db
from app.models.patient import Patient
from app.models.dossier_patient import DossierPatient
from app.models.donnees_cliniques import DonneesCliniques
from app.models.image_irm import ImageIRM
from app.models.analyses import AnalyseIA, AnalyseSymptomes, EvaluationRisque
from app.models.user import Utilisateur, Medecin, AgentAccueil, Admin
from app.models.commentaire_medical import CommentaireMedical
from app.models.rapport import Rapport

app = create_app()

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def seed_db():
    with app.app_context():
        try:
            print("Beginning the seeding process with Tunisian test data...")
            print("Clearing all previous data...")
            db.drop_all()
            db.create_all()
            print("Database tables recreated fresh.")

            admin_data = {
                'id': '55555555-5555-5555-5555-555555555555',
                'nom': 'Administrateur Systeme',
                'email': 'admin@hopital.tn',
                'password': 'password123'
            }
            admin = Admin.query.filter_by(email=admin_data['email']).first()
            if not admin:
                admin = Admin(
                    id=admin_data['id'],
                    nom=admin_data['nom'],
                    email=admin_data['email'],
                    motDePasse=hash_password(admin_data['password']),
                    etat='actif'
                )
                db.session.add(admin)
                db.session.commit()
            
            # --- 1. USER CREATION (Médecins & Agents d'accueil) ---
            agents_data = [
                {'id': '11111111-1111-1111-1111-111111111111', 'nom': 'Ben Ali, Ahmed', 'email': 'ahmed.accueil@hopital.tn', 'password': 'password123'},
                {'id': '22222222-2222-2222-2222-222222222222', 'nom': 'Trabelsi, Salma', 'email': 'salma.accueil@hopital.tn', 'password': 'password123'}
            ]
            agents = []
            for ad in agents_data:
                agent = AgentAccueil.query.filter_by(email=ad['email']).first()
                if not agent:
                    agent = AgentAccueil(id=ad['id'], nom=ad['nom'], email=ad['email'], motDePasse=hash_password(ad['password']), etat='actif')
                    db.session.add(agent)
                agents.append(agent)
            db.session.commit()

            medecins_data = [
                {'id': '33333333-3333-3333-3333-333333333333', 'nom': 'Dr. Khemiri, Youssef', 'email': 'dr.khemiri@hopital.tn', 'password': 'password123', 'specialiste': True},
                {'id': '44444444-4444-4444-4444-444444444444', 'nom': 'Dr. Mansour, Leila', 'email': 'dr.mansour@hopital.tn', 'password': 'password123', 'specialiste': False}
            ]
            medecins = []
            for md in medecins_data:
                med = Medecin.query.filter_by(email=md['email']).first()
                if not med:
                    med = Medecin(id=md['id'], nom=md['nom'], email=md['email'], motDePasse=hash_password(md['password']), specialiste=md['specialiste'], etat='actif')
                    db.session.add(med)
                medecins.append(med)
            db.session.commit()

            # --- 2. PATIENT CREATION (Tunisian Names) ---
            patients_data = [
                {'nom': 'Gharbi', 'prenom': 'Mohamed', 'cin': '12345678', 'dateNaissance': '1965-04-12', 'sexe': 'M'},
                {'nom': 'Jelassi', 'prenom': 'Fatma', 'cin': '01234567', 'dateNaissance': '1958-09-23', 'sexe': 'F'},
                {'nom': 'Bouazizi', 'prenom': 'Sami', 'cin': '09876543', 'dateNaissance': '1972-11-05', 'sexe': 'M'},
                {'nom': 'Hammami', 'prenom': 'Aicha', 'cin': '11223344', 'dateNaissance': '1980-02-15', 'sexe': 'F'}
            ]
            patients = []
            for pd in patients_data:
                patient = Patient.query.filter_by(nom=pd['nom'], prenom=pd['prenom']).first()
                if not patient:
                    patient = Patient(nom=pd['nom'], prenom=pd['prenom'], cin=pd['cin'], dateNaissance=pd['dateNaissance'], sexe=pd['sexe'])
                    db.session.add(patient)
                patients.append(patient)
            db.session.commit()

            print(f"Added/Verified {len(medecins)} Medecins, {len(agents)} Agents, and {len(patients)} Patients.")

            # --- 3. MEDICAL RECORDS MULTIPLE ENTRIES ---
            for idx, patient in enumerate(patients):
                
                # Dossier Patient
                dossier = DossierPatient.query.filter_by(patient_id=patient.id).first()
                if not dossier:
                    dossier = DossierPatient(
                        patient_id=patient.id, 
                        agent_id=agents[idx % len(agents)].id, 
                        medecin_id=medecins[idx % len(medecins)].id,
                        statut='OUVERT' if idx % 2 == 0 else 'FERME'
                    )
                    db.session.add(dossier)
                    db.session.commit()

                # Donnees Cliniques (With Tunisian Phone Numbers in notes)
                donnees = DonneesCliniques.query.filter_by(dossier_id=dossier.idDossier).first()
                if not donnees:
                    cities = ['Tunis', 'Sfax', 'Sousse', 'Bizerte']
                    phone_number = f"98 {123 + idx} {456 + idx}" # Generic tunisian phone +216 98 XXX XXX
                    fast_symptoms = 'Facial Droop, Speech Difficulty' if idx % 2 == 0 else 'Arm Weakness'
                    donnees = DonneesCliniques(
                        dossier_id=dossier.idDossier, 
                        fast=fast_symptoms, 
                        tension='140' if idx % 2 == 0 else '120', 
                        age=60 + idx, 
                        notes=f'Patient originaire de {cities[idx % len(cities)]}. Contact famille/urgence (+216 {phone_number}).'
                    )
                    db.session.add(donnees)
                    db.session.commit()

                # Image IRM
                image = ImageIRM.query.filter_by(dossier_id=dossier.idDossier).first()
                if not image:
                    image = ImageIRM(
                        dossier_id=dossier.idDossier,
                        format='MRI',
                        cheminStockage=f'https://res.cloudinary.com/demo/image/upload/v1/samples/mri_brain_{idx}.jpg',
                        qualiteOK=True
                    )
                    db.session.add(image)
                    db.session.commit()

                # Analyse IA
                analyse_ia = AnalyseIA.query.filter_by(image_id=image.idImage).first()
                if not analyse_ia:
                    analyse_ia = AnalyseIA(
                        probabiliteAVC=0.85 - (idx * 0.1), # Varying probabilities per patient
                        scoreConfiance=0.91,
                        modeleVersion='ResNet18',
                        image_id=image.idImage
                    )
                    db.session.add(analyse_ia)
                    db.session.commit()

                # Analyse Symptômes
                analyse_sym = AnalyseSymptomes.query.filter_by(donnees_cliniques_id=donnees.id).first()
                if not analyse_sym:
                    analyse_sym = AnalyseSymptomes(
                        valeur=0.75 - (idx * 0.1),
                        methode='Groq-LLM-FR',
                        donnees_cliniques_id=donnees.id
                    )
                    db.session.add(analyse_sym)
                    db.session.commit()

                # Evaluation Global Risque
                eval_risque = EvaluationRisque.query.filter_by(analyse_ia_id=analyse_ia.idAnalyse).first()
                if not eval_risque:
                    score = (analyse_ia.probabiliteAVC + analyse_sym.valeur) / 2
                    niveau = 'HIGH' if score > 0.7 else ('MEDIUM' if score > 0.4 else 'LOW')
                    eval_risque = EvaluationRisque(
                        scoreGlobal=score,
                        niveau=niveau,
                        analyse_ia_id=analyse_ia.idAnalyse,
                        analyse_symptomes_id=analyse_sym.id,
                        dossier_id=dossier.idDossier
                    )
                    db.session.add(eval_risque)
                    db.session.commit()

                # Commentaire Medical (Diagnosed by Medecin)
                commentaire = CommentaireMedical.query.filter_by(dossier_id=dossier.idDossier).first()
                if not commentaire:
                    text_comment = 'Suspicion d\'AVC confirmée. Un transfert urgent vers l\'hôpital Charles Nicolle est recommandé.' if niveau == 'HIGH' else 'Le patient doit rester en observation.'
                    commentaire = CommentaireMedical(
                        texte=text_comment,
                        medecin_id=medecins[idx % len(medecins)].id,
                        dossier_id=dossier.idDossier
                    )
                    db.session.add(commentaire)
                    db.session.commit()

                # Rapport Medical
                rapport = Rapport.query.filter_by(dossier_id=dossier.idDossier).first()
                if not rapport:
                    # Let's assign an optional 'modifie_par_id' to some reports to test it in the UI and pgAdmin
                    modificateur = medecins[(idx + 1) % len(medecins)].id if idx % 2 == 0 else None
                    
                    rapport = Rapport(
                        medecin_id=medecins[idx % len(medecins)].id,
                        dossier_id=dossier.idDossier,
                        statut='GENERATED',
                        modifie_par_id=modificateur
                    )
                    db.session.add(rapport)
                    db.session.commit()

            print("Database completely naturally seeded with multiple Tunisian entries across all tables!")
        except Exception as e:
            print(f"Error seeding database: {e}")
            db.session.rollback()

if __name__ == '__main__':
    seed_db()
