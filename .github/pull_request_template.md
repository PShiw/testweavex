## Summary

<!-- What does this PR do? 2-3 bullet points. -->

-
-

## Type of Change

- [ ] Bug fix
- [ ] New feature (Phase ___)
- [ ] Refactor / cleanup
- [ ] Documentation
- [ ] CI / config

## Related Issue

Closes #

## Testing

- [ ] Added / updated tests
- [ ] All tests pass locally (`pytest tests/ -v`)
- [ ] No new warnings introduced

## Design Rules Checklist

- [ ] No LLM output written to disk without review gate
- [ ] Stable ID algorithm unchanged (`generate_stable_id`)
- [ ] All persistence goes through `StorageRepository` — no direct DB/HTTP calls
- [ ] All LLM calls go through `LLMAdapter` — no direct provider SDK imports outside `testweavex/llm/`
- [ ] `tw` still behaves identically to `pytest` for standard flags

## Notes for Reviewers

<!-- Anything the reviewer should pay special attention to? -->
