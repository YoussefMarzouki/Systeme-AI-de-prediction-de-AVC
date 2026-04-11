import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { PatientService } from '../../services/patient.service';
import { DossierService } from '../../services/dossier.service';
import { StateService } from '../../services/state.service';

@Component({
  selector: 'app-registration',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './registration.component.html',
  styleUrl: './registration.component.css'
})
export class RegistrationComponent {
  registrationForm: FormGroup;
  registrationProgress = 25;
  isSubmitting = false;

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private patientService: PatientService,
    private dossierService: DossierService,
    private stateService: StateService
  ) {
    this.registrationForm = this.fb.group({
      fullLegalName: [''],
      cin: [''],
      dateOfBirth: [''],
      genderIdentity: [''],
      phoneNumber: [''],
      emailAddress: [''],
      homeAddress: [''],
      insuranceProvider: [''],
      policyNumber: [''],
      groupNumber: [''],
      emergencyContactName: [''],
      emergencyRelationship: [''],
      emergencyPhone: [''],
    });
  }

  onDiscard(): void {
    this.registrationForm.reset();
  }

  onSaveDraft(): void {
    console.log('Draft saved:', this.registrationForm.value);
  }

  onCompleteRegistration(): void {
    if (this.isSubmitting) return;
    this.isSubmitting = true;

    const val = this.registrationForm.value;

    // Parse full name
    const nameParts = (val.fullLegalName || '').split(' ');
    const prenom = nameParts[0] || 'Unknown';
    const nom = nameParts.slice(1).join(' ') || 'Unknown';

    // Parse gender to 1 letter required by some backends (M/F)
    let sexe = 'M';
    if(val.genderIdentity) {
        if(val.genderIdentity.toLowerCase().startsWith('f')) sexe = 'F';
    }

    const payload = {
      nom: nom,
      prenom: prenom,
      cin: val.cin || null,
      dateNaissance: val.dateOfBirth || '2000-01-01',
      sexe: sexe
    };

    // 1. Create Patient
    this.patientService.createPatient(payload).subscribe({
      next: (res) => {
        if (res.patient_id) {
          this.stateService.setPatientId(res.patient_id);
          // 2. Create dossier mapped to patient
          this.dossierService.createDossier().subscribe({
            next: (dossierRes) => {
              if (dossierRes.idDossier) {
                this.stateService.setDossierId(dossierRes.idDossier);
                this.isSubmitting = false;
                this.router.navigate(['/intake']);
              }
            },
            error: (err) => {
              console.error('Error creating dossier', err);
              this.isSubmitting = false;
              alert('Created patient but failed to create dossier.');
            }
          });
        }
      },
      error: (err) => {
        console.error('Error creating patient', err);
        this.isSubmitting = false;
        alert('Failed to create patient in database.');
      }
    });
  }
}
