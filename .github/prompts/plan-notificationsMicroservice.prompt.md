# Plan: Implementación Microservicio de Notificaciones

Este plan detalla la creación del microservicio de notificaciones usando **Node.js** y **MongoDB**, diseñado para ser ligero, independiente y fácil de mantener.

### Tecnologías
- **Lenguaje:** Node.js (JavaScript) - Sencillo y eficiente para I/O.
- **Framework:** Express.js - Minimalista y robusto para APIs REST.
- **Base de Datos:** MongoDB - Ideal para documentos anidados (notificaciones dentro de usuarios).
- **ODM:** Mongoose - Para modelado de datos.
- **Autenticación:** JSON Web Tokens (JWT) + bcrypt para hashing de contraseñas.

### Estructura del Proyecto
El servicio vivirá en una carpeta `notifications/` separada del código Django.

```text
notifications/
├── src/
│   ├── config/
│   │   └── db.js           # Conexión a MongoDB
│   ├── controllers/
│   │   ├── authController.js       # Lógica de login/registro
│   │   └── notificationController.js # Lógica de notificaciones
│   ├── middleware/
│   │   └── authMiddleware.js       # Validación de JWT
│   ├── models/
│   │   └── User.js         # Esquema de Usuario con notificaciones embebidas
│   ├── routes/
│   │   ├── authRoutes.js
│   │   └── notificationRoutes.js
│   └── app.js              # Configuración de Express
├── .env                    # Variables (PORT, MONGO_URI, JWT_SECRET)
├── package.json
└── server.js               # Punto de entrada
```

### Modelo de Datos (MongoDB)

Usaremos un esquema de **documentos embebidos**. Cada usuario tendrá un array con sus notificaciones. Esto simplifica las lecturas (una sola query trae usuario y sus mensajes).

**Schema `User`:**
```javascript
{
  username: { type: String, required: true, unique: true },
  password: { type: String, required: true }, // Hashed
  role: { type: String, enum: ['admin', 'bodeguero', 'vendedor'] },
  notifications: [
    {
      _id: ObjectId,
      message: String,
      read: { type: Boolean, default: false },
      timestamp: { type: Date, default: Date.now }
    }
  ]
}
```

### Especificación de la API

#### 1. Autenticación
- `POST /api/auth/register`: Crea un usuario en el microservicio (útil para sincronizar usuarios desde Django o crear admins).
- `POST /api/auth/login`: Retorna un JWT para autenticar futuras peticiones.

#### 2. Gestión de Notificaciones
Todas requieren header `Authorization: Bearer <token>`.

- **Crear Notificación (Envío):**
  - `POST /api/notifications`
  - **Body:** `{ "message": "...", "targetRole": "bodeguero" }` o `{ "targetUsername": "..." }`
  - **Lógica:** Usa `updateMany` de MongoDB para insertar la notificación en el array de todos los usuarios que coincidan con el rol, o `updateOne` para un usuario específico.

- **Leer Mis Notificaciones:**
  - `GET /api/notifications`
  - Retorna el array `notifications` del usuario autenticado.

- **Marcar como Leída:**
  - `PUT /api/notifications/:id/read`
  - Actualiza el estado `read: true` de una notificación específica dentro del array del usuario.

- **Eliminar Notificación:**
  - `DELETE /api/notifications/:id`
  - Elimina la notificación del array usando el operador `$pull`.

### Pasos de Implementación
1.  **Inicializar Proyecto:** Crear carpeta, `npm init`, instalar dependencias (`express`, `mongoose`, `dotenv`, `jsonwebtoken`, `bcryptjs`).
2.  **Configurar DB:** Script de conexión a MongoDB (puede ser local o Atlas).
3.  **Definir Modelo:** Crear `User.js` con el esquema propuesto.
4.  **Implementar Auth:** Controladores para registro y login.
5.  **Implementar CRUD Notificaciones:** Lógica para enviar (push a array) y gestionar (pull/update de array).
6.  **Integración:** Probar endpoints con Postman/cURL.

### Consideraciones de Seguridad
- Las contraseñas se almacenarán hasheadas (bcrypt).
- El microservicio validará su propio JWT, independiente de Django.
- La aplicación Django actuará como un "cliente" de este microservicio (usando una cuenta de servicio o token de admin) para disparar las notificaciones.
