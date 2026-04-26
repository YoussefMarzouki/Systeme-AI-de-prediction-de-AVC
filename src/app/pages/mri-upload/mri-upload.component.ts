import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import { PatientService } from '../../services/patient.service';
import { DossierService } from '../../services/dossier.service';
import { StateService } from '../../services/state.service';
import { ImageIrmService } from '../../services/image-irm.service';
import { DonneesCliniquesService } from '../../services/donnees-cliniques.service';
import { PredictionService } from '../../services/prediction.service';

interface UploadedFile {
  name: string;
  size: string;
  status: string;
  url?: string;
}

@Component({    
  selector: 'app-mri-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './mri-upload.component.html',
  styleUrl: './mri-upload.component.css'
})
export class MriUploadComponent implements OnInit {
  isDragOver = false;
  isSubmitting = false;
  uploadedFiles: UploadedFile[] = [];
  
  patientName = 'Unknown Patient';
  patientCin = 'N/A';

  // These should be passed from state or already persisted in backend
  symptomsText: string = '';
  tensionValue: number | null = null;
  ageText: string = '';

  // Symptom Analysis Data
  symptomAnalysisData: any = null;
  isAnalyzingSymptoms = false;

  constructor(
    private router: Router,
    public stateService: StateService,
    private imageIrmService: ImageIrmService,
    private predictionService: PredictionService
  ) {
    const nav = this.router.getCurrentNavigation();
    const state = nav?.extras.state as any;
    
    if (state?.patientDetails) {
      this.patientName = state.patientDetails.name || 'Unknown Patient';
      this.patientCin = state.patientDetails.cin || 'N/A';
    } else if (this.stateService.patientId) {
      this.patientName = 'Patient ID: ' + this.stateService.patientId;
    }
    
    if (state?.symptomsData) {
      this.symptomsText = state.symptomsData.symptomsText;
      this.tensionValue = state.symptomsData.tensionValue;
      this.ageText = state.symptomsData.ageText;
    }
  }

  ngOnInit(): void {
    if (this.symptomsText) {
      this.runSymptomAnalysis();
    }
  }

  runSymptomAnalysis(): void {
    this.isAnalyzingSymptoms = true;
    this.predictionService.predictSymptoms(this.symptomsText).subscribe({
      next: (res) => {
        this.symptomAnalysisData = res.prediction || res;
        this.isAnalyzingSymptoms = false;
      },
      error: (err) => {
        console.error('Symptom prediction failed:', err);
        this.isAnalyzingSymptoms = false;
      }
    });
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave(): void {
    this.isDragOver = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;
    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      this.uploadFile(event.dataTransfer.files[0]);
    }
  }

  onFileSelect(event: any): void {
    if (event.target.files && event.target.files.length > 0) {
      this.uploadFile(event.target.files[0]);
    }
  }

  private uploadFile(file: File): void {
    const newFile: UploadedFile = {
      name: file.name,
      size: (file.size / 1024 / 1024).toFixed(2) + ' MB',
      status: 'Uploading...'
    };
    this.uploadedFiles.push(newFile);
    const idx = this.uploadedFiles.length - 1;

    this.imageIrmService.uploadMriToCloudinary(file).subscribe({
      next: (res) => {
        if (res?.secure_url) {
          this.uploadedFiles[idx].status = 'Success';
          this.uploadedFiles[idx].url = res.secure_url;
          
          if (this.stateService.dossierId) {
            this.imageIrmService.linkMriToDossier(res.secure_url).subscribe({
              next: (dbRes) => console.log('Linked MRI to DB:', dbRes),
              error: (err) => console.error('Failed to link MRI to DB:', err)
            });
          }
        } else {
          this.uploadedFiles[idx].status = 'Failed';
        }
      },
      error: () => {
        this.uploadedFiles[idx].status = 'Error';
      }
    });
  }

  removeFile(index: number): void {
    this.uploadedFiles.splice(index, 1);
  }

  onDoItLater(): void {
    // Return to dashboard
    this.router.navigate(['/mg/dashboard']);
  }

  onSubmitAnalysis(): void {
    if (this.isSubmitting) return;
    this.isSubmitting = true;

    let imageUrl: string | null = null;
    if (this.uploadedFiles.length > 0 && this.uploadedFiles[0].url) {
      imageUrl = this.uploadedFiles[0].url;
    }

    if (!imageUrl) {
        alert("Please upload an MRI image to proceed with the analysis.");
        this.isSubmitting = false;
        return;
    }

    // Only call image prediction — symptom analysis was already done in ngOnInit
    this.predictionService.predictImage(imageUrl).subscribe({
      next: (imageRes) => {
        this.isSubmitting = false;
        const imageResult = imageRes.prediction || imageRes;

        // Merge cached symptom analysis with image prediction
        const mergedPrediction = {
          ...imageResult,
          symptom_probability: this.symptomAnalysisData?.symptom_probability ?? this.symptomAnalysisData?.probability ?? null,
          symptom_urgency: this.symptomAnalysisData?.urgency ?? this.symptomAnalysisData?.symptom_urgency ?? null,
          symptom_response: this.symptomAnalysisData?.response ?? this.symptomAnalysisData?.symptom_response ?? null,
          symptom_usage: this.symptomAnalysisData?.usage ?? this.symptomAnalysisData?.symptom_usage ?? null,
        };

        // Compute a simple fused probability if both are available
        if (mergedPrediction.probability != null && mergedPrediction.symptom_probability != null) {
          mergedPrediction.image_probability = mergedPrediction.probability;
          mergedPrediction.fused_probability = (
            0.6 * mergedPrediction.probability + 0.4 * mergedPrediction.symptom_probability
          );
        }

        this.router.navigate(['/mg/rapport'], {
          state: {
            prediction: mergedPrediction,
            patientDetails: {
              nom: this.patientName,
              tension: this.tensionValue,
              symptoms: [this.symptomsText || 'General assessment']
            },
            imageUrl: imageUrl
          }
        });
      },
      error: (err) => {
        console.error('Image prediction failed:', err);
        this.isSubmitting = false;
        alert("Wait, there was an issue processing the image prediction.");
      }
    });
  }
}
