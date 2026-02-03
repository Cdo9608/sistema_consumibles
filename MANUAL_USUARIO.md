# 📱 MANUAL DE USUARIO - Sistema de Inventario v2.0

## 🆕 ¿QUÉ CAMBIÓ?

**ANTES (Sistema Viejo):**
- ❌ Los datos se perdían al reiniciar
- ❌ Había que exportar manualmente
- ❌ Sin backups automáticos

**AHORA (Sistema Nuevo):**
- ✅ Datos se guardan automáticamente en GitHub
- ✅ Backups automáticos cada cambio
- ✅ Recuperación automática al reiniciar
- ✅ Múltiples copias de seguridad

## 🎯 CÓMO USAR EL SISTEMA

### 1️⃣ Al Entrar al Sistema

Verás un banner amarillo en la parte superior:
```
⚠️ IMPORTANTE - NUEVA VERSIÓN CON AUTO-GUARDADO
- ✅ Los datos ahora se guardan automáticamente en GitHub
- ✅ Backup automático cada vez que agregas/editas datos
- ✅ Exportación automática a la carpeta 'data/'
- 💾 Recomendación: Exporta a Excel al final del día por seguridad
```

**Esto es NORMAL** - solo te recuerda las mejoras.

### 2️⃣ Registrar Entradas/Salidas

**NADA CAMBIA AQUÍ** - funciona igual que antes:

1. Ve a "📥 Registrar Entrada" o "📤 Registrar Salida"
2. Llena el formulario
3. Haz clic en "✅ Registrar"

**NUEVO:** Verás el mensaje:
```
✅ Entrada registrada correctamente
🔄 Datos sincronizados automáticamente
```

Esto significa que tus datos ya están guardados en GitHub.

### 3️⃣ Ver Datos

- **Ver Entradas:** Lista todas las entradas registradas
- **Ver Salidas:** Lista todas las salidas registradas
- **Inventario/Stock:** Muestra stock calculado automáticamente

**Sin cambios** - funciona igual que antes.

### 4️⃣ Exportar Datos (AL FINAL DEL DÍA)

**⚠️ IMPORTANTE - HAZLO TODOS LOS DÍAS:**

1. Ve a "💾 Exportar Datos"
2. Haz clic en "📊 Exportar a Excel Completo"
3. **DESCARGA el archivo a tu computadora**
4. Guárdalo con un nombre claro, ejemplo: `Inventario_2026-02-03.xlsx`

**¿Por qué?**
- Es tu backup de seguridad FINAL
- Si algo sale muy mal con GitHub
- Tienes una copia local segura

### 5️⃣ Verificar que tus Datos Están Seguros

**Opción 1: En el Sidebar (Barra Lateral)**

Mira los números:
- Total Entradas: 245
- Total Salidas: 189
- Productos Bajo Stock: 12

Si ves números, tus datos están ahí.

**Opción 2: En GitHub**

1. Ve a: https://github.com/Cdo9608/sistema_consumibles/tree/main/data
2. Deberías ver archivos:
   - `entradas_persist.json`
   - `salidas_persist.json`
   - `backup_auto_YYYYMMDD_HHMMSS.xlsx`

Si ves estos archivos, tus datos están respaldados.

## ⚠️ SITUACIONES ESPECIALES

### ❓ "No veo mis datos de ayer"

**SI ACABAS DE MIGRAR:**
1. Es normal - los datos viejos se perdieron
2. Empieza de nuevo (revisa si alguien descargó Excel ayer)

**SI YA ESTABAS USANDO v2.0:**
1. Ve a "⚙️ Configuración"
2. Verifica que existan los archivos JSON
3. Si dice "✅ Existe" - los datos están ahí
4. Haz clic en el botón "🔄 Sincronizar Ahora"

### ❓ "¿Cada cuánto debo exportar?"

**Recomendación:**
- Mínimo: 1 vez al día (al final del día)
- Ideal: Después de sesiones de ingreso masivo de datos
- Backup semanal: Guardar en Google Drive/OneDrive

### ❓ "Vi un mensaje de error"

**Errores comunes:**

1. **"Error al guardar entrada"**
   - Verifica que llenaste todos los campos obligatorios (*)
   - Vuelve a intentar
   - Si persiste, contacta soporte

2. **"Error en sincronización"**
   - Normalmente se auto-resuelve
   - El sistema intentará de nuevo automáticamente
   - Si ves esto frecuentemente, reporta

3. **"No se encontró la base de datos"**
   - Espera 30 segundos
   - Recarga la página (F5)
   - El sistema se auto-recuperará

## 📋 CHECKLIST DIARIO

### ☀️ Al Iniciar el Día
- [ ] Abrir sistema
- [ ] Verificar que veo datos del día anterior
- [ ] Si no veo datos, ir a Configuración y revisar

### 🌙 Al Terminar el Día
- [ ] Ir a "💾 Exportar Datos"
- [ ] Exportar a Excel Completo
- [ ] Descargar el archivo
- [ ] Guardarlo en tu computadora con fecha clara
- [ ] (Opcional) Subir a Google Drive

### 📅 Una Vez por Semana
- [ ] Descargar TODOS los archivos de GitHub/data/
- [ ] Guardarlos en un lugar seguro (Drive, OneDrive)
- [ ] Verificar que tienes backups de las últimas 2 semanas

## 🚨 EN CASO DE EMERGENCIA

### Si se pierden datos:

1. **Mantén la calma** 🧘
2. **NO hagas más cambios** en el sistema
3. Contacta al administrador
4. Ten listos:
   - Última exportación Excel que tengas
   - Fecha aproximada de los datos perdidos
   - Cualquier captura de pantalla

### Si el sistema no carga:

1. Espera 2-3 minutos (puede estar reiniciándose)
2. Recarga la página (F5)
3. Si sigue sin cargar:
   - Ve a GitHub: https://github.com/Cdo9608/sistema_consumibles
   - Revisa la carpeta `data/`
   - Descarga los archivos .json y .xlsx como backup

## ❓ PREGUNTAS FRECUENTES

**P: ¿Puedo usar el sistema desde mi celular?**
R: Sí, funciona en navegador móvil, pero es más cómodo en computadora.

**P: ¿Cuántos usuarios pueden usar al mismo tiempo?**
R: Ilimitados, pero los cambios se sincronizan cada ~30 segundos.

**P: ¿Puedo eliminar registros?**
R: Sí, en "Ver Entradas" o "Ver Salidas", usa la sección "🗑️ Gestionar Registros".

**P: ¿Qué pasa si ingreso un dato mal?**
R: Elimínalo y vuelve a agregarlo. El sistema guarda todo automáticamente.

**P: ¿Necesito internet?**
R: Sí, siempre. Es un sistema en la nube.

**P: ¿Los datos son privados?**
R: Sí, solo personas con acceso al GitHub pueden verlos.

## 📞 SOPORTE

**Administrador del Sistema:**
- Email: [tu-email@empresa.com]
- GitHub: https://github.com/Cdo9608/sistema_consumibles

**Reportar Problemas:**
1. Describe qué estabas haciendo
2. Copia el mensaje de error completo
3. Adjunta captura de pantalla si es posible
4. Incluye fecha y hora

---

**Versión:** 2.0
**Última Actualización:** 3 de Febrero, 2026
**Creado para:** Personal de Inventario y Logística

## 🎉 ¡Eso es todo!

El sistema ahora es más seguro. Solo recuerda:
1. ✅ El sistema guarda automáticamente
2. ✅ Exporta Excel al final del día
3. ✅ Verifica que tus datos persisten

**¡A trabajar sin preocupaciones! 🚀**
