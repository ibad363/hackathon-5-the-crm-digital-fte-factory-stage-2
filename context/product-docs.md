# TaskVault — Product Documentation

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Core Features](#2-core-features)
3. [How-To Guides (Top 10)](#3-how-to-guides)
4. [API Overview](#4-api-overview)
5. [Billing & Subscription Management](#5-billing--subscription-management)
6. [Troubleshooting (Top 15 Issues)](#6-troubleshooting)
7. [Integration Guides](#7-integration-guides)
8. [Mobile App](#8-mobile-app)
9. [Admin & Permissions](#9-admin--permissions)
10. [Data Export & Account Deletion](#10-data-export--account-deletion)

---

## 1. Getting Started

### 1.1 Creating Your Account

1. Go to [https://app.taskvault.io/signup](https://app.taskvault.io/signup).
2. Enter your work email address and choose a password (min 8 characters, must include one number and one special character).
3. Verify your email by clicking the link sent to your inbox (check spam if not received within 2 minutes).
4. Choose your workspace name (this is your team's shared space — e.g., "Acme Engineering").
5. Select your plan: Free, Pro (14-day trial), or Enterprise (contact sales).
6. You're in! You'll land on the onboarding wizard.

### 1.2 Onboarding Wizard

The onboarding wizard walks you through:

- **Step 1 — Create your first project:** Give it a name and choose a view (Board, List, or Timeline).
- **Step 2 — Invite team members:** Enter email addresses or share an invite link. Free plan: up to 5 members.
- **Step 3 — Create your first task:** Add a task title, assign it to someone, and set a due date.
- **Step 4 — Connect an integration (optional):** Link Slack, GitHub, or Google Drive.
- **Step 5 — Tour complete:** Access the interactive tour anytime via **Help > Product Tour**.

### 1.3 System Requirements

- **Browser:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile:** iOS 15+ / Android 11+
- **Internet:** Stable connection required; offline mode available on Pro+ (syncs when reconnected)

---

## 2. Core Features

### 2.1 Tasks

Tasks are the fundamental unit of work in TaskVault.

**Task Fields:**
| Field | Description | Required |
|---|---|---|
| Title | Short description of the work | Yes |
| Description | Rich-text details, checklists, links | No |
| Assignee | Team member responsible | No |
| Due Date | Deadline for completion | No |
| Priority | Low, Medium, High, Urgent | No (default: Medium) |
| Labels | Color-coded tags (e.g., "bug", "feature", "design") | No |
| Status | To Do, In Progress, In Review, Done, Archived | Yes (default: To Do) |
| Subtasks | Nested child tasks | No |
| Attachments | Files up to 25 MB each (Free: 10 MB limit) | No |
| Time Tracked | Hours logged against this task (Pro+) | No |
| Comments | Threaded discussion on the task | No |

**Task Actions:**
- Create, edit, duplicate, delete
- Move between projects
- Convert to subtask (or promote subtask to task)
- Set recurring (daily, weekly, monthly, custom)
- Add dependencies (Task B blocked by Task A)
- Watch a task for notifications without being assigned

### 2.2 Projects

Projects are containers for related tasks.

**Project Views:**
- **Board View (Kanban):** Drag-and-drop cards between columns (statuses).
- **List View:** Flat or grouped list, sortable by any field.
- **Timeline View (Gantt):** Visual timeline with dependencies. (Pro+)
- **Calendar View:** Tasks plotted on a calendar by due date.

**Project Settings:**
- Name, description, color, icon
- Default view and task statuses (customizable)
- Member access (who can view / edit)
- Automations (rules triggered by task changes)

### 2.3 Team Members

**Roles:**
| Role | Permissions |
|---|---|
| **Owner** | Full control. Billing, settings, member management, delete workspace. |
| **Admin** | Manage members, projects, integrations. Cannot delete workspace or manage billing. |
| **Member** | Create/edit tasks and projects they belong to. Cannot manage workspace settings. |
| **Guest** | View-only access to specific projects. Cannot create tasks. (Pro+) |

**Inviting Members:**
- Go to **Settings > Members > Invite**.
- Enter email addresses (comma-separated for bulk).
- Choose role: Admin, Member, or Guest.
- Invitee receives an email with a join link (expires in 7 days).

**Removing Members:**
- Go to **Settings > Members**, click the three-dot menu next to the member, select **Remove**.
- Their tasks remain but are unassigned. Reassign via **Settings > Members > Offboarding Reassignment**.

### 2.4 Integrations

TaskVault supports native integrations with:

| Integration | What It Does | Plan Required |
|---|---|---|
| **Slack** | Post task updates to Slack channels; create tasks from Slack messages | Pro+ |
| **GitHub** | Link commits/PRs to tasks; auto-move tasks when PRs merge | Pro+ |
| **GitLab** | Same as GitHub integration | Pro+ |
| **Google Drive** | Attach Drive files to tasks; preview in-app | Free+ |
| **Jira** | Two-way sync of issues between Jira and TaskVault | Enterprise |
| **Zapier** | Connect TaskVault to 5,000+ apps via Zapier triggers/actions | Pro+ |
| **Webhooks** | Send HTTP POST payloads on task events to any URL | Pro+ |

### 2.5 Notifications

**Notification Types:**
- **In-App:** Bell icon in top-right. Red badge shows unread count.
- **Email Digest:** Daily or weekly summary of activity. Configure in **Settings > Notifications**.
- **Push (Mobile):** Real-time alerts on iOS/Android. Enable in mobile app settings.
- **Slack:** If Slack integration is active, get notifications in your chosen channel.

**What Triggers Notifications:**
- Task assigned to you
- Task you're watching is updated
- Someone comments on your task
- Task due date approaching (24h and 1h before)
- You're @mentioned in a comment or description
- Project you belong to has a new task

**Managing Notifications:**
- Mute specific projects or tasks
- Set Do Not Disturb hours (no push notifications)
- Choose per-channel: in-app, email, push, Slack (any combination)

---

## 3. How-To Guides

### 3.1 How to Create a Task

1. Open a project.
2. Click **+ New Task** (top of any column in Board view, or top of the list in List view).
3. Enter the task title.
4. (Optional) Click the task to open details and fill in description, assignee, due date, priority, labels.
5. Press **Enter** or click **Save**.

**Keyboard Shortcut:** Press `N` anywhere within a project to create a new task.

### 3.2 How to Invite a Team Member

1. Go to **Settings** (gear icon in sidebar) > **Members**.
2. Click **Invite Members**.
3. Enter one or more email addresses.
4. Select a role (Admin, Member, Guest).
5. Click **Send Invites**.
6. Invitees receive an email and can join within 7 days.

**Tip:** Share the workspace invite link for open joining (toggle in Settings > Members > Invite Link).

### 3.3 How to Create a Project

1. In the sidebar, click **+ New Project**.
2. Enter a project name.
3. Choose a color and icon.
4. Select the default view (Board, List, Timeline, Calendar).
5. Add members (or skip — you can add later).
6. Click **Create Project**.

### 3.4 How to Set Up a Slack Integration

1. Go to **Settings > Integrations > Slack**.
2. Click **Connect to Slack**.
3. Authorize TaskVault in the Slack OAuth popup.
4. Choose a default Slack channel for notifications.
5. Configure per-project: select which events post to which channels.
6. Click **Save**.

**Troubleshooting:** If the OAuth popup doesn't appear, disable your browser's popup blocker for taskvault.io.

### 3.5 How to Use the Timeline (Gantt) View

1. Open a project and click the **Timeline** tab (Pro+ required).
2. Tasks appear as horizontal bars based on their start and due dates.
3. Drag the edges of a bar to adjust dates.
4. Draw a line between two tasks to create a dependency.
5. Use the zoom controls to switch between day, week, and month views.
6. Click **Critical Path** to highlight the longest chain of dependent tasks.

### 3.6 How to Track Time on a Task

1. Open a task (Pro+ required).
2. Click the **Timer** icon in the task detail panel.
3. Click **Start** to begin tracking. The timer runs even if you navigate away.
4. Click **Stop** to log the time.
5. To add time manually, click **+ Add Time Entry** and enter hours and minutes.
6. View time reports in **Reports > Time Tracking**.

### 3.7 How to Set Up Workflow Automations

1. Open a project and go to **Settings > Automations**.
2. Click **+ New Rule**.
3. Choose a **trigger** (e.g., "When task status changes to Done").
4. Choose an **action** (e.g., "Send Slack notification to #releases").
5. (Optional) Add conditions (e.g., "Only if label = 'bug'").
6. Click **Save Rule**.

**Common Automations:**
- Auto-assign tasks created with the "bug" label to the QA lead.
- Move tasks to "Archived" 7 days after marked Done.
- Notify the project owner when a task is marked Urgent.

### 3.8 How to Export Data

1. Go to **Settings > Workspace > Data Export**.
2. Choose what to export: Tasks, Projects, Members, Time Entries, or All.
3. Choose format: CSV or JSON.
4. Click **Generate Export**.
5. You'll receive a download link via email within 5–30 minutes depending on data size.

### 3.9 How to Manage Billing

1. Go to **Settings > Billing** (Owner only).
2. View current plan, next billing date, and payment method.
3. To upgrade: click **Change Plan** and select the desired tier.
4. To downgrade: click **Change Plan**, select a lower tier. Changes take effect at the end of the current billing cycle.
5. To update payment method: click **Update Payment** and enter new card details.
6. To view invoices: click **Billing History** to download PDF invoices.

### 3.10 How to Use the Mobile App

1. Download "TaskVault" from the App Store (iOS) or Google Play (Android).
2. Log in with your existing credentials.
3. You'll see your workspace, projects, and tasks.
4. Tap any task to view/edit details, add comments, or log time.
5. Use the **+** button to create new tasks.
6. Enable push notifications in the app's settings for real-time alerts.
7. Offline mode (Pro+): tasks created offline sync automatically when you reconnect.

---

## 4. API Overview

### 4.1 Authentication

TaskVault uses **API keys** for authentication (Pro and Enterprise plans).

- Generate a key in **Settings > API > Generate Key**.
- Include the key in the `Authorization` header: `Authorization: Bearer fs_live_xxxxxxxxxxxx`.
- API keys are scoped to the workspace. Each workspace can have up to 10 active keys.
- Revoke keys in **Settings > API > Manage Keys**.

### 4.2 Base URL

```
https://api.taskvault.io/v1
```

### 4.3 Rate Limits

| Plan | Requests per minute |
|---|---|
| Pro | 60 |
| Enterprise | 300 |

Exceeding the limit returns HTTP `429 Too Many Requests` with a `Retry-After` header.

### 4.4 Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/tasks` | List tasks (supports filtering, pagination) |
| POST | `/tasks` | Create a task |
| GET | `/tasks/{id}` | Get a single task |
| PATCH | `/tasks/{id}` | Update a task |
| DELETE | `/tasks/{id}` | Delete a task |
| GET | `/projects` | List projects |
| POST | `/projects` | Create a project |
| GET | `/projects/{id}` | Get a single project |
| GET | `/members` | List workspace members |
| POST | `/members/invite` | Invite a member |
| GET | `/time-entries` | List time entries (Pro+) |
| POST | `/webhooks` | Register a webhook |

### 4.5 Pagination

All list endpoints return paginated results:
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "per_page": 50,
    "total": 230,
    "total_pages": 5
  }
}
```

Use query params `?page=2&per_page=50`.

### 4.6 Error Codes

| Code | Meaning |
|---|---|
| 400 | Bad Request — invalid parameters |
| 401 | Unauthorized — missing or invalid API key |
| 403 | Forbidden — insufficient permissions |
| 404 | Not Found — resource doesn't exist |
| 422 | Unprocessable Entity — validation error |
| 429 | Rate Limited — slow down |
| 500 | Internal Server Error — contact support |

---

## 5. Billing & Subscription Management

### 5.1 Plans & Pricing

| Plan | Monthly | Annual (per month) |
|---|---|---|
| Free | $0 | $0 |
| Pro | $29/user | $23.20/user |
| Enterprise | $99/user | $79.20/user |

### 5.2 Upgrading

- Upgrades take effect **immediately**.
- You are charged a prorated amount for the remainder of the current billing cycle.
- All features of the new plan become available instantly.

### 5.3 Downgrading

- Downgrades take effect at the **end of the current billing cycle**.
- If you exceed the lower plan's limits (e.g., more than 5 users on Free), you will be prompted to remove members or projects before the downgrade activates.
- Data is **never deleted** during a downgrade. Excess data becomes read-only.

### 5.4 Cancellation

- Go to **Settings > Billing > Cancel Subscription**.
- Your workspace remains active until the end of the billing period.
- After expiry, the workspace reverts to the Free plan.
- Data is retained for **90 days** after cancellation, then permanently deleted.
- To reactivate, simply choose a paid plan within the 90-day window.

### 5.5 Refund Policy

- **14-day money-back guarantee** for first-time subscribers.
- Refunds are processed within 5–10 business days.
- After 14 days, no refunds are issued; you can cancel to stop future charges.
- Enterprise contracts have custom refund terms outlined in the agreement.

### 5.6 Payment Methods

- Credit/debit card (Visa, Mastercard, Amex)
- Invoice billing for Enterprise (NET-30 terms)
- PayPal is **not** supported at this time.

### 5.7 Failed Payments

- If a payment fails, we retry 3 times over 7 days.
- You receive email alerts after each failed attempt.
- If all retries fail, your workspace is downgraded to Free after 7 days.
- Update your payment method in **Settings > Billing > Update Payment** to resolve.

---

## 6. Troubleshooting

### Issue 1: "I can't log in"

**Possible causes & solutions:**
- **Wrong password:** Click "Forgot Password" on the login page. A reset link is sent to your email.
- **Email not found:** Ensure you're using the email you signed up with. Check for typos.
- **Account locked:** After 5 failed login attempts, your account is locked for 15 minutes. Wait and try again.
- **SSO user:** If your company uses SSO (Enterprise), click "Sign in with SSO" instead of entering a password.
- **Browser cache:** Clear your browser cache and cookies, then try again.

### Issue 2: "I'm not receiving email notifications"

**Solutions:**
- Check **Settings > Notifications** — ensure email notifications are enabled.
- Check your spam/junk folder. Add `notifications@taskvault.io` to your safe senders.
- If using Gmail, check the Promotions or Updates tab.
- Verify your email address in **Settings > Profile > Email** (look for a "Verified" badge).

### Issue 3: "Tasks are not syncing on mobile"

**Solutions:**
- Ensure you have a stable internet connection.
- Force-close and reopen the app.
- Check that you're logged into the correct workspace.
- Update the app to the latest version (Settings > App Store/Play Store > Update).
- If on Pro+ with offline mode: tasks sync when you reconnect. Check for a "Syncing..." indicator.

### Issue 4: "I can't see a project that my teammate shared"

**Solutions:**
- Ask your teammate to check the project's member list (**Project Settings > Members**).
- If you're a Guest, you can only see projects explicitly shared with you.
- Workspace Admins can see all projects. If you're a Member, you need to be added to the project.

### Issue 5: "Slack integration isn't posting updates"

**Solutions:**
- Go to **Settings > Integrations > Slack** and check the connection status.
- If it says "Disconnected," click **Reconnect**.
- Verify the correct Slack channel is selected for the project.
- Ensure the TaskVault Slack app hasn't been removed from your Slack workspace.
- Check Slack channel permissions — the bot must be invited to private channels.

### Issue 6: "I accidentally deleted a task"

**Solutions:**
- Deleted tasks go to the **Trash** (accessible from the sidebar).
- Tasks remain in Trash for **30 days** before permanent deletion.
- Click the task in Trash and select **Restore** to recover it.
- If the 30-day window has passed, contact support — we may be able to recover it from backups (Enterprise only).

### Issue 7: "My file upload is failing"

**Solutions:**
- Check file size: Free plan = 10 MB max; Pro/Enterprise = 25 MB max.
- Supported formats: PDF, DOCX, XLSX, PPTX, PNG, JPG, GIF, SVG, ZIP, MP4 (under size limit).
- If the file is valid, try a different browser or disable browser extensions.
- Large files on slow connections may time out — try again on a faster network.

### Issue 8: "Timeline view is not showing my tasks"

**Solutions:**
- Timeline requires both a **start date** and a **due date** on each task. Tasks without dates won't appear.
- Timeline view is available on **Pro and Enterprise** plans only.
- If you recently upgraded, refresh the page or log out and back in.

### Issue 9: "I was charged after I cancelled"

**Solutions:**
- Cancellations take effect at the end of the billing cycle. The charge may be for the current (already active) period.
- Check your cancellation confirmation email for the exact end date.
- If you believe you were charged in error, email **billing@taskvault.io** with your invoice number.

### Issue 10: "The Gantt chart dependencies are broken"

**Solutions:**
- Ensure dependent tasks have valid date ranges (start date < due date).
- Circular dependencies are not allowed. Check that Task A → Task B → Task A doesn't exist.
- Remove and re-create the dependency link by clicking the connector line and pressing Delete.

### Issue 11: "API returns 401 Unauthorized"

**Solutions:**
- Verify your API key is correct and hasn't been revoked.
- Ensure the header format is exactly: `Authorization: Bearer fs_live_xxxx`.
- API keys are workspace-scoped. Check you're hitting the right workspace.
- API is available on Pro and Enterprise plans only.

### Issue 12: "I can't remove a team member"

**Solutions:**
- Only **Owners** and **Admins** can remove members.
- You cannot remove yourself if you're the only Owner. Transfer ownership first in **Settings > Workspace > Transfer Ownership**.
- If the member was invited via SSO, they must be deprovisioned from your identity provider.

### Issue 13: "Automations are not triggering"

**Solutions:**
- Check that the automation rule is **enabled** (toggle switch in Project Settings > Automations).
- Verify the trigger conditions match. For example, a rule set for "status changes to Done" won't fire if the task was directly moved to "Archived."
- Automations run asynchronously; there may be a 1–2 minute delay.
- Free plan: automations are limited to 3 rules per project.

### Issue 14: "My workspace is running slowly"

**Solutions:**
- Close unused browser tabs (TaskVault is resource-intensive with many open projects).
- Clear browser cache and disable unnecessary extensions.
- If a specific project is slow, it may have too many tasks (>5,000). Archive completed tasks.
- Check [status.taskvault.io](https://status.taskvault.io) for any ongoing platform incidents.

### Issue 15: "I need to recover data from a deleted workspace"

**Solutions:**
- Deleted workspaces are recoverable within **30 days** by contacting support@taskvault.io.
- After 30 days, data is permanently deleted and cannot be recovered.
- Enterprise customers with backup agreements may have extended recovery windows (check your contract).
- To prevent accidental deletion, enable **Workspace Deletion Protection** in Settings > Workspace > Security (Enterprise only).

---

## 7. Integration Guides

### 7.1 Slack Integration

**Setup:**
1. Navigate to **Settings > Integrations > Slack**.
2. Click **Connect to Slack** and authorize via OAuth.
3. Select a default channel for workspace-level notifications.
4. Per-project: go to **Project Settings > Integrations > Slack** and pick a channel.

**Features:**
- Receive notifications in Slack when tasks are created, updated, completed, or commented on.
- Create tasks directly from Slack using the `/taskvault create` command.
- Link a Slack message to a task by clicking **More actions > Create TaskVault Task**.

**Commands:**
| Command | Description |
|---|---|
| `/taskvault create [title]` | Create a new task in the default project |
| `/taskvault status` | Show your assigned tasks and their statuses |
| `/taskvault help` | List available commands |

### 7.2 GitHub Integration

**Setup:**
1. Navigate to **Settings > Integrations > GitHub**.
2. Click **Connect to GitHub** and authorize the TaskVault GitHub App.
3. Select which repositories to link.
4. Map repositories to TaskVault projects.

**Features:**
- Mention a task ID in a commit message (e.g., `fix: resolve bug FS-1234`) to auto-link.
- When a PR referencing a task is merged, the task can auto-move to "Done."
- View linked commits and PRs directly in the task detail panel.

### 7.3 Google Drive Integration

**Setup:**
1. Navigate to **Settings > Integrations > Google Drive**.
2. Click **Connect** and sign in with your Google account.
3. Grant TaskVault permission to access your Drive files.

**Features:**
- Attach Google Drive files (Docs, Sheets, Slides) to any task.
- Preview Drive files inline without leaving TaskVault.
- Changes to the Drive file are reflected in real-time within TaskVault.

---

## 8. Mobile App

### 8.1 Download

- **iOS:** [App Store](https://apps.apple.com/app/taskvault)
- **Android:** [Google Play](https://play.google.com/store/apps/details?id=io.taskvault)

### 8.2 Features

- Full task management (create, edit, assign, comment, change status)
- Project views (Board and List; Timeline not yet available on mobile)
- Push notifications for all notification types
- File attachments (photos from camera or gallery)
- Time tracking (start/stop timer, manual entry) — Pro+
- Offline mode (view and create tasks offline; syncs on reconnect) — Pro+
- Dark mode support

### 8.3 Known Limitations

- Timeline (Gantt) view is not yet available on mobile.
- File upload limit on mobile is 15 MB (vs. 25 MB on web for Pro+).
- Automation rules cannot be created or edited on mobile (view only).
- Bulk task operations (multi-select) are not available on mobile.

---

## 9. Admin & Permissions

### 9.1 Role Hierarchy

```
Owner > Admin > Member > Guest
```

### 9.2 Detailed Permissions

| Action | Owner | Admin | Member | Guest |
|---|---|---|---|---|
| Manage billing | Yes | No | No | No |
| Delete workspace | Yes | No | No | No |
| Transfer ownership | Yes | No | No | No |
| Manage members | Yes | Yes | No | No |
| Manage integrations | Yes | Yes | No | No |
| Create projects | Yes | Yes | Yes | No |
| Edit project settings | Yes | Yes | Project members only | No |
| Create tasks | Yes | Yes | Yes | No |
| Edit any task | Yes | Yes | Own + assigned tasks | No |
| View tasks | Yes | Yes | Projects they belong to | Shared projects only |
| Comment on tasks | Yes | Yes | Yes | View only |
| Delete tasks | Yes | Yes | Own tasks only | No |

### 9.3 SSO / SAML (Enterprise)

- TaskVault supports SAML 2.0 SSO with providers: Okta, Azure AD, OneLogin, Google Workspace.
- Configure in **Settings > Security > SSO**.
- When SSO is enforced, password login is disabled for all non-Owner accounts.
- SCIM provisioning is supported for automatic user creation/deprovisioning.

### 9.4 Audit Logs (Enterprise)

- View all workspace activity in **Settings > Security > Audit Logs**.
- Filterable by user, action type, date range.
- Exportable as CSV.
- Retained for 1 year.

---

## 10. Data Export & Account Deletion

### 10.1 Data Export

- **Who can export:** Owners and Admins.
- **What's included:** Tasks, projects, members, comments, attachments metadata, time entries.
- **Formats:** CSV, JSON.
- **How:** Settings > Workspace > Data Export > Select data > Generate.
- **Delivery:** Download link sent via email (valid for 7 days).
- **Note:** Actual file attachments are not included in the export. Request a separate attachment export by contacting support.

### 10.2 Account Deletion

**Deleting Your Personal Account:**
1. Go to **Settings > Profile > Delete Account**.
2. Confirm by typing your email address.
3. Your account is immediately deactivated.
4. Personal data is deleted within 30 days per our privacy policy.
5. Tasks you created remain in the workspace but are disassociated from your name.

**Deleting a Workspace:**
1. **Owner only.** Go to **Settings > Workspace > Delete Workspace**.
2. Confirm by typing the workspace name.
3. All projects, tasks, members, and data are scheduled for deletion.
4. 30-day recovery window (contact support to restore).
5. After 30 days, all data is permanently and irreversibly deleted.

### 10.3 GDPR & Data Requests

- TaskVault is GDPR compliant.
- To request a copy of your data: email **privacy@taskvault.io**.
- To request data deletion: email **privacy@taskvault.io** with subject "Data Deletion Request."
- Requests are processed within 30 days.
