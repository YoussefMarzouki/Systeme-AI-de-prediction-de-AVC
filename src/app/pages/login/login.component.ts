import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { LanguageService } from '../../services/language.service';
import { ThemeService } from '../../services/theme.service';
import { AuthService, type AppRole } from '../../services/auth.service';

type LoginRole = Exclude<AppRole, 'unknown'>;

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  email = '';
  password = '';
  errorMessage = '';
  isLoading = false;
  showPassword = false;
  selectedRole: LoginRole = 'agent';
  showSettings = false;

  roles: { key: LoginRole; label: string }[] = [
    { key: 'agent', label: 'ROLES.AGENT' },
    { key: 'mg', label: 'ROLES.DOCTOR' },
    { key: 'ms', label: 'ROLES.SPECIALIST' },
    { key: 'admin', label: 'ROLES.ADMIN' }
  ];

  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private translate: TranslateService,
    public languageService: LanguageService,
    public themeService: ThemeService
  ) {
    if (this.authService.isLoggedIn) {
      this.router.navigateByUrl(this.authService.getLandingRoute());
    }
  }

  toggleSettings(): void {
    this.showSettings = !this.showSettings;
  }

  changeLanguage(lang: string): void {
    this.languageService.setLanguage(lang);
    this.showSettings = false;
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }

  selectRole(role: LoginRole): void {
    this.selectedRole = role;
    this.errorMessage = '';
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  get isEmailInvalid(): boolean {
    if (!this.email) return false;
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return !pattern.test(this.email.trim());
  }

  onSubmit(): void {
    this.errorMessage = '';
    const email = this.email.trim();

    if (!email || !this.password) {
      this.errorMessage = this.translate.instant('LOGIN.ERR_REQUIRED');
      return;
    }

    if (this.isEmailInvalid) {
      this.errorMessage = "Format de l'email invalide (ex: nom@domaine.com)";
      return;
    }

    this.isLoading = true;
    this.authService.login(email, this.password).subscribe({
      next: () => {
        const actualRole = this.authService.currentRoleKey;
        if (actualRole !== this.selectedRole) {
          this.authService.clearSession();
          this.isLoading = false;
          this.errorMessage = this.translate.instant('LOGIN.ERR_ROLE_MISMATCH');
          return;
        }

        const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
        this.isLoading = false;
        this.router.navigateByUrl(returnUrl || this.authService.getLandingRoute());
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.error || this.translate.instant('LOGIN.ERR_AUTH_FAILED');
      }
    });
  }
}
