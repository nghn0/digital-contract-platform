# LegalVault Frontend Revamp --- Master Checklist

Use this as the implementation and QA checklist for the entire frontend
redesign.

------------------------------------------------------------------------

# A. PROJECT SAFETY

-   [ ] Existing project structure audited.
-   [ ] Current landing-page route identified.
-   [ ] Authentication routes identified.
-   [ ] Dashboard route identified.
-   [ ] Contract registry route identified.
-   [ ] Contract upload flow identified.
-   [ ] AI analysis/intelligence route identified.
-   [ ] Wallet/signing route identified.
-   [ ] Verification route identified.
-   [ ] Existing API clients identified.
-   [ ] Existing shared layouts identified.
-   [ ] Existing environment-variable dependencies identified.
-   [ ] Existing Supabase dependencies identified.
-   [ ] Existing blockchain/wallet dependencies identified.

## Backend safety

-   [ ] No API endpoints changed.
-   [ ] No API response contracts changed.
-   [ ] No auth logic changed.
-   [ ] No database schema changed.
-   [ ] No Supabase schema changed.
-   [ ] No backend middleware changed.
-   [ ] No blockchain logic changed.
-   [ ] No wallet signing logic changed.
-   [ ] No AI service changed.
-   [ ] No gRPC service changed.
-   [ ] No environment variables renamed or removed.
-   [ ] Existing dashboard functionality preserved.

------------------------------------------------------------------------

# B. BRAND / DESIGN SYSTEM

## Brand

-   [ ] LegalVault name consistently used.
-   [ ] Logo is consistent.
-   [ ] Favicon exists.
-   [ ] Product mark works on dark background.
-   [ ] Product mark works at small sizes.

## Colors

-   [ ] Near-black background.
-   [ ] Dark surface color.
-   [ ] Warm gold accent.
-   [ ] Bright gold accent.
-   [ ] Ivory/white primary text.
-   [ ] Muted secondary text.
-   [ ] Subtle borders.
-   [ ] No excessive neon colors.

## Typography

-   [ ] Serif display font selected.
-   [ ] Sans-serif UI font selected.
-   [ ] Headings have clear hierarchy.
-   [ ] Body text remains readable.
-   [ ] Mobile type scale is appropriate.

## Overall aesthetic

-   [ ] Premium legal-tech.
-   [ ] Modern SaaS.
-   [ ] Subtle Web3.
-   [ ] Not generic crypto.
-   [ ] Not generic AI startup.
-   [ ] Not obviously a college project.
-   [ ] Not overdesigned.

------------------------------------------------------------------------

# C. NAVBAR

-   [ ] Logo links to home.
-   [ ] Product link works.
-   [ ] How It Works link works.
-   [ ] Verification link works.
-   [ ] Sign-in/access CTA works.
-   [ ] Mobile navigation works.
-   [ ] Navbar remains readable over hero.
-   [ ] Navbar has appropriate scroll behavior.
-   [ ] No backend functionality embedded in navbar.

------------------------------------------------------------------------

# D. HERO

## Copy

-   [ ] Clear product value proposition.
-   [ ] Headline communicates contract understanding + integrity.
-   [ ] Supporting copy explains AI + signing + verification.
-   [ ] Primary CTA is obvious.
-   [ ] Secondary CTA exists.
-   [ ] CTA destinations are real existing routes.
-   [ ] No unsupported claims.

## Recommended headline

-   [ ] "Contracts should be easier to understand --- and harder to
    tamper with."

## Recommended supporting concepts

-   [ ] AI contract analysis.
-   [ ] Cryptographic verification.
-   [ ] Wallet signing.
-   [ ] Blockchain-backed record.

## Visual

-   [ ] Actual contract UI shown.
-   [ ] AI state shown.
-   [ ] Risk score shown.
-   [ ] Clause/risk state shown.
-   [ ] Signing state shown.
-   [ ] Verification state shown.
-   [ ] Visual is recognizable as the product.
-   [ ] No random 3D object.

------------------------------------------------------------------------

# E. HERO ANIMATION

## State machine

-   [ ] Upload state.
-   [ ] Upload progress.
-   [ ] AI analysis state.
-   [ ] Scan/extraction animation.
-   [ ] Risk state.
-   [ ] Clause highlighting.
-   [ ] Signing state.
-   [ ] Wallet/signature state.
-   [ ] Hash state.
-   [ ] Blockchain record state.
-   [ ] Verification state.
-   [ ] Successful completion.
-   [ ] Loop transition.

## Animation quality

-   [ ] Approximately 10--15 second loop.
-   [ ] Smooth transitions.
-   [ ] No abrupt state changes.
-   [ ] No distracting infinite motion.
-   [ ] Animation communicates functionality.
-   [ ] Animation does not call backend purely for decoration.
-   [ ] CTA remains clickable.
-   [ ] Animation does not block scrolling.
-   [ ] Reduced-motion fallback exists.

------------------------------------------------------------------------

# F. 3D / BACKGROUND

## Verification Field

-   [ ] Near-black base.
-   [ ] Subtle gold ambient glow.
-   [ ] Subtle perspective grid.
-   [ ] Floating contract.
-   [ ] Verification ring.
-   [ ] Hash fragments.
-   [ ] Thin connection lines.
-   [ ] Minimal particles.
-   [ ] Slow parallax.
-   [ ] No visual clutter.

## Explicitly avoid

-   [ ] No generic rotating cube.
-   [ ] No giant glowing sphere.
-   [ ] No random galaxy.
-   [ ] No crypto coins.
-   [ ] No token graphics.
-   [ ] No cyberpunk neon.
-   [ ] No huge starfield.
-   [ ] No excessive particle effects.
-   [ ] No WebGL unless actually justified.

------------------------------------------------------------------------

# G. PROBLEM SECTION

-   [ ] Section exists.
-   [ ] Heading explains the pain point.
-   [ ] Manual review problem explained.
-   [ ] Contract-risk problem explained.
-   [ ] Fragmented workflow problem explained.
-   [ ] No exaggerated statistics.
-   [ ] No unsupported market claims.

Recommended heading:

> A contract can be signed in seconds. Understanding it shouldn't take
> hours.

------------------------------------------------------------------------

# H. HOW IT WORKS

-   [ ] Upload.
-   [ ] Analyze.
-   [ ] Sign.
-   [ ] Verify.

## Copy

-   [ ] Upload explanation.
-   [ ] AI analysis explanation.
-   [ ] Signing explanation.
-   [ ] Verification explanation.

## Visual

-   [ ] Workflow is animated.
-   [ ] Scroll progression is smooth.
-   [ ] Central visual changes state.
-   [ ] No scroll-jacking.
-   [ ] Mobile workflow is usable.

------------------------------------------------------------------------

# I. PRODUCT DEMO

-   [ ] Large application/browser frame.
-   [ ] Realistic LegalVault UI.
-   [ ] Contract registry state.
-   [ ] AI intelligence state.
-   [ ] Signing state.
-   [ ] Verification state.
-   [ ] Visuals reflect actual application functionality.
-   [ ] No fabricated screens that imply nonexistent capabilities.

------------------------------------------------------------------------

# J. AI INTELLIGENCE

-   [ ] Section heading explains benefit.
-   [ ] Contract shown on one side.
-   [ ] AI insights shown on other side.
-   [ ] Risk score visual.
-   [ ] Potential risk visual.
-   [ ] Missing clause visual.
-   [ ] Clause extraction visual.
-   [ ] Scan animation.
-   [ ] Visual remains readable on mobile.

Recommended heading:

> Know what's inside before you sign.

------------------------------------------------------------------------

# K. SIGNING

-   [ ] Signing section exists.
-   [ ] Participant concept shown.
-   [ ] Contract shown.
-   [ ] Wallet signing shown.
-   [ ] Signature confirmation shown.
-   [ ] Finalized record shown.
-   [ ] MetaMask terminology only used if accurate to implementation.
-   [ ] No claim that signing automatically guarantees universal legal
    enforceability.

Recommended heading:

> Sign with cryptographic confidence.

------------------------------------------------------------------------

# L. BLOCKCHAIN / INTEGRITY

-   [ ] Signed document shown.
-   [ ] Hash generation visual.
-   [ ] Blockchain record visual.
-   [ ] Verification visual.
-   [ ] Hash match visual.
-   [ ] Integrity confirmation.
-   [ ] No cryptocurrency imagery.
-   [ ] No unsupported blockchain claims.

Recommended heading:

> A contract shouldn't change after everyone signs it.

------------------------------------------------------------------------

# M. VERIFICATION

-   [ ] Verification UI exists.
-   [ ] Upload/drop area shown.
-   [ ] Verify CTA shown.
-   [ ] Document hash shown.
-   [ ] Recorded hash shown.
-   [ ] Match state shown.
-   [ ] Blockchain record shown.
-   [ ] Confirmation state shown.
-   [ ] If public verification exists, CTA links to real route.
-   [ ] If not public, demo is clearly presented as a demonstration.

------------------------------------------------------------------------

# N. THREE PRODUCT PILLARS

## AI Contract Intelligence

-   [ ] Risk detection.
-   [ ] Missing terms.
-   [ ] Negotiation points.
-   [ ] Clause extraction.

## Cryptographic Signing

-   [ ] Wallet-based signing.
-   [ ] Signature association.
-   [ ] Contract record.

## Verifiable Records

-   [ ] Hash.
-   [ ] Blockchain record.
-   [ ] Verification.

------------------------------------------------------------------------

# O. FINAL CTA

-   [ ] Final CTA exists.
-   [ ] Strong headline.
-   [ ] Short supporting copy.
-   [ ] Primary application CTA.
-   [ ] Secondary workflow CTA.
-   [ ] Correct navigation.

Recommended:

> Ready to put your next contract under verification?

------------------------------------------------------------------------

# P. FOOTER

## Structure

-   [ ] Product description.
-   [ ] Product links.
-   [ ] How it works.
-   [ ] Verification.
-   [ ] Resources.
-   [ ] Legal.
-   [ ] Privacy Policy.
-   [ ] Terms of Use.
-   [ ] Disclaimer.
-   [ ] Copyright year.

## Footer quality

-   [ ] Professional.
-   [ ] Responsive.
-   [ ] Links work.
-   [ ] No dead links.
-   [ ] No fake contact information.
-   [ ] No fake company address.
-   [ ] No fake support email.

------------------------------------------------------------------------

# Q. PRIVACY POLICY

Before publishing:

-   [ ] Authentication data verified from code.
-   [ ] Personal data collection verified.
-   [ ] Contract storage verified.
-   [ ] Contract retention verified.
-   [ ] Contract access model verified.
-   [ ] AI processing verified.
-   [ ] Third-party services verified.
-   [ ] Cookies verified.
-   [ ] Analytics verified.
-   [ ] Wallet-related information verified.
-   [ ] Blockchain-recorded information verified.
-   [ ] Deletion behavior verified.

## Do not fabricate

-   [ ] No invented GDPR compliance.
-   [ ] No invented SOC 2.
-   [ ] No invented ISO 27001.
-   [ ] No invented security certification.
-   [ ] No invented encryption claims.
-   [ ] No invented retention periods.
-   [ ] No invented data-sharing policy.
-   [ ] No invented legal jurisdiction.

------------------------------------------------------------------------

# R. TERMS / DISCLAIMER

-   [ ] Terms page only contains factual/approved terms.
-   [ ] AI disclaimer exists if appropriate.
-   [ ] Legal advice disclaimer exists.
-   [ ] No claim of universal legal enforceability.
-   [ ] No guarantee of legal validity.
-   [ ] No guarantee of perfect AI analysis.
-   [ ] No unsupported security guarantee.

Recommended concept:

> LegalVault's AI analysis is intended to assist with contract review
> and understanding. It does not replace professional legal advice.

Have the project team/guide review legal wording before publication.

------------------------------------------------------------------------

# S. UNSUPPORTED CLAIMS TO REMOVE / AVOID

-   [ ] "GDPR Compliant" unless verified.
-   [ ] "SOC 2" unless verified.
-   [ ] "ISO 27001" unless verified.
-   [ ] "Enterprise Grade" unless supported.
-   [ ] "Legally Binding Worldwide" unless legally substantiated.
-   [ ] "100% Secure."
-   [ ] "Zero Downtime."
-   [ ] "Military Grade Encryption."
-   [ ] "Guaranteed Legal Validity."
-   [ ] "10,000+ users" unless real.
-   [ ] Fake testimonials.
-   [ ] Fake customer logos.
-   [ ] Fake statistics.
-   [ ] Fake partnerships.
-   [ ] Fake awards.
-   [ ] "Secured by RSA-2048" unless confirmed by actual implementation.

------------------------------------------------------------------------

# T. 21ST.DEV / COMPONENT INSPIRATION

Use 21st.dev selectively.

Potential areas:

-   [ ] Hero animations.
-   [ ] Hero parallax.
-   [ ] Scroll media expansion.
-   [ ] Background paths.
-   [ ] Spotlight.
-   [ ] Aurora background.
-   [ ] Grid patterns.
-   [ ] Beams.
-   [ ] Animated gradients.
-   [ ] Magnetic buttons.
-   [ ] Landing-page footers.

Useful categories:

-   [ ] Hero animations.
-   [ ] Hero scroll.
-   [ ] Hero.
-   [ ] Landing page.

Do not import components just because they look impressive.

Every component must have a product/UX purpose.

------------------------------------------------------------------------

# U. TOOLING

Preferred:

-   [ ] Existing Next.js setup.
-   [ ] Existing Tailwind setup.
-   [ ] Motion / Framer Motion where useful.
-   [ ] CSS.
-   [ ] SVG.

Avoid unnecessary introduction of:

-   [ ] Three.js.
-   [ ] React Three Fiber.
-   [ ] GSAP.
-   [ ] Lenis.
-   [ ] Lottie.
-   [ ] WebGL shaders.

Only introduce heavier tooling if it is clearly justified.

------------------------------------------------------------------------

# V. PERFORMANCE

-   [ ] No huge video background.
-   [ ] No large unnecessary assets.
-   [ ] No excessive particles.
-   [ ] No expensive continuous layout animations.
-   [ ] Transform/opacity preferred.
-   [ ] Lazy-load heavy below-fold elements.
-   [ ] Animation remains smooth.
-   [ ] Mobile performance checked.
-   [ ] Lighthouse/performance check performed if practical.

------------------------------------------------------------------------

# W. ACCESSIBILITY

-   [ ] Semantic HTML.
-   [ ] Keyboard navigation.
-   [ ] Visible focus states.
-   [ ] Buttons have clear labels.
-   [ ] Links have clear labels.
-   [ ] Sufficient text contrast.
-   [ ] Decorative animation does not contain essential information
    only.
-   [ ] `prefers-reduced-motion` implemented.
-   [ ] Reduced-motion users get usable static states.
-   [ ] Mobile touch targets are appropriate.

------------------------------------------------------------------------

# X. RESPONSIVE QA

## Desktop

-   [ ] 1440px+.
-   [ ] 1920px.
-   [ ] Large desktop does not develop huge empty areas.
-   [ ] Hero remains balanced.
-   [ ] Product visualization scales correctly.

## Tablet

-   [ ] Layout transitions cleanly.
-   [ ] Navigation remains usable.
-   [ ] Product demo remains legible.

## Mobile

-   [ ] 320px--375px.
-   [ ] 390px--430px.
-   [ ] Hero readable.
-   [ ] CTA accessible.
-   [ ] Product demo readable.
-   [ ] Workflow usable.
-   [ ] Footer stacks correctly.
-   [ ] No horizontal overflow.

------------------------------------------------------------------------

# Y. SEO

-   [ ] Page title.
-   [ ] Meta description.
-   [ ] OpenGraph title.
-   [ ] OpenGraph description.
-   [ ] OpenGraph image if appropriate.
-   [ ] Favicon.
-   [ ] Appropriate heading hierarchy.
-   [ ] Semantic page structure.
-   [ ] Sitemap if appropriate.
-   [ ] Robots configuration if appropriate.

Potential title:

> LegalVault --- AI Contract Analysis & Verifiable Signing

Potential description:

> Analyze contracts with AI, sign with connected wallets, and verify
> finalized documents using cryptographic records.

Verify all claims before publishing.

------------------------------------------------------------------------

# Z. FINAL REGRESSION TEST

## Authentication

-   [ ] Login.
-   [ ] Registration.
-   [ ] Logout.
-   [ ] Session persistence.

## Contract lifecycle

-   [ ] Upload.
-   [ ] Contract storage.
-   [ ] Contract registry.
-   [ ] Status updates.
-   [ ] Invitation flow if implemented.
-   [ ] Contract retrieval.

## AI

-   [ ] Analyze contract.
-   [ ] Display analysis.
-   [ ] Risk score.
-   [ ] Missing clauses.
-   [ ] Negotiation points.
-   [ ] Error handling.

## Signing

-   [ ] Wallet connection.
-   [ ] Signature request.
-   [ ] Signature submission.
-   [ ] Multiple participants if implemented.

## Blockchain

-   [ ] Finalization.
-   [ ] Hash anchoring.
-   [ ] Blockchain record.

## Verification

-   [ ] Verify contract.
-   [ ] Hash comparison.
-   [ ] Match result.
-   [ ] Mismatch/error result.

------------------------------------------------------------------------

# AA. FINAL VISUAL QUALITY CHECK

Ask these questions before deployment:

-   [ ] Does the hero explain the product in under 5 seconds?
-   [ ] Can a visitor understand Analyze → Sign → Verify?
-   [ ] Does the website show the actual application?
-   [ ] Does the animation demonstrate rather than decorate?
-   [ ] Does the page feel premium?
-   [ ] Does it feel like legal technology?
-   [ ] Does it avoid generic crypto aesthetics?
-   [ ] Does it avoid obvious "college project" language?
-   [ ] Are all claims defensible?
-   [ ] Is the footer complete?
-   [ ] Are legal pages factual?
-   [ ] Are there no fake customers or metrics?
-   [ ] Is the page fast?
-   [ ] Is mobile polished?
-   [ ] Does reduced-motion work?
-   [ ] Did existing application functionality remain unchanged?

------------------------------------------------------------------------

# AB. FINAL ACCEPTANCE CRITERIA

The redesign should be accepted only if all of the following are true:

``` text
[ ] Product positioning is immediately clear.
[ ] Hero has a strong hook.
[ ] Hero shows the actual product concept.
[ ] Product workflow is visually demonstrated.
[ ] AI analysis is explained.
[ ] Signing is explained.
[ ] Verification is explained.
[ ] Footer is complete.
[ ] Legal pages are factual.
[ ] No unsupported claims exist.
[ ] Animations are purposeful.
[ ] 3D background is restrained.
[ ] No unnecessary dependencies were introduced.
[ ] Mobile is polished.
[ ] Accessibility requirements are met.
[ ] Existing backend/API functionality is unchanged.
[ ] Existing application flows pass regression testing.
```

------------------------------------------------------------------------

# PRODUCT WEBSITE RULE

The most important principle for the entire redesign:

> **Do not make the site look like a product by adding more decoration.
> Make it look like a product by clearly communicating a real problem,
> showing the actual solution, demonstrating the workflow, providing
> trustworthy information, and making the application easy to enter.**

The design should communicate:

``` text
CONTRACT
    ↓
UNDERSTAND
    ↓
SIGN
    ↓
VERIFY
```

Everything else is secondary.
