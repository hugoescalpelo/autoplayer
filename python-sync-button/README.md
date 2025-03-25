# Button Player

En esta carpeta se encuentran los programas para probar el funcionamiento de 3 botones, resumido de la siguiente forma por Gabriela Perez Torres.

## 🎮 Esquema Completo de Funcionalidades - Sistema de 3 Botones

Este sistema utiliza solo **3 botones físicos** conectados a los GPIO de una Raspberry Pi:

- ⬅️ **Izquierda**
- ➡️ **Derecha**
- ☰ **Menú**

Cada botón puede ejecutar **dos acciones distintas** dependiendo de la duración de la pulsación:
- **Pulsación corta**: acción global (se replica en todo el video wall).
- **Pulsación larga**: acción local (solo afecta a la Raspberry donde se presiona el botón).

---

### 🧭 Mapeo de acciones por botón

| Botón       | Pulsación corta (Global)   | Pulsación larga (Local)     |
|-------------|-----------------------------|-------------------------------|
| ⬅️ Izquierda | `GLOBAL_PREV_GROUP`         | `LOCAL_REWIND`                |
| ➡️ Derecha   | `GLOBAL_NEXT_GROUP`         | `LOCAL_FAST_FORWARD`          |
| ☰ Menú       | `GLOBAL_TOGGLE_PLAY`        | `LOCAL_CYCLE_MODE`            |

---

### 🌍 Funciones Globales

Estas acciones se **envían vía UDP broadcast** a todas las Raspberry Pi del sistema.

| Comando             | Descripción                                              |
|---------------------|----------------------------------------------------------|
| `GLOBAL_PREV_GROUP` | Cambiar al grupo anterior de videos sincronizados.       |
| `GLOBAL_NEXT_GROUP` | Cambiar al siguiente grupo de videos sincronizados.      |
| `GLOBAL_TOGGLE_PLAY`| Alternar entre play y pausa en todo el video wall.       |

---

### 💻 Funciones Locales

Estas acciones **solo afectan la Raspberry Pi donde se presiona el botón**.

| Comando               | Descripción                                                 |
|-----------------------|-------------------------------------------------------------|
| `LOCAL_REWIND`        | Retrocede el video unos segundos.                           |
| `LOCAL_FAST_FORWARD`  | Adelanta el video unos segundos.                            |
| `LOCAL_CYCLE_MODE`    | Alterna entre modos locales:<br>↻ rotar 180°,<br>🅰/🅱 cambiar video A/B,<br>🔍 zoom in/out. |

---

💡 Este sistema permite manipular cada pantalla del video wall de forma independiente, pero también controlar la reproducción sincronizada desde cualquier unidad.

✨ Ideal para instalaciones interactivas de larga duración donde la interfaz debe ser simple pero poderosa.
