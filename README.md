# University of Muhammadia Saifia — Management System & Website

A complete management system for an Islamic madrasa / jamia. It has three parts:

| Part | Tech | Port | Purpose |
|---|---|---|---|
| `backend/` | Django 5+/6 · Django REST Framework · PostgreSQL | 8000 | REST API, business rules, permissions, Django admin |
| `portal/` | Astro (SSR, vanilla TypeScript) | 4322 | Management portal for every role (students, parents, teachers, accounts, admin…) |
| `website/` | React 18 · Vite · Tailwind | 4321 | **Separate** public website: about, programs, departments, faculty, online admission, merit lists, news & events, downloads… |

The website and the portal are independent sites. The website only calls the anonymous
`/api/site/public/…` endpoints (Django app `cms`). Its content (settings, departments, programs, faculty
profiles, news, announcements, calendar, gallery, downloads, FAQs, pages) is edited in the portal under
**Website** by the *Website / Media Manager*. Online admission applications (with uploaded documents) arrive in
**Admissions › Admission Applications**; contact messages in **Website CMS › Contact messages**.
Student / staff logins on the website link to the portal.

---

## Quick start (development)

```bash
# 1. PostgreSQL
docker compose up -d db

# 2. Backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # adjust if needed
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo      # demo data for every module + website content (optional)
.venv/bin/python manage.py seed_website   # only the website content (official UMS content + marked samples)
.venv/bin/python manage.py runserver 8000

# 3. Portal  (new terminal)
cd portal && cp .env.example .env && npm install && npm run dev      # http://localhost:4322

# 4. Website (new terminal)
cd website && cp .env.example .env && npm install && npm run dev     # http://localhost:4321
```

Django admin (superuser tools): http://localhost:8000/django-admin/

### Demo logins (after `seed_demo`)

| Role | Username | Password |
|---|---|---|
| Super admin | `admin` | `admin123` |
| Principal (Mohtamim) | `principal` | `madrasa123` |
| Administrator (Nazim) | `nazim` | `madrasa123` |
| Academic coordinator | `coordinator` | `madrasa123` |
| Teacher (Hifz) | `qari.yusuf` | `madrasa123` |
| Teacher (Dars-e-Nizami) | `ustadh.imran`, `mufti.abdullah` | `madrasa123` |
| Accountant | `accountant` | `madrasa123` |
| HR manager | `hr` | `madrasa123` |
| Admission officer | `admissions` | `madrasa123` |
| Exam controller | `exams` | `madrasa123` |
| Librarian / Warden / Transport / Store | `librarian`, `warden`, `transport`, `store` | `madrasa123` |
| Receptionist / Mufti / Media manager | `reception`, `mufti`, `media` | `madrasa123` |
| Student | `student1` … `student24` | `madrasa123` |
| Parent | `parent1` … `parent10` (`parent1` has two children) | `madrasa123` |

---

## Roles

Super Admin · Principal (Mohtamim) · Administrator (Nazim) · Academic Coordinator (Nazim-e-Taleemat) ·
Teacher (Ustadh/Ustadha) · Student · Parent/Guardian · Accountant · HR Manager · Admission Officer ·
Exam Controller · Librarian · Hostel Warden · Transport Manager · Receptionist · Store Keeper ·
Mufti (Dar-ul-Ifta) · Website/Media Manager · Support Staff.

Access is enforced in the API (not only hidden in the UI). Each viewset declares the roles that see
**all** rows, the roles that can **write**, the roles that may only **create** (e.g. students filing
complaints), and a **row scope** for everyone else:

- Students see only their own records; parents see only their children's.
- Teachers see the sections they teach (as class teacher, in an assignment or on the timetable).
- Staff with no special role see only their own HR records (attendance, payslips, advances).

---

## Modules

**Academics:** academic years (with Hijri), departments (Hifz, Nazra, Dars-e-Nizami, Alimah, Tajweed,
Ifta, Modern), classes/darjaat, sections/halaqat, subjects with kitab, rooms, teacher assignments,
periods, timetable (grid view), holidays, syllabus and lesson-plan tracking.

**People & records:** students, staff and teachers (each created together with a login), guardians
(optional parent login), qualifications, employment history, documents, disciplinary and medical records,
achievements, a visitor log, and a **360° record page** for every person: profile, attendance, leaves,
fees, results, hifz, hostel, transport, library, certificates and documents.

**Admissions:** online application from the website, then review, test/interview, accept, and
one-click **Enroll** (creates the student, the guardian and the login). Applicants can check their status
on the website. Promotions cover year-end promote, detain or graduate, with history.

**Attendance:**
- Daily or per-period student attendance, marked as present, absent, late, leave, half-day or excused.
- Guardians get an automatic notice when their child is marked absent.
- Staff check in and out themselves (time, IP and optional GPS, with late detection against duty start
  time). HR can also mark a bulk staff sheet.
- Approved leaves and live-class joins mark attendance automatically.
- Reports include percentages with a minimum threshold, a monthly register grid, today's overview and
  CSV export.

**Biometric attendance (fingerprint / face / card machines):**
- **Push (recommended):** ZKTeco, eSSL and compatible terminals push every punch to the server in real time over the ADMS/iclock protocol. Register the device's serial number, then set the device's *Cloud Server* to this server's address and port.
- **LAN pull:** for older ZK models, run `pip install pyzk` and schedule `python manage.py biometric_pull`.
- **Other brands / vendor software:** a JSON API (`POST /api/biometric/punches/` with an `X-Device-Key` header).
- **CSV / TXT / attlog.dat import** for offline devices.
- **How punches become attendance:** each person has a PIN (device user ID), and PINs can be generated automatically. Punches are deduplicated. For staff, the first punch is the check-in (late if after duty start plus grace) and the last is the check-out. For students, a punch marks them present or late. Approved leave and teacher-marked attendance are never overwritten.
- **Unknown PINs** are kept and applied automatically once the PIN is linked to a person.
- **End of day:** `python manage.py biometric_close_day [--students]` (nightly, via cron) marks enrolled people with no punch as absent.
- **Portal page:** Attendance → Biometric devices shows device online status, today's punches, setup steps, enrolments, the punch log, import, and re-processing.

**Leaves:**
- Leave types have yearly quotas, can be paid or unpaid, and can require a document.
- Staff, students and parents (on a child's behalf) can apply.
- Balances are checked, as are overlapping requests.
- Requests are routed to the right approver (class teacher or academic staff for students, HR or the
  principal for staff).
- Approving or rejecting syncs attendance, cancelling undoes it, and a substitute teacher can be named.
- Unpaid leave flows into payroll.

**LMS:**
- Courses can be section-based, open (self-enrol) or manual, with modules and lessons (text, YouTube,
  audio, PDF, link). Lessons can be released on a schedule and completion is tracked.
- Assignments support file or text submission, late rules and grading with feedback.
- Quizzes support MCQ, multi-select, true/false and short answers, with a timer, attempt limits, shuffle,
  auto-grading plus manual grading, and answer review.
- Courses also have discussions, a gradebook, a homework diary, and an optional completion certificate.

**Live classes:**
- Supported platforms are Jitsi, Google Meet and Zoom.
- One-off or weekly recurring schedules, with students notified.
- Students join through the portal, which marks them present or late automatically.
- When the teacher ends the class, students who never joined are marked absent. A participation report
  shows minutes attended, and a recording link can be added.

**Quran programs:**
- *Noorani Qaida:* all 17 lessons (*takhti*) with each student's status (in progress, needs repetition, passed). Finishing the Qaida records a completion and issues a certificate.
- *Nazra:* a 30-para reading grid. Every full reading is recorded as a khatm, a Nazra certificate is issued, and the grid resets for the next khatm.
- *Hifz:* a 30-para grid tracking each para through in progress, memorised and tested. A Hifz sanad is generated automatically when all 30 paras are tested.
- *Tarjuma-tul-Quran:* surah-by-surah progress for all 114 surahs. The percentage is weighted by ayah count (out of 6,236), with tests and a certificate when all 114 are tested.
- *Daily lesson sheet:* one sheet per halqa for Qaida, Nazra, Hifz, Murajaah (revision), Tarjuma and Tajweed. It records Sabaq (surah and ayah range, or lines), Sabqi, Manzil, mistakes, *atkan* (hesitations), a tajweed or understanding score and remarks.
- *Checklists:* Tajweed rules, Qira'at, the six Kalimas, Iman-e-Mujmal and Mufassal, Masnoon duas and ahadith (with Arabic, translation and source), short surahs to memorise, and the Namaz/Wudu practical. Each item is marked per student or for a whole halqa at once. The lists are editable.
- *Khatm register:* Qaida, Nazra, Hifz and Tarjuma completions are recorded automatically, and Dor (revision) cycles are recorded by hand.
- Parents and students see all of this read-only. It also appears in each student's full record and on the parent dashboard.

**Examinations:**
- Exams and date sheets, with marks entry per paper (locking supported).
- Results tabulation with positions, using Wifaq-style grading (Mumtaz, Jayyid Jiddan, Jayyid, Maqbool,
  Rasib).
- Printable report cards and result publishing with notifications.
- Certificates and Asnaad with a serial number and a public verification page.

**Finance & accounts:**
- Fee heads and fee structures (by department or class, monthly/annual/term/one-time, boarders-only).
- Scholarships and concessions (orphan, needy/Zakat, merit, sibling, staff child, Hafiz) with the fund
  that bears them.
- Bulk invoice generation, including transport fares, plus late fees and reminders.
- Cash collection with receipts; parents can upload a bank/JazzCash/Easypaisa proof for the accountant to
  verify.
- A defaulters list.
- Donations and donors, with pledges from the website.
- **Separate fund balances** for Zakat, Sadaqah, Lillah, Waqf, Fitrah, Construction and Qurbani.
- Expenses with an approval step, other income, and budget vs actual.
- A finance dashboard with charts.

**HR & payroll:**
- Recurring allowances and deductions, and salary advances (Qarz-e-Hasana) recovered in installments.
- Monthly payroll that deducts absences and unpaid leave.
- Approve or pay payslips; paying a payslip books it as a salary expense.
- Printable payslips.

**Library:**
- A catalogue that supports Arabic titles and e-books.
- Issue, return, renew and reservations, with automatic overdue fines and reminders.
- A public catalogue search on the website.

**Hostel:** hostels, rooms and beds with allocations, occupancy, mess menu, gate passes (parent request,
warden approval, then out and returned), and the night roll call.

**Transport:** vehicles (insurance and fitness expiry), routes and stops, and assigned users. Fares are
added to invoices automatically.

**Inventory:** assets (including waqf items) and vendors, plus stock items with in/out movements and
low-stock alerts.

**Communication:**
- A notice board targeted by role and/or section.
- In-app notifications (bell).
- Private messaging; students and parents can message staff only.
- A calendar of events, holidays, exams and live classes.
- Complaints and suggestions (can be anonymous), and parent-teacher meetings.

**Public website (React, `website/`) and its content (`cms` app, portal menu “Website”):**
- Bilingual English / Urdu (RTL) site: home, about & leadership, programs & courses (filter by Quran,
  Dars-e-Nizami, Takhassus, short courses, online), departments, faculty directory, campus life & gallery,
  news, events, announcements, academic calendar, download center, FAQs, CMS pages (rules, privacy, terms)
  and site-wide search (Ctrl+K).
- **Online admission form** (4 steps, mirrors the Jamia's paper form) with document uploads (photo, CNIC,
  guardian CNIC, certificates…). Applications get a `UMS-YYYY-XXXXXX` number, land in the portal's
  admission queue (source “Website”, with aggregate % from the entered results) and notify the admission office.
- **Track application** by number + CNIC: status timeline, remarks, documents received, merit position.
- **Merit lists:** create in Admissions › Merit lists, press *Generate from applications* (ranks applicants of
  the program/session by aggregate), publish.
- Everything is edited in the portal under **Website** (settings & content JSON, departments, programs,
  faculty profiles, news, announcements, calendar, gallery, downloads, testimonials, FAQs, pages).
  Images can be uploaded or given as a URL. Text marked `[Placeholder]` / `[Sample]` still has to be replaced.
- Website API: `GET /api/site/public/{settings,home,search,programs,departments,faculty,news,events,
  announcements,calendar,gallery,documents,merit-lists,testimonials,faqs,pages/<slug>}`,
  `POST /api/site/public/{contact,admissions,admissions/track}`.
- Kept from the portal's own CMS: contact inbox, newsletter subscribers and the Dar-ul-Ifta question queue.
  (The previous Astro website is archived in `_backup/website-astro-2026-11-22.tar.gz`.)

**Administration:** user accounts (reset password, activate/deactivate), a full **audit trail** of every
create, update, delete and export, global search, CSV export on every list, and printable documents
(fee challans, receipts, payslips, certificates, ID cards, donation receipts).

---

## Live classes: which platform is cheapest?

| Option | Cost | Limits | Setup |
|---|---|---|---|
| **Jitsi on `meet.jit.si`** (default) | Free | Works out of the box. The first participant may have to sign in to become moderator, and embedding is limited, so the portal opens it in a new tab | Nothing to configure |
| **Self-hosted Jitsi** (recommended for scale) | Free software; only a VPS (~US$10–20/month) | Unlimited minutes and participants (server-bound); can be embedded inside the portal | Set `JITSI_DOMAIN=meet.yourmadrasa.org`, `JITSI_EMBED=true` |
| **Google Meet** | Free with a Google account. **Google Workspace for Education Fundamentals is free** for eligible non-profit schools | Personal accounts: 60 minutes for 3+ people. Workspace for Education: 100 participants, no time limit | Google Cloud OAuth client + refresh token with `calendar.events` scope → `GOOGLE_CLIENT_ID/SECRET/REFRESH_TOKEN` |
| **Zoom** | Free plan has a 40-minute limit; paid from ~US$15/host/month | — | Server-to-Server OAuth app → `ZOOM_ACCOUNT_ID/CLIENT_ID/CLIENT_SECRET` |

**Recommendation:** start with Jitsi (zero cost). If the madrasa is a registered non-profit, apply for
Google Workspace for Education Fundamentals and switch `LIVE_CLASS_DEFAULT_PROVIDER=google_meet`, or
self-host Jitsi. You can pick the platform per class. Attendance tracking works the same with every
provider, because students join through the portal.

---

## Configuration (`backend/.env`)

See `backend/.env.example`. Important keys: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`,
`CORS_ALLOWED_ORIGINS` (website + portal origins), `FRONTEND_URL` (portal, used for password-reset links),
`POSTGRES_*`, email (`EMAIL_BACKEND`, `EMAIL_HOST`…), and the live-class provider keys.

Institution-level settings (name, logo, address, bank details for donations, library fine per day, late
fee, attendance grace minutes, minimum attendance %, working days, prayer-time city) are edited in the
portal under **Administration → Institution Settings**.

---

## Backend layout (standard Django + DRF)

```
backend/
  config/                 settings, urls (each app included under /api/)
  core/                   shared base classes
    roles.py              role list + role groups
    permissions.py        RolePermission (reads attributes declared on each viewset)
    viewsets.py           BaseModelViewSet: scoping, audit, CSV export, portal metadata
    serializers.py        LabeledModelSerializer (adds *_label / *_display for the UI)
    scopes.py             row-level visibility helpers (own / children / teacher's sections)
    metadata.py, views.py /api/meta/, /api/options/, /api/search/, /api/dashboard/
    management/commands/seed_demo.py
  <app>/                  accounts, academics, people, attendance, leaves, lms, liveclasses,
    models.py             exams, hifz, finance, library, hostel, transport, inventory,
    serializers.py        communication, website
    views.py              ModelViewSets + @action workflows + APIViews
    services.py           business logic (where it's non-trivial)
    urls.py               SimpleRouter + paths
    admin.py
```

Every viewset is explicit:

```python
class LeaveTypeViewSet(BaseModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    resource_key = "leave-types"      # URL + portal key
    read_roles = ALL                  # who sees all rows
    write_roles = HR + ACADEMIC       # who can create/update/delete
    group, icon = "Leaves", "tag"     # portal menu
```

The portal reads `/api/meta/<key>/` to build its tables and forms, so a new model needs just a
serializer, a viewset and a router line, and it appears in the portal menu for the right roles.

### Tests

```bash
cd backend && .venv/bin/python manage.py test core --noinput
```

These are end-to-end API tests on the demo data. They cover every resource for every role, the
permission boundaries, attendance, leave approval, fee collection, invoice and payroll generation, quiz
auto-grading, LMS progress, live-class attendance, results, hifz, the admission-to-enrolment flow, the
library and messaging, plus the public API.

---

## Deploying on Railway

The repo deploys as **4 Railway services** in one project: PostgreSQL + `backend` + `portal` + `website`.
Each app folder has a `Dockerfile` and a `railway.json` (health check, restart policy).

**1. Create the project**
1. New Project → *Deploy from GitHub repo* → pick this repo. Repeat *+ New → GitHub Repo* until you have three
   services; name them `backend`, `portal`, `website`.
2. *+ New → Database → PostgreSQL*.
3. For each service, open **Settings**:
   - **Root Directory**: `/backend`, `/portal`, `/website` respectively.
   - **Config file path**: `/backend/railway.json`, `/portal/railway.json`, `/website/railway.json`
     (Railway does not look inside the root directory for this file by itself).
   - **Networking → Generate Domain** (gives `https://<name>-production.up.railway.app`; or add your own domain).
4. `backend` → **Volumes → New volume**, mount path **`/app/media`** (uploaded photos, documents, website images;
   without it they are lost on every deploy).

**2. Variables** (service → *Variables*; `${{...}}` are Railway references, type them as shown)

| Service | Variable | Value |
|---|---|---|
| backend | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| backend | `DJANGO_SECRET_KEY` | a long random string (`python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| backend | `DJANGO_DEBUG` | `false` |
| backend | `DJANGO_ALLOWED_HOSTS` | your custom API domain if any (the Railway domain is added automatically) |
| backend | `CORS_ALLOWED_ORIGINS` | `https://${{website.RAILWAY_PUBLIC_DOMAIN}},https://${{portal.RAILWAY_PUBLIC_DOMAIN}}` |
| backend | `FRONTEND_URL` | `https://${{portal.RAILWAY_PUBLIC_DOMAIN}}` (password-reset links) |
| backend | `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL` | first deploy only — creates the super admin; delete afterwards |
| backend | `SEED_WEBSITE` | `true` (default): loads the UMS website content if the site has none; `false` to skip |
| backend | optional | `TIME_ZONE`, email (`EMAIL_*`), live classes (`GOOGLE_*`, `ZOOM_*`, `JITSI_*`), `WEB_CONCURRENCY` |
| portal | `PUBLIC_API_URL` | `https://${{backend.RAILWAY_PUBLIC_DOMAIN}}` |
| portal | `PUBLIC_WEBSITE_URL` | `https://${{website.RAILWAY_PUBLIC_DOMAIN}}` |
| website | `VITE_API_URL` | `https://${{backend.RAILWAY_PUBLIC_DOMAIN}}/api/site` |
| website | `VITE_PORTAL_URL` | `https://${{portal.RAILWAY_PUBLIC_DOMAIN}}` |

`PUBLIC_*` and `VITE_*` are baked into the build, so **redeploy portal/website after changing them** (or after
changing domains). `PORT` is set by Railway — don't set it yourself.

**3. Deploy** — deploy `backend` first (it runs migrations, creates the super admin and loads the website
content on start; health check `/healthz`), then `portal` and `website`. Sign in to the portal with the super admin.

Useful: *backend → ⋯ → Shell* (or `railway run`) for `python manage.py createsuperuser`,
`python manage.py seed_website --reset`, or `python manage.py seed_demo` (demo data — not for a live site).
Biometric devices in push mode must reach the backend domain over the internet with HTTPS (port 443); older
models that only speak plain HTTP should use the CSV import or the LAN pull command run on a local machine instead.

---

## Production

```bash
docker compose --profile full up -d --build      # db + api + website + portal
docker compose exec api python manage.py createsuperuser
```

Checklist:
- Set `DJANGO_DEBUG=false` and a strong `DJANGO_SECRET_KEY`.
- Set real `DJANGO_ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`.
- Configure SMTP for password-reset and fatwa-answer emails.
- Put the three services behind HTTPS (nginx, Caddy or Traefik), e.g. `api.`, `portal.` and `www.`
  subdomains.
- Serve `/media/` from a persistent volume or object storage.
- Back up the PostgreSQL volume regularly.
