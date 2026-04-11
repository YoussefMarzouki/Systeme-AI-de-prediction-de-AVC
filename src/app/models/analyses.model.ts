export interface DonneesCliniques {
  id?: string;
  dateSaisie?: Date | string;
  fast?: string;
  tension?: string;
  age?: number;
  notes?: string;
  dossier_id: string;
}

export interface ImageIRM {
  idImage?: string;
  format?: string;
  cheminStockage: string;
  dateAcquisition?: Date | string;
  qualiteOK?: boolean;
  dossier_id: string;
}

export interface AnalyseIA {
  idAnalyse?: string;
  dateAnalyse?: Date | string;
  probabiliteAVC: number;
  scoreConfiance: number;
  modeleVersion: string;
  image_id: string;
}

export interface AnalyseSymptomes {
  id?: string;
  valeur: number;
  methode: string;
  donnees_cliniques_id: string;
}

export interface EvaluationRisque {
  id?: string;
  scoreGlobal: number;
  niveau: string;
  analyse_ia_id: string;
  analyse_symptomes_id: string;
  dossier_id: string;
}
