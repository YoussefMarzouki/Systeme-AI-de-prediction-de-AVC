import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
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
  selector: 'app-intake',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './intake.component.html',
  styleUrl: './intake.component.css'
})
export class IntakeComponent {
  intakeForm: FormGroup;
  patientFound = false;
  showManualEntry = false;
  searchQuery = '';
  isDragOver = false;
  isSubmitting = false;

  selectedPatient = {
    name: '',
    dob: '',
    cin: ''
  };

  symptoms = [
    { label: 'Balance/Vision Impairment', icon: 'eye', checked: false },
    { label: 'Facial Droop', icon: 'face', checked: false },
    { label: 'Arm Weakness', icon: 'arm', checked: false },
    { label: 'Speech Difficulty', icon: 'speech', checked: false },
    { label: 'Severe Headache', icon: 'head', checked: false },
    { label: 'Leg Weakness', icon: 'leg', checked: false },
    { label: 'Confusion', icon: 'brain', checked: false },
    { label: 'Numbness', icon: 'numb', checked: false }
  ];

  uploadedFiles: UploadedFile[] = [];

  constructor(
    private fb: FormBuilder, 
    private router: Router,
    private patientService: PatientService,
    private dossierService: DossierService,
    public stateService: StateService,
    private imageIrmService: ImageIrmService,
    private donneesCliniquesService: DonneesCliniquesService,
    private predictionService: PredictionService
  ) {
    this.intakeForm = this.fb.group({
      patientSearch: [''],
      fullName: [''],
      dateOfBirth: [''],
      cin: [''],
      symptomOnsetTime: [''],
      tension: [120],
      triageNotes: [''],
    });

    const nav = this.router.getCurrentNavigation();
    const state = nav?.extras.state as { patientDetails?: any };

    // Check if patient exists from previous registration step or dashboard click
    if (this.stateService.patientId) {
      this.patientFound = true;
      if (state?.patientDetails) {
        this.selectedPatient.name = state.patientDetails.name;
        this.selectedPatient.cin = state.patientDetails.cin || 'N/A';
        // Auto-fill search with cin or name so it's clear
        this.intakeForm.patchValue({ patientSearch: state.patientDetails.cin || state.patientDetails.name });
      } else {
        this.selectedPatient.name = 'Patient ID ' + this.stateService.patientId;
      }
    }
  }

  onSearchPatient(): void {
    const query = this.intakeForm.get('patientSearch')?.value;
    if (query && query.trim().length >= 1) {
      this.patientService.searchPatients(query).subscribe({
        next: (res) => {
          if (res.patients && res.patients.length > 0) {
            const p = res.patients[0];
            this.patientFound = true;
            this.showManualEntry = false;
            this.selectedPatient = {
              name: `${p.prenom} ${p.nom}`,
              dob: p.dateNaissance,
              cin: p.cin || 'N/A'
            };
            this.stateService.setPatientId(p.id);
            // Dossier creation is now deferred until submission
            this.stateService.setDossierId('');
          } else {
            this.onPatientNotFound();
          }
        },
        error: (err) => console.error('Search error', err)
      });
    }
  }

  onChangePatient(): void {
    this.patientFound = false;
    this.showManualEntry = false;
    this.intakeForm.get('patientSearch')?.reset();
    this.stateService.setPatientId('');
    this.stateService.setDossierId('');
    this.uploadedFiles = []; // Clear any uploaded files to prevent wrong assignment
  }

  onPatientNotFound(): void {
    this.patientFound = false;
    this.showManualEntry = true;
  }

  toggleSymptom(index: number): void {
    this.symptoms[index].checked = !this.symptoms[index].checked;
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
          // Linking to DB will happen on submit to avoid orphaned records
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

  onDiscardDraft(): void {
    this.intakeForm.reset();
    this.patientFound = false;
    this.showManualEntry = false;
    this.symptoms.forEach(s => s.checked = false);
    this.stateService.setPatientId('');
    this.stateService.setDossierId('');
  }

  onSavePending(): void {
    console.log('Saved as pending:', this.intakeForm.value);
  }

  onSubmitAnalysis(): void {
    if (this.isSubmitting) return;
    this.isSubmitting = true;

    const activeSymptoms = this.symptoms.filter(s => s.checked).map(s => s.label);
    const tensionValue = this.intakeForm.get('tension')?.value;
    const onsetTime = this.intakeForm.get('symptomOnsetTime')?.value;
    
    let fastData = { symptoms: activeSymptoms, tension: tensionValue };
    let notes = this.intakeForm.get('triageNotes')?.value || '';
    
    if (onsetTime) {
      notes += ` | Symptom onset time: ${onsetTime}`;
    }

    const dob = this.patientFound ? this.selectedPatient.dob : this.intakeForm.get('dateOfBirth')?.value;
    let ageText = '';
    if (dob) {
      const birth = new Date(dob);
      const diff = new Date().getTime() - birth.getTime();
      const age = Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
      if (!isNaN(age)) {
        ageText = `Patient age: ${age} years. `;
      }
    }
    
    // Add ageText temporarily to fastData to pass it around if needed locally,
    // though the main target is the AI prompt in predictFused
    (fastData as any).ageText = ageText;

    // IF NO DOSSIER EXISTS (which is now always true because we deferred it)
    if (!this.stateService.dossierId) {
      if (!this.stateService.patientId) {
        const val = this.intakeForm.value;
        const nameParts = (val.fullName || '').split(' ');
        const prenom = nameParts[0] || 'Unknown';
        const nom = nameParts.slice(1).join(' ') || 'Manual';

        const payload = {
          nom: nom,
          prenom: prenom,
          cin: val.cin || null,
          dateNaissance: val.dateOfBirth || '2000-01-01',
          sexe: 'M' // Default
        };

        // 1. Create Patient
        this.patientService.createPatient(payload as any).subscribe({
          next: (res) => {
            this.stateService.setPatientId(res.patient_id);
            this.createDossierAndContinue(fastData, notes);
          },
          error: () => { this.isSubmitting = false; alert("Failed to create manual patient."); }
        });
      } else {
        // Patient exists, just create dossier
        this.createDossierAndContinue(fastData, notes);
      }
    } else {
      this.submitSymptoms(fastData, notes);
    }
  }

  private createDossierAndContinue(fastData: any, notes: string) {
    this.dossierService.createDossier().subscribe({
      next: (dres) => {
        this.stateService.setDossierId(dres.idDossier);
        // Submit Symptoms
        this.submitSymptoms(fastData, notes);
      },
      error: () => {
        this.isSubmitting = false;
        alert("Failed to create dossier.");
      }
    });
  }

  private submitSymptoms(fastData: any, notes: string) {
    this.donneesCliniquesService.addDonneesCliniques(fastData, notes).subscribe({
      next: (res) => {
        if (res.status === 'success') {
          this.isSubmitting = false;
          const ageText = (fastData as any).ageText || '';
          const symptomsText = ageText + "Symptoms: " + fastData.symptoms.join(', ') + ". Notes: " + notes;

          // Route to Step 2 (MRI Upload Component)
          this.router.navigate(['/mg/mri-upload'], {
            state: {
              patientDetails: this.selectedPatient,
              symptomsData: {
                symptomsText: symptomsText,
                tensionValue: fastData.tension,
                ageText: ageText
              }
            }
          });
        } else {
          this.isSubmitting = false;
          alert("Failed to save clinical data.");
        }
      },
      error: (err) => {
        console.error('Save symptoms error:', err);
        this.isSubmitting = false;
        alert("Wait, there was an issue saving clinical data.");
      }
    });
  }
}
