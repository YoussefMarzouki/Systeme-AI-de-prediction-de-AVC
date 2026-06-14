import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors } from '@angular/forms';

function fullNameValidator(control: AbstractControl): ValidationErrors | null {
  const value = control.value || '';
  if (value.trim().length > 0 && !value.trim().includes(' ')) {
    return { noSpace: true };
  }
  return null;
}

function pastDateValidator(control: AbstractControl): ValidationErrors | null {
  if (!control.value) return null;
  const selectedDate = new Date(control.value);
  const now = new Date();
  if (selectedDate > now) {
    return { futureDate: true };
  }
  return null;
}
import { Router } from '@angular/router';
import { PatientService } from '../../services/patient.service';
import { DossierService } from '../../services/dossier.service';
import { StateService } from '../../services/state.service';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-registration',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslateModule],
  templateUrl: './registration.component.html',
  styleUrl: './registration.component.css'
})
export class RegistrationComponent {
  registrationForm: FormGroup;
  registrationProgress = 25;
  isSubmitting = false;
  cinExistsError = false;

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private patientService: PatientService,
    private dossierService: DossierService,
    private stateService: StateService
  ) {
    this.registrationForm = this.fb.group({
      fullLegalName: ['', [Validators.required, fullNameValidator]],
      cin: ['', [Validators.required, Validators.pattern('^\\d{8}$')]],
      dateOfBirth: ['', [Validators.required, pastDateValidator]],
      genderIdentity: ['', Validators.required],
      phoneNumber: ['', [Validators.required, Validators.pattern('^(20|21|22|50|51|52|53|90|91|92)\\d{6}$')]],
      emailAddress: ['', [Validators.required, Validators.pattern('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$')]],
      homeAddress: ['', Validators.required],
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

  onCheckCin(): void {
    const cin = this.registrationForm.value.cin;
    if (!cin) {
      this.cinExistsError = false;
      return;
    }
    this.patientService.checkCinExists(cin).subscribe({
      next: (res) => {
        this.cinExistsError = res.exists;
      },
      error: (err) => {
        console.error('Error checking CIN', err);
      }
    });
  }

  onCompleteRegistration(): void {
    if (this.isSubmitting) return;

    if (this.registrationForm.invalid) {
      alert('Please fill out all required fields correctly.');
      this.registrationForm.markAllAsTouched();
      return;
    }

    if (this.cinExistsError) {
      alert('This CIN is already saved. You cannot register a new patient with an existing CIN.');
      return;
    }

    const val = this.registrationForm.value;
    
    if (!val.cin) {
      alert('Please enter a CIN before continuing');
      return;
    }

    this.isSubmitting = true;

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
      sexe: sexe,
      telephone: val.phoneNumber,
      email: val.emailAddress,
      adresse: val.homeAddress
    };

    // 1. Create Patient
    this.patientService.createPatient(payload).subscribe({
      next: (res) => {
        if (res.patient_id) {
          this.stateService.setPatientId(res.patient_id);
          // 2. Create dossier mapped to patient (only if medecin, or actually maybe agent should just create the patient without an empty dossier if they aren't doing intake? Let's keep it creating a dossier since they registered them, but redirect accordingly)
          this.dossierService.createDossier().subscribe({
            next: (dossierRes) => {
              if (dossierRes.idDossier) {
                this.stateService.setDossierId(dossierRes.idDossier);
                this.isSubmitting = false;
                
                if (this.stateService.currentRole !== 'agent') {
                  alert('Save complete!');
                  this.router.navigate([`${this.stateService.routePrefix}/intake`]);
                } else {
                  alert('Save complete!');
                  this.router.navigate(['/agent/dashboard']);
                }
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
