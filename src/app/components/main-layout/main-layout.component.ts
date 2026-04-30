import { Component, OnInit } from '@angular/core';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { HeaderComponent } from '../header/header.component';
import { filter } from 'rxjs/operators';
import { StateService } from '../../services/state.service';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [RouterOutlet, SidebarComponent, HeaderComponent],
  templateUrl: './main-layout.component.html',
  styleUrl: './main-layout.component.css'
})
export class MainLayoutComponent implements OnInit {
  constructor(private router: Router, private state: StateService) {
    this.updateRoleFromUrl(this.router.url);
  }

  ngOnInit() {
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      this.updateRoleFromUrl(event.urlAfterRedirects || event.url);
    });
  }

  private updateRoleFromUrl(url: string) {
    Promise.resolve().then(() => {
      if (url.startsWith('/mg')) {
        this.state.setRole('mg');
      } else if (url.startsWith('/ms')) {
        this.state.setRole('ms');
      } else if (url.startsWith('/agent')) {
        this.state.setRole('agent');
      }
    });
  }
}
