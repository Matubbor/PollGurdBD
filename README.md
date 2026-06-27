# PollGuard BD

PollGuard BD is an offline desktop assistant for a fictional paper-based
election demonstration. It is designed for polling officers—not voters—and
runs locally with Python, CustomTkinter, SQLite, `hashlib`, and standard Python
libraries.

This COM668 AT3 project uses demonstration data only. It does **not** provide
internet voting, online monitoring, blockchain voting, national-election
integration, or access to real voter data.

## Features

- **Local officer login:** Authenticates salted, SHA-256-hashed credentials
  stored in SQLite.
- **Voter Logging:** Validates the entered ID, compares its SHA-256 digest with
  the local register, rejects unknown or duplicate voters, and atomically marks
  an eligible voter and issues one ballot.
- **Ballot Tracking:** Shows issued, cast, spoiled, and pending totals. An
  officer can select a pending ballot and mark it Cast or Spoiled. Every issue
  and status update is written to the ballot activity log.
- **Reports:** Shows turnout and ballot totals, then writes a timestamped JSON
  report to `reports/generated_reports/`. Each report includes a SHA-256 hash
  calculated from its canonical summary data.
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
│   └── report_service.py          # Report creation
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

CustomTkinter must be installed during setup, but PollGuard BD itself does not
make any internet requests and can be demonstrated fully offline afterward.

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

## Suggested demonstration flow

1. Sign in as `admin`.
2. In **Voter Logging**, enter `1000000001` and issue its ballot.
3. Enter the same ID again to demonstrate duplicate-voter detection.
4. Enter `1000000002` to issue a second ballot.
5. Open **Ballot Tracking**, select a pending ballot, and mark it Cast or
   Spoiled.
6. Open **Reports**, review the totals, and generate a hashed JSON report.
7. Show the new file in `reports/generated_reports/`.

## Report integrity

The report hash is calculated over all report fields except
`report_hash_sha256`, using JSON with sorted keys and compact separators. If
any protected total or timestamp is edited later, recalculating the SHA-256
digest will no longer match the embedded hash. The database also records the
filename, timestamp, and original digest for the local audit trail.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

The tests use temporary databases and do not modify the demonstration
database. They cover:

- rejection of a duplicate voter and prevention of a second ballot; and
- issued, cast, spoiled, and pending ballot count calculations.
