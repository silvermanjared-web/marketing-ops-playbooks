# CRO Test Planning Framework

A 90-day conversion rate optimization roadmap structured in three phases. Each phase builds on the previous — quick wins establish testing velocity, foundation tests address structural issues, and optimization tests pursue compounding gains.

## Principles

**Test one variable at a time.** Multivariate tests require traffic volumes most B2B and mid-market sites do not have. Sequential A/B tests with clear isolation produce actionable results faster.

**Statistical rigor is non-negotiable.** A test that runs for three days on 200 visitors proves nothing. Define sample size requirements before launch, not after you see a result you like.

**Document everything.** The value of a CRO program compounds over time. A test that "failed" teaches you something about your audience. But only if someone writes down what was tested, what happened, and what it means.

**Prioritize by impact and effort.** Not all tests are equal. A headline test on a page with 50,000 monthly visitors matters more than a button color test on a page with 500.

---

## Phase 1: Quick Wins (Weeks 1-4)

**Goal:** Establish testing velocity and capture low-effort gains.

Quick wins are not trivial. They are high-confidence changes based on known UX best practices or obvious friction points. The goal is to generate early results that build organizational buy-in for the program.

### Test Categories

| Test Area | Example Hypotheses |
|-----------|-------------------|
| Form optimization | Reducing form fields from 8 to 5 will increase completion rate by 15%, because most users abandon at optional fields |
| Headline clarity | Replacing the feature-focused headline with a benefit-focused headline will increase CTA clicks by 10%, because users scan for relevance before reading details |
| CTA specificity | Changing "Submit" to "Get Your Free Assessment" will increase form starts by 12%, because specific CTAs set clearer expectations |
| Mobile friction | Making the primary CTA sticky on mobile will increase mobile conversion rate by 8%, because 60%+ of users never scroll to the below-fold CTA |
| Page speed | Reducing page load time from 4.2s to under 2s will decrease bounce rate by 20%, because each additional second of load time increases bounce probability |

### Phase 1 Cadence

- Week 1: Audit current pages, identify friction points, set up analytics tracking
- Week 2: Launch first 2 tests
- Week 3: Monitor, launch 1-2 additional tests
- Week 4: Analyze results, document learnings, plan Phase 2

---

## Phase 2: Foundation (Weeks 5-8)

**Goal:** Address structural conversion issues — layout, information architecture, and trust.

Foundation tests tackle the elements that frame the entire conversion experience. These take longer to build and longer to reach significance, but they move the needle more than surface-level changes.

### Test Categories

| Test Area | Example Hypotheses |
|-----------|-------------------|
| Page layout | Moving social proof above the fold will increase time-on-page by 25% and form starts by 10%, because trust signals reduce evaluation anxiety |
| Social proof format | Replacing logo bars with specific outcome metrics ("2,400 companies reduced costs by 30%") will increase CVR by 8%, because specificity is more persuasive than brand association |
| Navigation simplification | Removing the top navigation on landing pages will increase conversion rate by 15%, because navigation provides escape routes from the conversion path |
| Content hierarchy | Leading with the problem statement instead of the product description will increase scroll depth by 30%, because users need to feel understood before they evaluate solutions |
| Value proposition | Testing three distinct value proposition angles (cost savings, time savings, risk reduction) will identify which resonates most with the primary audience segment |

### Phase 2 Cadence

- Week 5: Design and develop foundation tests based on Phase 1 learnings
- Week 6: Launch 2 structural tests
- Week 7: Monitor, iterate on test variants if needed
- Week 8: Analyze, document, incorporate winners into default experience

---

## Phase 3: Optimization (Weeks 9-12)

**Goal:** Pursue segmentation, personalization, and compounding gains.

Optimization tests build on the foundation. By this phase, you know what your audience responds to. Now test whether different segments respond to different things.

### Test Categories

| Test Area | Example Hypotheses |
|-----------|-------------------|
| Audience segmentation | Showing industry-specific case studies to visitors from identified verticals will increase CVR by 20%, because relevance reduces the mental work of self-qualifying |
| Traffic source alignment | Customizing the landing page headline to match the ad copy that drove the visit will increase conversion rate by 12%, because message match reduces cognitive dissonance |
| Return visitor experience | Showing a simplified form (pre-filled where possible) to return visitors will increase conversion rate by 25%, because repeat visits signal high intent |
| Urgency and scarcity | Adding time-limited offer framing to high-intent pages will increase conversion rate by 10%, because urgency compresses the decision timeline |
| Post-conversion flow | Optimizing the thank-you page with next steps and referral prompts will increase downstream engagement by 15%, because post-conversion is a peak attention moment |

### Phase 3 Cadence

- Week 9: Segment analysis, personalization planning
- Week 10: Launch segmented tests
- Week 11: Monitor, launch additional optimizations
- Week 12: Full program review, plan next quarter

---

## Hypothesis Structure

Every test must have a written hypothesis before launch. No exceptions.

**Format:**
> If we [specific change], then [specific metric] will [direction] by [estimated amount], because [reasoning based on evidence or principle].

**Good example:**
> If we replace the generic hero image with a product screenshot showing the dashboard, then demo request rate will increase by 12%, because showing the product reduces uncertainty about what the prospect is signing up for.

**Bad example:**
> If we make the page better, conversions will go up.

The hypothesis does not need to be correct. It needs to be specific enough that the test result either confirms or refutes it.

---

## Statistical Requirements

| Parameter | Minimum Requirement |
|-----------|-------------------|
| Confidence level | 95% (p < 0.05) |
| Statistical power | 80% minimum |
| Minimum detectable effect | Define before test launch — typically 10-20% relative lift for most pages |
| Sample size | Calculate using the above parameters. Do not stop a test early because one variant "looks" better. |
| Test duration | Minimum 2 full business weeks to capture day-of-week effects |
| Traffic allocation | 50/50 split for two-variant tests. Adjust for multi-variant. |

### When to Call a Test

- **Winner:** Reached required sample size AND statistical significance AND the result holds across the full test duration (not just a subset of days)
- **No winner:** Reached required sample size AND no statistical significance. Document the null result — it is still a learning.
- **Inconclusive:** Did not reach required sample size within a reasonable timeframe. The page does not have enough traffic for this test. Try a higher-impact change or a different page.

---

## Prioritization Framework

Use ICE scoring to rank tests:

| Factor | Score (1-10) | Definition |
|--------|-------------|------------|
| **I**mpact | How much will this move the target metric if it wins? | |
| **C**onfidence | How confident are you it will win, based on evidence? | |
| **E**ase | How easy is it to implement and launch? | |

**ICE Score = (I + C + E) / 3**

Rank all proposed tests by ICE score. Run the highest-scoring tests first. Revisit the backlog after each phase.

---

## Reporting Template

After each test, document:

1. **Hypothesis** — What you expected and why
2. **Test design** — What changed, traffic split, duration
3. **Results** — Statistical significance, lift/decline, confidence interval
4. **Segments** — Did the result hold across devices, sources, geographies?
5. **Decision** — Implement winner / revert / iterate
6. **Learning** — What this tells you about your audience, applicable to future tests
