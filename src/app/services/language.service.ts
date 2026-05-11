import { Injectable, Renderer2, RendererFactory2 } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

@Injectable({
  providedIn: 'root'
})
export class LanguageService {
  private renderer: Renderer2;

  constructor(
    private translate: TranslateService,
    rendererFactory: RendererFactory2
  ) {
    this.renderer = rendererFactory.createRenderer(null, null);
    
    const savedLang = localStorage.getItem('language') || 'en';
    this.setLanguage(savedLang);
  }

  setLanguage(lang: string) {
    this.translate.use(lang);
    localStorage.setItem('language', lang);
    
    // Handle RTL
    if (lang === 'ar') {
      this.renderer.setAttribute(document.documentElement, 'dir', 'rtl');
      this.renderer.setAttribute(document.documentElement, 'lang', 'ar');
      document.body.classList.add('rtl');
    } else {
      this.renderer.setAttribute(document.documentElement, 'dir', 'ltr');
      this.renderer.setAttribute(document.documentElement, 'lang', lang);
      document.body.classList.remove('rtl');
    }
  }

  getCurrentLanguage(): string {
    return this.translate.currentLang || 'en';
  }
}
