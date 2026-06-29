# PollGuard BD

PollGuard BD is an offline desktop assistant for a fictional paper-based
election demonstration. It is designed for polling officers—not voters—and
runs locally with Python, CustomTkinter, SQLite, `hashlib`, and Fernet
encryption from the `cryptography` package.

This COM668 AT3 project uses demonstration data only. It does **not** provide
internet voting, online monitoring, blockchain voting, national-election
integration, or access to real voter data.

## Features

- **Local officer login:** Authenticates credentials stored as salted,
  600,000-iteration PBKDF2-HMAC-SHA256 password hashes in SQLite.
- **Voter Logging:** Validates the entered ID, compares its SHA-256 digest with
  the local register, rejects unknown or duplicate voters, and atomically marks
  an eligible voter and issues one ballot.
- **Ballot Tracking:** Shows issued, cast, spoiled, and pending totals. An
  officer can select a pending ballot and mark it Cast or Spoiled. Every issue
  and status update is written to the ballot activity log.
- **Reports:** Shows turnout and ballot totals, then writes both a readable
  `.json` demonstration copy and a Fernet-encrypted `.pgbd` secure copy to
  `reports/generated_reports/`. The report also carries a SHA-256 integrity
  hash calculated from its canonical summary data.
- **Local persistence:** All election activity is stored in
  `database/pollguard.db`; no network connection is used at runtime.

## Project structure

```text
PollGurdBD/
├── app.py                         # Application entry point
├── config.py                      # Local paths and app settings
├── security.py                    # Password, voter ID, and report hashing
├── voter_verification.py          # Voter ID input validation
├── database/
│   ├── db_init.py                 # Database setup command
│   ├── schema.py                  # Tables and fictional seed data
│   └── repository.py              # SQLite data-access layer
├── services/
│   ├── auth_service.py            # Login application logic
│   ├── election_service.py        # Voter and ballot use cases
│   ├── encryption_service.py      # Local Fernet encryption/key handling
│   └── report_service.py          # Hashed JSON and encrypted report creation
├── ui/
│   └── views.py                   # CustomTkinter screens
├── tests/
│   └── test_election_service.py   # Core rule tests
└── reports/generated_reports/     # Generated local JSON reports
```

## Setup

Python 3.9 or newer is recommended. If your system provides `python3` instead
of `python` (common on macOS), use `python3` in the commands below.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\activate
```

The setup installs CustomTkinter and `cryptography`. PollGuard BD itself makes
no internet requests and can be demonstrated fully offline afterward.

## Initialize the database

From the project root, run:

```bash
python database/db_init.py
```

This creates `database/pollguard.db`, all five required tables, two officer
accounts, and 15 fictional voter records. Re-running the command is safe: it
keeps existing activity. To deliberately erase the local demonstration and
start again:

```bash
python database/db_init.py --reset
```

## Run the desktop app

```bash
python app.py
```

The app also checks the schema at startup without deleting existing records.

## Demo credentials and voter IDs

Primary demonstration login:

```text
Username: admin
Password: admin123
```

Alternative login:

```text
Username: officer1
Password: pollguard123
```

Fictional voter IDs range from `1000000001` through `1000000015`. These values
exist solely for the software demonstration. The database stores SHA-256
digests and masked references rather than these entered identifiers.

## Exact COM668 AT3 demonstration flow

Before presenting, reset the fictional data and start the application:

```bash
python database/db_init.py --reset
python app.py
```

Then demonstrate these steps in order:

1. Explain that the machine is offline and the application uses only its local
   SQLite database. Sign in with `admin` / `admin123`.
2. Open **Voter Logging**. Submit an empty value and `ABC1234567` to show input
   validation.
3. Enter `9999999999` to show that a validly formatted but unknown voter is
   rejected.
4. Enter `1000000001`. Show the success message and newly issued ballot code.
5. Enter `1000000001` again. Show that duplicate participation is rejected and
   no second ballot is issued.
6. Enter `1000000002` to issue another ballot.
7. Open **Ballot Tracking**. Point out issued, cast, spoiled, and pending
   totals and the activity audit log.
8. Select the first pending ballot and choose **Mark Cast**. Select the other
   pending ballot and choose **Mark Spoiled**. Explain that these are terminal
   states and cannot be changed again.
9. Open **Reports** and review registered voters, ballot totals, turnout, and
   timestamp. Select **Generate secure report**.
10. In `reports/generated_reports/`, show the readable `.json` copy and its
    `report_hash_sha256` field. Then show that the matching `.pgbd` file is
    encrypted and unreadable without the local Fernet key.
11. Close by stating that all IDs are fictional, there is no internet voting
    or national infrastructure integration, and all processing remains local.

## Hashing, password derivation, and encryption

These mechanisms have deliberately separate purposes:

- **PBKDF2-HMAC-SHA256 password derivation:** Officer passwords are combined
  with unique random salts and processed for 600,000 iterations. This makes
  offline password guessing more expensive than the previous single SHA-256
  operation. Passwords are never stored directly.
- **SHA-256 report hashing (integrity):** The report hash covers every report
  field except `report_hash_sha256`, using JSON with sorted keys and compact
  separators. Editing a protected value causes a recalculated hash to differ.
  Hashing does **not** hide report contents.
- **Fernet report encryption (confidentiality):** The exact readable JSON bytes
  are encrypted into the `.pgbd` file. This conceals the contents from anyone
  without the local key and also authenticates the encrypted token. Encryption
  does not replace the visible SHA-256 integrity fingerprint used in the
  report and database audit record.

The key is generated on first report creation at
`database/report_encryption.key`, remains on the local machine, and is excluded
from Git. Do not delete it while encrypted reports still need to be opened.
For this classroom demonstration the readable JSON is intentionally retained
for inspection; the `.pgbd` file is the secure report output.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

The tests use temporary databases and do not modify the demonstration
database. They cover:

- invalid voter ID format rejection;
- unknown voter ID rejection;
- duplicate voter detection and second-ballot prevention;
- terminal Cast/Spoiled status enforcement;
- issued, cast, spoiled, and pending count calculations; and
- report hash, readable JSON, encrypted `.pgbd`, decryption, and database audit
  record creation.
