import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, of, from } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class ClinicalApiService {
  private apiUrl = '/api/v1';

  // State 
  private patientIdSource = new BehaviorSubject<string | null>(null);
  currentPatientId$ = this.patientIdSource.asObservable();

  private dossierIdSource = new BehaviorSubject<string | null>(null);
  currentDossierId$ = this.dossierIdSource.asObservable();

  // Cloudinary Config - Authenticated Upload
  private cloudinaryUrl = 'https://api.cloudinary.com/v1_1/dny3jsbuo/image/upload';
  private cloudinaryApiKey = '942173935372859';
  private cloudinaryApiSecret = 'w4h-IbYEhznCHf6v4SKVomkZYa4';

  constructor(private http: HttpClient) { }

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

  /**
   * Registers a new patient.
   */
  createPatient(data: { nom: string, prenom: string, dateNaissance: string, sexe: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/patients`, data);
  }

  /**
   * Creates a dossier for the patient. 
   */
  createDossier(isMedecin: boolean = false): Observable<any> {
    const payload = {
      patient_id: this.patientId,
      is_medecin: isMedecin
    };
    return this.http.post(`${this.apiUrl}/dossiers`, payload);
  }

  /**
   * Adds 'Donnees Cliniques' (symptoms) to a dossier
   */
  addDonneesCliniques(fastData: { symptoms: string[] }, additionalNotes: string): Observable<any> {
    const payload = {
      fast: fastData.symptoms.join(', '), // Convert list to string for DB String(100)
      notes: additionalNotes
    };
    return this.http.post(`${this.apiUrl}/dossiers/${this.dossierId}/donnees-cliniques`, payload);
  }

  /**
   * Upload an image to Cloudinary using signed authentication
   */
  uploadMriToCloudinary(file: File): Observable<{ secure_url: string } | null> {
    const timestamp = Math.round(new Date().getTime() / 1000);

    return from(this.generateSignature(timestamp)).pipe(
      switchMap(signature => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('api_key', this.cloudinaryApiKey);
        formData.append('timestamp', timestamp.toString());
        formData.append('signature', signature);

        return this.http.post<any>(this.cloudinaryUrl, formData).pipe(
          map(response => ({ secure_url: response.secure_url })),
          catchError(error => {
            console.error('Cloudinary Upload Error:', error);
            return of(null);
          })
        );
      })
    );
  }

  /**
   * Helper to generate SHA-1 signature required by Cloudinary for authenticated uploads
   */
  private async generateSignature(timestamp: number): Promise<string> {
    // Cloudinary requires signing the parameters alphabetically. Since we only use timestamp,
    // the string to sign is exactly: timestamp=<timestamp><API_SECRET>
    const strToSign = `timestamp=${timestamp}${this.cloudinaryApiSecret}`;
    const buf = new TextEncoder().encode(strToSign);
    const hashBuffer = await crypto.subtle.digest('SHA-1', buf);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    // Convert to hex
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Links a Cloudinary MRI URL to the patient's dossier in PostgreSQL.
   */
  linkMriToDossier(url: string, format: string = 'MRI'): Observable<any> {
    const payload = { url, format };
    return this.http.post(`${this.apiUrl}/dossiers/${this.dossierId}/image-metadata`, payload);
  }

  /**
   * Search for patients by name or MRN
   */
  searchPatients(query: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/patients/search?q=${query}`);
  }
}
