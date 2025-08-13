
────────────────────────────────────────
PROMPT
────────────────────────────────────────
You are an expert full-stack engineer.
Create a complete, production-grade, enterprise-level web application using the following exact specifications.
Do not add TODOs, placeholders, or examples—every file must be fully functional, optimized, and future-proof.

1. TECH STACK
   • Backend: Node.js 18, Express 4, MongoDB 7, Mongoose, JWT auth, bcrypt, Joi validation, Winston logging, Swagger docs, rate-limiting, Helmet, CORS, compression.
   • Frontend: React 18, Vite, Redux Toolkit, React-Router-DOM, Axios, Tailwind CSS.
   • Tooling: Docker & docker-compose, GitHub Actions CI (test on push/PR).

2. FUNCTIONAL REQUIREMENTS
   • User system: register, login, JWT, role-based access (user | admin).
   • Product CRUD: name, description, price, category, inStock flag, ownership.
   • Admin endpoints: list/delete any user.
   • Validation on all inputs; global error handler.
   • Soft performance: compound index on Product.name + category; unique index on User.email.
   • Logging: HTTP + app-level (Winston).
   • API docs: auto-generated Swagger UI at /api-docs.
   • Frontend pages: Home, Login, Register, User Dashboard, Admin Dashboard.
   • Responsive Tailwind UI.

3. PROJECT STRUCTURE & FILES
   server/
     ├── package.json
     ├── server.js
     ├── app.js
     ├── config/db.js
     ├── models/User.js
     ├── models/Product.js
     ├── controllers/authController.js
     ├── controllers/userController.js
     ├── controllers/productController.js
     ├── routes/auth.js
     ├── routes/user.js
     ├── routes/admin.js
     ├── routes/product.js
     ├── middleware/auth.js
     ├── middleware/errorHandler.js
     ├── middleware/validation.js
     ├── utils/logger.js
     ├── utils/swagger.js
     ├── .env
     ├── .gitignore
     └── Dockerfile

   client/
     ├── package.json
     ├── vite.config.js
     ├── tailwind.config.js
     ├── src/main.jsx
     ├── src/App.jsx
     ├── src/index.css
     ├── src/store/store.js
     ├── src/store/authSlice.js
     ├── src/services/api.js
     ├── src/services/auth.service.js
     ├── src/services/product.service.js
     ├── src/router/Router.jsx
     ├── src/components/Layout/Header.jsx
     ├── src/components/Auth/LoginForm.jsx
     ├── src/components/Auth/RegisterForm.jsx
     ├── src/components/Product/ProductList.jsx
     ├── src/components/Product/ProductForm.jsx
     ├── src/pages/HomePage.jsx
     ├── src/pages/LoginPage.jsx
     ├── src/pages/RegisterPage.jsx
     ├── src/pages/DashboardPage.jsx
     ├── src/pages/AdminPage.jsx
     └── Dockerfile (optional)

   docker-compose.yml
   .github/workflows/ci.yml

4. IMPLEMENTATION RULES
   • Use modern ES modules everywhere.
   • No console.log—use Winston.
   • All secrets via .env (never hard-code).
   • Use async/await; wrap async routes with try/catch → next(err).
   • Mongoose pre-save hook to hash passwords (bcrypt 12 rounds).
   • JWT expiry 7 days.
   • Rate-limit: 200 req / 15 min window.
   • All endpoints return JSON: { success, data, message }.
   • Frontend: Redux Toolkit slices + RTK Query-style services.
   • Responsive Tailwind components (no inline styles).
   • Docker: multistage builds for both services; compose includes MongoDB.

5. OUTPUT
Generate every file listed above exactly as specified.
When complete, output a single shell script named run.sh that:
   #!/usr/bin/env bash
   set -e
   npm --prefix server install
   npm --prefix client install
   docker-compose up --build

Ensure the entire codebase is ready for `git init && ./run.sh`.
