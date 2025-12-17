---
id: task-14
title: 'FIX: pgvector Extension for Local PostgreSQL 18'
status: To Do
assignee: []
created_date: '2025-12-17 07:34'
labels:
  - fix
  - database
  - pgvector
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Local PostgreSQL 18 on Windows missing pgvector extension (no pre-built binaries available). Semantic search disabled on local database. Vector embeddings stored as TEXT instead of vector(1536).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Document workaround: Railway ($5/month) or Supabase (free tier)
- [ ] #2 Update deployment docs with Railway/Supabase setup instructions
- [ ] #3 Test semantic search on Railway/Supabase
- [ ] #4 Optional: Investigate compiling pgvector from source for PG18
- [ ] #5 Optional: Test PostgreSQL 13 downgrade (complex, not recommended)
- [ ] #6 Update ISSUES_LOG.md with resolution status
<!-- AC:END -->
