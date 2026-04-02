import { Routes } from '@angular/router';
import { MainLayoutComponent } from './components/main-layout/main-layout.component';
import { RegistrationComponent } from './pages/registration/registration.component';
import { IntakeComponent } from './pages/intake/intake.component';

export const routes: Routes = [
  {
    path: '',
    component: MainLayoutComponent,
    children: [
      { path: '', redirectTo: 'registration', pathMatch: 'full' },
      { path: 'dashboard', redirectTo: 'registration', pathMatch: 'full' },
      { path: 'registration', component: RegistrationComponent },
      { path: 'intake', component: IntakeComponent },
      { path: 'appointments', component: RegistrationComponent }, // placeholder
      { path: 'records', component: IntakeComponent }, // placeholder
    ]
  },
  { path: '**', redirectTo: '' }
];
