export interface Rapport {
  idRapport?: string;
  dateGeneration?: Date | string;
  dateModification?: Date | string;
  statut?: string;
  cheminFichier?: string;
  contenu?: any;
  medecin_id: string;
  modifie_par_id?: string;
  dossier_id: string;
}
