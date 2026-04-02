import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
import { ClinicalApiService } from '../../services/clinical-api.service';

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
    mrn: ''
  };

  symptoms = [
    { label: 'Balance/Vision Impairment', icon: 'eye', checked: false },
    { label: 'Facial Droop', icon: 'face', checked: false },
    { label: 'Arm Weakness', icon: 'arm', checked: false },
    { label: 'Speech Difficulty', icon: 'speech', checked: false },
  ];

  uploadedFiles: UploadedFile[] = [];

  constructor(private fb: FormBuilder, private api: ClinicalApiService) {
    this.intakeForm = this.fb.group({
      patientSearch: [''],
      fullName: [''],
      dateOfBirth: [''],
      mrn: [''],
      symptomOnsetTime: [''],
      triageNotes: [''],
    });

    // Check if patient exists from previous registration step
    if (this.api.patientId) {
      // In a real scenario we might fetch the generated patient.
      this.patientFound = true;
      this.selectedPatient.name = 'Patient ID ' + this.api.patientId;
    }
  }

  onSearchPatient(): void {
    const query = this.intakeForm.get('patientSearch')?.value;
    if (query && query.trim().length >= 1) {
      this.api.searchPatients(query).subscribe({
        next: (res) => {
          if (res.patients && res.patients.length > 0) {
            const p = res.patients[0];
            this.patientFound = true;
            this.showManualEntry = false;
            this.selectedPatient = {
              name: `${p.prenom} ${p.nom}`,
              dob: p.dateNaissance,
              mrn: p.id.substring(0, 8).toUpperCase()
            };
            this.api.setPatientId(p.id);
            // Need a dossier for this patient
            this.api.createDossier().subscribe(d => this.api.setDossierId(d.idDossier));
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
    this.api.setPatientId('');
    this.api.setDossierId('');
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

    this.api.uploadMriToCloudinary(file).subscribe({
      next: (res) => {
        if (res?.secure_url) {
          this.uploadedFiles[idx].status = 'Success';
          this.uploadedFiles[idx].url = res.secure_url;
          
          // Link to PostgreSQL DB
          this.api.linkMriToDossier(res.secure_url).subscribe({
             next: (dbRes) => console.log('Linked MRI to DB:', dbRes),
             error: (err) => console.error('Failed to link MRI to DB:', err)
          });
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
    this.uploadedFiles = [];
  }

  onSavePending(): void {
    console.log('Saved as pending:', this.intakeForm.value);
  }

  onSubmitAnalysis(): void {
    if (this.isSubmitting) return;
    this.isSubmitting = true;

    const activeSymptoms = this.symptoms.filter(s => s.checked).map(s => s.label);
    const fastData = { symptoms: activeSymptoms };
    const notes = this.intakeForm.get('triageNotes')?.value || '';

    // IF NO DOSSIER EXISTS (e.g. Manual Entry or Direct Link)
    if (!this.api.dossierId) {
      const val = this.intakeForm.value;
      
      // Parse full name
      const nameParts = (val.fullName || '').split(' ');
      const prenom = nameParts[0] || 'Unknown';
      const nom = nameParts.slice(1).join(' ') || 'Manual';

      const payload = {
        nom: nom,
        prenom: prenom,
        dateNaissance: val.dateOfBirth || '2000-01-01',
        sexe: 'M' // Default
      };

      // 1. Create Patient
      this.api.createPatient(payload).subscribe({
        next: (res) => {
          this.api.setPatientId(res.patient_id);
          // 2. Create Dossier
          this.api.createDossier().subscribe({
            next: (dres) => {
              this.api.setDossierId(dres.idDossier);
              // 3. Submit Symptoms
              this.submitSymptoms(fastData, notes);
            }
          });
        },
        error: () => { this.isSubmitting = false; alert("Failed to create manual patient."); }
      });
    } else {
      this.submitSymptoms(fastData, notes);
    }
  }

  private submitSymptoms(fastData: any, notes: string) {
    this.api.addDonneesCliniques(fastData, notes).subscribe({
      next: (res) => {
        if (res.status === 'success') {
          alert('Assessment successfully submitted to database!');
        }
        this.isSubmitting = false;
      },
      error: (err) => {
        console.error('Error adding symptoms', err);
        alert('Failed to submit symptoms.');
        this.isSubmitting = false;
      }
    });
  }
}
