import { Component, OnInit } from '@angular/core';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatBadgeModule } from '@angular/material/badge';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { NavbarComponent } from './components/navbar/navbar.component';
import { ToastComponent } from './components/toast/toast.component';
import { AuthService } from './services/auth.service';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatBadgeModule,
    MatTooltipModule,
    RouterLink,
    RouterLinkActive,
    NavbarComponent,
    ToastComponent
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  title = 'Elô - Sistema Inteligente';
  showLayout = false;

  constructor(
    public authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Monitora mudanças de rota para controlar layout
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: NavigationEnd) => {
      this.updateLayout(event.url);
    });

    // Monitora estado de autenticação
    this.authService.currentUser$.subscribe(user => {
      this.updateLayout(this.router.url);
    });
  }

  private updateLayout(url: string): void {
    const publicRoutes = ['/login', '/agendamento'];
    const isPublicRoute = publicRoutes.includes(url);
    const isAuthenticated = this.authService.isAuthenticated;
    
    // Só mostra layout se não for rota pública E estiver autenticado
    this.showLayout = !isPublicRoute && isAuthenticated;
    
    // Se não está autenticado e não está em rota pública, redireciona para login
    if (!isAuthenticated && !isPublicRoute) {
      this.router.navigate(['/login']);
    }
  }

  logout(): void {
    this.authService.logout();
  }
} 