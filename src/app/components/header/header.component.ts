import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { StateService } from '../../services/state.service';
import { AuthService } from '../../services/auth.service';
import { TranslateModule } from '@ngx-translate/core';
import { LanguageService } from '../../services/language.service';
import { ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslateModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.css'
})
export class HeaderComponent {
  showSettings = false;

  constructor(
    public state: StateService, 
    private authService: AuthService,
    public languageService: LanguageService,
    public themeService: ThemeService
  ) {}

  get userName(): string {
    return this.authService.currentUser?.nom || 'User';
  }

  get userRole(): string {
    if (this.state.isCurrentUserAdmin) return 'ROLES.ADMIN';
    if (this.state.isCurrentUserSpecialiste) return 'ROLES.SPECIALIST';
    if (this.state.currentRole === 'mg') return 'ROLES.GENERALIST';
    return 'ROLES.RECEPTION';
  }

  get userInitials(): string {
    return this.userName
      .split(/[,\s]+/)
      .filter(n => n.length > 0)
      .map(n => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  }

  get prefix(): string {
    return this.state.routePrefix;
  }

  toggleSettings() {
    this.showSettings = !this.showSettings;
  }

  changeLanguage(lang: string) {
    this.languageService.setLanguage(lang);
    this.showSettings = false;
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }
}
