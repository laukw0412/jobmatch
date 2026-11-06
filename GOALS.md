# JobMatch — Product Goals

## Purpose

Build a usable AI-assisted job matching application that compares a candidate's information with a job description and produces actionable, evidence-based recommendations.

This document defines **what the product must accomplish**, not which libraries, databases, language models, or architecture must be used. Technical choices may be reconsidered during independent architecture reviews.

## Inputs

- One or more candidate documents, such as resumes, career histories, qualifications, and certificates
- A job description supplied as pasted text or a URL
- User confirmation or correction of the extracted job description
- Optional user corrections to candidate information or matching results

## Outputs

- A readable, confirmable job description
- Structured job requirements
- Requirement-level matching assessments supported by traceable candidate evidence
- Clear distinctions between supported, partially supported, missing, and unknown evidence
- Skill gaps and uncertainties
- Actionable application recommendations

## Required MVP Capabilities

1. Ingest multiple candidate documents into a reusable personal information collection.
2. Preserve the ability to recover at least five prior profile/document versions.
3. Extract or accept job descriptions and show the extracted text for confirmation before analysis.
4. Use retrieval-augmented generation (RAG) to find evidence from candidate information.
5. Analyze job requirements against that evidence without inventing qualifications.
6. Present results and recommendations in a standalone GUI.
7. Report document-read failures explicitly rather than silently ignoring them.
8. Permit manual JD text entry when website extraction fails.

## Product-Level Constraints

- The initial release should be practical, usable, and simple enough to finish quickly.
- Candidate evidence and source provenance must remain reviewable.
- Do not treat today's implementation as a permanent architectural requirement.
- Preserve user control over decisions that affect stored candidate data.

## Non-Goals for the Initial Release

- Autonomous submission of job applications
- Enterprise-scale distributed infrastructure
- Supporting every job board and document format perfectly
- Implementing multiple agents merely for architectural sophistication

## Acceptance Criteria

An end-to-end user can supply candidate documents and a JD, confirm the JD, receive an evidence-supported requirement-by-requirement analysis, review gaps and recommendations in the GUI, and recover earlier document/profile versions.

## Change Policy

This file is the product-level baseline. Any change to the intended inputs, outputs, or required behavior must be proposed explicitly and approved by the user before editing this file.
