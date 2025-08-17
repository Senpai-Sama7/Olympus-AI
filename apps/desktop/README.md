# Desktop Application

Tauri or Electron-based desktop client for the agentic assistant.

## Overview

This directory will contain the desktop application featuring:
- Chat-first UI with one main input box
- Mode selection (Observe/Draft/Autopilot)
- Visual flow builder
- Memory search interface
- Settings and preferences
- System tray integration

## Structure (to be implemented)

```
desktop/
├── src/
│   ├── main/            # Main process (Electron) or Rust (Tauri)
│   ├── components/      # React components
│   │   ├── Chat/
│   │   ├── FlowBuilder/
│   │   └── Dashboard/
│   ├── pages/           # Main views
│   ├── services/        # API communication
│   └── store/           # State management
├── package.json
└── tsconfig.json
```

## Phase 7 Implementation

The desktop app will be primarily built in Phase 7, with:
- Chat interface (earlier phases will use web UI)
- Visual flow builder with drag-and-drop
- Natural language to flow compilation

See `/plans/migration-plan.md` for details.