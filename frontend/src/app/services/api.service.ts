import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Autenticação
  login(credentials: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/login/`, credentials);
  }

  // Clientes
  getClients(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/clients/`);
  }

  // Atendimentos
  getAtendimentos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/atendimentos/`);
  }

  // Mensagens
  getMensagens(atendimentoId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/mensagens/${atendimentoId}/`);
  }

  enviarMensagem(mensagem: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/mensagens/`, mensagem);
  }

  // Consultas
  getConsultas(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/consultas/`);
  }

  agendarConsulta(consulta: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/consultas/`, consulta);
  }

  // Agendamento Online
  getAvailableTimeSlots(date: Date, consultationType: string): Observable<string[]> {
    const formattedDate = date.toISOString().split('T')[0];
    return this.http.get<string[]>(`${this.apiUrl}/appointments/available-slots/?date=${formattedDate}&type=${consultationType}`);
  }

  createAppointment(appointmentData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/appointments/book/`, appointmentData);
  }
} 