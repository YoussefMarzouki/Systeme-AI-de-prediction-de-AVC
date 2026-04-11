import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, from, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { StateService } from './state.service';

@Injectable({
  providedIn: 'root'
})
export class ImageIrmService {
  private apiUrl = '/api/v1/dossiers';
  private cloudinaryUrl = 'https://api.cloudinary.com/v1_1/dny3jsbuo/image/upload';
  private cloudinaryApiKey = '942173935372859';
  private cloudinaryApiSecret = 'w4h-IbYEhznCHf6v4SKVomkZYa4';

  constructor(private http: HttpClient, private state: StateService) {}

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
    const strToSign = `timestamp=${timestamp}${this.cloudinaryApiSecret}`;
    const buf = new TextEncoder().encode(strToSign);
    const hashBuffer = await crypto.subtle.digest('SHA-1', buf);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Links a Cloudinary MRI URL to the patient's dossier in PostgreSQL.
   */
  linkMriToDossier(url: string, format: string = 'MRI'): Observable<any> {
    const payload = { url, format };
    return this.http.post(`${this.apiUrl}/${this.state.dossierId}/image-metadata`, payload, { headers: this.state.getAuthHeaders() });
  }
}
