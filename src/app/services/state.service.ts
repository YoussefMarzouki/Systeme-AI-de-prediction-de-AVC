import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class StateService {
  // State 
  private patientIdSource = new BehaviorSubject<string | null>(null);
  currentPatientId$ = this.patientIdSource.asObservable();

  private dossierIdSource = new BehaviorSubject<string | null>(null);
  currentDossierId$ = this.dossierIdSource.asObservable();

  // Mock Authentication State
  public isCurrentUserMedecin = false; // Default: Agent d'accueil role

  getAuthHeaders() {
    // Fixed UUIDs configured in backend/seed.py
    const agentId = '11111111-1111-1111-1111-111111111111'; // Ben Ali, Ahmed (Agent d'accueil)
    const medecinId = '33333333-3333-3333-3333-333333333333'; // Dr. Khemiri, Youssef (Medecin)
    
    return { 
      'User-ID': this.isCurrentUserMedecin ? medecinId : agentId 
    };
  }

  setPatientId(id: string) {
    this.patientIdSource.next(id);
  }

  get patientId(): string | null {
    return this.patientIdSource.value;
  }

  setDossierId(id: string) {
    this.dossierIdSource.next(id);
  }

  get dossierId(): string | null {
    return this.dossierIdSource.value;
  }
}
