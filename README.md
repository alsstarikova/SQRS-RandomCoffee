# SQRS-RandomCoffee

## Configuring Mail SMTP to send emails from a Python application

### 1. Create an "Application Password" in Mail Ru

- Open it https://id.mail.ru/security
- In the security section, find "Passwords for external applications" and create a password for the application (for example, "SQRS project") - you must select SMTP to send emails.
- Copy the generated password — you will need it in the settings.

### 2. Write the settings in `.env`
