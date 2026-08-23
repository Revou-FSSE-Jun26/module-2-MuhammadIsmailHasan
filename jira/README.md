# Jira import files

Revoshop backlog, generated from the Checkpoint 3 rubric plus the v2 business rules. Three files, two import strategies.

| File | Purpose |
|------|---------|
| `import-to-jira.py` | **Route 0, recommended.** Creates everything via the REST API. No CSV wizard, no field mapping. |
| `.env.jira.example` | Template for your credentials. Copy to `.env.jira`, which is git-ignored. |
| `01-epics.csv` | **Route A, pass 1.** The 11 epics. No `Issue Id` column, so it imports anywhere. |
| `02-stories.csv` | **Route A, pass 2 template.** 60 children with `EPIC_*` placeholders in the `Parent` column. Do not import directly — run the script first. |
| `set-epic-keys.py` | Rewrites those placeholders into the real epic keys and emits `02-stories-linked.csv`. |
| `jira-import-all.csv` | **Route B.** Everything in one file, linked via `Issue Id` / `Parent`. Only works if `Issue Id` is mappable. |

`01-epics.csv` and `02-stories.csv` are generated from `jira-import-all.csv`. Edit the combined file and regenerate rather than editing all three.

## Two tiers

Everything carries an `mvp` or `improvement` label. Filter on it in Jira to separate graded scope from extras.

**Tier 1 — `mvp` (22 items, 56 points).** The rubric endpoints plus the JWT foundation.

**Tier 2 — `improvement` (38 items, 119 points).** The rest of the v2 business rules, starting with the DTO layer.

| # | Epic | Tier | Items | Pts |
|---|---|---|---|---|
| 1 | MVP - Auth Foundation with JWT and Roles | mvp | 8 | 18 |
| 2 | MVP - Order Module | mvp | 7 | 21 |
| 3 | MVP - Product and Category Compliance | mvp | 3 | 5 |
| 4 | MVP - Migrations Seeders Tests and Docs | mvp | 4 | 12 |
| 5 | IMPROVEMENT - Marshmallow DTO Layer | improvement | 8 | 21 |
| 6 | IMPROVEMENT - Auth Enhancements | improvement | 3 | 9 |
| 7 | IMPROVEMENT - User Profile and Addresses | improvement | 7 | 24 |
| 8 | IMPROVEMENT - Product Catalog Enhancements | improvement | 7 | 22 |
| 9 | IMPROVEMENT - Order Status Lifecycle | improvement | 7 | 25 |
| 10 | IMPROVEMENT - Seller Ownership Rules | improvement | 3 | 8 |
| 11 | IMPROVEMENT - Data Integrity and Robustness | improvement | 3 | 10 |
| | | | **60** | **175** |

### Why JWT sits in tier 1

The rubric marks JWT optional, but building it before the order module means `POST /orders` and `GET /orders` read the caller from the token on the first write. The alternative — ship orders with `user_id` in the body, then swap in tokens later — means writing those endpoints twice and retesting them.

Two knock-on effects: buyer-scoping on order read and delete now lands in tier 1 (tickets `206`, `207`) instead of waiting for an improvement epic, and epic 10 shrinks to the seller-specific rules only.

### Why DTO is the first improvement epic

Retrofitting Marshmallow onto the ~15 endpoints in epics 7 to 9 costs far more than writing those endpoints against schemas from the start. Ticket `501` carries an explicit note not to start it before every rubric requirement passes.

## Where you stand against the rubric

13 of the 16 required endpoints already exist in some form.

| Module | Status |
|---|---|
| `POST /users` | exists at `/users/register` — path mismatch (ticket `101`) |
| `POST /auth/login` | **missing** (ticket `102`) |
| Product CRUD, 5 routes | all exist; `DELETE` needs the active-order guard (ticket `301`) |
| Category CRUD, 5 routes | all exist; `GET /<id>` hides products behind `?with_products=true` (ticket `303`) |
| Order module, 4 routes | **all missing**, and `order_items` has no `quantity` column (epic 2) |

## Build order

```
TIER 1
  101, 102          registration path + credential login
  103, 104, 105     JWT config, token issuance, role normalization
  106, 107, 108     decorators, /auth/me, error handlers      <- 106 BLOCKS epic 2
  203               DECIDE auth compatibility policy          <- BLOCKS 204-207
  201               order items rework                        <- BLOCKS 204-207, 301
  202               orders blueprint
  204, 205, 206, 207    the four order endpoints
  301, 302          product delete guard
  303               category detail (1 pt, quick win, do anytime)
  401 - 404         migration, seeders, tests, docs

TIER 2
  epic 5   DTO layer            <- do not start until tier 1 fully passes
  epic 11  1101, 1102           correctness bugs, promote above the feature epics
  epic 6   auth enhancements
  epic 7   profile + addresses
  epic 8   product catalog      <- 801 gates 1001
  epic 9   order lifecycle      <- 907 needs epic 7
  epic 10  seller rules         <- 1003 gates 1002
```

Two hard blockers inside tier 1: **`106`** (decorators) gates every order endpoint, and **`201`** gates the order endpoints plus the product delete guard. `order_items` is a bare `db.Table` with no `quantity`, so an order cannot express "two of this item" until 201 lands.

Note `1101` and `1102` are labelled `improvement` but priced `High`. They fix real correctness bugs (overselling under concurrency, no database floor on stock), so pull them ahead of the tier-2 feature epics.

## Decisions to make before starting

| Ticket | Question | Blocks |
|---|---|---|
| `203` | Token-only, or fall back to `user_id` in the body? **Grading risk — read this one.** | `204`–`207` |
| `101` | Rename `/users/register` to `/users`, or keep an alias? | — |
| `207` | Does `DELETE /orders/<id>` restore stock? Recommendation is in the ticket. | `903` |
| `205` | Does the order list carry line items, or summaries only? | — |
| `705` | Does "add address at user" mean the user output DTO? Ticket assumes yes. | — |
| `1003` | Can one order contain products from multiple sellers? | `1002` |

**Ticket 203 is the one to read first.** The rubric says sending `user_id` is *enough*, so a grader's script may call `POST /orders` with no `Authorization` header. Against a token-only endpoint that returns 401 and looks broken. The ticket lays out three options; the recommendation is token-only plus a prominent two-step login example at the top of the README, which is also an acceptance criterion on ticket `404`.

## Known tradeoffs baked into the MVP

Worth writing into your project README so they read as deliberate:

- The MVP stock decrement is a read-then-write and will oversell under concurrent requests. Ticket `1101` hardens it.
- There is no database-level floor on stock. Ticket `1102` adds the CHECK constraint.
- No rate limiting on login, so it is brute-forceable. Ticket `603`.
- Access tokens only, no refresh or revocation, so logout is client-side. Ticket `602`.

## Import

Three routes. **Route 0 is the easiest** — it skips the CSV wizard entirely, so the missing `Issue Id` option stops mattering.

| | Route | Use when |
|---|---|---|
| **0** | REST API — `import-to-jira.py` | Recommended. One command, no wizard, no field mapping. |
| **A** | Two-pass CSV — `01-epics.csv` then `02-stories.csv` | You prefer the wizard and `Issue Id` is **not** in the dropdown. |
| **B** | Single-pass CSV — `jira-import-all.csv` | You prefer the wizard and `Issue Id` **is** available. |

## Route 0: REST API (recommended)

No mapping screens, no `Issue Id` problem. The script creates the 11 epics, then the 60 children with their parent already linked.

### 1. Create an API token

Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens) → **Create API token**. Copy it.

### 2. Put your credentials in `.env.jira`

```bash
cd jira
cp .env.jira.example .env.jira
chmod 600 .env.jira
```

Then edit `.env.jira`:

```
JIRA_SITE=https://yourname.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=paste_token_here
JIRA_PROJECT_KEY=REV
```

`.env.jira` is git-ignored, so it will not be committed. `chmod 600` stops other accounts on the machine from reading it — the script warns you if the permissions are too open.

**Never paste this file's contents into chat, an issue, or a commit.** An Atlassian API token is not scoped to one project: it acts as your whole account across every Jira and Confluence space you can reach. If a token is ever exposed, [revoke it](https://id.atlassian.com/manage-profile/security/api-tokens) and create a new one. Revoking takes seconds and breaks nothing else.

Environment variables still work and take precedence over the file, if you prefer them:

```bash
 export JIRA_API_TOKEN=paste_token_here   # leading space hides it from shell history
```

### Finding your project key

The project key is the prefix on your issue keys — `RS` if your tickets are `RS-1`, `RS-2`. Three ways to find it:

- **URL:** open the project and read the address bar — `.../jira/software/projects/RS/boards/1`
- **Any ticket:** the part before the hyphen
- **Projects → View all projects:** there is a `Key` column

Or ask Jira directly. This needs only the first three variables, not `JIRA_PROJECT_KEY`:

```bash
python3 import-to-jira.py --list-projects
```

```
Projects visible to you (3):

  KEY    TYPE             NAME
  -----  ---------------  --------------------
  RS     company-managed  Revoshop
  MOD2   team-managed     Module 2 Work
  SCRUM  company-managed  My Scrum Project
```

It also shows each project's type, so you can confirm you are pointing at a company-managed one.

### 3. Dry run first

```bash
cd jira
python3 import-to-jira.py
```

Creates nothing. It verifies your credentials, confirms the project exists and you can create issues in it, checks that Epic, Story, Task and Bug all exist, checks the four priority values, and locates the Story Points custom field. Any problem is reported before a single item is created.

### 4. Create everything

```bash
python3 import-to-jira.py --execute
```

Prints each item as it goes: `+ RS-12 -> RS-2  Add POST /orders to place an order`.

**Safe to re-run.** Items are matched by summary, so anything already present is skipped rather than duplicated. If it stops halfway — network drop, permission error — just run it again and it picks up where it left off.

### 5. Verify

```
project = RS AND issuetype != Epic AND parent IS EMPTY
```

Zero results means all 60 children are linked. For the tier count:

```
project = REV AND labels = mvp AND issuetype != Epic
```

Expect 22. Without the `issuetype` clause you get 26, because the 4 MVP epics carry the label too.

### If it fails

- **`missing credential(s)`** — `.env.jira` is absent or a line is blank. Check you are running from inside the `jira/` directory, since the script looks for the file next to itself.
- **`HTTP 401`** — wrong email, or the token was revoked. The email must be the Atlassian account address, not a display name.
- **`project not found, or you lack Create Issue permission`** — wrong `JIRA_PROJECT_KEY`. Run `--list-projects` to see the exact keys.
- **`project is missing issue type(s)`** — the project's issue type scheme lacks one of Epic, Story, Task, Bug. Add it, or ask your admin.
- **`Field 'customfield_...' cannot be set. It is not on the appropriate screen`** — handled automatically. Despite the wording, the usual cause is the field's issue type context, not a screen; see below.
- **Story Points stored but not visible** — the field is not on the issue screen; see below.

### Story Points: two separate things people confuse

**Being settable** and **being visible** are controlled by different settings. Diagnosing the wrong one wastes a lot of time.

#### Why `Task` and `Bug` reject the field

Not a screen problem. A custom field has a **context** that restricts which issue types it applies to. The stock Story Points context covers Epic and Story only:

```
context 'Default Configuration Scheme for Story Points'
  issue types: ['Epic', 'Story']
```

Fix: **Settings → Issues → Custom fields → Story Points → ⋯ → Contexts and default value**, then edit the context so Task and Bug are included. Re-run `--fix-points` afterwards.

#### Why the field is invisible on the issue view

A value can be stored and still not render, because the field is not on the issue type's screen. Check every screen the project uses — they are often shared, so Story and Task may sit on the same one.

Fix: **Settings → Issues → Screens**, open the screen your issue types use, and add **Story Points**.

#### Where it is visible without any config

The Scrum **Backlog** shows estimates as a badge on each row, independent of screens, as long as the board's estimation field is Story Points. Check under **Board settings → Estimation**.

#### Do not trust `createmeta` for this

An earlier version of this script filtered the payload using `createmeta`, which looked sensible and was wrong. On a real Cloud project `createmeta` omits Story Points for *every* issue type, including Story, where it demonstrably works:

```
Story   16 fields listed | points present: False   <- but Story accepts it fine
```

The result was a silent failure: items were created successfully with their estimates quietly dropped. No error, nothing to notice.

The script now probes at write time instead. It sends the field, and when a type rejects it, records that type and stops sending it — so each unsupported type costs one wasted call, not sixty. `project`, `issuetype`, `summary` and `parent` are never dropped.
- **`CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`** — handled automatically; see below.
- **`HTTP 410 ... The requested API has been removed`** — already fixed. Atlassian removed `/rest/api/2/search` (CHANGE-2046); the script now uses `/rest/api/3/search/jql`. If you still see this, you are running an older copy of the script.

### Which REST endpoints this uses

Atlassian is retiring endpoints on a rolling schedule, so if this breaks later, these are the calls to check:

| Purpose | Endpoint |
|---|---|
| Verify credentials | `GET /rest/api/2/myself` |
| List projects (`--list-projects`) | `GET /rest/api/2/project/search` |
| Check project, issue types | `GET /rest/api/2/issue/createmeta` |
| Check priorities | `GET /rest/api/2/priority` |
| Find Story Points field | `GET /rest/api/2/field` |
| Find existing items (dedupe) | `GET /rest/api/3/search/jql` |
| Create an item | `POST /rest/api/2/issue` |

Search deliberately uses v3 because the v2 and v3 `/search` endpoints were both removed. Creation stays on v2 because it accepts a plain-text `description`; v3 would require Atlassian Document Format, which would mean converting all 71 descriptions for no benefit.

### About the certificate warning

On macOS, Python installers from python.org do not use the system Keychain. They ship their own CA bundle that only gets installed when you run `Install Certificates.command`. If that step was skipped, the CA file is missing entirely and every HTTPS request fails.

The script detects this and falls back to the `certifi` bundle, printing:

```
note: system CA bundle missing, using certifi instead
```

That is informational, not an error. Certificate verification stays fully enabled — self-signed and expired certificates are still rejected.

To fix it permanently for every Python program on your machine, run the installer once:

```bash
open "/Applications/Python 3.14/Install Certificates.command"
```

Adjust the version number to match your install. After that the note disappears.

---

The two CSV routes below are kept as alternatives if you would rather use the wizard.

## Route A: two-pass (no `Issue Id` required)

Epics have no parent, so pass 1 needs no ID column at all. Children then reference the real epic keys Jira assigned, which the helper script fills in for you.

### Pass 1 — import the epics

Upload `01-epics.csv`. Columns: `Issue Type`, `Summary`, `Description`, `Priority`, `Labels`, `Labels`. Map each by name.

You get 11 epics. Note the key of the **first** one, e.g. `RS-1`.

### Pass 2 — link the children

Confirm the epic order the script expects:

```bash
cd jira
python3 set-epic-keys.py --show
```

If you imported into an empty project the keys are sequential, so pass only the first:

```bash
python3 set-epic-keys.py --start RS-1
```

If they are not sequential, list all 11 in epic order:

```bash
python3 set-epic-keys.py --keys RS-4,RS-5,RS-6,RS-7,RS-8,RS-9,RS-10,RS-11,RS-12,RS-13,RS-14
```

The script writes **`02-stories-linked.csv`** and prints how many items attached to each epic. Check that table before importing — it should read 8, 7, 3, 4, 8, 3, 7, 7, 7, 3, 3, totalling 60. If a count looks wrong, your key order is wrong.

Then import `02-stories-linked.csv`, mapping the `Parent` column to the **Parent** field. `Parent` accepts a real issue key, which is why this route needs no `Issue Id`.

Sanity checks the script performs for you: key format, exactly 11 keys, no duplicates, every `Parent` value resolved, and row count preserved. It refuses to write a partial file.

## Route B: single-pass (`Issue Id` available)

Use `jira-import-all.csv`.

### Before you import

Check these three things on the project, otherwise rows fail mid-import and you have to clean up partial data:

1. The issue type scheme includes **Epic, Story, Task and Bug**. A default company-managed Scrum or Kanban project has all four.
2. The priority scheme includes **Highest, High, Medium and Low**. The Jira default does.
3. **Story Points** is on the create/edit screen for Story, Task and Bug. If it is not, the column silently fails to map — see the field notes below.

Import into an empty project the first time. If something goes wrong, deleting the project is far easier than unpicking 60 half-imported items.

### Steps

1. Jira → **Settings (cog) → System → External system import**.
2. If you land on the new experience, click **Switch to the old experience** in the top right. The "Import issues from CSV" option on the work item menu is a different, more limited importer and cannot create parent-child hierarchy.
3. Choose **CSV**, upload `jira-import-all.csv`, and select your project.
4. Map the columns:

   | CSV column | Map to |
   |---|---|
   | `Issue Id` | Issue Id |
   | `Parent` | Parent |
   | `Issue Type` | Issue Type |
   | `Summary` | Summary |
   | `Description` | Description |
   | `Priority` | Priority |
   | `Story Points` | Story Points |
   | `Labels` (both columns) | Labels |

5. Save the mapping configuration file that Jira offers at the end. If you need to re-import, it saves redoing step 4.

### If a field is missing from the mapping dropdown

**`Issue Id` or `Issue Key` missing** — common on Cloud, even in the old experience. Two options:

- Easiest: switch to route A above, which does not use `Issue Id`.
- Or make it appear: the legacy importer only offers `Issue Id` when the **Linked Issues** field is on all screens. Add it under Settings → Issues → Screens, then restart the import. See [Atlassian KB on mapping Issue ID and Parent](https://confluence.atlassian.com/jirakb/unable-to-map-issueid-and-parentid-fields-via-csv-in-external-system-import-1318387840.html).

**`Issue Type`, `Summary` or `Priority` missing** — you are still in the new import experience, which exposes a reduced field set. Click **Switch to the old experience**, labelled **Switch to legacy** on some instances. Those are core fields; the legacy importer always offers them.

**`Parent` missing but `Parent Link` or `Epic Link` present** — your instance predates the field consolidation. Map to `Parent Link`, or `Epic Link` if that is all there is. Both still work.

### Notes specific to company-managed

- The hierarchy column is **`Parent`**. In route B it holds the parent's `Issue Id`; in route A it holds the parent's real issue key. There is no separate `Parent Id` field — that name was from an older importer.
- **There is no `Epic Name` column.** Atlassian deprecated `Epic Name`; epics are titled by `Summary` now, matching how team-managed projects always worked. Epic titles live in the `Summary` column like every other row.
- Both `Labels` columns map to the same **Labels** field. Jira merges them into two labels per item. Expected, not a mapping error.
- Epics must exist before their children are linked. Because everything is in one file keyed by `Issue Id`, the importer handles that ordering itself — no need to split the file.

### Verifying afterwards

Run this JQL in the issue search to confirm nothing came in unparented:

```
project = <YOUR_KEY> AND issuetype != Epic AND parent IS EMPTY
```

Zero results means all 60 children linked correctly. Then check the counts: 11 epics, 60 children, 71 items total. `labels = mvp AND issuetype != Epic` should give 22 items — 26 without the issuetype clause, since the MVP epics are labelled too.

The numbering is deliberate: epics are `1`–`11`, and each child's id starts with its epic number (children of epic 2 are `201`–`207`). Easy to spot a mislinked row.

## Placeholder reference

`set-epic-keys.py` handles this substitution for you. The table is here only so you can check the script's output, or do it by hand if you prefer.

| Placeholder | Epic | Children |
|---|---|---|
| `EPIC_MVP_AUTH` | MVP - Auth Foundation with JWT and Roles | 8 |
| `EPIC_MVP_ORDERS` | MVP - Order Module | 7 |
| `EPIC_MVP_CATALOG` | MVP - Product and Category Compliance | 3 |
| `EPIC_MVP_HARDEN` | MVP - Migrations Seeders Tests and Docs | 4 |
| `EPIC_DTO` | IMPROVEMENT - Marshmallow DTO Layer | 8 |
| `EPIC_AUTH_PLUS` | IMPROVEMENT - Auth Enhancements | 3 |
| `EPIC_PROFILE` | IMPROVEMENT - User Profile and Addresses | 7 |
| `EPIC_PRODUCT` | IMPROVEMENT - Product Catalog Enhancements | 7 |
| `EPIC_ORDER_LIFECYCLE` | IMPROVEMENT - Order Status Lifecycle | 7 |
| `EPIC_AUTHZ` | IMPROVEMENT - Seller Ownership Rules | 3 |
| `EPIC_INTEGRITY` | IMPROVEMENT - Data Integrity and Robustness | 3 |

## Field notes

- **Columns** are exactly: `Issue Id`, `Parent`, `Issue Type`, `Summary`, `Description`, `Priority`, `Story Points`, `Labels`, `Labels`. Nine headers, all mapping to real Jira fields.
- **Issue Type** uses Jira defaults only: Epic, Story, Task, Bug. The two investigation tickets (`203`, `1003`) are `Task` with a `spike` label, since `Spike` is not a default type and would fail to map.
- **Labels** appears twice as a column header. That is how Jira CSV import expresses multi-value fields — do not merge the columns. First is the tier, second is the domain.
- **Story Points** maps directly in company-managed projects, provided the field is on the create/edit screen. (Team-managed projects call it `Story point estimate` instead — not your case.) If the mapping still fails, skip the column, import without estimates, and set them in Jira afterwards.
- Descriptions contain real newlines inside quoted fields (RFC 4180). The old external system importer handles this. If yours objects, re-save with descriptions collapsed to single lines.
- Priorities used: Highest, High, Medium, Low.
