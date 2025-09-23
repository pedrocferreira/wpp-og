import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { authGuard } from './shared/auth.guard';

export const routes: Routes = [
  // Rota raiz redireciona baseado na autenticação
  { 
    path: '', 
    redirectTo: '/login', 
    pathMatch: 'full' 
  },
  
  // Páginas públicas
  { 
    path: 'login', 
    component: LoginComponent 
  },
  { 
    path: 'agendamento', 
    loadComponent: () => import('./components/public-booking/public-booking.component')
      .then(m => m.PublicBookingComponent) 
  },
  
  // Páginas protegidas (requer autenticação)
  { 
    path: 'dashboard', 
    loadComponent: () => import('./components/dashboard/dashboard.component')
      .then(m => m.DashboardComponent), 
    canActivate: [authGuard] 
  },
  { 
    path: 'google-calendar', 
    loadComponent: () => import('./components/google-calendar/google-calendar.component')
      .then(m => m.GoogleCalendarComponent), 
    canActivate: [authGuard] 
  },
  { 
    path: 'chat', 
    loadComponent: () => import('./components/chat/chat.component')
      .then(m => m.ChatComponent), 
    canActivate: [authGuard] 
  },
  
  // Rota para páginas não encontradas
  { 
    path: '**', 
    redirectTo: '/login' 
  }
];
