---
title: Release 7.0.0
---

## Git Graph

``` mermaid
gitGraph
    commit tag: "7.0.0"
    commit
    branch release
    commit
    branch development
    commit
    commit
    commit
    commit
    checkout development
    branch feature/class-refactoring
    commit
    checkout development
    merge feature/class-refactoring
    commit
    checkout development
    commit id:"test defore merge"
    checkout release
    merge development
    checkout main
    merge release tag: "7.0.1"
```