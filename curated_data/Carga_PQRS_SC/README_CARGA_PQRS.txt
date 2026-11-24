CARGA PQRS - SAN CRISTÓBAL
==========================

FUENTE
------
pqrs_sdg_2022_2026.csv

PERFILAMIENTO
-------------
Registros fuente: 75.613
Registros San Cristóbal: 4.026
Radicados únicos San Cristóbal: 4.026
Periodo observado: 14/03/2022 a 11/08/2026

CATÁLOGOS
---------
tipo_peticion: 7 valores cargados
medio_recepcion: 7 valores
subtema_pqrs: 82 valores

El valor fuente "NA" se interpreta como ausencia de dato y se convierte a NULL.
El valor "No definido" en TIPO_PETICION se conserva porque es una categoría
explícita de la fuente, aunque constituye un hallazgo de calidad.

DECISIÓN DE LOCALIDAD
---------------------
Todos los registros seleccionados tienen:
NOMBRE_LOCALIDAD = ALCALDIA LOCAL DE SAN CRISTOBAL

Por tanto:
id_localidad = 4

LOCALIDAD_CODI NO representa el código estándar de localidad de Bogotá:
aparecen 545, 460, 555, 695, 645 y valores faltantes.

Por ello:
- NO se usa LOCALIDAD_CODI como FK.
- Se preserva como pqrs.codigo_localidad_fuente para linaje y calidad.

NULOS DESPUÉS DE NORMALIZAR "NA"
--------------------------------
Tipo de petición: 448
Tiempo trámite: 448
Observación general: 15
Observación SAC: 3.949
Última dependencia: 188
Radicado respuesta: 144
Fecha respuesta: 144
Fecha seguimiento: 15
Código localidad fuente: 508

CALIDAD TEMPORAL
----------------
Todas las fechas no-NA cumplen el formato dd/MM/yyyy HH:mm:ss y se convierten
a timestamp.

Existen 4 registros donde VIGENCIA no coincide con el año de FECHA_REGISTRO.
Se conserva VIGENCIA tal como viene en la fuente y no se sobrescribe con el año
de la fecha. El archivo de control identifica esos radicados.

No se calculan duraciones adicionales a partir del orden de las fechas porque
la semántica de FECHA_REGISTRO, RADI_FECH_RADI y FECHA_ASIGNACION no garantiza
una secuencia temporal estricta en la fuente.

AJUSTE DEL MODELO
-----------------
No se requiere ajuste del DBML.

Las longitudes reales caben dentro de los tipos ya definidos y la opcionalidad
de tipo_peticion, medio_recepcion y subtema es compatible con el modelo actual.

ESTADO_ORFEO, dependencias y usuario se conservan como atributos de PQRS.
No se crean catálogos adicionales en V1 porque no son necesarios para la
integración principal y hacerlo aumentaría la complejidad sin aportar una
relación nueva con los demás dominios.

ORDEN DE EJECUCIÓN EN DBEAVER
-----------------------------
1. sql/01_carga_pqrs.sql
2. sql/02_validar_pqrs.sql

RESULTADOS ESPERADOS
--------------------
pqrs: 4.026
tipo_peticion: 7
medio_recepcion: 7
subtema_pqrs: 82

VISTA CREADA
------------
vw_pqrs_detalle

La vista entrega la PQRS con los nombres de sus catálogos y la localidad,
lista para consumo analítico.

IMPORTANTE PARA EL PROYECTO
---------------------------
PQRS NO se relaciona directamente con proyecto o meta porque la fuente no
incluye una llave institucional que soporte esa asociación.

Cualquier relación futura PQRS → tema/sector/meta deberá construirse como una
capa analítica explícita (por reglas, clasificación o IA), nunca como una FK
inventada dentro del modelo transaccional.
