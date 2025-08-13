# Olympus AI — User Guide (Non-Technical)

Welcome! This guide walks you through Olympus AI’s core features in plain language. You don’t need to be technical to follow along.

## 1. Signing in and your dashboard

- Open your browser to `http://localhost` (or your company URL).
- Click “Register” to create an account, or “Sign in” if you already have one.
- After signing in, you’ll see your dashboard with quick links to Products and (if you are an admin) the Admin area.

## 2. Browsing and managing products

- From the home page, filter by category, search by keywords, and page through results.
- Click “Add Product” to create a product. Fill out the form and submit.
- To edit or delete a product you own, click the buttons on the product card.
- Admins can see and manage all products and users.

## 3. Knowledge search (optional)

- Olympus AI can ingest and index documents. Ask your IT team to set up ingestion.
- Once ready, a Retrieval API answers similarity searches from your content.
- Typical use: search for paragraphs related to your query across a large corpus.

## 4. Safe local code tasks (Exec Service)

This is a “safe box” where small scripts can run. It’s great for tasks like formatting files, generating simple reports, or light data processing.

- Your IT team will give you an API key and the service URL, e.g. `http://localhost:8082`.
- Use the provided Postman collection `postman/exec-service.postman_collection.json`.
- In Postman:
  - Open the collection and set environment variable `EXEC_API_KEY` to your key.
  - Open the “Execute Local Code (Python)” request.
  - The request sends a small Python program to run in a secure container.
  - The code can only read/write inside its sandbox folder; it cannot access the rest of the system.
  - Click “Send” and you’ll get the output of the script (stdout/stderr) and an exit code.

Notes:

- Network is blocked by default. If a script needs internet access, your IT team must enable it and you must confirm it per request.
- Everything is logged, including what ran and the result, for compliance.

## 5. Controlled web automation (WebBot Service)

This allows the system to open pages, click buttons, type into forms, and take screenshots automatically. It runs in a “headless” browser you can’t see—but it behaves like a user would.

- Your IT team will give you an API key and service URL, e.g. `http://localhost:8083`.
- Use the provided Postman collection `postman/webbot-service.postman_collection.json`.
- In Postman:
  - Set environment variable `WEBBOT_API_KEY` to your key.
  - Open the “Interact Web (Navigate + Screenshot)” request.
  - The request includes a sequence of actions like “go to a URL” and “take a screenshot”.
  - Click “Send”. The screenshot will be saved inside the sandbox folder for later download.

Notes:

- Sensitive actions (typing passwords, file uploads, generating PDFs) require an extra confirmation.
- All actions are recorded for auditing.

## 6. Where are my files?

- The services use a shared sandbox folder on the server.
- Ask IT for the mapped location if you need to retrieve generated files (e.g., screenshots or CSVs).

## 7. Getting help

- If something doesn’t work or you see an error, contact IT. They can look at the audit logs to help.
- For product support or feature requests, reach out to your product owner.

## Appendix — Sample requests

### Exec Service (Python example)

```json
{
  "language": "python",
  "code": "print('hello from sandbox')",
  "workdir": "demo",
  "allow_network": false,
  "confirm_sensitive": true
}
```

### WebBot Service (Navigate + Screenshot)

```json
{
  "actions": [
    { "type": "goto", "url": "https://example.org" },
    { "type": "screenshot", "path": "shots/example.png" }
  ],
  "confirm_sensitive": true
}
```
