import { Injectable, Renderer2, RendererFactory2 } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private renderer: Renderer2;
  private isDarkMode = false;

  constructor(rendererFactory: RendererFactory2) {
    this.renderer = rendererFactory.createRenderer(null, null);
    
    // Load saved preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      this.setDarkMode(true);
    }
  }

  toggleTheme() {
    this.setDarkMode(!this.isDarkMode);
  }

  setDarkMode(isDark: boolean) {
    this.isDarkMode = isDark;
    if (isDark) {
      this.renderer.addClass(document.body, 'dark-mode');
      localStorage.setItem('theme', 'dark');
    } else {
      this.renderer.removeClass(document.body, 'dark-mode');
      localStorage.setItem('theme', 'light');
    }
  }

  get isDark(): boolean {
    return this.isDarkMode;
  }
}
