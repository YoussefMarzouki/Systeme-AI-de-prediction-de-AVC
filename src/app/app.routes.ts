import { Routes } from '@angular/router';
import { MainLayoutComponent } from './components/main-layout/main-layout.component';
import { RegistrationComponent } from './pages/registration/registration.component';
import { IntakeComponent } from './pages/intake/intake.component';
import { RapportComponent } from './pages/rapport/rapport.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { MriUploadComponent } from './pages/mri-upload/mri-upload.component';

export const routes: Routes = [
  {
    path: 'agent',
    component: MainLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent },
      { path: 'registration', component: RegistrationComponent }
    ]
  },
  {
    path: 'mg',
    component: MainLayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent },
      { path: 'registration', component: RegistrationComponent },
      { path: 'intake', component: IntakeComponent },
      { path: 'mri-upload', component: MriUploadComponent },
      { path: 'rapport', component: RapportComponent }
    ]
  },
  { path: '', redirectTo: '/agent/dashboard', pathMatch: 'full' },
  { path: '**', redirectTo: '/agent/dashboard' }
];
