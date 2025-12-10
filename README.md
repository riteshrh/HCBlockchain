# Healthcare Blockchain - Secure Medical Records Prototype

A blockchain-based prototype for secure, patient-controlled medical records. This project decentralizes Electronic Health Records (EHR) to give patients ownership of their health data while maintaining security and enabling seamless sharing with healthcare providers.

## The Problem

Current EHR systems are centralized, creating single points of failure and making data vulnerable to breaches. Patient information is fragmented across multiple hospitals and providers, making collaboration difficult and limiting patient control over their own health data.

## Our Solution

Instead of storing entire medical records on the blockchain (which would be expensive and raise privacy concerns), we store cryptographic hashes and access logs on-chain. The actual encrypted medical data lives off-chain. This approach gives us:

- **Tamper-proof audit trail** of all record access and consent changes
- **Patient ownership** with easy consent management via smart contracts
- **Secure encryption** using AES-256 for sensitive medical data
- **Interoperability** through HL7 FHIR-compliant REST APIs
- **Privacy** by keeping medical data off-chain and encrypted

## How It Works

### System Overview

This system uses a hybrid approach: medical records are stored encrypted in a traditional database, while blockchain stores cryptographic hashes and access logs. This gives you the security and immutability of blockchain without storing sensitive data on-chain.

### User Roles

The system has three types of users:

1. **Patients** - Own their medical records and control who can access them
2. **Providers** - Healthcare professionals who need patient consent to view records
3. **Admins** - System administrators who manage providers and monitor the system

### Complete Flow

#### 1. Registration

**Patient Registration:**
- Patient signs up with name, email, and password
- System creates a unique identity with cryptographic keys
- Patient can immediately start uploading records

**Provider Registration:**
- Provider signs up with name, email, and password
- System creates a unique identity with cryptographic keys
- Provider status is "Pending" until admin approves
- Once approved, provider can receive consent from patients

**Admin Account:**
- Created separately using a secure script
- Admins can approve/reject providers and monitor system health

#### 2. Patient Uploads a Medical Record

When a patient uploads a medical record:
- The record content is encrypted using AES-256 encryption
- A cryptographic hash (fingerprint) of the record is generated
- The encrypted record is stored in the database
- The hash is stored on the blockchain as a transaction
- A new block is created on the blockchain containing this transaction
- The blockchain chain grows by one block

**Why this matters:** The hash on blockchain proves the record hasn't been tampered with. If anyone changes the record, the hash won't match.

#### 3. Patient Grants Consent to Provider

When a patient wants to share a record with a provider:
- Patient selects which provider and which record(s) to share
- Patient can set expiration date for the consent
- A consent transaction is created and stored in the database
- The consent transaction is also recorded on the blockchain
- A new block is created on the blockchain containing this consent transaction
- The blockchain chain grows by one block

**Why this matters:** The blockchain provides an immutable audit trail of all consent grants and revocations.

#### 4. Provider Accesses Patient Record

When a provider wants to view a patient's record:
- System checks if the provider has valid consent from the patient
- If consent exists and hasn't expired, access is granted
- The encrypted record is retrieved from the database
- The record is decrypted using the encryption key
- Provider can view the decrypted content
- An access log entry is created (stored in database and optionally on blockchain)

**Why this matters:** Providers can only access records they have explicit consent for. All access attempts are logged.

#### 5. Patient Revokes Consent

If a patient wants to stop sharing with a provider:
- Patient revokes consent through the consent management interface
- The consent status is updated to "revoked" in the database
- A revocation transaction is recorded on the blockchain
- A new block is created on the blockchain
- Provider can no longer access that patient's records

**Why this matters:** Patients have full control. They can grant and revoke access at any time.

### Blockchain in This System

**What is stored on blockchain:**
- Cryptographic hashes of medical records (proof of integrity)
- Consent transactions (grants and revocations)
- Access logs (who accessed what and when)

**What is NOT stored on blockchain:**
- Actual medical record content (too sensitive and expensive)
- Patient personal information (privacy protection)
- Encryption keys (security protection)

**How the blockchain works:**
- All users share the same blockchain chain
- Every action (record upload, consent grant, etc.) creates a transaction
- Transactions are grouped into blocks
- Each block is cryptographically linked to the previous block
- Once a block is added, it cannot be changed (immutability)
- Everyone can verify the chain to ensure no tampering occurred

**Example:** If Patient A uploads a record, Patient B grants consent, and Patient C uploads another record, all three actions are recorded in the same blockchain chain. The chain grows with each action, creating a complete audit trail.

### Security Features

**Encryption:**
- All medical records are encrypted using AES-256 before storage
- Only authorized users with proper consent can decrypt and view records
- Encryption keys are securely managed and never stored on blockchain

**Access Control:**
- Role-based access control ensures users can only perform actions allowed for their role
- Patients can only access their own records
- Providers need explicit consent to access patient records
- Admins can manage providers but cannot access patient records

**Blockchain Security:**
- Cryptographic hashing ensures data integrity
- Immutable audit trail prevents tampering
- Proof-of-work mechanism secures block creation
- All transactions are verifiable by anyone

### Admin Dashboard

Admins have access to a special dashboard where they can:
- View blockchain status and health
- See system statistics (chain length, pending transactions, etc.)
- Approve or reject provider registration requests
- Monitor system operations

### Key Benefits

1. **Patient Control:** Patients own their data and decide who can access it
2. **Security:** Military-grade encryption protects sensitive medical information
3. **Transparency:** Blockchain provides an immutable audit trail
4. **Privacy:** Medical content stays off-chain, only hashes and logs are on-chain
5. **Trust:** Cryptographic proofs ensure data hasn't been tampered with
6. **Compliance:** Complete audit trail helps with healthcare regulations

## Tech Stack

- **Backend**: Python + FastAPI
- **Blockchain**: SimpleBlockchain (Python-native implementation)
- **Database**: PostgreSQL (Supabase)
- **Encryption**: AES-256
- **APIs**: RESTful
- **Frontend**: React with Vite

## How to Run the Project

### Prerequisites

Before running the project, ensure you have the following installed:

- **Python 3.13** or higher
- **Node.js 18** or higher (for frontend)
- **PostgreSQL** database (or Supabase account)
- **Git**

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd HCBlockchain
```

### Step 2: Backend Setup

#### 2.1 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2.2 Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2.3 Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Database Configuration
DB_HOST=your-database-host.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-database-password

# Security Keys
JWT_SECRET=your-secret-jwt-key-change-in-production
ENCRYPTION_KEY=your-32-byte-encryption-key
JWT_ALGORITHM=HS256
JWT_EXPIRY=3600

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Configuration
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Blockchain Configuration
BLOCKCHAIN_PROVIDER=bigchaindb
BLOCKCHAIN_NODE=http://localhost:9984
```

**Important:** Generate secure keys for `JWT_SECRET` and `ENCRYPTION_KEY`. The encryption key must be exactly 32 bytes.

#### 2.4 Initialize Database

```bash
cd backend
alembic upgrade head
```

This will create all necessary database tables.

#### 2.5 Create Admin Account (Optional)

```bash
python scripts/create_admin.py
```

Follow the prompts to create an admin account.

#### 2.6 Run Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at:
- **API Base URL**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

### Step 3: Frontend Setup

#### 3.1 Navigate to Frontend Directory

```bash
cd frontend
```

#### 3.2 Install Dependencies

```bash
npm install
```

#### 3.3 Configure API Endpoint

Ensure the frontend is configured to connect to the backend API. The default configuration should point to `http://localhost:8000`.

#### 3.4 Run Frontend Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (Vite default port).

### Step 4: Access the Application

1. **Patient Portal**: `http://localhost:5173` - Register as a patient and start uploading records
2. **Provider Portal**: `http://localhost:5173` - Register as a provider (requires admin approval)
3. **Admin Portal**: `http://localhost:5173` - Login with admin credentials to manage providers

### Quick Start Commands

**Run everything in one go:**

```bash
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Testing the System

1. **Register as Patient**:
   - Go to registration page
   - Create account with email and password
   - Login and upload a medical record

2. **Register as Provider**:
   - Register with provider role
   - Wait for admin approval (or approve yourself if you're admin)

3. **Grant Consent**:
   - Patient logs in and grants consent to provider
   - Consent is recorded on blockchain

4. **Access Records**:
   - Provider logs in and accesses patient records (with consent)
   - System verifies blockchain integrity before access

5. **View Blockchain**:
   - Access blockchain explorer at `http://localhost:8000/blockchain-explorer`
   - View all blocks, transactions, and tampering events

### Troubleshooting

**Backend won't start:**
- Check if port 8000 is available: `lsof -i :8000`
- Verify database connection in `.env` file
- Ensure all dependencies are installed: `pip install -r requirements.txt`

**Frontend won't start:**
- Check if Node.js is installed: `node --version`
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check if port 5173 is available

**Database connection errors:**
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists and is accessible

**Blockchain errors:**
- The system uses a custom blockchain that initializes automatically
- Check `backend/blockchain_data.json` exists after first run
- Verify file permissions for blockchain storage

### Production Deployment

For production deployment:

1. Set `API_RELOAD=false` in `.env`
2. Use a production WSGI server like Gunicorn:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
3. Configure proper CORS origins
4. Use environment variables for all secrets
5. Set up proper database backups
6. Configure HTTPS/SSL certificates

For more detailed setup instructions, see [SETUP_GUIDE.md](./docs/SETUP_GUIDE.md).

## Team

- **Krina Trivedi** - Scrum Master & Blockchain Developer
- **Ritesh Revansiddappa Honnalli** - Backend Developer & Architect
- **Vivek Reddy Pulakannti** - UI/UX Developer & QA