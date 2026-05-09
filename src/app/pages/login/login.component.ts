import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService, type AppRole } from '../../services/auth.service';

type LoginRole = Exclude<AppRole, 'unknown'>;

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  email = '';
  password = '';
  errorMessage = '';
  isLoading = false;
  showPassword = false;
  selectedRole: LoginRole = 'ms';

  roles: { key: LoginRole; label: string }[] = [
    { key: 'mg', label: 'Generalist' },
    { key: 'ms', label: 'Specialist' },
    { key: 'admin', label: 'Admin' },
    { key: 'agent', label: 'Agent' }
  ];

  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute
  ) {
    if (this.authService.isLoggedIn) {
      this.router.navigateByUrl(this.authService.getLandingRoute());
    }
  }

  selectRole(role: LoginRole): void {
    this.selectedRole = role;
    this.errorMessage = '';
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  onSubmit(): void {
    this.errorMessage = '';
    const email = this.email.trim();

    if (!email || !this.password) {
      this.errorMessage = 'Veuillez saisir votre identifiant clinique et votre mot de passe.';
      return;
    }

    this.isLoading = true;
    this.authService.login(email, this.password).subscribe({
      next: () => {
        const actualRole = this.authService.currentRoleKey;
        if (actualRole !== this.selectedRole) {
          this.authService.clearSession();
          this.isLoading = false;
          this.errorMessage = 'Le role selectionne ne correspond pas au compte saisi.';
          return;
        }

        const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
        this.isLoading = false;
        this.router.navigateByUrl(returnUrl || this.authService.getLandingRoute());
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.error || 'Authentification echouee. Verifiez vos coordonnees.';
      }
    });
  }
}
