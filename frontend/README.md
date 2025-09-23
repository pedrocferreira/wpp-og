# Frontend - Sistema Inteligente

Este é o frontend do Sistema Inteligente de Gestão & Atendimento, desenvolvido com Angular 17+ e Angular Material.

## 🎨 Design Moderno

O frontend foi modernizado com:

### ✨ Características Visuais
- **Logo personalizado**: Uso do `logo.png` em todos os componentes
- **Tema roxo moderno**: Paleta de cores unificada com tons de roxo (#8B5CF6, #A855F7, #7C3AED)
- **Efeitos glassmorphism**: Backdrop blur e transparências
- **Animações suaves**: Transições e hover effects modernos
- **Design responsivo**: Otimizado para desktop, tablet e mobile

### 🎯 Componentes Principais

#### Navbar
- Logo centralizado com efeitos hover
- Gradiente roxo moderno
- Menu de usuário com informações detalhadas
- Responsivo com animações suaves

#### Tela de Login
- Design glassmorphism com blur
- Logo animado com hover effects
- Campos de input modernizados
- Botões com gradientes e sombras
- Background animado com partículas

#### Cards e Elementos
- Bordas arredondadas consistentes
- Sombras suaves com tons de roxo
- Hover effects em todos os componentes interativos
- Scrollbar personalizada

### 🌈 Paleta de Cores

```scss
:root {
  --primary-purple: #8B5CF6;
  --primary-purple-light: #A855F7;
  --primary-purple-dark: #7C3AED;
  --secondary-purple: #DDD6FE;
  --purple-50: #FAF5FF;
  --purple-100: #F3E8FF;
  --purple-200: #E9D5FF;
  --white: #ffffff;
}
```

### 📱 Responsividade

O design se adapta automaticamente a diferentes tamanhos de tela:
- **Desktop**: Layout completo com todos os elementos
- **Tablet**: Elementos condensados mantendo funcionalidade
- **Mobile**: Interface otimizada para touch com textos maiores

## 🚀 Tecnologias

- **Angular 17+**: Framework principal
- **Angular Material**: Componentes de UI
- **SCSS**: Estilização avançada
- **TypeScript**: Linguagem de programação
- **Responsive Design**: Design adaptativo

## 📦 Estrutura

```
frontend/
├── src/
│   ├── app/
│   │   ├── components/
│   │   │   ├── navbar/           # Barra de navegação
│   │   │   ├── login/            # Tela de login
│   │   │   ├── dashboard/        # Dashboard principal
│   │   │   └── ...
│   │   └── services/             # Serviços da aplicação
│   ├── assets/
│   │   ├── logo.png             # Logo principal
│   │   └── ...
│   └── styles.scss              # Estilos globais
```

## 🛠 Desenvolvimento

```bash
# Instalar dependências
npm install

# Executar em desenvolvimento
ng serve

# Build para produção
ng build --prod
```

## 🎨 Customização

Para personalizar o tema, edite as variáveis CSS em `src/styles.scss`:

```scss
:root {
  --primary-purple: #SUA_COR;
  --primary-purple-light: #SUA_COR_CLARA;
  --primary-purple-dark: #SUA_COR_ESCURA;
}
```

## 📋 Features

- ✅ Design moderno e responsivo
- ✅ Tema roxo unificado
- ✅ Logo personalizado
- ✅ Animações suaves
- ✅ Efeitos glassmorphism
- ✅ Componentes Material customizados
- ✅ Scrollbar personalizada
- ✅ Dark mode ready

## 🔧 Configurações

O projeto está configurado com:
- Angular Material com tema customizado
- SCSS para estilização avançada
- Variáveis CSS para fácil manutenção
- Classes utilitárias para desenvolvimento rápido

---

**Desenvolvido com ❤️ e muito ☕**