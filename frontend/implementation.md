# LegalVault Frontend Revamp --- Implementation Specification

## 1. Objective

Redesign the public frontend of the existing Digital Contract Platform /
LegalVault application so it presents as a polished, credible legal-tech
product.

This is a **frontend-only productization effort**.

The existing backend and application workflows must remain operational.

------------------------------------------------------------------------

# 2. Product Positioning

## Product name

LegalVault

## Product concept

AI-powered contract analysis combined with wallet-based signing and
cryptographic/blockchain-backed verification.

## Core user story

``` text
Understand the contract.
        ↓
Review potential issues.
        ↓
Sign the agreement.
        ↓
Create a verifiable record.
        ↓
Verify integrity later.
```

## Recommended positioning

> Contracts should be easier to understand --- and harder to tamper
> with.

Supporting message:

> LegalVault combines AI-powered contract analysis with cryptographic
> verification and blockchain-backed signing to help you review,
> execute, and verify digital contracts in one workflow.

Do not overclaim legal validity, security certifications, compliance, or
enterprise capabilities.

------------------------------------------------------------------------

# 3. Landing Page Information Architecture

Implement the landing page in this order:

``` text
1. Navbar
2. Hero
3. Product Demo / Signature Animation
4. Problem
5. How It Works
6. AI Contract Intelligence
7. Signing
8. Verification / Blockchain Integrity
9. Three Product Pillars
10. Final CTA
11. Footer
```

Do not add unnecessary sections merely to make the page longer.

------------------------------------------------------------------------

# 4. Navbar

Suggested structure:

``` text
LegalVault

Product
How it works
Verification

                         Sign in
                         Access Vault
```

Possible alternative:

``` text
LegalVault

Product   How it works   Verification

                         Connect / Access Vault
```

Use existing authentication/navigation destinations.

Do not expose implementation details in the primary navigation.

Avoid navigation items such as:

-   gRPC
-   Supabase
-   Ethereum
-   AI Engine
-   Blockchain Architecture

Those are implementation details, not product navigation.

------------------------------------------------------------------------

# 5. Hero Implementation

## Layout

Desktop:

``` text
┌─────────────────────────────────────────────────────┐
│                                                     │
│  TEXT / CTA                     PRODUCT VISUAL      │
│                                                     │
│  Contracts should...            Contract.pdf       │
│  harder to tamper...            AI Analysis        │
│                                 Risk Score 72      │
│  description                   ⚠ Risks             │
│                                 ✓ Clauses           │
│  [Analyze] [How it works]                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

Mobile:

``` text
Headline
Description
CTA
Product visualization
```

## Headline

> Contracts should be easier to understand --- and harder to tamper
> with.

Highlight selected words such as:

-   understand
-   tamper with

with the gold accent.

## CTA

Primary:

> Analyze a Contract →

Secondary:

> See How It Works

The primary CTA should route into the existing appropriate application
flow.

The secondary CTA should scroll to the workflow section.

------------------------------------------------------------------------

# 6. Hero Product Visualization

Do not use a generic 3D object.

Create a floating contract interface.

## Base document

Display something visually similar to:

``` text
┌───────────────────────────────┐
│                               │
│       AGREEMENT.pdf           │
│                               │
│ ───────────────────────────   │
│                               │
│ Parties                       │
│ Payment Terms                 │
│ Liability                     │
│ Termination                   │
│                               │
└───────────────────────────────┘
```

## Surrounding layers

-   subtle gold glow
-   perspective grid
-   verification ring
-   small hash strings
-   thin connecting lines
-   small status chips
-   restrained particles

## Movement

Document:

-   slow vertical float
-   tiny rotation/parallax

Verification ring:

-   slow rotation

Hash fragments:

-   slow movement between stages

Status chips:

-   fade/reveal

Keep all motion subtle.

------------------------------------------------------------------------

# 7. Hero Product Advertisement

Implement the visual state machine:

``` text
UPLOAD
  ↓
ANALYZE
  ↓
RISK DETECTED
  ↓
SIGN
  ↓
HASH
  ↓
VERIFIED
```

Suggested timing:

``` text
Upload:       1.5–2.0 sec
Analysis:     2.0–2.5 sec
Risk result:  2.0 sec
Signing:      2.0 sec
Verification: 2.0–3.0 sec
Transition:   0.3–0.6 sec
```

Total target:

Approximately 10--15 seconds.

Do not create fake backend requests simply for the animation.

This should be a self-contained visual demonstration.

------------------------------------------------------------------------

# 8. Product Demo

Create a large rounded browser frame.

Suggested title:

> See LegalVault in action

Inside, show a realistic application UI.

Possible visual states:

### State A

Contract registry.

### State B

AI intelligence split view.

### State C

Signing.

### State D

Verification.

Prefer using real screenshots/components from the actual app where
possible so the marketing site accurately represents the product.

------------------------------------------------------------------------

# 9. Problem Section

Heading:

> A contract can be signed in seconds. Understanding it shouldn't take
> hours.

Three visual cards:

### Manual review

Long documents and manual inspection.

### Unclear risk

Potentially important terms can be difficult to identify.

### Fragmented workflow

Reviewing, signing, and verifying can involve separate steps/tools.

Then transition to:

> One workflow.

Keep this concise.

------------------------------------------------------------------------

# 10. Workflow Section

Heading:

> From document to verifiable agreement.

Use four stages:

``` text
01
UPLOAD
Bring your contract into LegalVault.

02
ANALYZE
AI identifies potential risks,
missing terms and negotiation points.

03
SIGN
Participants review and sign
using connected wallets.

04
VERIFY
Check the finalized contract
against its cryptographic record.
```

## Scroll animation

Use sticky or progressive layout if appropriate:

``` text
Stage 01 → Stage 02 → Stage 03 → Stage 04
```

The central visual should update between states.

Avoid scroll-jacking.

Normal browser scrolling must remain intact.

------------------------------------------------------------------------

# 11. AI Intelligence Section

Heading:

> Know what's inside before you sign.

Use a large two-pane product visual.

Left:

``` text
CONTRACT

Parties
Payment
Liability
Termination
...
```

Right:

``` text
AI INSIGHTS

Risk Score
72

⚠ Potential risk
⚠ Missing clause
✓ Parties identified
✓ Clauses extracted
```

Use subtle scan-line animation.

Highlight individual clauses as they are "analyzed."

The visual should communicate:

``` text
Document
   ↓
Clause extraction
   ↓
Risk detection
   ↓
Structured insights
```

------------------------------------------------------------------------

# 12. Signing Section

Heading:

> Sign with cryptographic confidence.

Visual:

``` text
PARTICIPANT A
      │
      ├──── CONTRACT ────┤
      │                  │
PARTICIPANT B             │
                           ↓
                     WALLET SIGNATURES
                           ↓
                     FINALIZED RECORD
```

Animate signatures appearing one after another.

Use wallet terminology accurately.

Do not claim the system provides legal advice or guarantees
enforceability.

------------------------------------------------------------------------

# 13. Blockchain / Integrity Section

Heading:

> A contract shouldn't change after everyone signs it.

Visual:

``` text
SIGNED CONTRACT
       ↓
HASH
       ↓
BLOCKCHAIN RECORD
       ↓
VERIFY
```

## Animation

1.  Contract card compresses into a hash.
2.  Hash characters animate.
3.  Hash travels along a thin gold path.
4.  Blockchain node receives it.
5.  Verification returns.
6.  Green/neutral confirmation state appears.

Do not make this look like cryptocurrency trading.

No coins. No token graphics. No crypto charts.

The visual language is document integrity, not speculation.

------------------------------------------------------------------------

# 14. Verification Section

Create a polished verification UI.

Initial:

``` text
Verify a contract

[ Drop contract here ]

[ Verify ]
```

Result:

``` text
✓ CONTRACT VERIFIED

Document hash
8d72f8...92a1

Recorded hash
8d72f8...92a1

MATCH

Blockchain record
0x71...a91
```

If this is not actually a public verifier, label the visual as a
demonstration.

If the existing verification application is usable, CTA should navigate
to it.

------------------------------------------------------------------------

# 15. Three Product Pillars

Use these instead of generic feature cards:

## AI Contract Intelligence

Surface potential risks, missing terms and negotiation points before
signing.

## Cryptographic Signing

Sign agreements using connected Web3 wallets.

## Verifiable Records

Compare a contract against its recorded cryptographic hash to detect
changes after finalization.

------------------------------------------------------------------------

# 16. Final CTA

Heading:

> Ready to put your next contract under verification?

Copy:

> Analyze the agreement. Sign it. Keep a verifiable record.

Buttons:

``` text
[ Access Vault → ]
[ Explore how it works ]
```

------------------------------------------------------------------------

# 17. Footer Implementation

Structure:

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

Only include destinations that actually exist.

------------------------------------------------------------------------

# 18. 3D / Background Implementation

## Name

The Verification Field

## Layers

### Layer 1

Near-black background.

### Layer 2

Radial gold ambient glow.

### Layer 3

Very subtle perspective grid.

### Layer 4

Floating document.

### Layer 5

Verification ring.

### Layer 6

Hash particles.

### Layer 7

Minimal connection lines.

## Avoid

-   generic galaxy
-   giant glowing sphere
-   rotating cube
-   crypto coins
-   excessive stars
-   neon cyberpunk
-   giant blockchain globe

The 3D environment must explain the product.

------------------------------------------------------------------------

# 19. Animation Library / Tooling Strategy

Preferred:

-   existing Next.js setup
-   Tailwind if already present
-   Motion / Framer Motion
-   CSS
-   SVG

Potential 21st.dev inspiration categories:

-   hero animations
-   hero parallax
-   scroll media expansion
-   background paths
-   spotlight
-   aurora background
-   grid pattern
-   beams background
-   animated gradient background
-   magnetic buttons
-   landing-page footers

Useful 21st.dev areas:

-   https://21st.dev/community/components/explore/hero-animations
-   https://21st.dev/community/components/explore/hero-scroll
-   https://21st.dev/community/components/s/hero
-   https://21st.dev/community/components/s/landing-page

Use these as inspiration/component sources, not as a reason to import
unnecessary dependencies.

------------------------------------------------------------------------

# 20. Performance Rules

Prefer animations based on:

-   transform
-   opacity
-   CSS
-   SVG

Use lazy loading for below-fold heavy content.

Avoid:

-   autoplay background video
-   massive animation assets
-   expensive continuous layout calculations
-   unnecessary WebGL
-   scroll-jacking
-   hundreds of particles

Implement:

``` text
prefers-reduced-motion
```

For reduced-motion users, replace complex motion with static product
states and simple fades.

------------------------------------------------------------------------

# 21. Responsive Rules

Desktop:

-   two-column hero
-   large product visualization
-   horizontal workflow
-   large application mockups

Tablet:

-   reduce visual size
-   maintain two-column where practical
-   simplify background effects

Mobile:

``` text
Headline
↓
Copy
↓
CTA
↓
Product animation
↓
Workflow
```

Simplify 3D effects on mobile.

Never allow the decorative animation to interfere with CTA interaction.

------------------------------------------------------------------------

# 22. Legal Page Implementation

Before generating policy content, inspect actual implementation.

Determine:

-   authentication information
-   personal information
-   uploaded document storage
-   retention
-   AI processing
-   third-party services
-   cookies
-   analytics
-   blockchain-recorded data
-   deletion behavior
-   wallet information
-   contract access controls

Only describe what the application actually does.

Do not copy a generic enterprise SaaS privacy policy.

------------------------------------------------------------------------

# 23. SEO / Metadata

Add appropriate:

-   `<title>`
-   meta description
-   OpenGraph metadata
-   favicon
-   social preview image if appropriate
-   sitemap if appropriate
-   robots configuration if appropriate

Potential title:

> LegalVault --- AI Contract Analysis & Verifiable Signing

Potential description:

> Analyze contracts with AI, sign with connected wallets, and verify
> finalized documents using cryptographic records.

Verify that every phrase accurately reflects the implementation before
publishing.

------------------------------------------------------------------------

# 24. Component Principles

Components should be:

-   composable
-   visually isolated
-   easy to remove
-   responsive
-   animation-aware
-   independent from backend implementation

Marketing components should not directly depend on backend internals.

The landing page should primarily:

-   display product information
-   animate representative UI
-   navigate to existing application routes

------------------------------------------------------------------------

# 25. Data / Backend Boundary

The marketing page should not introduce new backend dependencies just to
display animations.

Avoid:

``` text
Landing page → backend request → fake analytics state
Landing page → AI API → decorative animation
Landing page → blockchain RPC → decorative animation
```

Instead:

``` text
Landing page
   ↓
Static / deterministic product demonstration
   ↓
Existing application CTA
```

When the user enters the real application, existing backend behavior
takes over.

------------------------------------------------------------------------

# 26. Regression Safety

Before merging, verify:

### Auth

-   Login
-   Registration
-   Session persistence
-   Logout

### Contracts

-   Upload
-   Contract list
-   Contract status
-   Invitations if present
-   Contract details

### AI

-   Analysis request
-   Results
-   Risk information
-   Missing clauses
-   Negotiation points

### Signing

-   Wallet connection
-   Signature request
-   Signature submission
-   Multi-party signing if implemented

### Blockchain

-   Finalization
-   Hash anchoring
-   Blockchain record

### Verification

-   Verification request
-   Hash comparison
-   Result display

No marketing redesign should break these flows.

------------------------------------------------------------------------

# 27. Implementation Order

Execute in this exact order unless the existing codebase dictates a
safer variation:

``` text
1. Audit existing project
2. Record route/API boundaries
3. Create/standardize design tokens
4. Build Navbar
5. Build Footer
6. Build Hero structure
7. Build Hero product animation
8. Build Problem section
9. Build Workflow section
10. Build Product Demo
11. Build AI section
12. Build Signing section
13. Build Blockchain/Integrity section
14. Build Verification section
15. Build Final CTA
16. Add legal pages based on actual data practices
17. Add SEO metadata
18. Add responsive behavior
19. Add reduced-motion behavior
20. Performance pass
21. Full application regression test
22. Deploy
```

------------------------------------------------------------------------

# 28. Definition of Done

The redesign is complete only when:

-   The site looks like a coherent legal-tech product.
-   The hero immediately explains what LegalVault does.
-   The hero contains an actual product visualization.
-   The workflow is understandable without reading documentation.
-   AI analysis is visually demonstrated.
-   Signing is visually demonstrated.
-   Verification is visually demonstrated.
-   Footer is complete and professional.
-   Legal pages exist only where their content can be supported.
-   No fake statistics or customers exist.
-   No unsupported compliance claims exist.
-   No unsupported security claims exist.
-   No random decorative 3D elements exist.
-   Animations are purposeful.
-   Mobile works.
-   Reduced motion works.
-   Existing application routes work.
-   Backend functionality remains unchanged.
-   No API contracts were broken.
-   No database changes were introduced solely for marketing.
