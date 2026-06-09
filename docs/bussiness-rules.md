Reglas de negocio del blog — Referencia para el Chatbot RAG

Este documento es la fuente de verdad del chatbot que gestiona las solicitudes de clientes para crear, actualizar o eliminar entradas de blog en los sitios Amarte / Marte Website Builder. Cada regla aquí recogida refleja la implementación técnica real del sistema de blog y debe seguirse de forma exacta.

---

## Descripción general del sistema

Los sitios Amarte utilizan un sistema de blog estático basado en ficheros, construido sobre Vite + React 18 + TypeScript + react-i18next. No existe base de datos, panel CMS ni API en tiempo real para el contenido del blog. Todos los artículos viven como entradas en ficheros JSON de traducción versionados:

- `src/i18n/locales/es/blog.json` — contenido en español (idioma principal)
- `src/i18n/locales/en/blog.json` — contenido en inglés (opcional, espeja la estructura española)

Cualquier cambio en el blog requiere editar esos ficheros, reconstruir el sitio y desplegarlo. Por eso cada solicitud de blog se convierte en un ticket de seguimiento.

---

## Proceso conversacional

Toda solicitud de blog sigue este flujo de tres pasos. El chatbot no avanza al siguiente paso hasta completar el actual.

---

### Paso 1 — Recopilación del contenido mediante preguntas

El chatbot recoge la información del artículo haciendo preguntas una a una. El orden recomendado es:

1. **¿Para qué dominio es el artículo?**
   El dominio es el identificador del proyecto de blog (p.ej. `empresa.com`). Se usa para buscar tickets existentes en el paso 2 y para etiquetar el ticket final.

2. **¿Cuál es el título del artículo?**
   Máximo 90 caracteres. El chatbot deriva el slug automáticamente y lo muestra para confirmación.

3. **¿Cuál es la fecha de publicación?**
   Formato ISO (YYYY-MM-DD). Si el cliente no especifica, usar la fecha de hoy.

4. **¿Tienes un resumen o excerpt?**
   1–3 frases, máximo 300 caracteres. Si no lo proporciona, pedirlo o generarlo a partir del body.

5. **¿Quién es el autor?**
   Nombre completo. Por defecto, el nombre de la empresa si no se especifica.

6. **¿Tienes imagen de cabecera?**
   Si sí: recoger nombre de fichero y texto alternativo (`alt`). Si no: continuar sin `heroImg`.

7. **¿Qué etiquetas quieres usar?**
   Proponer etiquetas de la taxonomía aprobada según el contenido. Confirmar con el cliente.

8. **¿Cuál es el contenido del artículo (body)?**
   Texto plano. El chatbot convierte saltos de párrafo a `\n\n`. Sin HTML ni Markdown.

9. **¿El sitio es bilingüe (ES + EN)?**
   Si sí: preguntar si el cliente tiene versión en inglés. Si no, crear la entrada en inglés con nota de traducción pendiente.

El chatbot no crea ningún ticket hasta tener confirmados todos los campos obligatorios: `dominio`, `título`, `fecha`, `slug` y `body`.

---

### Paso 2 — Verificación de tickets existentes para el dominio

Antes de crear el ticket, el chatbot busca en Jira tickets abiertos para el mismo dominio y operación:

- **Identificador de búsqueda**: el dominio (p.ej. `empresa.com`)
- **JQL sugerida**: `project = SUP AND text ~ "{dominio}" AND statusCategory != Done ORDER BY created DESC`
- Si se encuentra un ticket abierto para el mismo dominio y slug → informar al cliente y preguntar si quiere actualizar ese ticket en lugar de crear uno nuevo.
- Si no hay tickets previos → continuar al Paso 3.

Este paso evita crear tickets duplicados para el mismo artículo.

---

### Paso 3 — Creación del ticket con todos los campos

Una vez recopilada y verificada toda la información, el chatbot muestra un resumen completo y solicita confirmación explícita antes de crear el ticket:

```
📋 Voy a crear el siguiente ticket en Jira:

   Dominio:    {dominio}
   Operación:  INSERT
   Slug:       {slug}
   Título:     {titulo}
   Fecha:      {fecha}
   Etiquetas:  {tags}
   Autor:      {autor}
   Idioma(s):  {ES | EN | Ambos}

¿Lo confirmo? (sí / no)
```

Solo tras respuesta afirmativa se crea el ticket con la plantilla definida en la sección "Plantilla de ticket". El cliente recibe el número de referencia y el SLA comprometido (24 horas laborables).

Si una solicitud llega un viernes después de las 17:00 (Europe/Madrid) o durante el fin de semana, el plazo de 24 horas comienza el siguiente día laborable a las 09:00.

---

## Estructura de datos de un artículo

Cada artículo se almacena como una clave de primer nivel dentro de `blog.json`. La clave es el slug — el identificador de URL del artículo.

### Estructura completa

```json
{
  "mi-slug-de-articulo": {
    "title": "Título del artículo",
    "date": "2026-06-09",
    "excerpt": "Resumen breve que se muestra en el listado y en las páginas de etiquetas.",
    "authorName": "Nombre del autor",
    "heroImg": {
      "src": "/uploads/blog/nombre-imagen.jpg",
      "alt": "Texto alternativo descriptivo para accesibilidad",
      "caption": "Pie de foto opcional que se muestra bajo la imagen"
    },
    "tags": [
      { "slug": "seo", "label": "SEO" },
      { "slug": "ia", "label": "IA" }
    ],
    "body": "Primer párrafo.\n\nSegundo párrafo.\n\nTercer párrafo."
  }
}
```

### Referencia de campos

| Campo | Obligatorio | Tipo | Reglas |
|-------|-------------|------|--------|
| slug (la clave) | Sí | string | Kebab-case, minúsculas, sin acentos, sin espacios. Único en el fichero. Ejemplo: `como-mejorar-tu-seo-en-2026` |
| title | Sí | string | Encabezado H1 y título en la pestaña del navegador. Máximo 90 caracteres recomendado. |
| date | Sí | string | Formato ISO 8601: YYYY-MM-DD. Controla el orden en el listado del blog. |
| excerpt | No (muy recomendado) | string | 1–3 frases, máximo 300 caracteres. Se muestra en el listado y en las páginas de filtro por etiqueta. Si falta, no aparece previsualización en el listado. |
| authorName | No | string | Nombre completo del autor. Se muestra en la cabecera del artículo. |
| heroImg.src | No | string | Ruta absoluta que comienza por `/uploads/blog/`. El fichero debe estar desplegado en el directorio público. Si no hay imagen, omitir el bloque `heroImg` completo. |
| heroImg.alt | Sí si heroImg presente | string | Texto descriptivo para accesibilidad y SEO. Nunca dejarlo vacío. |
| heroImg.caption | No | string | Pie de foto breve. Puede ser cadena vacía `""` u omitirse. |
| tags | No (muy recomendado) | array | Array de objetos de etiqueta `{ slug, label }`. Ver reglas de etiquetas más abajo. |
| body | No (muy recomendado) | string | Contenido principal del artículo. Párrafos separados por `\n\n`. Sin etiquetas HTML. |

---

## Reglas del slug (identificador de URL)

El slug es tanto la clave JSON como el segmento de ruta en la URL. No puede modificarse tras la publicación sin romper los enlaces existentes (y la indexación en buscadores).

**Reglas:**

- Solo minúsculas: `como-usar-ia`, no `Como-Usar-IA`
- Guiones como separadores de palabras: `seo-local-para-pymes`, no guiones bajos ni espacios
- Sin caracteres acentuados: `optimizacion`, no `optimización`; `educacion`, no `educación`
- Sin caracteres especiales: nada de `?`, `&`, `#`, `%`, `.`, `/`
- Breve y descriptivo: apuntar a 3–7 palabras significativas
- Debe ser único entre todos los artículos del fichero — el chatbot debe verificar que ningún artículo existente usa el mismo slug antes de confirmar una solicitud de creación

**Ejemplos válidos:** `discovery-gap-visibilidad-digital`, `internacionalizacion-pagina-web`, `de-seo-a-geo-2026`

---

## Reglas de etiquetas

Las etiquetas son la forma principal en que los lectores navegan por contenido relacionado. Aparecen en la página del artículo y activan la página de filtro `/blog/tag/{tagSlug}`. Definirlas incorrectamente rompe la navegación por etiquetas.

### Estructura de un objeto etiqueta

```json
{ "slug": "seo-local", "label": "SEO Local" }
```

El slug es el identificador compatible con URLs; el label es el nombre legible para mostrar.

### Reglas del slug de etiqueta

- Minúsculas, kebab-case, sin acentos: `seo-local`, no `SEO Local` ni `seo_local`
- El slug de la etiqueta aparece en la URL: `/blog/tag/seo-local`
- Reutilizar slugs de etiquetas existentes siempre que sea posible. Crear un slug nuevo cuando ya existe uno equivalente fragmenta el índice de etiquetas.
- El slug es sensible a mayúsculas: `ia` e `IA` serían dos etiquetas distintas. Usar siempre minúsculas.

### Reglas del label de etiqueta

- El label es el nombre de visualización; puede usar capitalización natural: "SEO", "IA", "Core Web Vitals"
- Para términos técnicos de una sola palabra, usar la forma canónica: "SEO" no "seo", "IA" no "Ia"
- Para labels de varias palabras, usar mayúscula inicial solo en nombres propios: "Agentes conversacionales", "Kit Digital", "Core Web Vitals"
- El label para un slug dado debe ser coherente en todos los artículos. Si `seo` tiene el label "SEO" en un artículo, debe ser "SEO" en todos — los labels inconsistentes crean nombres duplicados en el índice de etiquetas.

### Taxonomía de etiquetas aprobada

Usar etiquetas de esta lista siempre que el contenido encaje. Solo crear una etiqueta nueva si ninguna de estas aplica.

**Tecnología e IA**

| Slug | Label |
|------|-------|
| ia | IA |
| agentes-conversacionales | Agentes conversacionales |
| chatgpt | ChatGPT |
| gemini | Gemini |
| llmstxt | llms.txt |
| cms | CMS |
| wordpress | WordPress |
| tina | Tina CMS |
| sanity | Sanity |
| strapi | Strapi |
| websitebuilder | Website Builder |
| martewebsitebuilder | Marte Website Builder |
| constructorweb | Constructor web |

**SEO y visibilidad**

| Slug | Label |
|------|-------|
| seo | SEO |
| seo-tecnico | SEO técnico |
| seo-local | SEO local |
| geo | GEO |
| posicionamiento-ia | Posicionamiento IA |
| discovery | Discovery |
| optimizacion | Optimización |
| core-web-vitals | Core Web Vitals |

**Desarrollo web y rendimiento**

| Slug | Label |
|------|-------|
| velocidad | Velocidad |
| velocidad-web | Velocidad web |
| rendimiento | Rendimiento |
| design | Diseño |
| ux | UX |
| accesibilidad | Accesibilidad |
| i18n | i18n |
| internacionalizacion | Internacionalización |

**Negocio y marketing**

| Slug | Label |
|------|-------|
| pymes | PYMEs |
| ecommerce | E-commerce |
| kit-digital | Kit Digital |
| case-exito | Caso de éxito |
| ia-negocios | IA para negocios |
| innovacion | Innovación |
| edih | EDIH |
| educacion | Educación |
| marte | Marte |

**Recomendación:** usar entre 2 y 5 etiquetas por artículo. Más de 6 diluye la señal. Menos de 2 hace el artículo difícil de descubrir por tema.

### Crear una etiqueta nueva

Cuando el contenido genuinamente no encaje en ninguna etiqueta existente, el chatbot puede proponer una nueva. Reglas para la creación de etiquetas nuevas:

- Confirmar que no existe ningún sinónimo ya en uso (p.ej., no crear `inteligencia-artificial` si ya existe `ia`)
- El nuevo slug debe seguir las mismas reglas de kebab-case, minúsculas y sin acentos
- Documentar el nuevo slug y label en este fichero bajo la tabla de taxonomía anterior cuando el ticket se resuelva

---

## Reglas del contenido del cuerpo (body)

El campo `body` contiene el texto completo del artículo. Se renderiza con CSS `whitespace-pre-line`, lo que significa:

- `\n` produce un salto de línea
- `\n\n` produce un salto de párrafo
- No se interpretan etiquetas HTML — no usar `<b>`, `<p>`, `<ul>` ni ningún marcado
- No se renderiza Markdown — no usar `**negrita**`, `# encabezados` ni `- listas`; aparecerían como caracteres literales

### Directrices de contenido (estándares de experto en desarrollo web)

Un cuerpo de texto bien estructurado mejora tanto la legibilidad como el GEO (Generative Engine Optimization — cómo los motores de búsqueda con IA citan el contenido). Aplicar estas reglas al revisar o generar contenido:

- **Estructurar la narrativa en secciones claras.** Usar un ritmo de párrafos natural: introducir el tema, desarrollar 3–5 puntos principales, cerrar con una llamada a la acción o conclusión. Cada párrafo debe tener entre 3 y 6 líneas.

- **Escribir los títulos de sección como frases en texto plano, no en Markdown.** Como no se renderiza marcado, los títulos se escriben como una frase corta en su propia línea seguida de una línea en blanco. Ejemplo:

  ```
  Por qué el rendimiento web impacta en tus ventas

  Un segundo de retraso en la carga de tu web...
  ```

- **Sin separadores horizontales.** No insertar `---` como separador visual. Separar secciones con una línea en blanco (`\n\n`).

- **Longitud mínima viable:** 400 palabras para que el artículo tenga valor SEO. Longitud ideal: 800–1 500 palabras.

- **Evitar contenido duplicado.** El excerpt suele ser el primer párrafo del artículo. No pegarlo literalmente en el body salvo que el artículo sea muy corto. El contenido duplicado entre excerpt y body perjudica la indexación en buscadores.

- **Lenguaje sencillo, frases directas.** Evitar la jerga corporativa. Preferir ejemplos concretos a afirmaciones abstractas.

---

## Operaciones

### INSERT — Crear un nuevo artículo

El chatbot debe recopilar y validar todo lo siguiente antes de crear un ticket:

- **Título** — obligatorio, máximo 90 caracteres
- **Fecha** — obligatorio, formato ISO. Por defecto, la fecha de hoy si el cliente no especifica.
- **Slug** — derivado del título por el chatbot (minúsculas, kebab-case, sin acentos). Mostrar el slug propuesto al cliente y confirmar antes de crear el ticket. Verificar que no exista ya.
- **Excerpt** — muy recomendado. Pedir al cliente un resumen de 1–3 frases si no se proporciona.
- **Nombre del autor** — preguntar al cliente; por defecto, el nombre de su empresa/contacto si no especifica.
- **Imagen de cabecera** — preguntar si dispone de un fichero de imagen. Si es así, recoger el nombre de fichero y el texto alternativo. Si no, el artículo se crea sin imagen de cabecera.
- **Etiquetas** — obligatorio. Proponer etiquetas de la taxonomía aprobada según el contenido del artículo. Confirmar con el cliente antes de añadirlas.
- **Body** — obligatorio. Recoger el texto completo del artículo en texto plano; el chatbot convierte los saltos de párrafo a `\n\n`.

Tanto `es/blog.json` (español) como `en/blog.json` (inglés) deben actualizarse si el sitio es multilingüe. Preguntar al cliente si dispone del contenido en inglés. Si no, el fichero inglés recibe la misma entrada con una nota indicando que la traducción está pendiente.

### UPDATE — Editar un artículo existente

El chatbot debe:

- Identificar el artículo por slug o título. Si el cliente no conoce el slug, buscar por título.
- Preguntar qué campo(s) se desean cambiar. Mostrar los valores actuales de los campos que el cliente quiere editar para que pueda confirmar los cambios.
- **Los cambios de slug no están permitidos en artículos publicados.** Si el cliente solicita cambiar el slug, explicar que rompe los enlaces existentes y ofrecer crear un artículo nuevo en su lugar.
- Los cambios de fecha están permitidos y actualizan la posición en el listado del blog.
- Los cambios de etiquetas (añadir, eliminar, renombrar) siguen las mismas reglas de etiquetas que INSERT.
- Los cambios en el body reemplazan el campo completo — las ediciones parciales en línea no están soportadas; el cliente debe proporcionar el texto completo actualizado.

### DELETE — Eliminar un artículo

Antes de confirmar la eliminación, el chatbot debe:

- Identificar el artículo por slug o título y mostrar al cliente el título y la fecha para confirmación.
- Advertir que la eliminación es permanente y que cualquier enlace externo al artículo devolverá un 404.
- Exigir una frase de confirmación explícita del cliente (p.ej., "Sí, elimina este artículo").
- Eliminar de ambos `es/blog.json` y `en/blog.json`.

La eliminación suave (ocultar un artículo sin eliminarlo) no está soportada de forma nativa. Si el cliente desea ocultar temporalmente un artículo, la única opción es eliminarlo y volver a crearlo más adelante.

---

## Lista de validación previa al ticket

Antes de crear un ticket, el chatbot debe verificar:

- [ ] El slug está en minúsculas, kebab-case, sin acentos ni caracteres especiales
- [ ] El slug no existe ya (para operaciones INSERT)
- [ ] La fecha está en formato YYYY-MM-DD
- [ ] El título está presente y tiene menos de 90 caracteres
- [ ] Si se incluye heroImg, el campo alt no está vacío
- [ ] Todas las etiquetas usan slugs en minúsculas y labels coherentes que coinciden con la taxonomía aprobada
- [ ] El body usa `\n\n` para los saltos de párrafo, sin HTML ni Markdown
- [ ] Ambos ficheros de idioma están contemplados si el sitio es bilingüe
- [ ] El cliente ha confirmado todos los valores de los campos antes de crear el ticket

---

## Plantilla de ticket

Al crear el ticket en el gestor de incidencias, usar esta estructura:

```
Título: [BLOG] [INSERT|UPDATE|DELETE] {título del artículo} — {dominio del sitio}

Sitio:          {dominio}
ID de cliente:  {crm_id}
Operación:      INSERT | UPDATE | DELETE
Slug:           {slug}
Idioma(s):      ES | EN | Ambos

Campos a modificar:
- title: "..."
- date: "..."
- excerpt: "..."
- authorName: "..."
- heroImg.src: "/uploads/blog/..."
- heroImg.alt: "..."
- tags: [{ slug: "...", label: "..." }, ...]
- body: (ver texto adjunto)

SLA: 24 horas laborables desde la creación del ticket
Confirmado por el cliente: Sí
```

---

## Preguntas frecuentes para el chatbot

**¿Puede el cliente publicar el artículo por su cuenta?** No. El blog es un fichero estático — no hay panel CMS ni acceso de administrador. Todos los cambios pasan por el equipo de Marte a través del proceso de tickets.

**¿Puede el cliente añadir imágenes directamente?** No. Los ficheros de imagen deben subirse al directorio `/public/uploads/blog/` del sitio durante el despliegue. El cliente debe proporcionar el fichero de imagen y el chatbot captura el nombre del fichero; el equipo gestiona la subida.

**¿Qué ocurre si el cliente quiere programar un artículo para una fecha futura?** Establecer el campo `date` en la fecha futura deseada. El artículo aparecerá en el listado del blog ordenado por esa fecha, pero será técnicamente visible en el JSON en cuanto se realice el despliegue. La publicación programada real (ocultar hasta una fecha futura) no está soportada.

**¿Puede un artículo existir solo en español y no en inglés?** Sí. Si el sitio es bilingüe, un artículo que existe en `es/blog.json` pero no en `en/blog.json` simplemente no aparecerá cuando el usuario navegue en inglés. Esta es una situación aceptable.

**¿Cuál es la longitud máxima del body?** No hay límite estricto. Los artículos de hasta 3 000 palabras son habituales. Los artículos muy largos (5 000+ palabras) pueden afectar al rendimiento de carga de la página — dividirlos en una serie si el contenido es tan extenso.

**¿Puede un artículo no tener etiquetas?** Técnicamente sí. En la práctica, un artículo sin etiquetas es invisible en la navegación por etiquetas y más difícil de descubrir. Siempre recomendar al menos 2 etiquetas.
