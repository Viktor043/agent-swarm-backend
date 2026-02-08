# Lovable Development Workflow

## Objective
Develop features for Lovable-generated dashboard while maintaining Lovable's patterns and enabling bidirectional sync with GitHub.

## Required Inputs
- Task description (feature to add or bug to fix)
- Lovable project GitHub repository URL
- Local development environment

## Execution Steps

1. **Sync Lovable Project from GitHub**
   - Tool: `tools/development/lovable_sync.py`
   - Clone or pull latest changes from GitHub
   - Command: `lovable_sync.clone_or_sync()`
   - Verify project structure exists locally
   - Expected location: `/Users/vik043/Desktop/Agentic Workflow/lovable-dashboard`

2. **Analyze Existing Component Structure**
   - Tool: `tools/development/react_analyzer.py`
   - Analyze React/TypeScript component patterns
   - Identify:
     - Component hierarchy and dependencies
     - Styling approach (Tailwind CSS, Shadcn)
     - State management patterns
     - Supabase integration patterns
     - Common hooks and utilities
   - Command: `analyzer.analyze_project()`
   - Output: Component structure map, patterns, conventions

3. **Read Existing Components for Context**
   - Identify components related to the feature
   - Read component source code
   - Understand:
     - Props and interfaces
     - State management approach
     - API call patterns (Supabase queries)
     - Styling conventions (Tailwind classes)
   - Tool: `lovable_sync.read_component(component_name)`

4. **Create Feature Branch**
   - Tool: `tools/development/git_operations.py`
   - Create branch from main: `feature/task-description`
   - Command: `git checkout -b feature/add-twitter-connector`
   - Ensures changes are isolated for review

5. **Implement Changes Following Lovable Patterns**
   - **For New Component**:
     - Create in `src/components/` directory
     - Use TypeScript (.tsx extension)
     - Follow functional component pattern with hooks
     - Use Tailwind CSS for styling
     - Use Shadcn UI components if applicable
     - Example structure:
       ```typescript
       import { useState } from 'react';
       import { Button } from "@/components/ui/button";

       interface TwitterConnectorProps {
         onPost: (message: string) => void;
       }

       export const TwitterConnector = ({ onPost }: TwitterConnectorProps) => {
         const [message, setMessage] = useState('');

         return (
           <div className="flex flex-col gap-4">
             {/* Component UI */}
           </div>
         );
       };
       ```

   - **For Supabase Integration**:
     - Use Supabase client from Lovable's setup
     - Follow existing query patterns
     - Example:
       ```typescript
       import { supabase } from '@/integrations/supabase/client';

       const { data, error } = await supabase
         .from('watch_messages')
         .select('*')
         .order('created_at', { ascending: false });
       ```

   - **For Styling**:
     - Use Tailwind utility classes
     - Follow existing spacing/color conventions
     - Use Shadcn components for UI elements
     - Ensure responsive design (mobile-first)

6. **Run Tests**
   - Tool: `tools/testing/run_pytest.py` (for backend)
   - Run: `npm test` or `npm run test` (for React)
   - Verify:
     - Component renders without errors
     - Props work correctly
     - State updates as expected
     - API calls succeed
   - Fix any failing tests before proceeding

7. **Build and Verify**
   - Run: `npm run build`
   - Check for TypeScript errors
   - Check for build warnings
   - Verify bundle size is reasonable
   - Test in development mode: `npm run dev`
   - Manual verification:
     - Component displays correctly
     - Interactions work
     - Responsive on mobile
     - No console errors

8. **Commit Changes**
   - Tool: `tools/development/git_operations.py`
   - Stage changes: `git add .`
   - Commit with clear message:
     - Format: `feat: add Twitter connector component`
     - Include description of what was added
     - Mention any breaking changes
   - Command: `git commit -m "feat: add Twitter connector with Supabase integration"`

9. **Push to GitHub**
   - Tool: `tools/development/lovable_sync.py`
   - Push branch: `lovable_sync.push_to_github(branch_name)`
   - Command: `git push -u origin feature/add-twitter-connector`
   - Creates remote branch for review

10. **Lovable Sync (Optional)**
    - If you want changes to appear in Lovable:
      - Go to Lovable dashboard
      - Sync from GitHub
      - Lovable will pull latest changes
    - If deploying independently:
      - Skip Lovable sync
      - Deploy via Cloud Run, Vercel, or Netlify directly

11. **Create Pull Request**
    - Tool: GitHub CLI (`gh pr create`)
    - Title: Brief description of feature
    - Body: Detailed explanation, screenshots if UI changes
    - Request review from team or human
    - Link to related issues if applicable

12. **Verify Integration**
    - Test watch → dashboard communication
    - Verify new feature works with existing flow
    - Check Supabase data updates correctly
    - Ensure no regressions in other components

## Expected Outputs
- Feature implemented following Lovable's React/TypeScript patterns
- Code committed to feature branch
- Changes pushed to GitHub
- Pull request created for review
- All tests passing
- No build errors

## Edge Cases
- **Lovable project not cloned yet**:
  - Run `lovable_sync.clone_from_github()` first
  - Verify GitHub credentials in .env
  - Check GITHUB_REPO and GITHUB_TOKEN are set

- **TypeScript errors**:
  - Check interface/type definitions match existing patterns
  - Ensure imports are correct
  - Verify Shadcn components are imported properly
  - Run `npm run type-check` to see all errors

- **Styling doesn't match Lovable's design**:
  - Review existing components for Tailwind class patterns
  - Use same color scheme (check tailwind.config)
  - Follow spacing conventions (gap-4, p-6, etc.)
  - Use Shadcn components instead of custom UI elements

- **Supabase integration fails**:
  - Verify Supabase client is initialized
  - Check table/column names match schema
  - Ensure RLS (Row Level Security) policies allow operation
  - Test queries in Supabase dashboard first

- **Build fails**:
  - Check for missing dependencies: `npm install`
  - Verify all imports are correct
  - Look for circular dependencies
  - Check for unused imports (can cause errors)

- **Merge conflicts**:
  - Pull latest main: `git pull origin main`
  - Resolve conflicts manually
  - Test after resolving
  - Commit merge resolution

## Learning Loop
- Document Lovable-specific patterns discovered
- Note common Tailwind class combinations
- Track Supabase query patterns that work well
- Identify Shadcn components that are most useful
- Update this workflow with new conventions
- Share learnings with other agents via context store

## Lovable Best Practices

### Component Structure
- Keep components small and focused (single responsibility)
- Extract reusable logic into custom hooks
- Use TypeScript for all props and state
- Export interfaces for reusability

### Styling
- Mobile-first responsive design
- Use Tailwind utility classes
- Avoid custom CSS unless absolutely necessary
- Use Shadcn for common UI patterns (buttons, forms, modals)

### State Management
- useState for local component state
- useContext for shared state (if needed)
- Supabase for persistent data
- Avoid Redux/Zustand unless complexity demands it

### Performance
- Use React.memo for expensive components
- useMemo for expensive calculations
- useCallback for callback functions passed as props
- Lazy load heavy components: `const Heavy = lazy(() => import('./Heavy'))`

### Integration with Watch App
- Dashboard receives watch messages via `/functions/v1/chat` endpoint
- Watch polls `/functions/v1/watch-config` for configuration updates
- Use Supabase realtime subscriptions for live updates
- Handle offline scenarios gracefully

## Example: Adding Social Media Connector

**Task**: Add Twitter connector to post watch messages

**Steps**:
1. Sync Lovable project
2. Analyze existing connector components (if any)
3. Create `src/components/TwitterConnector.tsx`
4. Implement UI with Shadcn Button and Input components
5. Add Supabase integration to store Twitter posts
6. Use `tools/connectors/twitter_client.py` for API calls
7. Test component in isolation
8. Integrate with main dashboard
9. Commit, push, create PR
10. Verify watch → dashboard → Twitter flow works

**Result**: Dashboard now has Twitter posting capability that follows Lovable's design patterns and integrates seamlessly with existing architecture.
