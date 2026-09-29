# Designer Style UX Spec — Sudoku-inator

## Overview
Sudoku-inator is a desktop puzzle app for both casual and advanced Sudoku players. The product should feel calm, trustworthy, and easy to learn, while still supporting deeper variant play, advanced strategies, and technical reliability.

This specification defines the user experience direction for the current product phase. It focuses on clarity, accessibility, feedback quality, and a clean progression from new user onboarding to expert play.

## Product Personality
The app should feel:
- Calm and focused rather than noisy or crowded
- Confident and trustworthy in its board logic
- Helpful without being patronizing
- Flexible enough for casual play and advanced puzzle solving
- Visually precise, with strong hierarchy and clear state communication

## Design Goals
1. Make the board instantly understandable.
2. Reduce friction for new players.
3. Make advanced features discoverable without overwhelming beginners.
4. Keep error states clear, recoverable, and non-destructive.
5. Support keyboard-first and accessibility-conscious workflows.

## Primary Users
### Casual Player
- Wants to quickly start a game
- Prefers simple actions and clear feedback
- Needs obvious controls and low mental overhead

### Puzzle Enthusiast
- Wants variant rules to be clear and consistent
- Values advanced hints, conflict highlighting, and difficulty information
- Needs accurate board logic and good status communication

### Accessibility User
- Uses keyboard navigation or needs larger, legible controls
- Needs high contrast and clear labels
- Wants predictable focus and readable information hierarchy

## Core Experience Principles
### 1. Show state clearly
The user should always know:
- which cell is selected
- whether the board has a conflict
- whether a hint, pencil mode, or move is active
- what variant rules are currently in effect

### 2. Make recovery easy
Actions such as undo, restart, and reload should be obvious and safe. Destructive actions should include confirmation or a clear recovery path.

### 3. Keep the board central
The board is the primary object of attention. Controls and status should support the board rather than compete with it.

### 4. Progressive disclosure
New users should see essential controls first. Advanced options should be available when needed, but not visually overwhelming.

### 5. Acknowledge the game state
The app should communicate generation failures, save issues, invalid imports, or variant constraints with calm, specific, actionable messaging.

## User Journeys
### Journey 1: First-time user starts a game
- User opens the app.
- User sees a clear, ready-to-play state with a visible new game action.
- User selects a variant and difficulty.
- User sees a quick summary of important rules.
- Board loads and user is immediately ready to play.

### Journey 2: Standard casual play
- User makes a move.
- The board confirms validity through highlight and feedback.
- User uses undo, hint, or pencil mode without confusion.
- User completes the puzzle and sees a summary with meaningful stats.

### Journey 3: Advanced variant play
- User selects a variant such as Str8ts, Killer, or Jigsaw.
- Variant-specific rule cues are visible without needing to hunt for them.
- Board highlights and candidate logic reflect the variant constraints accurately.
- Difficulty or rule explanation remains available in context.

### Journey 4: Recovering from error or interruption
- User loads a save, imports a puzzle, or restarts.
- The app presents a clear status message and recovered board state.
- No destructive action occurs without user confirmation when appropriate.

## Layout and Information Architecture
### Main screen structure
- Top toolbar or menu for game actions
- Board center stage
- Status area for difficulty, stats, and helpful prompts
- Secondary panels only when needed for variant or puzzle-specific information

### Modal/dialog structure
Dialogs should be:
- concise
- context-rich
- focused on one decision
- easy to dismiss or confirm

Examples:
- new game dialog with variant, difficulty, and hint settings
- completion dialog with summary, actions, and clear next steps
- import/export or save/load confirmations

## Interaction Patterns
### Board interactions
- Clear focus ring or highlight for selected cell
- Distinct visual states for fixed, editable, conflicting, and highlighted cells
- Candidate overlay should be readable and not crowd the board
- Black cells and cage boundaries should be visually distinct without becoming noisy

### Feedback signals
Use a consistent set of signals:
- normal states: neutral board tone
- selected state: strong contrast highlight
- conflict state: clear error color with high readability
- variant rule states: subtle but legible boundaries or tinted zones
- success state: calm completion confirmation rather than excessive celebration

### Control patterns
- Menus and toolbars should use common, predictable labels
- Buttons should be discoverable and aligned with the user’s task flow
- Avoid hidden functionality behind deep menu nesting for common actions

## Design System Direction
### Visual hierarchy
- Primary actions: high clarity and strong contrast
- Secondary actions: reduced emphasis but still discoverable
- Status and alerts: short labels, readable contrast, icon or color added without reliance on color alone

### Color guidance
- Maintain readable contrast in both light and dark themes
- Use color to clarify state, not as the only signal
- Avoid overly saturated or low-contrast combinations

### Typography
- Use clear, readable fonts with adequate spacing
- Ensure labels remain legible at varying display sizes
- Keep status labels short and precise

### Layout spacing
- Maintain consistent spacing around cells, controls, and dialogs
- Use alignment and grouping to reduce visual noise
- Preserve enough whitespace for the board to remain the focus

## Accessibility Requirements
The app must be usable for a broad range of players.

### Required accessibility behaviors
- Keyboard navigation for all major actions
- Visible focus states for interactive controls
- High-contrast states for selection and conflict indicators
- Resizable or scalable text and controls where possible
- Labels and actions must not depend on color alone
- Short, specific feedback text in dialogs and status areas

### Additional support
- Reduce motion and noise where possible
- Support larger window layouts for better readability
- Ensure advanced actions are still discoverable without requiring a mouse

## Edge Cases and Error States
The interface should handle the following gracefully:
- generation failure or retry loop
- invalid imported data
- save/load errors
- restart requests when work is in progress
- variant-specific rule confusion
- empty or incomplete board states

The app should never feel silent or ambiguous when a problem occurs. Each error should be:
- understandable
- actionable
- recoverable when possible

## Success Metrics
The UX is successful if:
- first-time users can start a game without confusion
- common actions are discoverable without help docs
- players can complete a puzzle with minimal friction
- accessibility-related issues are reduced in repeated use
- variant rule explanations feel clear instead of technical or hidden
- users feel confident about restart, save/load, and completion flows

## Recommended Next Design Iterations
1. Standardize board feedback and visual states
2. Improve first-run onboarding and quick-start guidance
3. Improve accessibility and keyboard flows
4. Clarify advanced variant rule presentation
5. Review dialogs and status messaging for consistency

## Related project documentation
- [README.md](README.md)
- [milestone_roadmap.md](milestone_roadmap.md)
- [IMPLEMENTATION_ISSUES.md](IMPLEMENTATION_ISSUES.md)
- [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
