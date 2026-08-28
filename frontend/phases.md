# LegalVault Frontend Revamp --- Phases

## Purpose

This document defines the phased execution plan for redesigning the
existing LegalVault / Digital Contract Platform frontend into a
polished, product-grade legal-tech landing experience.

**Scope constraint:** This is a frontend/presentation-layer redesign.
Existing backend functionality, APIs, authentication, Supabase behavior,
wallet signing, AI analysis, blockchain functions, database schema, and
existing application functionality must remain intact.

The redesign should make the application feel like a real product
without making unsupported claims or pretending that the project has
capabilities it does not actually have.

------------------------------------------------------------------------

# Phase 0 --- Audit Before UI Changes

## Goal

Understand the current frontend and establish hard boundaries before
changing anything.

### Inspect

-   Current landing page route.
-   Authentication routes.
-   Dashboard route.
-   Contract registry route.
-   Contract upload flow.
-   AI analysis/intelligence route.
-   Wallet connection and signing flow.
-   Contract verification route.
-   Existing API client functions.
-   Shared layouts/components.
-   Existing navigation.
-   Existing styles/theme.
-   Environment-variable usage.
-   Existing backend/API route names.
-   Existing Supabase integrations.
-   Existing blockchain/wallet integrations.

### Required rule

Do not change backend behavior merely to support the new landing page.

### Do not modify unless absolutely necessary

-   API endpoints.
-   API response contracts.
-   Authentication logic.
-   Supabase schema.
-   Database queries.
-   Contract APIs.
-   Blockchain functions.
-   Wallet signing functions.
-   AI service.
-   gRPC integration.
-   Environment variables.
-   Backend middleware.
-   Existing dashboard functionality.

------------------------------------------------------------------------

# Phase 1 --- Design System

Establish the visual language before implementing individual sections.

## Visual direction

The desired aesthetic is:

**premium legal technology + modern SaaS + subtle Web3**

It should NOT look like a generic crypto landing page.

### Palette

-   Background: near-black, approximately `#080808`.
-   Surface: approximately `#11100E`.
-   Gold: approximately `#D9AD2B`.
-   Bright gold: approximately `#F1C94A`.
-   Primary text: approximately `#F4EEE5`.
-   Muted text: approximately `#918A80`.
-   Borders: subtle translucent white, approximately
    `rgba(255,255,255,.08)`.

These values are starting design tokens, not mandatory immutable values.

## Typography

Use:

-   Elegant serif display typography for major headlines.
-   Modern sans-serif typography for body/UI.
-   Preserve the existing luxury/legal visual character where it works.

Target feeling:

-   premium
-   trustworthy
-   restrained
-   technical
-   modern

Avoid:

-   excessive gradients
-   crypto aesthetics
-   neon colors
-   giant decorative effects

------------------------------------------------------------------------

# Phase 2 --- Marketing Shell

Create the public-facing product shell without coupling it to backend
logic.

Suggested organization:

``` text
app/
├── page.tsx
│
├── (marketing)/
│   ├── how-it-works/
│   ├── privacy/
│   ├── terms/
│   └── disclaimer/
│
├── (app)/
│   ├── dashboard/
│   ├── contracts/
│   ├── intelligence/
│   ├── verify/
│   └── ...
│
components/
├── marketing/
│   ├── Navbar.tsx
│   ├── Hero.tsx
│   ├── ProductDemo.tsx
│   ├── Problem.tsx
│   ├── Workflow.tsx
│   ├── AISection.tsx
│   ├── SigningSection.tsx
│   ├── VerificationSection.tsx
│   ├── FinalCTA.tsx
│   └── Footer.tsx
│
├── animations/
│   ├── ContractAnimation.tsx
│   ├── HashAnimation.tsx
│   └── VerificationAnimation.tsx
```

This is a suggested structure; adapt it to the existing project rather
than forcing a rewrite.

------------------------------------------------------------------------

# Phase 3 --- Hero

Replace the current centered/static hero with a product-focused hero.

## Primary positioning

Recommended headline:

> Contracts should be easier to understand --- and harder to tamper
> with.

Recommended supporting copy:

> LegalVault combines AI-powered contract analysis with cryptographic
> verification and blockchain-backed signing to help you review,
> execute, and verify digital contracts in one workflow.

Primary CTA:

> Analyze a Contract →

Secondary CTA:

> See How It Works

Supporting capability line:

> AI analysis · Wallet signatures · Blockchain verification

## Hero visual

Do not use a random 3D cube, globe, glowing sphere, or generic Web3
particle field.

The visual should represent the product itself.

Concept: **The Verification Field**

A floating digital contract/document sits inside a subtle perspective
scene. Around it:

-   thin gold connection lines
-   hash fragments
-   small nodes
-   a verification ring
-   restrained ambient lighting
-   subtle depth/parallax

Conceptual flow:

``` text
Contract
   ↓
AI analysis
   ↓
Wallet signature
   ↓
Cryptographic hash
   ↓
Blockchain record
   ↓
Verified
```

------------------------------------------------------------------------

# Phase 4 --- Signature Product Advertisement Animation

Build an approximately 10--15 second looping visual demonstration of the
actual product workflow.

## Frame 1 --- Upload

``` text
Upload Contract

Employment_Agreement.pdf

[████████████████████]
Uploading...
```

## Frame 2 --- AI analysis

``` text
AI Analysis

Extracting clauses...
████████████░░░

Identifying obligations...
```

## Frame 3 --- Analysis complete

``` text
Analysis complete

Risk score
72 / 100

⚠ 3 potential risks
⚠ 2 missing clauses
✓ 14 clauses identified
```

## Frame 4 --- Clause review

``` text
Termination Clause

"...either party may terminate
the agreement..."

⚠ Ambiguous
```

## Frame 5 --- Signing

``` text
Awaiting signatures

You                         Counterparty
✓ Signed                    ✓ Signed

        MetaMask
```

## Frame 6 --- Verification

``` text
CONTRACT VERIFIED

SHA-256
8a2f...91cd

Blockchain record
0x73a...c821

✓ Integrity confirmed
```

This animation should visually communicate the full product without
requiring the user to read large paragraphs.

It should be a visual demonstration, not fake live backend activity.

------------------------------------------------------------------------

# Phase 5 --- Problem Section

Recommended heading:

> A contract can be signed in seconds. Understanding it shouldn't take
> hours.

Use three concise concepts:

### Before --- Manual review

Long documents, unclear clauses, and back-and-forth between parties.

### Risk --- What did you actually agree to?

Missing terms and potentially problematic clauses can be difficult to
identify without legal expertise.

### After --- One workflow

Analyze the document, sign it, and verify the finalized record.

Do not make unsupported quantitative claims.

------------------------------------------------------------------------

# Phase 6 --- How It Works

Recommended heading:

> From document to verifiable agreement.

Four stages:

### 01 --- Upload

Bring your contract into LegalVault.

### 02 --- Analyze

AI identifies potential risks, missing terms, and negotiation points.

### 03 --- Sign

Participants review and sign using connected wallets.

### 04 --- Verify

The finalized contract can be checked against its cryptographic record.

## Visual behavior

Prefer a scroll-driven product story.

As the user scrolls:

``` text
UPLOAD
  ↓
ANALYZE
  ↓
SIGN
  ↓
VERIFY
```

The central product visualization should change state rather than
showing four unrelated static cards.

------------------------------------------------------------------------

# Phase 7 --- Product Demo

Create a large browser/application frame titled:

> See LegalVault in action

The visual should show an authentic-looking representation of the
existing application.

Suggested sequence:

``` text
Contract Analysis
       ↓
Contract Registry
       ↓
Signing
       ↓
Verification
```

Use real application UI/screens where possible.

Do not fabricate functionality that does not exist.

------------------------------------------------------------------------

# Phase 8 --- AI Intelligence Section

Recommended heading:

> Know what's inside before you sign.

Supporting copy:

> LegalVault analyzes the structure of a contract and surfaces potential
> risks, missing information and areas worth reviewing.

Visual:

``` text
┌──────────────────────┬─────────────────────────┐
│ CONTRACT              │ AI INSIGHTS             │
│                       │                         │
│ 01 Parties            │ Risk Score              │
│ 02 Payment            │ 72                      │
│ 03 Liability          │                         │
│ 04 Termination        │ ⚠ High Risk             │
│                       │ Missing clause          │
│                       │ Ambiguous wording       │
└──────────────────────┴─────────────────────────┘
```

This should mirror the actual documented AI dashboard concept: contract
content on one side and structured insights on the other.

------------------------------------------------------------------------

# Phase 9 --- Signing Section

Recommended heading:

> Sign with cryptographic confidence.

Explain the user outcome rather than shouting about blockchain.

Visual:

``` text
Person A ────┐
             ├── Contract
Person B ────┘
       ↓
Wallet signatures
       ↓
Finalized record
```

The existing project documentation describes MetaMask-based signing, so
use wallet-signing terminology accurately.

------------------------------------------------------------------------

# Phase 10 --- Blockchain / Integrity Section

Recommended heading:

> A contract shouldn't change after everyone signs it.

Visual:

``` text
Signed document
      ↓
Cryptographic hash
      ↓
Blockchain record
      ↓
Independent verification
```

Animation:

1.  Show the document.
2.  Generate/animate a hash representation.
3.  Transition the hash into a blockchain record.
4.  Display confirmation.
5.  Show a verification state.

Example end state:

``` text
✓ DOCUMENT INTEGRITY VERIFIED
```

Do not claim that blockchain makes the entire legal agreement
universally legally valid.

------------------------------------------------------------------------

# Phase 11 --- Verification Section

Make verification a visually distinct feature.

Suggested interface:

``` text
Verify a contract

┌──────────────────────────────┐
│                              │
│      Drop contract here      │
│                              │
│            ↓                 │
└──────────────────────────────┘

             [ Verify ]
```

Demo result:

``` text
✓ CONTRACT VERIFIED

Document hash
8d72f8...92a1

Recorded hash
8d72f8...92a1

MATCH

Blockchain record
0x71...a91

Integrity confirmed
```

If the actual verification route is functional, link to it.

If it is not a public verification interface, label the marketing visual
clearly as a demonstration rather than pretending it is an independent
public verifier.

------------------------------------------------------------------------

# Phase 12 --- Three Product Pillars

Replace generic current feature cards with three actual differentiators.

## AI Contract Intelligence

> Surface potential risks, missing terms and negotiation points before
> you sign.

Visual:

``` text
CONTRACT
   ↓
CLAUSES + RISKS
   ↓
EXTRACTED / FLAGGED
```

## Cryptographic Signing

> Sign agreements through connected Web3 wallets and associate
> signatures with the contract record.

Visual:

``` text
Person A ──┐
           ├── Contract
Person B ──┘
      ↓
Wallet signatures
```

## Verifiable Records

> Compare a contract against its recorded cryptographic hash to detect
> changes after finalization.

Visual:

``` text
DOCUMENT
   ↓
SHA-256
   ↓
HASH
   ↓
BLOCKCHAIN RECORD
   ↓
VERIFY
```

Do not use "Global Access" as a headline feature unless the product
genuinely differentiates on it.

------------------------------------------------------------------------

# Phase 13 --- Final CTA

Recommended:

> Ready to put your next contract under verification?

Supporting:

> Analyze the agreement. Sign it. Keep a verifiable record.

Primary:

> Access Vault →

Secondary:

> Explore how it works

Avoid ending the site with "Create your account here." That makes the
experience feel like a project rather than a product.

------------------------------------------------------------------------

# Phase 14 --- Footer

Required product footer structure:

``` text
LegalVault

AI-powered contract analysis and verifiable signing.

Product
  Features
  How it works
  Verification

Resources
  Contract analysis
  Signing
  Verification

Legal
  Privacy Policy
  Terms of Use
  Disclaimer

© 2026 LegalVault
```

Add support/contact information only if the project actually has an
appropriate destination.

------------------------------------------------------------------------

# Phase 15 --- Legal / Policy Pages

Do not invent legal or compliance information.

Potential pages:

-   Privacy Policy
-   Terms of Use
-   AI / Legal Disclaimer

Before writing the Privacy Policy, inspect the actual implementation
for:

-   personal data collected
-   authentication data stored
-   contract storage and retention
-   who can access contracts
-   what is sent to the AI service
-   what gets written on-chain
-   whether blockchain records can be deleted
-   cookies
-   analytics
-   third-party services
-   retention/deletion behavior

If the implementation does not establish an answer, do not fabricate
one.

Avoid unsupported claims such as:

-   GDPR compliant
-   SOC 2
-   ISO 27001
-   enterprise security
-   legally binding worldwide
-   100% secure
-   zero downtime
-   military-grade encryption
-   guaranteed legal validity

The existing homepage claim "Secured by RSA-2048" should also be
verified against the actual implementation before retaining it.

Recommended disclaimer concept:

> LegalVault's AI analysis is intended to assist with contract review
> and understanding. It does not replace professional legal advice.

Have the team/guide review the wording before publication.

------------------------------------------------------------------------

# Phase 16 --- Motion System

Animations should communicate product behavior.

  Element            Animation                  Intensity
  ------------------ -------------------------- -----------
  Navbar             fade/slide on load         Low
  Hero text          staggered reveal           Medium
  Gold accent        subtle gradient movement   Low
  Product mockup     floating                   Low
  Hash particles     slow movement              Low
  AI scan            scanning line              Medium
  Risk cards         sequential reveal          Medium
  Workflow           scroll progression         Medium
  Document           perspective/parallax       Low
  Blockchain nodes   pulse                      Low
  CTA                arrow movement on hover    Low
  Feature cards      slight lift                Low
  Footer             reveal                     Very Low

## Signature animation

The main visual narrative should be:

``` text
CONTRACT
    ↓
AI ANALYSIS
    ↓
SIGNED
    ↓
HASH
    ↓
BLOCKCHAIN
    ↓
VERIFIED ✓
```

This is the site's primary motion identity.

------------------------------------------------------------------------

# Phase 17 --- Technical Animation Strategy

Prefer:

-   Next.js existing stack
-   Tailwind if already present
-   Motion / Framer Motion
-   CSS gradients
-   CSS perspective
-   SVG

Do not automatically introduce:

-   Three.js
-   React Three Fiber
-   WebGL shaders
-   GSAP
-   Lenis
-   Lottie

Use WebGL/3D libraries only if a simpler CSS/SVG/Motion implementation
cannot achieve the visual.

The landing page should remain lightweight.

Use:

-   `transform`
-   `opacity`
-   GPU-friendly animation
-   lazy loading
-   `prefers-reduced-motion`

Avoid:

-   scroll-jacking
-   heavy autoplay videos
-   huge background videos
-   expensive continuously animated DOM properties
-   excessive particles

------------------------------------------------------------------------

# Phase 18 --- Responsive Design

Desktop:

``` text
Headline + CTA       Product visualization
```

Mobile:

``` text
Headline
↓
CTA
↓
Product visualization
↓
Workflow
```

Simplify the 3D/ambient scene on mobile.

Do not merely shrink the desktop layout.

------------------------------------------------------------------------

# Phase 19 --- Final QA / Regression

Before deployment:

### Marketing

-   Hero renders.
-   Hero animation loops.
-   CTAs navigate correctly.
-   Product demo is understandable.
-   Workflow communicates the product.
-   Footer links work.
-   Legal pages are reachable.
-   Mobile layout works.

### Existing application

-   Login works.
-   Registration works.
-   Dashboard works.
-   Upload works.
-   AI analysis works.
-   Contract registry works.
-   Real-time status behavior still works.
-   Wallet connection works.
-   Signing works.
-   Finalization works.
-   Verification works.

### Technical

-   No API changes.
-   No backend changes unless unavoidable.
-   No database changes.
-   No broken environment variables.
-   No console errors.
-   No broken routes.
-   Reduced-motion mode works.
-   Mobile viewport works.
-   Performance remains acceptable.
