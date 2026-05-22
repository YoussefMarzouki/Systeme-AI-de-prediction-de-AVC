import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { forkJoin } from 'rxjs';

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
      this.handleFiles(event.dataTransfer.files);
    }
  }

  onFileSelect(event: any): void {
    if (event.target.files && event.target.files.length > 0) {
      this.handleFiles(event.target.files);
    }
  }

  private handleFiles(files: FileList | File[]): void {
    const remainingSlots = 5 - this.uploadedFiles.length;
    if (remainingSlots <= 0) {
      alert("You have already uploaded the maximum limit of 5 images.");
      return;
    }

    const filesToUpload = Array.from(files).slice(0, remainingSlots);
    if (files.length > remainingSlots) {
      alert(`Only the first ${remainingSlots} image(s) were accepted. You can upload a maximum of 5 images.`);
    }

    filesToUpload.forEach(file => this.uploadFile(file));
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

  hasUploadingFiles(): boolean {
    return this.uploadedFiles.some(file => file.status === 'Uploading...');
  }

  onDoItLater(): void {
    // Return to dashboard
    this.router.navigate([`${this.stateService.routePrefix}/dashboard`]);
  }

  onSubmitAnalysis(): void {
    if (this.isSubmitting) return;
    this.isSubmitting = true;

    // Filter successfully uploaded images
    const validFileUrls = this.uploadedFiles
      .filter(file => file.status === 'Success' && file.url)
      .map(file => file.url as string);

    if (validFileUrls.length === 0) {
      alert("Please upload at least one MRI image to proceed with the analysis.");
      this.isSubmitting = false;
      return;
    }

    // Call all image predictions in parallel
    const predictionRequests = validFileUrls.map(url => 
      this.predictionService.predictImage(url)
    );

    forkJoin(predictionRequests).subscribe({
      next: (responses: any[]) => {
        this.isSubmitting = false;
        
        // Map raw responses to clean result structures
        const sliceResults = responses.map((res, index) => {
          const prediction = res.prediction || res;
          return {
            ...prediction,
            imageUrl: validFileUrls[index]
          };
        });

        // Log each slice analysis output for easy debugging
        console.log("=== MRI Slice Analysis Outputs ===");
        sliceResults.forEach((slice, index) => {
          const originalFile = this.uploadedFiles.find(f => f.url === slice.imageUrl);
          console.log(`Slice ${index + 1} [${originalFile?.name || 'File'}]:`, {
            probability: slice.probability,
            confidence: slice.confidence,
            class: slice.predicted_class || 'N/A'
          });
        });

        // Compute average probability and confidence across all slices (Option B)
        const avgProbability = sliceResults.reduce((sum, item) => sum + item.probability, 0) / sliceResults.length;
        const avgConfidence = sliceResults.reduce((sum, item) => sum + item.confidence, 0) / sliceResults.length;

        // Log the averaged results
        console.log("=== Aggregated (Average) Scores ===");
        console.log(`Average MRI Stroke Probability: ${avgProbability}`);
        console.log(`Average Prediction Confidence: ${avgConfidence}`);

        // Find the worst-case slice (highest stroke risk probability) to use as visual and metadata representative
        const highestRiskSlice = sliceResults.reduce((max, current) => 
          (current.probability > max.probability) ? current : max
        , sliceResults[0]);

        // Merge cached symptom analysis with the averaged predictions
        const mergedPrediction = {
          ...highestRiskSlice, // Keep visual and structural info from representative slice
          probability: avgProbability, // Override with average probability across all slices
          confidence: avgConfidence, // Override with average confidence across all slices
          symptom_probability: this.symptomAnalysisData?.symptom_probability ?? this.symptomAnalysisData?.probability ?? null,
          symptom_urgency: this.symptomAnalysisData?.urgency ?? this.symptomAnalysisData?.symptom_urgency ?? null,
          symptom_response: this.symptomAnalysisData?.response ?? this.symptomAnalysisData?.symptom_response ?? null,
          symptom_usage: this.symptomAnalysisData?.usage ?? this.symptomAnalysisData?.symptom_usage ?? null,
          all_slices: sliceResults // Store details of all slices for potential use in reports
        };

        // Compute the fused probability
        if (mergedPrediction.probability != null && mergedPrediction.symptom_probability != null) {
          mergedPrediction.image_probability = mergedPrediction.probability;
          mergedPrediction.fused_probability = (
            0.6 * mergedPrediction.probability + 0.4 * mergedPrediction.symptom_probability
          );
        }

        // Save the merged prediction to the backend first!
        this.predictionService.finalizePrediction(mergedPrediction).subscribe({
          next: () => {
            this.router.navigate([`${this.stateService.routePrefix}/rapport`], {
              state: {
                prediction: mergedPrediction,
                patientDetails: {
                  nom: this.patientName,
                  tension: this.tensionValue,
                  symptoms: [this.symptomsText || 'General assessment']
                },
                imageUrl: highestRiskSlice.imageUrl // Display the highest risk slice image primarily
              }
            });
          },
          error: (finalizeErr) => {
            console.error('Failed to save aggregated prediction on backend:', finalizeErr);
            // Navigate anyway as a fallback
            this.router.navigate([`${this.stateService.routePrefix}/rapport`], {
              state: {
                prediction: mergedPrediction,
                patientDetails: {
                  nom: this.patientName,
                  tension: this.tensionValue,
                  symptoms: [this.symptomsText || 'General assessment']
                },
                imageUrl: highestRiskSlice.imageUrl
              }
            });
          }
        });
      },
      error: (err) => {
        console.error('Image batch prediction failed:', err);
        this.isSubmitting = false;
        alert("Wait, there was an issue processing the image prediction batch.");
      }
    });
  }
}
