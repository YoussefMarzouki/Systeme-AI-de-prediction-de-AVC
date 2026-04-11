export interface Patient {
  id?: string;
  cin?: string;
  nom: string;
  prenom: string;
  dateNaissance: Date | string;
  age?: number;
  sexe: string;
}
