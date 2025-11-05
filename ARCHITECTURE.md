# System Architecture

## Overview

This document outlines the architecture for the Healthcare Blockchain prototype, detailing how the system components interact to provide secure, patient-controlled medical records management.

## System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐           │
│  │   Patient   │  │  Provider   │  │    Admin   │           │
│  │    Portal   │  │    Portal   │  │   Portal   │           │
│  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘           │
└─────────┼────────────────┼───────────────┼──────────────────┘
          │                │               │
          │          HTTPS/REST API        │
          │                │               │
┌─────────▼────────────────▼───────────────▼──────────────────┐
│                       API Gateway Layer                     │
│                    (FastAPI Application)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │   Auth   │  │ Records  │  │  Consent │  │   Audit  │     │
│  │  Service │  │ Service  │  │ Service  │  │  Service │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└─────────┬───────────────────────────────────────────────────┘
          │
          │
┌─────────▼────────────────────────────────────────────────────┐
│                    Business Logic Layer                      │
│  • Encryption/Decryption (AES-256)                           │
│  • Hash Generation (SHA-256)                                 │
│  • Smart Contract Interaction                                │
│  • RBAC (Role-Based Access Control)                          │
│  • FHIR Data Transformation                                  │
└─────────┬────────────────────────────────────────────────────┘
          │
          │
┌─────────▼──────────────┐          ┌─────────────────────────┐
│   Blockchain Layer     │          │     Storage Layer       │
│   (BigchainDB/         │          │   (PostgreSQL/MongoDB)  │
│    Multichain)         │          │                         │
│                        │          │  • Encrypted medical    │
│  • Asset Registration  │          │    records (off-chain)  │
│  • Consent Contracts   │          │  • User credentials     │
│  • Access Logging      │          │  • Metadata             │
│  • Audit Trail         │          │                         │
└────────────────────────┘          └─────────────────────────┘
```

## Core Components

### 1. Frontend Layer
**Technology**: HTML, CSS, JavaScript (React or Vue.js)

**Components**:
- **Patient Portal**: Registration, record upload, consent management, audit viewing
- **Provider Portal**: Login, patient search, record request, record viewing (with consent)
- **Admin Portal**: Provider approval, system monitoring

**Responsibilities**:
- User interface for all stakeholders
- Form validation and user input handling
- Displaying audit trails and access logs

---

### 2. API Gateway Layer (FastAPI)
**Technology**: Python, FastAPI

**Services**:

#### Authentication Service
- User registration and login
- JWT token generation and validation
- Cryptographic identity generation (public/private keys)
- Password hashing

#### Records Service
- Medical record upload and validation
- Hash generation (SHA-256)
- Integration with blockchain for hash storage
- Integration with storage layer for encrypted data
- Record retrieval and decryption

#### Consent Service
- Consent granting/revocation
- Smart contract interaction
- Consent status checking
- Provider access validation

#### Audit Service
- Blockchain querying for audit logs
- Access history retrieval
- Transaction filtering and formatting

---

### 3. Business Logic Layer
**Technology**: Python

**Key Modules**:

- **Encryption Module**:
  - AES-256 encryption for medical records
  - Key derivation and management
  - Secure key storage

- **Hash Generation**:
  - SHA-256 hash computation
  - Ensures data integrity

- **Smart Contract Interface**:
  - Consent contract deployment
  - Consent status queries
  - Access validation

- **Access Control**:
  - RBAC implementation
  - Permission checking
  - Role validation

- **FHIR Transformation**:
  - HL7 FHIR standard compliance
  - Data format conversion
  - Interoperability support

---

### 4. Blockchain Layer
**Technology**: BigchainDB or Multichain

**On-Chain Data**:
- Medical record hashes (SHA-256)
- Consent transactions
- Access logs (who accessed what, when)
- Provider-patient relationships

**Smart Contracts**:
- **Consent Management Contract**:
  - Consent granting
  - Consent revocation
  - Consent querying
  - Access validation

**Transaction Types**:
- Medical record hash registration
- Consent grant/revoke
- Access request/response logs

---

### 5. Storage Layer (Off-Chain)
**Technology**: PostgreSQL or MongoDB

**Stored Data**:
- **Encrypted medical records** (AES-256 encrypted)
- User credentials (hashed passwords)
- User metadata (name, role, registration date)
- Session information

**Access Pattern**:
- Records accessed only after blockchain validation
- Decryption happens only for authorized access
- Metadata indexes for fast querying

---

## Security Architecture

### Authentication Flow
```
1. User provides credentials → Auth Service
2. Credentials validated → Database check
3. JWT token generated → Returned to client
4. Subsequent requests include JWT token
5. Auth Service validates token on each request
```

### Encryption Scheme
```
Plain Record → AES-256 Encryption → Encrypted Storage (Off-Chain)
              ↓
          Hash Generation (SHA-256)
              ↓
          Blockchain Storage (Hash only)
```

### Access Control Flow
```
1. Provider requests record access
2. API checks blockchain for consent
3. If consent exists → Proceed to decrypt record
4. If no consent → Return access denied
5. Log access attempt to blockchain
```

---

## Data Flow Architecture

### Record Upload Flow
```
Patient uploads record
    ↓
API receives record
    ↓
Generate SHA-256 hash
    ↓
Encrypt record with AES-256
    ↓
Store encrypted record off-chain
    ↓
Store hash on blockchain
    ↓
Return success to patient
```

### Record Access Flow
```
Provider requests record
    ↓
API checks blockchain for consent
    ↓
If consent exists:
    ↓
    Retrieve encrypted record from off-chain DB
    ↓
    Validate provider's role and permissions
    ↓
    Decrypt record
    ↓
    Log access to blockchain
    ↓
    Return decrypted record to provider
```

### Consent Management Flow
```
Patient creates/updates consent
    ↓
API validates request
    ↓
Create/update smart contract on blockchain
    ↓
Blockchain records transaction
    ↓
Return success to patient
```

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | HTML/CSS/JS, React/Vue | User interfaces |
| API Gateway | FastAPI | RESTful API endpoints |
| Business Logic | Python | Encryption, hashing, validation |
| Blockchain | BigchainDB/Multichain | Immutable ledger, smart contracts |
| Storage | PostgreSQL/MongoDB | Encrypted off-chain data |
| Authentication | JWT | Secure token-based auth |
| Encryption | AES-256 | Data encryption |
| Hashing | SHA-256 | Data integrity |

---

## Deployment Architecture

```
                    Internet
                       ↓
              [ Load Balancer ]
                       ↓
            ┌──────────┴──────────┐
    [Frontend Server]     [API Server]
            │                    │
            │              ┌─────┴─────┐
            │         [Blockchain]  [Database]
            │                         
            └─────────────────────────┘
                  (Direct API calls)
```

---

## Scalability Considerations

- **Horizontal Scaling**: Frontend and API servers can be scaled independently
- **Database Sharding**: Patient data can be sharded by region or ID
- **Blockchain**: Use federated nodes for better throughput
- **Caching**: Redis for frequently accessed consent status
- **CDN**: For frontend static assets

