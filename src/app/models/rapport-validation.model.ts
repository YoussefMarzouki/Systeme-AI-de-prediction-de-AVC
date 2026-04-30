export type RapportValidationStatus = 'PENDING_VALIDATION' | 'VALIDATED' | 'REJECTED';

export interface QueueCase {
  rapport_id: string;
  dossier_id: string;
  patient_id: string;
  patient_name: string;
  patient_initials: string;
  patient_gender: string;
  patient_age: number | null;
  modality: string;
  ai_irm_score: number | null;
  ai_symptom_score: number | null;
  ai_probability_score: number | null;
  fused_score: number | null;
  time_since_onset: string;
  risk_level: string;
  status: 'very-high-risk' | 'high-risk' | 'medium' | 'low';
  rapport_status: string;
  date_generation?: string | null;
}

export interface MedicalComment {
  id: string;
  texte: string;
  date?: string | null;
  medecin_id: string;
}

export interface CaseDetail {
  rapport_id: string;
  dossier_id: string;
  rapport_status: string;
  patient_id: string;
  patient_name: string;
  patient_cin?: string | null;
  patient_gender: string;
  patient_age: number | null;
  risk_level: string;
  predicted_class: string;
  confidence_score: number | null;
  ai_irm_score: number | null;
  ai_symptom_score: number | null;
  ai_probability_score: number | null;
  fused_score: number | null;
  ai_assessment: string;
  clinical_data: {
    fast?: string | null;
    tension?: string | null;
    notes?: string | null;
    age?: number | null;
  };
  image_urls: string[];
  total_slices: number;
  comments: MedicalComment[];
  contenu?: any;
  date_generation?: string | null;
  date_modification?: string | null;
  modifie_par_id?: string | null;
}

export interface ValidateRapportPayload {
  notes?: string;
  predicted_class?: string;
  ai_assessment?: string;
}

export interface RejectRapportPayload {
  notes?: string;
}
