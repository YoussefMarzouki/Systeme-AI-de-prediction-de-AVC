export interface Utilisateur {
  id?: string;
  nom: string;
  email: string;
  etat: string;
  type: string;
}

export interface Medecin extends Utilisateur {
  specialiste?: boolean;
}

export interface AgentAccueil extends Utilisateur {}
export interface Admin extends Utilisateur {}
