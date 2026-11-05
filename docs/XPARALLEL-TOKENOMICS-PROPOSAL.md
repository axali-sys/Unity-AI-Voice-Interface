# XParallel Tokenomics Proposal

**Version:** 1.0  
**Status:** Design proposal only — not issued, deployed, audited, or approved for sale  
**Integration target:** OneAI Workspace / XParallel AI Verse  
**Branch:** `feat/xparallel-tokenomics-design`

## 1. Purpose and architecture fit

XParallel is the proposed interoperability, discovery, coordination, and governed-execution layer for independent AI agents, services, and workspaces. OneAI remains the human-facing workspace and command center. The Parallel Verse is the persistent ecosystem layer. This proposal describes a possible governance and ecosystem-participation token; it does not create a token contract, wallet, sale, exchange listing, or payment requirement.

The token must remain separate from authentication and authorization. It must never replace `XP_TOKEN`, user credentials, UIDaaS/session identity, workspace permissions, execution approval, or billing controls. Holding a proposed token must not grant privileged API access or bypass Omni approval gates.

## 2. Fixed-supply assumptions

- Proposed maximum supply: **1,000,000,000 units**.
- Assumed price for scenario math only: **US$1.00**.
- Arithmetic fully diluted valuation at that assumption: **US$1,000,000,000**.
- Founder allocation: **500,000,000 units (50%)**.
- Inflation: none proposed; any future change requires a separately reviewed governance and legal process.
- Current issued supply: **0** under this proposal.
- Current circulating supply: **0** under this proposal.
- Current market price / market capitalization: **not established**.

The US$1 price is not a target, peg, guarantee, forecast, or statement of current market value. FDV is maximum supply multiplied by an assumed price, not cash raised or an independently supported company valuation.

## 3. Proposed allocation

| Category | Units | Share | Intended use |
|---|---:|---:|---|
| Founders | 500,000,000 | 50% | Long-term creation and leadership, subject to vesting |
| Ecosystem treasury | 200,000,000 | 20% | Grants, integrations, infrastructure, research |
| Community and adoption | 120,000,000 | 12% | Transparent participation programs |
| Contributors and developers | 80,000,000 | 8% | Approved work, tools, maintenance |
| Strategic partnerships | 50,000,000 | 5% | Milestone-based ecosystem collaborations |
| Security and liquidity reserve | 50,000,000 | 5% | Audits, incident response; any liquidity use separately approved |
| **Total** | **1,000,000,000** | **100%** | |

## 4. Vesting and circulation policy

- Founders: 12-month cliff followed by monthly vesting over 48 months. No founder vesting during the first 12 months; then approximately 10.42 million units per month for 48 months.
- Contributors: 12-month cliff followed by monthly vesting over 36 months.
- Treasury: release only against approved budgets, milestones, and public reporting.
- Community: gradual, eligibility-based releases; no unrestricted day-one distribution.
- Partnerships: milestone-based release with conflict-of-interest review.
- Security/liquidity reserve: initially locked; movements require documented approval and reporting.

Illustrative cumulative circulating-supply ceilings for planning are: launch 30M; year 1 80M; year 2 180M; year 3 300M; year 4 450M; year 5 600M. These are **not a committed issuance schedule**. Actual circulation must be defined by enforceable transfer restrictions and on-chain evidence; allocations held in a treasury are not automatically circulating.

Before any issuance, publish the wallet-by-wallet allocation, vesting contracts, unlock dates, and a reconciliation method. Avoid treating all unlocked tokens as liquid at the assumed price.

## 5. Governance and utility

Possible uses, only if implemented and legally approved:
- Vote on ecosystem grants, integration priorities, standards proposals, and community budgets.
- Participate in transparent developer grant and interoperability programs.
- Help prioritize audits, identity tooling, abuse prevention, and incident response.

Governance safeguards:
- Token voting must not grant API roles, reveal secrets, authorize deployments, execute agents, or bypass workspace isolation.
- Use proposal thresholds, quorum, vote disclosure, conflict-of-interest rules, timelocks for consequential changes, and independent controls over treasury movements.
- Consider vote caps, delegation controls, or other anti-capture mechanisms because the founder allocation is 50%.
- Keep essential product access available without speculative token ownership wherever feasible.
- Do not promise dividends, guaranteed returns, buybacks, price support, or exchange liquidity.

## 6. Architecture integration

Logical boundaries:
- **OneAI Workspace:** displays proposal status and, if later approved, governance information.
- **XParallel / Parallel Verse:** could host a future governance adapter and public proposal index.
- **Omni:** retains plan → approval → execution → verification controls. Token votes cannot substitute for operational approval.
- **UIDaaS / authz:** remains the source of authenticated principal, roles, and access policy; token balances are not authorization credentials.
- **Jellybox / artifact layer:** may retain proposal documents and audit evidence only through existing verified storage capabilities.
- **Billing:** current API billing remains separate. No token payments or balance accounting are enabled by this proposal.

Implementation should be staged: design documentation → local/read-only scenario model → legal/economic review → test-only prototype if separately approved → separate issuance decision. This branch only adds the proposal and read-only model; it does not connect a chain, create wallets, or enable transfers.

## 7. Dilution, valuation, and risks

At an assumed US$1 price, the arithmetic FDV is US$1 billion. This is hypothetical only. If 100 million units actually circulated at US$1, the arithmetic circulating market capitalization would be US$100 million, but this is not cash available to the project and does not establish that the price can be realized. Large unlocks or concentrated holdings may materially affect market price and liquidity.

A fixed maximum supply only prevents inflation if the eventual contract enforces the cap and cannot be upgraded to bypass it. Unlocks can still dilute holders economically by increasing tradable supply. The 50% founder allocation creates concentration and governance-capture risks and should be independently reviewed before launch.

Legal and operational review must address jurisdiction and issuer structure; securities/financial-services classification; consumer disclosures; AML/CFT and sanctions; tax/accounting; privacy; governance liability; cybersecurity and smart-contract audit; custody; market integrity; and any applicable registration or licensing. Legal classification depends on facts, distribution, functionality, and how the token is marketed—not on calling it a “governance token.”

Official starting references:
- US SEC, “Transactions Involving Crypto Assets” (updated April 22, 2026): https://www.sec.gov/resources-small-businesses/capital-raising-building-blocks/transactions-involving-crypto-assets
- FATF, “Virtual Assets”: https://www.fatf-gafi.org/en/topics/virtual-assets.html

These are reference points, not legal advice for South Sudan or any other jurisdiction. Obtain qualified counsel before accepting funds, distributing transferable tokens, or operating a token-related service.

## 8. Valuation scenarios (not predictions)

| Assumed unit price | FDV at 1B maximum supply | Arithmetic value at 100M circulating |
|---:|---:|---:|
| $0.001 | $1,000,000 | $100,000 |
| $0.01 | $10,000,000 | $1,000,000 |
| $0.10 | $100,000,000 | $10,000,000 |
| $1.00 | $1,000,000,000 | $100,000,000 |

Token market capitalization is not the valuation of the underlying XParallel company. Business valuation must be assessed separately using verified technology, intellectual-property rights, users, revenue, costs, growth, and comparable transactions.

## 9. Non-goals and release gates

This proposal does **not**:
- issue or mint tokens;
- deploy smart contracts or create wallets;
- sell, distribute, list, or advertise a token for investment;
- change production, DNS, billing, authentication, or existing OneAI/XParallel routes;
- represent the proposed $1 price as current market price or guarantee;
- claim that governance, treasury, or token-transfer capabilities are implemented.

Any later real issuance requires a separate explicit approval after legal review, independent tokenomics review, threat modeling, smart-contract audit, custody/treasury controls, public disclosures, and tested governance procedures.
