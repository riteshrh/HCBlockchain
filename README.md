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

## Tech Stack

- **Backend**: Python + FastAPI
- **Blockchain**: BigchainDB or Multichain
- **Encryption**: AES-256
- **APIs**: RESTful, HL7 FHIR compliant
- **Frontend**: Web-based UI for patients and providers

## Team

- **Krina Trivedi** - Scrum Master & Blockchain Developer
- **Ritesh Revansiddappa Honnalli** - Backend Developer & Architect
- **Vivek Reddy Pulakannti** - UI/UX Developer & QA

## Project Status

🚧 **Under Development** - ECE 574 Fall 2025

This is a prototype being developed using Agile methodology with 2-week sprints.

