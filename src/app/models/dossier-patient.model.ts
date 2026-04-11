export interface DossierPatient {
  idDossier?: string;
  dateCreation?: Date | string;
  statut?: string;
  patient_id: string;
  agent_id?: string;
  medecin_id?: string;
}
