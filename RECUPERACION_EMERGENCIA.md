# 🆘 GUÍA DE RECUPERACIÓN DE EMERGENCIA

## ❌ PROBLEMA ACTUAL

**Los datos ingresados ayer se PERDIERON** porque:
- SQLite en Streamlit Cloud **NO es persistente**
- Los datos solo existían en memoria/contenedor temporal
- No hubo exportación a Excel
- La carpeta `data/` en GitHub está vacía
- El contenedor se reinició y todo se borró

## 🔍 INTENTOS DE RECUPERACIÓN

### Opción 1: Verificar si alguien descargó Excel ayer ✅
**PREGUNTA A TODOS LOS USUARIOS:**
- ¿Alguien usó el botón "Exportar a Excel" ayer?
- ¿Alguien descargó algún archivo del sistema?
- Revisa tu carpeta de Descargas por archivos con nombre `inventario_completo_*.xlsx`

### Opción 2: Capturas de pantalla 📸
- Si alguien tomó capturas de pantalla de las tablas
- Podrían recuperarse datos manualmente desde las imágenes
- Es tedioso pero es mejor que perder todo

### Opción 3: Caché del navegador 🌐
**Para usuarios que tuvieron la app abierta ayer:**
1. NO cierres el navegador si aún tienes la pestaña abierta
2. Presiona F12 (Herramientas de desarrollador)
3. Ve a la pestaña "Application" o "Almacenamiento"
4. Revisa:
   - Local Storage
   - Session Storage
   - IndexedDB
5. Puede haber rastros de datos temporales

### Opción 4: Logs del servidor ⚠️
- Los logs que compartiste NO muestran los datos
- Solo muestran que la app se inició correctamente
- No hay forma de recuperar datos desde los logs

## ❌ NO HAY MÁS OPCIONES

Si ninguna de las opciones anteriores funciona, **los datos están permanentemente perdidos**.

## ✅ SOLUCIÓN PERMANENTE - NUEVA VERSIÓN

He creado una **versión mejorada** (`app_mejorado.py`) que previene esto:

### 🔒 Características de Protección:

1. **Auto-guardado Triple:**
   - ✅ SQLite (temporal para velocidad)
   - ✅ Archivos JSON en `data/` (persistente en GitHub)
   - ✅ Backups Excel automáticos en `data/`

2. **Sincronización Automática:**
   - Cada vez que agregas/editas datos → se guarda en GitHub
   - Sin intervención manual necesaria
   - Backups automáticos cada cambio

3. **Recuperación Automática:**
   - Al reiniciar, busca archivos JSON
   - Restaura datos automáticamente
   - No se pierde nada

4. **Advertencias Visibles:**
   - Banner en la parte superior
   - Recordatorios de exportar
   - Indicadores de sincronización

## 🚀 MIGRAR A LA NUEVA VERSIÓN

### Paso 1: Reemplazar app.py

```bash
# En tu repositorio local
cp app.py app_viejo.py  # Backup del anterior
cp app_mejorado.py app.py

# Commit y push
git add .
git commit -m "Actualización urgente: Sistema de persistencia automática"
git push origin main
```

### Paso 2: Crear carpeta data/

```bash
mkdir -p data
touch data/.gitkeep
git add data/.gitkeep
git commit -m "Agregar carpeta data para persistencia"
git push origin main
```

### Paso 3: Configurar .gitignore

Crea o actualiza `.gitignore`:

```
# Base de datos temporal (no persistir)
inventario.db
*.db

# Pero SÍ incluir archivos JSON y Excel de data/
!data/*.json
!data/*.xlsx
!data/.gitkeep
```

## 📋 PROTOCOLO DE USO DIARIO

### ✅ NUEVA RUTINA OBLIGATORIA:

1. **Al iniciar el día:**
   - Verificar que los datos del día anterior estén visibles
   - Si no: ir a "Configuración" y revisar archivos JSON

2. **Durante el día:**
   - Los datos se guardan automáticamente
   - NO necesitas hacer nada extra
   - Aparecerá "🔄 Datos sincronizados" al guardar

3. **Al final del día:**
   - Ir a "💾 Exportar Datos"
   - Hacer clic en "📊 Exportar a Excel Completo"
   - DESCARGAR el archivo a tu computadora
   - **ESTE ES TU BACKUP DE SEGURIDAD FINAL**

4. **Una vez por semana:**
   - Descargar TODOS los backups de `data/`
   - Guardarlos en Google Drive o similar
   - Limpiar backups muy antiguos

## 🔥 PLAN DE EMERGENCIA

Si algo sale mal:

1. **Ve a la carpeta `data/` en GitHub:**
   - https://github.com/Cdo9608/sistema_consumibles/tree/main/data

2. **Descarga los archivos:**
   - `entradas_persist.json`
   - `salidas_persist.json`
   - `backup_auto_*.xlsx` (el más reciente)

3. **Restaurar localmente:**
   ```bash
   # Usa el script de importación
   python importar_datos.py
   ```

## ⚠️ LECCIONES APRENDIDAS

### ❌ NUNCA MÁS:
- Confiar solo en SQLite en la nube
- Asumir que los datos persisten sin verificar
- Esperar hasta el final del día para guardar

### ✅ SIEMPRE:
- Múltiples backups automáticos
- Archivos en GitHub (versionados)
- Exportación manual al final del día
- Verificar que los datos persisten

## 📞 CONTACTO EN CASO DE PROBLEMAS

Si necesitas ayuda:
1. Revisa los archivos en GitHub: `data/`
2. Verifica los logs de Streamlit Cloud
3. Contacta al equipo de soporte

## 🎯 PRÓXIMOS PASOS INMEDIATOS

1. ✅ Implementar `app_mejorado.py`
2. ✅ Crear carpeta `data/` en GitHub
3. ✅ Configurar `.gitignore` correctamente
4. ✅ INFORMAR A TODOS LOS USUARIOS del nuevo protocolo
5. ✅ Hacer prueba completa:
   - Agregar dato de prueba
   - Verificar que aparece en `data/`
   - Reiniciar app
   - Verificar que el dato persiste

## 📚 DOCUMENTACIÓN ADICIONAL

- `MANUAL_USUARIO.md` - Guía para usuarios finales
- `MANUAL_TECNICO.md` - Detalles técnicos
- `FAQ.md` - Preguntas frecuentes

---

**ÚLTIMA ACTUALIZACIÓN:** 3 de febrero, 2026
**VERSIÓN:** 2.0 (Con persistencia automática)
**ESTADO:** 🔴 CRÍTICO - Migración urgente requerida
