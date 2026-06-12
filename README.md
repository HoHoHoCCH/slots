![Slots repo banner](repo_banner.png)

# Slots

Save slots for your local directory - Checkpoint your progress along the way with no commitment.

Slots is a small CLI for creating save slots inside a coding project. It is useful when you want to attempt a refactor, compare approaches, or let an AI coding agent make changes while keeping an easy restore point.

## Installation

```powershell
pip install slots-cli
```

For MCP support:

```powershell
pip install "slots-cli[mcp]"
```

## Quickstart

Create a save slot before making risky changes:

```powershell
slots init
slots save before-refactor
```

Make your edits, then check what changed:

```powershell
slots status
```

```diff
Difference from base state
3 changed: 1 added, 1 modified, 1 removed

Added (1)
+  new_feature.py

Modified (1)
!  app.py

Removed (1)
-  old_utils.py
```

Restore the save slot if you want to go back:

```powershell
slots load before-refactor
```

Undo the most recent load if you change your mind:

```powershell
slots revert
```

## Commands

### Initialize

```powershell
slots init
```

Creates `.slots/` and records the base state. All saves are tied to the same base state.

Refresh the base state:

```powershell
slots init --refresh
```

This clears existing save slots and aligns the base state with the current respository.

### Save

```powershell
slots save before-refactor
```

Creates a named save slot from the current project state.

### Status

```powershell
slots status
```

Shows differences between the current project and the base state.

```powershell
slots status --latest
```

Shows differences between the current project and the most recent save slot.

### List

```powershell
slots list
```

Lists save slots.

### Load

```powershell
slots load before-refactor
```

Loads added and modified files from a save slot.

```powershell
slots load before-refactor --remove-files
```

Also removes files that were deleted in the save slot.

### Revert

```powershell
slots revert
```

Reverts the most recent load using the automatic pre-load backup.

### Delete

```powershell
slots delete before-refactor
```

Deletes a save slot.

### Reset

```powershell
slots reset
```

Deletes all Slots data from the project.

## MCP Support

Slots includes a MCP server so AI coding tools can create and restore save slots.

Install with MCP support:

```powershell
pip install "slots-cli[mcp]"
```

Then run the MCP server:

```powershell
slots-mcp
```

### Common Installation commands:

**Codex**

```powershell
codex mcp add slots -- slots-mcp
```

**Claude Code**

```powershell
claude mcp add slots -- slots-mcp
```

## Notes

Slots is not a replacement for Git - it is designed to work alongside it as a lightweight local checkpoint tool.

Before loading a slot, Slots creates a backup in `.slots/backups/`. You can restore the latest load with:

```powershell
slots revert
```
