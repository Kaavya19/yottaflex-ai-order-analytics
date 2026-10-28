# AI prompt history and disclosure

This project was created with AI assistance in Codex. The conversation prompts that materially guided implementation are reproduced below; prompt responses are omitted. No external AI tool was used in this session.

## User prompts

The two user messages below record the project-related prompts received in this conversation. Formatting and repeated page chrome were simplified, and the substantive project requirements and FAQ points were retained. No separate prompt was submitted to another AI tool.

### Prompt 1 — submission guidance

> YottaFlex AI
> RECRUITMENT DRIVE
> Candidate Project Submission Guidelines
> Show us how you think, build, validate, and work with AI.
> YOUR CHALLENGE WINDOW
> 72 HOURS Your submission window is 72 hours. Artifact timestamps will be used to verify the window.
> 01 MAKE IT RUN
> Submit working, executable code. Include clear steps so another person can install dependencies, configure the project, run it, and verify key behavior.
> EXECUTABLE
> 02 SHOW YOUR WORK
> Use a public GitHub repository. Make the evolution of your work understandable through the code, meaningful commits, and supporting context.
> PUBLIC REPOSITORY
> 03 USE LLMs TRANSPARENTLY
> LLM tools are allowed. Submit your prompt history and explain where AI accelerated your work, where you relied heavily on it, and what you personally reviewed, changed, or validated.
> PROMPT HISTORY REQUIRED
> 04 MAKE YOUR REASONING VISIBLE
> Help reviewers understand the problem, assumptions, key decisions, trade-offs, testing approach, limitations, and how you know the solution works.
> EXPLAIN THE WHY
> BE READY TO WALK US THROUGH YOUR SOLUTION. We value sound judgment, working software, honest AI disclosure, and clear communication.

### Prompt 2 — project brief and FAQ

> Business Context / Problem
> Deliver a complete small platform that ingests two sources, validates and transforms data, loads a dimensional model, exposes analytical queries, and includes monitoring, tests, and documentation.
>
> Objective and Scope
> Deliver a working Data Engineering solution within 72 hours for: Deliver a complete small platform that ingests two sources, validates and transforms data, loads a dimensional model, exposes analytical queries, and includes monitoring, tests, and documentation. The solution should be runnable locally or in a clearly documented cloud environment, expose failures and data-quality issues, and produce measurable outputs. Target level: 0–3 years of experience. Prioritize correctness, clear design, maintainability, and evidence of testing over unnecessary complexity.
>
> Primary Actors / Systems
> Data engineer, source system or file/API producer, storage/processing layer, target analytical consumer, and pipeline operator.
>
> Business Workflow and Rules
> 1. Define source and target schemas, data types, keys, and assumptions.
> 2. Generate or provide a small reproducible sample dataset and a larger scalable dataset generator.
> 3. Implement ingestion, validation, transformation, and target publishing.
> 4. Make reruns safe; record run status, row counts, rejects, and errors.
> 5. Include automated tests and demonstrate expected results with sample queries or reports.
>
> Entities and Relationships
> Identify the source entities and their keys, relationships, grain, and important business rules. Document nullability, uniqueness, referential integrity, and any derived fields. Keep rejected or anomalous records traceable to their source. Where history matters, preserve change or event history instead of silently overwriting it.
>
> ID / Nomenclature Conventions
> Use stable, deterministic IDs; consistent snake_case table and column names; ISO-8601 timestamps; and explicit run_id / source_file fields where applicable. Document naming choices in the README.
>
> Implementation Instructions (Granular)
> Step 1 — Write a concise README, data dictionary, architecture diagram or flow description, and setup instructions.
> Step 2 — Implement the core pipeline with clear modules/functions and configurable paths or parameters.
> Step 3 — Add schema validation, business-rule checks, duplicate handling, and an explicit reject/quarantine path.
> Step 4 — Add logging and operational metrics: run ID, start/end time, input/output counts, rejected count, and failure reason.
> Step 5 — Add automated tests for the happy path, empty input, malformed records, duplicates, nulls, and at least two domain-specific edge cases.
> Step 6 — Make the load idempotent and document retry, restart, and backfill behavior where applicable.
> Step 7 — Provide reproducible sample data; use synthetic data unless public data has clear reuse rights. Keep any expected-answer labels separate from input data.
> Step 8 — Demonstrate output correctness with reconciliation queries, assertions, or a validation report.
> Step 9 — Include a simple performance measurement and identify one reasonable optimization.
> Step 10 — Submit source code, tests, sample input/output, README, schema/data dictionary, and a short design/trade-off note.
>
> Suggested Volume and Coverage
> Support a small starter sample for quick review and a configurable larger run (for example, 100,000+ records where practical). Include normal data, boundary values, duplicate records, missing values, late or out-of-order data where relevant, and deliberately labelled invalid records. Use a fixed random seed for reproducibility.
>
> Required Edge Cases / Negative Scenarios
> Malformed input; missing required field; duplicate key/event; unexpected schema change; empty batch; partial failure and retry; late or out-of-order data where relevant; invalid reference key; and rerun of the same input.
>
> Validation Rules / Acceptance Criteria
> Primary keys and referential integrity are checked; transformation rules are deterministic; source-to-target counts and key aggregates reconcile or explain differences; invalid records are traceable; reruns do not create unintended duplicates; tests pass; setup and run instructions work from a clean environment.
>
> Evaluation Focus
> Correctness and data quality (30%); pipeline design and code clarity (20%); testing and edge-case handling (20%); idempotency, recovery, and observability (15%); performance reasoning (10%); documentation and reproducibility (5%). Candidates should explain design choices and limitations.
>
> 72-Hour Deliverables
> 1. Working source code and dependency/setup files.
> 2. Reproducible sample data or generator.
> 3. Automated tests and execution evidence.
> 4. Output dataset/report plus reconciliation results.
> 5. README covering architecture, assumptions, run instructions, known limitations, and possible next steps.
>
> Scope Guidance
> A complete, tested vertical slice is preferred over an unfinished enterprise-scale implementation. External services are optional; provide a local mock or clear setup instructions if credentials are required. Do not commit secrets or use data that you are not authorized to access.
>
> Before you submit, make sure you have Pushed your code to a public GitHub repository; Added a README explaining how to run it; Included any tests the problem asks for.
>
> Candidate FAQ (PDF)
> Submission Guidelines (PDF)
> Submit your work. You can submit once, so check everything before you do.
> GitHub repository URL*: https://github.com/username/repo. The repository must be public so we can review it. Your submission is final once sent.
> Deadline: Fri 30 Oct 2026, 16:39 (UTC).
> How it works: Build the solution locally. Push it to a public GitHub repository. Submit the link here before the deadline.
> Questions? Stuck on the brief? Our recruitment team can help. contactus@yottaflex.ai
>
> Help & FAQs
> 1. When does my 72-hour window start? When YottaFlex AI sends you the project. Your deadline is exactly 72 hours later, using the recorded send timestamp and its time zone.
> 2. Can I submit early? Yes. Submit as soon as ready. Keep your public repository available and editable until the 72-hour deadline; the latest version at the deadline is evaluated.
> 3. How do I submit my repository link? Create a new, dedicated public GitHub repository. Send the link from the same email address used during recruitment and follow the submission instructions provided.
> 4. What belongs in my repository? Include your code, prompt history, and relevant supporting artifacts in a clearly identifiable directory. There is no fixed list of documents or prescribed format.
> 5. Which AI tools may I use? Any LLM or AI coding tool is allowed, including cloud-based and locally hosted tools. AI use is unrestricted; your judgment, understanding, ownership, and validation matter.
> 6. What prompt history is required? Include all prompts submitted to every AI tool you used. AI responses are optional. If a tool cannot export prompts, keep a reasonable record and disclose the limitation.
> 7. Must I write all code myself? The project must be your individual work. AI and public learning resources are allowed; implementation help from other people is not. Understand the core logic, key design choices, dependencies, and limitations.
> 8. Can I choose my own technology stack? Yes. Choose suitable languages, frameworks, and storage. Use only free or locally runnable services, and avoid unusually large or slow dependencies where possible.
> 9. Must I provide a live demo or automated test suite? No hosted demo or automated test suite is mandatory. Provide clear setup/run instructions and demonstrate how you verified the core functionality. Document environment needs and limitations.
> 10. Can I reuse existing code? Standard dependencies and small illustrative snippets are acceptable. Do not import a complete solution or existing code that performs the core project work. Follow licenses and provide attribution where required.
> 11. What if requirements are unclear or work is incomplete? Make reasonable assumptions and explain them. Partial solutions are acceptable if you state what works, what remains incomplete, known limitations, and next steps. Explain any requirement deviations.
> 12. What must I keep out of a public repository? Never include secrets, credentials, personal or sensitive information, or proprietary code you are not authorized to publish. Use safe sample data and local configuration; explain setup in the README.

## What AI did and candidate review required

AI drafted the pipeline structure, synthetic sample and generator, tests, schema documentation, and operational/design notes. The candidate should review every implementation detail, run the commands from a clean environment, inspect rejects and query results, and amend any behavior they cannot explain. In particular, verify and understand: all-or-nothing behavior on schema-level failure; row-level reject accounting; first-in-batch duplicate policy; stale customer update handling; timezone normalization; monetary rounding; and idempotency. Candidate should add their own dated commits and any changes made during review. This file records prompts, not proof of independent authorship.
