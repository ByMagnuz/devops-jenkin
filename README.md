# Laboratorio DevOps Jenkins + GitHub + simuladores mainframe

**Propósito:** experimentar Pipeline-as-Code sin acceso a z/OS. Es un laboratorio didáctico: **ninguno** de los scripts es IBM DBB, SonarQube, Nexus Repository ni IBM Wazi Deploy reales. Tampoco se compila COBOL: se produce un artefacto ficticio de tipo `.load`.

## Arquitectura

GitHub (ramas, PR, Jenkinsfile) → Jenkins Multibranch → pruebas unitarias (Python) → DBB simulado → quality gate simulado → Nexus simulado (versiones, SHA-256) → Wazi Deploy simulado (TEST → QA → PREPROD → PROD).

- **PR o rama de desarrollo:** checkout, pruebas, build y calidad. **No publica ni despliega**.
- **Rama `main`:** ejecuta lo anterior y publica un artefacto inmutable; automáticamente lo despliega a TEST.
- **Promoción opcional:** al elegir QA/PREPROD/PROD en `PROMOTE_TO`, Jenkins solicita aprobación antes de cada ambiente. **Se promueve el mismo archivo versionado**: no se vuelve a compilar entre ambientes.
- **Estado de despliegue:** `/opt/devops-lab/environments/TEST/current.json` y equivalentes. Los módulos ficticios están bajo `versions/<version>/LOADLIB/`.

## 1. Requisitos del servidor Magnus

Primero instala Jenkins LTS y verifica su acceso web. Requisitos de este repo: Git y Python 3, sin `pip` ni bibliotecas externas. Además, plugin Jenkins **GitHub Branch Source**, **Pipeline**, **Pipeline: Declarative**, **JUnit**, y **Git** (algunos vienen con la instalación recomendada).

En Debian, comprobar:

```bash
java -version
jenkins --version || true
python3 --version
git --version
sudo systemctl status jenkins --no-pager
sudo ss -lntp | grep ':8080 '
```

Si no hay Python y Git:

```bash
sudo apt update
sudo apt install -y python3 git
```

**Almacenamiento del laboratorio.** Si Jenkins está instalado como servicio local y los builds corren con el usuario `jenkins`:

```bash
sudo install -d -o jenkins -g jenkins -m 0750 /opt/devops-lab/nexus-sim
sudo install -d -o jenkins -g jenkins -m 0750 /opt/devops-lab/environments
```

NO hagas `chmod 777`. Si Jenkins corre en Docker, K3s o agente remoto, hay que montar estos directorios y ajustar permisos en ese agente; los comandos anteriores asumen servicio local Debian.

## 2. Prueba los simuladores SIN Jenkins primero

Desde la raíz de este repositorio:

```bash
python3 -m tools.run_tests
python3 -m tools.mock_dbb --source fuentes/cobol --copybooks fuentes/copybooks --output dist/programas.tar.gz --commit DEMO
python3 -m tools.mock_sonar --source fuentes --report reports/quality.json
python3 -m tools.mock_nexus publish --repository /tmp/devops-lab-nexus --artifact dist/programas.tar.gz --name demo-cobol --version local-001
python3 -m tools.mock_nexus verify --repository /tmp/devops-lab-nexus --name demo-cobol --version local-001
python3 -m tools.mock_wazi deploy --repository /tmp/devops-lab-nexus --environments /tmp/devops-lab-ambientes --name demo-cobol --version local-001 --target TEST
python3 -m tools.smoke_test --environments /tmp/devops-lab-ambientes --target TEST --version local-001
cat /tmp/devops-lab-ambientes/TEST/current.json
```

La prueba usa `/tmp`; el pipeline de Jenkins usa `/opt/devops-lab` para persistencia.

## 3. Crear el repositorio GitHub

En GitHub crea un repositorio llamado `devops-jenkins-mainframe-lab` (preferiblemente **privado** si agregas datos internos; para este ejemplo público también funciona) y **no** agregues archivos de plantilla si vas a subir esta carpeta ya preparada. Copia los archivos del ZIP a una carpeta normal, entra a ella y ejecuta:

```bash
git init
git branch -M main
git add .
git commit -m "laboratorio inicial DevOps con Jenkins"
git remote add origin https://github.com/TU_USUARIO/devops-jenkins-mainframe-lab.git
git push -u origin main
```

GitHub requiere un método autorizado para push (por ejemplo, Git Credential Manager, token PAT o SSH); no pegues credenciales en el Jenkinsfile.

## 4. Crear el job en Jenkins

1. Abre `http://192.168.1.73:8080` desde tu LAN.
2. **Manage Jenkins → Plugins**: confirma `Git`, `Pipeline`, `GitHub Branch Source` y `JUnit`.
3. **New Item → Multibranch Pipeline**, nombre `devops-mainframe-lab`.
4. **Branch Sources → Add source → GitHub**.
5. Configura el propietario (`Owner`) y el nombre (`Repository`) del repositorio. Añade credenciales con acceso de lectura si es privado; almacénalas en el almacén de Jenkins, no en los scripts.
6. En **Behaviors**, habilita detección de ramas y **Discover pull requests from origin**. Para el aprendizaje de PR es razonable construir la revisión de merge con la rama de destino.
7. **Build Configuration**: ruta del script `Jenkinsfile`.
8. Guardar y seleccionar **Scan Multibranch Pipeline Now** (o configurar `Scan Multibranch Pipeline Triggers` para un intervalo si tu versión lo ofrece).
9. Entra al trabajo `main` → **Build with Parameters** → `PROMOTE_TO=TEST` y ejecuta.
10. Verifica **Stage View/visualizador de pipeline**, **Console Output**, **Tests**, **Artifacts** y los directorios de `/opt/devops-lab`.

**Webhooks:** GitHub no puede hacer POST a `192.168.1.73:8080` desde Internet. Empieza con el escaneo manual/por intervalos. En otra fase configura conectividad pública HTTPS segura con autenticación, un túnel administrado o un agente autorizado; nunca abras Jenkins directamente por port forwarding sin seguridad.

**Seguridad de PR:** los PR no publican ni despliegan en este Jenkinsfile, pero un PR puede cambiar su propio `Jenkinsfile` o scripts; ejecuta PR no confiables solo en agentes aislados sin secretos ni acceso a servicios sensibles. Para practicar utiliza un repo y colaboradores de confianza.

## 5. Experimento con Pull Request

```bash
git checkout -b feature/mostrar-saldo
# Edita el DISPLAY del archivo fuentes/cobol/SALDOS.cbl
git add fuentes/cobol/SALDOS.cbl
git commit -m "ajuste mensaje de saldos"
git push -u origin feature/mostrar-saldo
```

En GitHub crea un Pull Request hacia `main`. En Jenkins escanea el proyecto Multibranch; cuando `GitHub Branch Source` detecte el PR aparecerá un subjob de PR para ejecutar las validaciones. Revisa logs y estatus. Luego aprueba y mergea en GitHub. Jenkins detectará `main` en un nuevo escaneo y ejecutará la publicación y despliegue TEST.

## 6. Simular un error de calidad

Agrega `      * TODO: corregir` en `SALDOS.cbl`, `commit`, `push` y abre un PR. El stage `04 - SonarQube: quality gate SIMULADO` debe fallar. El archivo `reports/quality.json` muestra el hallazgo. Corrige y vuelve a enviar el `push`; en Jenkins vuelve a escanear y ejecuta de nuevo.

También puedes romper el `COPY CLIENTE.` renombrándolo a `COPY INEXISTENTE.`: la simulación de DBB fallará por dependencia no encontrada.

## 7. Experimentar promociones y rollback

En un `main` build, selecciona **Build with Parameters** y elige `QA`, `PREPROD` o `PROD`. Jenkins pide una aprobación en cada ambiente posterior a TEST. Todas las promociones de la ejecución usan el mismo archivo de `/opt/devops-lab/nexus-sim/demo-cobol/<version>/programas.tar.gz` y verifican su SHA-256.

Para observar la versión activa:

```bash
cat /opt/devops-lab/environments/TEST/current.json
find /opt/devops-lab/environments -maxdepth 5 -type f
```

**Rollback didáctico manual:** conserva la versión anterior, y ejecuta `python3 -m tools.mock_wazi deploy --repository ... --environments ... --name demo-cobol --version VERSION_ANTERIOR --target TEST` desde el checkout local, con permisos del usuario correspondiente. En un sistema real se necesita aprobación/auditoría y podrían existir pasos adicionales de retroceso (datos, DB, etc.).

## 8. Significado de cada archivo

- `Jenkinsfile`: orquestación completa, condiciones por rama, parámetros, aprobaciones y publicación de reportes.
- `fuentes/cobol/SALDOS.cbl`: programa COBOL de demostración (no ejecutado).
- `fuentes/copybooks/CLIENTE.cpy`: copybook usado por el programa.
- `tools/mock_dbb.py`: detecta programa/dependencias y produce `.load` ficticios en `.tar.gz`.
- `tools/mock_sonar.py`: implementa unas pocas reglas didácticas y bloquea por errores.
- `tools/mock_nexus.py`: almacena por versión, checksum e impide sobrescribir una versión con contenido distinto.
- `tools/mock_wazi.py`: recupera el archivo versionado, verifica integridad y simula despliegue.
- `tools/smoke_test.py`: comprueba el resultado del despliegue.
- `tools/run_tests.py`, `tests/`: pruebas unitarias y reporte compatible con JUnit.

## Limitaciones importantes

- DBB real compila y realiza construcción incremental en un entorno preparado de z/OS. Aquí no se ejecuta ningún compilador COBOL ni se genera un módulo ejecutable.
- SonarQube real tiene servidor, scanner, perfiles de calidad e historial. Aquí solo se aplican reglas de ejemplo.
- Nexus real ofrece repositorios por formato, autenticación, API HTTP y políticas. Aquí usamos almacenamiento local versionado.
- Wazi Deploy real interpreta paquetes y descriptores, se conecta al objetivo y controla despliegues reales. Aquí solo se crean carpetas simuladas.
- Los ambientes simulados están en un mismo Linux. En producción normalmente son destinos y credenciales separados.

Este laboratorio está diseñado para **comprender la orquestación**, no para reproducir íntegramente el comportamiento interno de los productos comerciales.
