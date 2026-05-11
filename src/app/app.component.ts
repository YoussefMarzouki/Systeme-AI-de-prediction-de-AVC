import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { LanguageService } from './services/language.service';
import { ThemeService } from './services/theme.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: '<router-outlet></router-outlet>',
  styles: [':host { display: block; }']
})
export class AppComponent {
  title = 'ClinicalLens';
  constructor(
    private languageService: LanguageService,
    private themeService: ThemeService
  ) {}
}
