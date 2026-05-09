import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export type UserRole = 'agent' | 'mg' | 'ms' | 'admin';

@Injectable({
  providedIn: 'root'
})
export class StateService {
  // State 
  private patientIdSource = new BehaviorSubject<string | null>(null);
  currentPatientId$ = this.patientIdSource.asObservable();

  private dossierIdSource = new BehaviorSubject<string | null>(null);
  currentDossierId$ = this.dossierIdSource.asObservable();

  public currentRole: UserRole = this.resolveStoredRole();

  get isCurrentUserMedecin(): boolean {
    return this.currentRole === 'mg';
  }

  set isCurrentUserMedecin(value: boolean) {
    this.currentRole = value ? 'mg' : 'agent';
  }

  get isCurrentUserSpecialiste(): boolean {
    return this.currentRole === 'ms';
  }

  get isCurrentUserDoctor(): boolean {
    return this.currentRole === 'mg' || this.currentRole === 'ms';
  }

  get isCurrentUserAdmin(): boolean {
    return this.currentRole === 'admin';
  }

  setRole(role: UserRole) {
    this.currentRole = role;
  }

  get routePrefix(): string {
    if (this.currentRole === 'mg') return '/mg';
    if (this.currentRole === 'ms') return '/ms';
    if (this.currentRole === 'admin') return '/admin';
    return '/agent';
  }

  getAuthHeaders() {
    const storedUser = this.getStoredUser();
    if (storedUser?.id) {
      return {
        'User-ID': storedUser.id
      };
    }

    // Fallback UUIDs configured in backend/seed.py
    const agentId = '11111111-1111-1111-1111-111111111111'; // Ben Ali, Ahmed (Agent d'accueil)
    const medecinGeneralisteId = '44444444-4444-4444-4444-444444444444'; // Dr. Mansour, Leila (Medecin generaliste)
    const medecinSpecialisteId = '33333333-3333-3333-3333-333333333333'; // Dr. Khemiri, Youssef (Medecin specialiste)
    const adminId = '55555555-5555-5555-5555-555555555555'; // Admin seed account
    
    let userId = agentId;
    if (this.currentRole === 'mg') userId = medecinGeneralisteId;
    if (this.currentRole === 'ms') userId = medecinSpecialisteId;
    if (this.currentRole === 'admin') userId = adminId;

    return { 
      'User-ID': userId
    };
  }

  private resolveStoredRole(): UserRole {
    const user = this.getStoredUser();
    if (user?.type === 'admin') return 'admin';
    if (user?.type === 'agent_accueil') return 'agent';
    if (user?.type === 'medecin') return user.specialiste ? 'ms' : 'mg';
    return 'agent';
  }

  private getStoredUser(): any {
    const raw = localStorage.getItem('strokeai_user');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
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
