# Calculadora de Nutrición Parenteral en UCI

Una aplicación web moderna, intuitiva y segura para el cálculo y prescripción de Nutrición Parenteral (NP) en pacientes críticos. Diseñada para su uso en entornos clínicos (UCI, Reanimación) con un enfoque en la seguridad del paciente y la usabilidad.

## Características

-   **Cálculo Antropométrico**: Peso Ideal, Ajustado y BMI automático.
-   **Seguridad**: Alertas automáticas para dosis de glucosa (g/kg/h) y lípidos.
-   **Guía Paso a Paso**: Ayuda didáctica para la prescripción.
-   **Generador de Órdenes**: Copia un texto formateado listo para la historia clínica.
-   **Diseño Moderno**: Interfaz oscura/clara, responsiva y optimizada para móviles y escritorio.
-   **Lógica Clínica**: Basada en guías ESPEN/ASPEN para paciente crítico (Sepsis, Realimentación, etc).

## Instalación / Uso

Este proyecto es una aplicación web estática (HTML/CSS/JS). No requiere servidor ni instalación compleja.

### Opción 1: Ejecutar Localmente
1.  Descarga la carpeta `NPT_Calculator_Web`.
2.  Abre el archivo `index.html` en cualquier navegador moderno (Chrome, Edge, Firefox).

### Opción 2: GitHub Pages
1.  Sube este repositorio a GitHub.
2.  Activa **GitHub Pages** en la configuración del repositorio.
3.  La calculadora estará disponible online inmediatamente.

## Estructura del Proyecto

```
NPT_Calculator_Web/
├── css/
│   └── styles.css      # Sistema de diseño y estilos variables
├── js/
│   ├── logic.js        # Lógica pura de cálculo (sin UI code)
│   └── app.js          # Controlador de la interfaz y eventos
├── index.html          # Estructura principal
└── README.md           # Documentación
```

## Créditos

Basado en la versión original `v4 DEF` de la Calculadora de NP UCI.
Refactorizado y modernizado para una mejor experiencia de usuario y mantenibilidad.
