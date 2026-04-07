# FreshPowder — Go-To-Market Strategy

## Product Summary

FreshPowder is a ski & snowboard deal aggregator that tracks prices across 15+ North American retailers every 6 hours, matches expert review scores, and surfaces the best deals through a fast, filterable interface. It is invite-gated to create exclusivity and control growth.

**Live at:** https://snow-deals.onrender.com

---

## Target Audience

### Phase 1: Chinese Diaspora Skiers in North America (Seed)
- Active in WeChat ski groups, Rednote (小红书), USCardForum (USCF)
- Price-sensitive, deal-oriented, often buy gear online
- Strong word-of-mouth culture within tight community groups
- Many are intermediate skiers upgrading gear = high purchase intent

### Phase 2: Broader North American Ski Community (Scale)
- Reddit r/skiing, r/snowboarding, r/skideals
- Facebook ski groups (regional: "Colorado Ski Deals", "PNW Ski Swap", etc.)
- Ski forums: TGR (TetonsGravityResearch), EpicSki, SkiTalk
- Deal-hunting communities: Slickdeals, FatWallet

### Phase 3: International (Future)
- Add European retailers (Blue Tomato, Snowinn, Bergfreunde)
- Add Japanese retailers for the Japan ski market

---

## Repo Visibility

**Status: Private** (changed 2026-04-07)

Rationale: Scraper configs, store-specific selectors, categorization rules, and keyword lists are competitive advantages. Keeping the repo private prevents cloning. GitHub Actions and Render deployment work identically on private repos.

---

## Revenue Model

### Stage 1: Free + Affiliate Links (Now → 1,000 users)
- Replace direct retailer links with affiliate links where available
- Major programs to join:
  - **evo** — AvantLink affiliate program (8-12% commission)
  - **Backcountry/Steep & Cheap** — AvantLink (5-7%)
  - **REI** — AvantLink (5%)
  - **Moosejaw** — AvantLink (7-10%)
  - **The House** — AvantLink / ShareASale
  - **Altitude Sports** — direct affiliate program
  - **Amazon** — Amazon Associates (4-8% on sporting goods)
- Estimated revenue: ~$2-5 per click-through-purchase at average $300 cart = $1-3 per conversion
- At 1% conversion rate on 100 daily clicks = $1-3/day = **$30-90/month early stage**

### Stage 2: Freemium Features (1,000+ users)
Keep core deal browsing free. Add paid tier ("FreshPowder Pro", ~$5-8/month or $49/year):
- **Price alerts** — Get notified when a specific product drops below your target price
- **Price history charts** — See 30/60/90-day price trends per product
- **Size watchlist** — Track your sizes across brands, get notified when your size is in stock + on sale
- **Early access** — See deals 1 hour before free users (scrape results held briefly)
- **No ads** — If we ever add sponsor placements

### Stage 3: Sponsored Placements (5,000+ users)
- Featured store/brand placements in the deal grid (clearly labeled "Sponsored")
- Newsletter sponsorships
- Seasonal campaign partnerships with retailers

### Revenue Projection (Conservative)
| Stage | Users | Monthly Revenue | Source |
|-------|-------|----------------|--------|
| Seed | 100 | $0 | Free, no affiliate yet |
| Early | 500 | $50-150 | Affiliate links |
| Growth | 2,000 | $300-800 | Affiliate + early Pro subs |
| Scale | 10,000 | $2,000-5,000 | Affiliate + Pro + sponsors |

---

## Invitation Model & Virality

### Current System
- Invite codes are human-readable: `POWDER-SUMMIT-42`
- Each code allows 5 uses
- Admin generates codes manually via `/admin/codes`
- Waitlist captures emails for users without codes

### Proposed Viral Loop

**"Give 3, Get Perks"**

1. New user signs up with an invite code
2. They immediately receive **3 personal invite codes** to share
3. When all 3 codes are used, the original user unlocks a perk:
   - Badge on their profile ("Early Rider" / "Powder Pioneer")
   - Could unlock Pro features for 1 month when we have them
4. Their invitees also get 3 codes each → exponential growth

**Implementation:**
- Link each generated code to the inviter's session
- Track referral chain: who invited whom
- Auto-generate 3 codes on successful signup
- Show "Your invite codes" section in the UI (new route: `/my-codes`)
- Each code is single-use (not 5) to increase sharing urgency

**Viral coefficient math:**
- Each user gets 3 invites
- If 50% of invites are used → 1.5 new users per user
- Viral coefficient K = 1.5 (>1.0 = exponential growth)
- 100 seed users → 150 → 225 → 337 → 506 → ... ~1,000 in 5 cycles

### Code Distribution Strategy
| Channel | Codes | Format |
|---------|-------|--------|
| WeChat groups (personal) | 20 codes | Post with screenshot + code |
| Rednote post | 10 codes | "Comment to get a code" (engagement bait) |
| USCardForum thread | 10 codes | Forum post with first-come codes |
| Reddit r/skideals | 5 codes | Comment drop |
| Friends & ski buddies | 10 codes | Direct message |

**Total seed: ~55 codes → potential reach of 55 × 1.5^n users**

---

## Channel Strategy

### Tier 1: Owned / Direct (Week 1-2)

**WeChat Ski Groups**
- Post a screenshot of the UI showing a great deal (high discount, known brand)
- Include 3-5 invite codes directly in the message
- Message template: "Built a tool that tracks ski deals across 15+ stores every 6 hours. Found [Brand X] at 60% off yesterday. Here are a few invite codes if you want to try: [codes]. Let me know if you want more."
- Follow up with periodic "deal of the day" screenshots to keep engagement

**Rednote (小红书)**
- Create a post: "我做了一个滑雪装备比价网站" (I built a ski gear price comparison site)
- Include screenshots of the landing page and deal grid
- Drop 5-10 invite codes in comments to first responders
- Use hashtags: #滑雪 #滑雪装备 #省钱 #北美滑雪 #ski
- Post weekly "best deals this week" content to build following

**USCardForum**
- Create a thread in the deals/lifestyle section
- Position as: "Free tool for tracking ski/snowboard deals — invite-only beta"
- USCF users are deal-savvy, will appreciate the discount % focus
- Drop codes, ask for feedback

### Tier 2: Community Seeding (Week 2-4)

**Reddit**
- r/skideals — Most directly relevant. Post when you find an exceptional deal, mention "found via my deal tracker" with link
- r/skiing and r/snowboarding — Participate genuinely, mention FreshPowder when relevant (don't spam)
- r/SkiGear — Gear discussion, mention price tracking when someone asks "is this a good price?"
- Key: Be a helpful community member first, promoter second. Reddit hates self-promotion.

**Facebook Ski Groups**
- Regional groups: "Colorado Ski & Ride Deals", "PNW Ski Deals", "Northeast Ski Deals"
- Same approach: share genuine deals, mention the tool
- Many of these groups have thousands of members

**Ski Forums**
- TetonsGravityResearch (TGR) forums — Gear Talk section
- Newschoolers — Park/freestyle audience, younger demographic
- EpicSki — Older/more affluent skier demographic

### Tier 3: Content & SEO (Month 2+)

**Blog / Content Strategy**
- "Best Ski Deals This Week" — Weekly roundup post
- "When to Buy Ski Gear" — Seasonal buying guide (evergreen SEO)
- "Best Budget Skis 2025-2026" — Buyer's guide linking to tracked deals
- Host on a subdomain or `/blog` route

**SEO for Landing Page**
- Landing page (`/invite`) is already indexable
- Add OG image for social sharing
- Target keywords: "ski deals", "snowboard deals", "ski gear sale", "best ski prices"

### Tier 4: Partnerships (Month 3+)
- Ski clubs and university ski teams — Offer bulk invite codes
- Ski podcasts — Sponsor a segment or offer codes to listeners
- Ski influencers on Instagram/YouTube — "Built by a skier, for skiers" angle

---

## Launch Timeline

### Week 1: Soft Launch
- [ ] Join affiliate programs (evo, Backcountry, REI via AvantLink)
- [ ] Generate 60 invite codes
- [ ] Seed WeChat groups (20 codes)
- [ ] Post on Rednote (10 codes)
- [ ] Post on USCardForum (10 codes)
- [ ] Share with friends/ski buddies (10 codes)
- [ ] Monitor analytics dashboard for click-through and usage

### Week 2: Gather Feedback
- [ ] Check admin stats: which stores get most clicks? Which filters used?
- [ ] Collect user feedback via WeChat / DM
- [ ] Fix any reported bugs or UX issues
- [ ] Implement viral invite loop (auto-generate codes on signup)

### Week 3-4: Expand
- [ ] Post on Reddit r/skideals
- [ ] Join Facebook ski deal groups
- [ ] Create weekly "best deals" content for Rednote
- [ ] Set up affiliate link replacement in card URLs
- [ ] Track affiliate conversions

### Month 2: Content & Growth
- [ ] Build email list from waitlist signups
- [ ] Send first "Weekly Deals" email
- [ ] Start blog content for SEO
- [ ] Implement price history tracking (Pro feature foundation)
- [ ] Evaluate user numbers and viral coefficient

### Month 3+: Monetize
- [ ] Launch Pro tier if user base > 1,000
- [ ] Approach retailers for sponsored placements
- [ ] Expand to European retailers if demand exists

---

## Key Metrics to Track

| Metric | Tool | Target (Month 1) |
|--------|------|-------------------|
| Registered users | Admin dashboard | 200 |
| Daily active users | Event analytics | 30 |
| Deal clicks/day | `/admin/stats` | 100 |
| Invite code conversion | Auth DB queries | 60% of codes used |
| Viral coefficient (K) | Referral tracking | > 1.0 |
| Affiliate revenue | AvantLink dashboard | First $ earned |
| Waitlist signups | Admin waitlist tab | 50 |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Retailers block scraper | No deals to show | Rotate user agents, respect rate limits, have backup selectors |
| Low viral coefficient | Slow growth | Increase invite codes per user, add sharing incentives |
| Seasonality (summer slump) | Usage drops May-Oct | Add off-season deals (hiking, camping gear), or accept seasonal nature |
| Competitor launches similar tool | Market share split | First-mover advantage, community building, unique features (reviews integration) |
| Free tier too generous | No Pro conversion | Gate advanced features (alerts, history) early, even before charging |

---

## Open Decisions

- [ ] **Affiliate program applications** — Need to apply to AvantLink, Amazon Associates. Some require existing traffic numbers.
- [ ] **Email infrastructure** — Need a transactional email provider for waitlist/alerts (Resend, Postmark, or SendGrid free tier)
- [ ] **Custom domain** — Consider `freshpowder.deals` or `getfreshpowder.com` instead of `snow-deals.onrender.com`
- [ ] **Bilingual support** — Should the landing page / UI have a Chinese language option for Phase 1 audience?
- [ ] **Mobile app** — PWA (Progressive Web App) could be a quick win for mobile users without building native apps
