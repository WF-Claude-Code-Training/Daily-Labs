# Use Case Presentation Guide

## Structure: Bring Your Own Greenfield Project

### Before the Session

Each person should select a **greenfield project** from their own line of work. Choose something real enough that a plan, build, and test cycle makes sense, such as:

- A script
- A small tool
- A workflow
- A report generator
- Another project that fits the person's role

Keep the concept broad, but arrive with **two to three concrete components** already identified. Do not plan the entire project in advance.

### During Day 3

Each person will work through the governed workflow and select **two to three components** to build during the session. Each component should map to a Skill or subagent use:

- **Component A:** Something that reuses or creates a Skill, such as a formatting convention, domain checklist, or repeatable transformation.
- **Component B:** Something delegated to a subagent, such as a research or lookup task, test-writing task, or review task. Verify the result through diff review before merging.
- **Component C (optional):** A second subagent or Skill combination, or the safety-control component, such as a hook or guardrail configured for the project.

Run the same governed loop practiced on Days 1 and 2 for each component:

1. Enter **plan mode**.
2. Reach a **checkpoint**.
3. Perform a **diff review**.
4. Run **tests as a gate**.

This process creates the evidence trail, including Git log entries and audit log entries if configured, that each person will cite in their capstone report.

### Track Evidence as You Go

Record the following during the session, rather than reconstructing the numbers from memory afterward. Every number should be backed by evidence:

- **Skills used or created**, with a one-line benefit for each
- **Subagents invoked**, including the verification step that confirmed each result was satisfactory
- **Token usage per line of code produced**, surfaced by the tool or estimated from API or CLI usage logs
- **The hook or guardrail configured**, including why it was selected

### After Training Ends

Each person's project continues with their own LoB team. The Day 3 session is the **seed and proof of concept**, not the finished product.

The two to three components built during the session become the reference pattern. This includes:

- Packaged Skills
- Defined subagent roles
- A configured guardrail

The team can extend this pattern afterward.

## Quick Preparation Checklist

Each person should confirm that they have:

- [ ] Chosen a greenfield project scoped to two to three buildable components
- [ ] Started a token-usage-per-LoC table to complete live, rather than estimating after the fact
- [ ] Identified one hook or guardrail to describe generically, without project-specific business content
- [ ] The individual ready to field questions and answers

## Schedule

| Time | Block |
| --- | --- |
| 8:30 am to 12:30 pm ET | Build capstone (4 hours) |
| 12:30 pm to 1:30 pm | Lunch |
| 1:30 pm to 2:25 pm ET | Build capstone: final polish and evidence preparation |
| 2:25 pm to 2:30 pm | Kickoff: confirm presenter list, format, and running order |
| 2:30 pm to approximately 3:50 pm | Presentations for approximately nine participants |
| 3:50 pm to 4:00 pm | Wrap-up and close |

## Continue on Capstone and complete evidence preparation

The final 55-minute build block, should be used to complete pending capstone work and then capture the token-usage-per-LOC table.

This preparation separates a presenter who can support their numbers live from one who is searching for them during the presentation.

## Presentation Format

The presentation window is **80 minutes, from 2:30 pm to 3:50 pm**.

| Format | Content | Questions and answers | Approximate total per person | Capacity in 80 minutes |
| --- | ---: | ---: | ---: | ---: |
| Full slot | 5 minutes | Approximately 3 minutes | Approximately 8 minutes | Approximately 9 people |
