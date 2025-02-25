# Pulpomatic Libs

Librería común que contiene utilidades compartidas entre los diferentes scripts de Pulpomatic. Esta librería encapsula lógica reutilizable y funcionalidades comunes.

## Estructura

```
libs/
├── src/             # Código fuente de la librería
│   ├── __init__.py  # Exporta las funciones y clases públicas
│   ├── logger.py    # Configuración y utilidades de logging
│   └── pulpo_api.py # Cliente y funciones para interactuar con la API
├── setup.py         # Configuración del paquete
└── readme.md        # Este archivo
```

## Instalación

Para instalar la librería en modo desarrollo:

```bash
cd libs
pip install -e .
```

## Uso

Para usar la librería en tus scripts:

```python
from libs import setup_logger, pulpo_api

# Configurar el logger
logger = setup_logger()

# Usar funciones de pulpo_api
pulpo_api.some_function()
```

## Añadir Nuevas Librerías

Para añadir una nueva librería al proyecto:

1. Crea un nuevo archivo Python en el directorio `src/`:
   ```bash
   touch src/mi_nueva_libreria.py
   ```

2. Implementa tu código en el nuevo archivo:
   ```python
   # src/mi_nueva_libreria.py
   def mi_funcion():
       pass
   ```

3. Exporta las funciones en `src/__init__.py`:
   ```python
   from .mi_nueva_libreria import mi_funcion
   ```

4. Si tu librería requiere nuevas dependencias:
   - Añádelas al `install_requires` en `setup.py`
   - Reinstala el paquete: `pip install -e .`

No es necesario hacer ninguna configuración adicional. El `setup.py` está configurado para detectar automáticamente todos los módulos Python en el directorio `src/`.

## Buenas Prácticas

1. **Documentación**:
   - Añade docstrings a todas las funciones y clases
   - Actualiza este README si añades nuevos módulos
   - Incluye ejemplos de uso

2. **Código**:
   - Sigue las convenciones de código existentes
   - Usa tipos cuando sea posible
   - Mantén las funciones pequeñas y enfocadas

3. **Dependencias**:
   - Minimiza el número de dependencias externas
   - Especifica versiones exactas si son críticas
   - Documenta por qué se necesita cada dependencia

4. **Testing**:
   - Añade tests para tu nueva funcionalidad
   - Verifica que los cambios no rompen código existente

## Mantenimiento

- Revisa y actualiza las dependencias periódicamente
- Mantén la documentación actualizada
- Sigue las convenciones de versionado semántico