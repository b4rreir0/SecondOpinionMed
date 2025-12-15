# Especificación Técnica - Second Opinion Med

## Reglas de Negocio

### 1. Rol del Responsable del Caso
- **Función Primaria:** Redactor final oficial de la institución.
- **Responsabilidad:** Sintetizar el consenso del Comité Multidisciplinario (MDT) en un informe formal dirigido al paciente, emitido "En nombre de la Institución".

### 2. Algoritmo de Asignación Automática y Equitativa (Rotativa)
- **Regla Base:** Basada en la especialidad oncológica requerida.
- **Mecanismo de Rotación (Round Robin):**
  - Lista ordenada de responsables por especialidad.
  - Asignación secuencial, reinicio al completar la lista.
  - Objetivo: Distribución equitativa de carga.

### 3. Protocolo de Comunicación con el Paciente
- **Contacto Telefónico:** Número de teléfono prominente como "Dato Crítico".
- **Iniciativa:** Solo por miembros del MDT analizando el caso.
- **Registro:** Toda llamada debe registrarse con fecha, hora, médico y resumen.

## Diagrama de Flujo del Algoritmo de Asignación

```mermaid
flowchart TD
    A[Caso Nuevo Ingresa<br>Especialidad: Pulmón] --> B{¿Hay responsables<br>para esta especialidad?}

    B -- Sí --> C[Obtener lista ordenada<br>de responsables de Pulmón]
    C --> D{Verificar estado de carga<br>del próximo en la lista}
    
    D -- Disponible --> E[Asignar caso al responsable]
    E --> F[Rotar lista:<br>Mover responsable al final]
    F --> G[Asignación Completada]

    D -- No Disponible<br>Ej. Vacaciones --> H[Marcar como temporalmente<br>no disponible]
    H --> I[Buscar siguiente<br>responsable en lista]
    I --> D

    B -- No --> J[Estado: "Pendiente de Asignación<br>Especialista"<br>Notificar a Coordinación]
```

## Tabla de Estados del Sistema

| Estado del Sistema | ¿Quién lo Cambia? | Significado y Acciones Permitidas |
|--------------------|-------------------|-----------------------------------|
| Pendiente de Asignación | Sistema (automático) | Caso en cola esperando responsable disponible. |
| Asignado a [Dr. X] | Sistema (automático) | Responsable revisa documentación, puede solicitar info o enviar a MDT. |
| Esperando Info del Paciente | Responsable del Caso | Contacto al paciente para documentos faltantes. |
| En Análisis por MDT | Responsable del Caso | Discusión activa. Habilita "Contactar al Paciente" para miembros MDT. |
| Informe en Redacción | Responsable del Caso | Decisión tomada, redacción del informe institucional. |
| Concluido – Informe Enviado | Sistema (automático) | Informe enviado, caso archivado. |

**Nota:** La función "llamar al paciente" solo visible en estado "En Análisis por MDT" para roles "Miembro MDT" o "Responsable".