import { Routes } from '@angular/router';
import { MainLayoutComponent } from './components/main-layout/main-layout.component';
import { RegistrationComponent } from './pages/registration/registration.component';
import { IntakeComponent } from './pages/intake/intake.component';
import { RapportComponent } from './pages/rapport/rapport.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { MriUploadComponent } from './pages/mri-upload/mri-upload.component';
import { ValidationQueueComponent } from './pages/validation-queue/validation-queue.component';
import { CaseEvaluationComponent } from './pages/case-evaluation/case-evaluation.component';
import { LoginComponent } from './pages/login/login.component';
import { AdminComponent } from './pages/admin/admin.component';
import { AdminDashboardComponent } from './pages/admin-dashboard/admin-dashboard.component';
import { authChildGuard, authGuard } from './guards/auth.guard';
import { roleChildGuard, roleGuard } from './guards/role.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  {
    path: 'agent',
    component: MainLayoutComponent,
    canActivate: [authGuard, roleGuard],
    canActivateChild: [authChildGuard, roleChildGuard],
    data: { roles: ['agent'] },
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent },
      { path: 'registration', component: RegistrationComponent }
    ]
  },
  {
    path: 'mg',
    component: MainLayoutComponent,
    canActivate: [authGuard, roleGuard],
    canActivateChild: [authChildGuard, roleChildGuard],
    data: { roles: ['mg'] },
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent },
      { path: 'registration', component: RegistrationComponent },
      { path: 'intake', component: IntakeComponent },
      { path: 'mri-upload', component: MriUploadComponent },
      { path: 'rapport', component: RapportComponent }
    ]
  },
  {
    path: 'ms',
    component: MainLayoutComponent,
    canActivate: [authGuard, roleGuard],
    canActivateChild: [authChildGuard, roleChildGuard],
    data: { roles: ['ms'] },
    children: [
      { path: '', redirectTo: 'validation-queue', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent },
      { path: 'registration', component: RegistrationComponent },
      { path: 'intake', component: IntakeComponent },
      { path: 'mri-upload', component: MriUploadComponent },
      { path: 'rapport', component: RapportComponent },
      { path: 'validation-queue', component: ValidationQueueComponent },
      { path: 'case-evaluation', component: CaseEvaluationComponent },
      { path: 'case-evaluation/:id', component: CaseEvaluationComponent }
    ]
  },
  {
    path: 'admin',
    component: MainLayoutComponent,
    canActivate: [authGuard, roleGuard],
    canActivateChild: [authChildGuard, roleChildGuard],
    data: { roles: ['admin'] },
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: AdminDashboardComponent },
      { path: 'patients', component: DashboardComponent },
      { path: 'users', component: AdminComponent }
    ]
  },
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: '**', redirectTo: '/login' }
];
