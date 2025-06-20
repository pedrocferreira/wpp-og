import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatStepperModule } from '@angular/material/stepper';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-appointment-booking',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatStepperModule,
    MatSnackBarModule,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="booking-container">
      <mat-card class="booking-card">
        <mat-card-header>
          <mat-card-title>🗓️ Agendamento de Consulta</mat-card-title>
          <mat-card-subtitle>Escolha a data, horário e tipo de consulta</mat-card-subtitle>
        </mat-card-header>

        <mat-card-content>
          <mat-stepper [linear]="true" #stepper>
            <!-- Etapa 1: Tipo de Consulta -->
            <mat-step [stepControl]="consultationTypeForm">
              <ng-template matStepLabel>Tipo de Consulta</ng-template>
              <form [formGroup]="consultationTypeForm" class="step-form">
                <h3>Selecione o tipo de consulta:</h3>
                <mat-form-field appearance="fill">
                  <mat-label>Tipo de consulta</mat-label>
                  <mat-select formControlName="type">
                    <mat-option value="presencial">🏥 Consulta Presencial</mat-option>
                    <mat-option value="online">💻 Consulta Online (Telemedicina)</mat-option>
                  </mat-select>
                </mat-form-field>
                <div class="step-actions">
                  <button mat-raised-button color="primary" matStepperNext 
                          [disabled]="!consultationTypeForm.valid">
                    Próximo
                  </button>
                </div>
              </form>
            </mat-step>

            <!-- Etapa 2: Data e Horário -->
            <mat-step [stepControl]="dateTimeForm">
              <ng-template matStepLabel>Data e Horário</ng-template>
              <form [formGroup]="dateTimeForm" class="step-form">
                <h3>Escolha a data:</h3>
                <mat-form-field appearance="fill">
                  <mat-label>Data da consulta</mat-label>
                  <input matInput [matDatepicker]="picker" formControlName="date"
                         [min]="minDate" [matDatepickerFilter]="dateFilter">
                  <mat-datepicker-toggle matSuffix [for]="picker"></mat-datepicker-toggle>
                  <mat-datepicker #picker></mat-datepicker>
                </mat-form-field>

                <h3>Horários disponíveis:</h3>
                <div class="time-slots" *ngIf="availableTimeSlots.length > 0">
                  <button 
                    *ngFor="let slot of availableTimeSlots"
                    mat-stroked-button
                    [color]="dateTimeForm.get('time')?.value === slot ? 'primary' : ''"
                    (click)="selectTimeSlot(slot)"
                    class="time-slot-btn">
                    {{slot}}
                  </button>
                </div>
                <div *ngIf="dateTimeForm.get('date')?.value && availableTimeSlots.length === 0"
                     class="no-slots">
                  📅 Não há horários disponíveis para esta data. Escolha outra data.
                </div>

                <div class="step-actions">
                  <button mat-button matStepperPrevious>Voltar</button>
                  <button mat-raised-button color="primary" matStepperNext 
                          [disabled]="!dateTimeForm.valid">
                    Próximo
                  </button>
                </div>
              </form>
            </mat-step>

            <!-- Etapa 3: Dados de Contato -->
            <mat-step [stepControl]="contactForm">
              <ng-template matStepLabel>Confirmação</ng-template>
              <form [formGroup]="contactForm" class="step-form">
                <h3>Confirme seus dados:</h3>
                
                <mat-form-field appearance="fill">
                  <mat-label>Nome completo</mat-label>
                  <input matInput formControlName="name" placeholder="Seu nome completo">
                </mat-form-field>

                <mat-form-field appearance="fill">
                  <mat-label>WhatsApp</mat-label>
                  <input matInput formControlName="whatsapp" placeholder="(11) 99999-9999">
                </mat-form-field>

                <mat-form-field appearance="fill">
                  <mat-label>E-mail (opcional)</mat-label>
                  <input matInput type="email" formControlName="email" placeholder="seu@email.com">
                </mat-form-field>

                <div class="appointment-summary">
                  <h4>📋 Resumo do Agendamento:</h4>
                  <div class="summary-item">
                    <strong>Tipo:</strong> {{getConsultationTypeLabel()}}
                  </div>
                  <div class="summary-item">
                    <strong>Data:</strong> {{getFormattedDate()}}
                  </div>
                  <div class="summary-item">
                    <strong>Horário:</strong> {{dateTimeForm.get('time')?.value}}
                  </div>
                </div>

                <div class="step-actions">
                  <button mat-button matStepperPrevious>Voltar</button>
                  <button mat-raised-button color="primary" 
                          (click)="confirmAppointment()"
                          [disabled]="!contactForm.valid || isLoading">
                    <mat-spinner diameter="20" *ngIf="isLoading"></mat-spinner>
                    {{isLoading ? 'Agendando...' : '✅ Confirmar Agendamento'}}
                  </button>
                </div>
              </form>
            </mat-step>

            <!-- Etapa 4: Confirmação -->
            <mat-step>
              <ng-template matStepLabel>Concluído</ng-template>
              <div class="success-message">
                <h3>🎉 Agendamento Confirmado!</h3>
                <p>Seu agendamento foi realizado com sucesso. Você receberá uma confirmação via WhatsApp em breve.</p>
                
                <div class="appointment-details">
                  <h4>📅 Detalhes do Agendamento:</h4>
                  <div class="detail-item">
                    <strong>Tipo:</strong> {{getConsultationTypeLabel()}}
                  </div>
                  <div class="detail-item">
                    <strong>Data:</strong> {{getFormattedDate()}}
                  </div>
                  <div class="detail-item">
                    <strong>Horário:</strong> {{dateTimeForm.get('time')?.value}}
                  </div>
                  <div class="detail-item">
                    <strong>Cliente:</strong> {{contactForm.get('name')?.value}}
                  </div>
                </div>

                <button mat-raised-button color="primary" (click)="newAppointment()">
                  Fazer Novo Agendamento
                </button>
              </div>
            </mat-step>
          </mat-stepper>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styleUrls: ['./appointment-booking.component.scss']
})
export class AppointmentBookingComponent implements OnInit {
  consultationTypeForm: FormGroup;
  dateTimeForm: FormGroup;
  contactForm: FormGroup;
  
  availableTimeSlots: string[] = [];
  minDate = new Date();
  isLoading = false;
  prefilledWhatsapp = '';

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private route: ActivatedRoute,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.consultationTypeForm = this.fb.group({
      type: ['', Validators.required]
    });

    this.dateTimeForm = this.fb.group({
      date: ['', Validators.required],
      time: ['', Validators.required]
    });

    this.contactForm = this.fb.group({
      name: ['', Validators.required],
      whatsapp: ['', [Validators.required, Validators.pattern(/^\(\d{2}\)\s\d{4,5}-\d{4}$/)]],
      email: ['']
    });
  }

  ngOnInit() {
    // Verificar se há WhatsApp na URL
    this.route.queryParams.subscribe(params => {
      if (params['whatsapp']) {
        this.prefilledWhatsapp = params['whatsapp'];
        this.contactForm.patchValue({ whatsapp: this.formatWhatsApp(this.prefilledWhatsapp) });
      }
    });

    // Observar mudanças na data para carregar horários disponíveis
    this.dateTimeForm.get('date')?.valueChanges.subscribe(date => {
      if (date) {
        this.loadAvailableTimeSlots(date);
      }
    });
  }

  formatWhatsApp(phone: string): string {
    // Remove caracteres não numéricos
    const cleaned = phone.replace(/\D/g, '');
    // Remove o código do país se presente
    const withoutCountry = cleaned.startsWith('55') ? cleaned.substring(2) : cleaned;
    // Formata no padrão (XX) XXXXX-XXXX
    return withoutCountry.replace(/(\d{2})(\d{4,5})(\d{4})/, '($1) $2-$3');
  }

  dateFilter = (d: Date | null): boolean => {
    const day = (d || new Date()).getDay();
    // Permitir apenas de segunda a sexta (1-5) e sábados (6)
    return day !== 0; // Bloquear domingos
  };

  loadAvailableTimeSlots(date: Date) {
    const consultationType = this.consultationTypeForm.get('type')?.value;
    
    this.apiService.getAvailableTimeSlots(date, consultationType).subscribe({
      next: (slots) => {
        this.availableTimeSlots = slots;
      },
      error: (error) => {
        console.error('Erro ao carregar horários:', error);
        this.setDefaultTimeSlots();
      }
    });
  }

  setDefaultTimeSlots() {
    // Horários padrão caso não consiga carregar do backend
    this.availableTimeSlots = [
      '08:00', '09:00', '10:00', '11:00',
      '14:00', '15:00', '16:00', '17:00'
    ];
  }

  selectTimeSlot(time: string) {
    this.dateTimeForm.patchValue({ time });
  }

  getConsultationTypeLabel(): string {
    const type = this.consultationTypeForm.get('type')?.value;
    return type === 'presencial' ? '🏥 Consulta Presencial' : '💻 Consulta Online';
  }

  getFormattedDate(): string {
    const date = this.dateTimeForm.get('date')?.value;
    if (!date) return '';
    
    return new Intl.DateTimeFormat('pt-BR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }).format(date);
  }

  confirmAppointment() {
    if (!this.contactForm.valid || !this.dateTimeForm.valid || !this.consultationTypeForm.valid) {
      return;
    }

    this.isLoading = true;

    const appointmentData = {
      client_name: this.contactForm.get('name')?.value,
      client_whatsapp: this.contactForm.get('whatsapp')?.value,
      client_email: this.contactForm.get('email')?.value,
      consultation_type: this.consultationTypeForm.get('type')?.value,
      date: this.dateTimeForm.get('date')?.value,
      time: this.dateTimeForm.get('time')?.value
    };

    this.apiService.createAppointment(appointmentData).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.snackBar.open('Agendamento confirmado! Você receberá uma confirmação via WhatsApp.', 'Fechar', {
          duration: 5000,
          panelClass: ['success-snackbar']
        });
        // Avançar para o último step
        setTimeout(() => {
          // Aqui você pode implementar lógica adicional se necessário
        }, 1000);
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Erro ao criar agendamento:', error);
        this.snackBar.open('Erro ao realizar agendamento. Tente novamente.', 'Fechar', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      }
    });
  }

  newAppointment() {
    // Reset forms
    this.consultationTypeForm.reset();
    this.dateTimeForm.reset();
    this.contactForm.reset();
    
    if (this.prefilledWhatsapp) {
      this.contactForm.patchValue({ whatsapp: this.formatWhatsApp(this.prefilledWhatsapp) });
    }

    // Reset stepper
    window.location.reload();
  }
} 