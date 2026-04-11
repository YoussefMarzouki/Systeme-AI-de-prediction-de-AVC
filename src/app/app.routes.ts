import { Routes } from '@angular/router';
import { MainLayoutComponent } from './components/main-layout/main-layout.component';
import { RegistrationComponent } from './pages/registration/registration.component';
import { IntakeComponent } from './pages/intake/intake.component';
import { RapportComponent } from './pages/rapport/rapport.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';

export const routes: Routes = [
  {
    path: '',
    component: MainLayoutComponent,
    children: [
      { path: '', redirectTo: 'registration', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent },
      { path: 'registration', component: RegistrationComponent },
      { path: 'intake', component: IntakeComponent },
      { path: 'rapport', component: RapportComponent },
      { path: 'appointments', component: RegistrationComponent }, // placeholder
      { path: 'records', component: IntakeComponent }, // placeholder
    ]
  },
  { path: '**', redirectTo: '' }
];
