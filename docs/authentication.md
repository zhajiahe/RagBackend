# Authentication

This application uses JWT (JSON Web Token) based authentication for API access.

## Features

- User registration and login
- JWT token generation and validation
- Password hashing with bcrypt
- Token-based API protection

## Endpoints

### Registration
- **POST** `/auth/register`
- Register a new user account

### Login
- **POST** `/auth/login`
- Authenticate user and receive JWT token

### Token
- **POST** `/auth/token`
- OAuth2 compatible token endpoint

## Usage

1. Register a new user or login with existing credentials
2. Use the returned JWT token in the `Authorization` header
3. Format: `Bearer <your-jwt-token>`

## Configuration

The JWT configuration can be customized via environment variables:

- `SECRET_KEY`: Secret key for JWT signing
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 1 week)

## Security

- Passwords are hashed using bcrypt
- JWT tokens have configurable expiration
- All protected endpoints require valid authentication 