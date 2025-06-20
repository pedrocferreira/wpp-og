import { Routes } from '@angular/router';
import { PublicBookingComponent } from './components/public-booking/public-booking.component';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', loadComponent: () => import('./components/dashboard/dashboard.component').then(m => m.DashboardComponent) },
  { path: 'chat', loadComponent: () => import('./components/chat/chat.component').then(m => m.ChatComponent) },
  { path: 'agendamento', loadComponent: () => import('./components/public-booking/public-booking.component').then(m => m.PublicBookingComponent) }
];
