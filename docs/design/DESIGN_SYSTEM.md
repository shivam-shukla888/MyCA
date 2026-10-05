# myCA Design System

## Source of truth

The uploaded Stitch export's `sovereign_ledger/DESIGN.md` is the base design reference.


## Source of truth: uploaded Stitch ZIP

The current Stitch export contains:
- `home_myca_financial_operating_system/code.html` + screenshot
- `money_net_worth_cash_flow_ledgers/code.html` + screenshot
- `goals_wealth_milestones_simulator/code.html` + screenshot
- `ask_myca_private_advisory_desk/code.html` + screenshot
- `sovereign_ledger/DESIGN.md`

Observed design-system facts:
- Surface foundation: `#f9f9f7`
- Primary: `#000000`
- Primary container: `#131b2e`
- Secondary: `#486458`
- Secondary container: `#c7e7d7`
- Tertiary container: `#331200`
- Error: `#ba1a1a`
- On-surface: `#1a1c1b`
- Fonts: Newsreader for display/headlines; Manrope for body, labels and numerals.
- Desktop display size in the source system: 48px / 56px.
- Mobile display size: 36px / 44px.
- Spacing tokens include 4px, 8px, 16px, 24px and 40px equivalents.
- Rounded tokens are 4px, 8px, 12px, 16px, 24px and full.
- The design uses Material Symbols for icons.
- The visual philosophy is quiet, authoritative and human, and explicitly rejects neon gradients, luminous shadows and AI-spark/robot visual tropes.


## Responsive layout

Source design describes:
- desktop: 12-column grid
- tablet: 8-column grid
- mobile: 4-column grid

The implementation must preserve responsive intent rather than merely shrinking desktop layouts.

## Shape

Use the source system's rounded scale. Do not introduce a competing radius language.

## Visual principles

- quiet
- authoritative
- human
- editorial/private-wealth feel
- high information quality without visual noise

Avoid:
- AI sparkle icons
- robot/brain graphics
- neon gradients
- excessive glassmorphism
- futuristic glowing cards
- gamified financial fear/FOMO patterns

## Simplicity layer

Technical terms should be translated into ordinary language where possible.

Examples:
- Net Worth -> Meri total financial value
- Liabilities -> Mera karz
- Cash Flow -> Paisa aaya / paisa gaya
- Asset Allocation -> Paisa kahan laga hai
- Tax Liability -> Kitna tax dena pad sakta hai

Use progressive disclosure:
1. simple answer
2. short explanation
3. calculation/source/details
