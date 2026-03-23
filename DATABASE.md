# Database Schema

## Overview
The database uses **PostgreSQL** in production and **SQLite** for local development. Both are handled via the SQLAlchemy ORM for seamless switching.

## Tables

### 1. `users`
Stores user account information.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | SERIAL / INT | PK | Unique ID |
| `username` | VARCHAR(50) | Unique | Login name |
| `email` | VARCHAR(120) | Unique, Not Null | Contact email |
| `password_hash` | VARCHAR(255) | Not Null | Bcrypt hash |
| `role_id` | INT | FK -> roles.id | Role reference (1=Admin, 2=User) |
| `created_at` | TIMESTAMP | Default Now | Creation date |

### 2. `recommendations`
Stores prediction history.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INT | PK, Auto Inc | Unique ID |
| `user_id` | INT | FK -> users.id | User reference |
| `crop_type` | VARCHAR(50) | Not Null | Input crop |
| `nitrogen` | FLOAT | Not Null | Input N |
| `phosphorus` | FLOAT | Not Null | Input P |
| `potassium` | FLOAT | Not Null | Input K |
| `ph` | FLOAT | Not Null | Input pH |
| `prediction` | VARCHAR(100) | Not Null | ML Output |
| `confidence` | FLOAT | Not Null | Confidence % |
| `timestamp` | DATETIME | Default Now | Date of test |

### 3. `audit_logs` (Optional/Future)
Tracks system usage and security events.

## Relationships
- **One-to-Many**: `User` can have multiple `Recommendations`.
- **Cascade Delete**: Deleting a User deletes their Recommendations.

## Indexes
- `idx_users_email`: For faster login lookup.
- `idx_recommendations_user_id`: For fetching history efficiently.
