# Sprint 9 Testing Guide: User Dashboard & History Management

This guide provides comprehensive testing steps for all Sprint 9 features implemented in the Kisan Smart application.

## Prerequisites

1. Backend server running (`python run.py`)
2. Database populated with some test prediction data
3. Logged-in user account
4. Modern browser (Chrome, Firefox, Edge, Safari)

---

## 1. User Dashboard Testing

### 1.1 Quick Stats Cards

**Test Steps:**
1. Navigate to `/home` after login
2. Observe the 4 stat cards: Total Predictions, This Month, Avg Confidence, Crops Analyzed

**Expected Results:**
- [ ] Numbers animate from 0 to actual values (count-up animation)
- [ ] Total Predictions shows correct count
- [ ] This Month shows current month's count with trend indicator
- [ ] Trend shows "+X from last month" in green or "-X from last month" in red
- [ ] Avg Confidence displays percentage
- [ ] Crops Analyzed shows unique crop count
- [ ] Cards have hover effect (slight lift and shadow)

### 1.2 Recent Activity Widget

**Test Steps:**
1. View the "Recent Predictions" section on dashboard
2. Click on a prediction row
3. Test with empty history (new user)

**Expected Results:**
- [ ] Shows last 5 predictions in table format
- [ ] Displays: crop (with icon), fertilizer, quantity, confidence badge, date
- [ ] Confidence badges are color-coded (green ≥80%, yellow 60-79%, red <60%)
- [ ] Clicking row navigates to `/history`
- [ ] "View All" button navigates to `/history`
- [ ] Empty state shows for new users with "Make Your First Prediction" CTA

### 1.3 Quick Actions

**Test Steps:**
1. Click "New Prediction" button
2. Click "View Full History" button
3. Click "Export All Data" button

**Expected Results:**
- [ ] New Prediction → navigates to `/predict`
- [ ] View Full History → navigates to `/history`
- [ ] Export All Data → triggers CSV download

### 1.4 Dashboard Charts (Optional)

**Test Steps:**
1. Check if charts section is visible (only when data available)
2. View "Predictions Over Time" line chart
3. View "Predictions by Crop" bar chart

**Expected Results:**
- [ ] Charts section hidden when no data
- [ ] Charts section visible when predictions exist
- [ ] Timeline chart shows predictions by month/week
- [ ] Crop chart shows horizontal bars for each crop type
- [ ] Charts are responsive and properly formatted

---

## 2. Prediction History Testing

### 2.1 Initial Load

**Test Steps:**
1. Navigate to `/history`
2. Observe initial table load

**Expected Results:**
- [ ] Breadcrumb shows: Home > History
- [ ] Page title: "Prediction History"
- [ ] "New Prediction" button in header
- [ ] Table loads with predictions sorted by date (newest first)
- [ ] Shows 20 items per page
- [ ] Results count displays correctly (e.g., "47 predictions")

### 2.2 Search Functionality

**Test Steps:**
1. Type crop name in search box (e.g., "wheat")
2. Type fertilizer name (e.g., "urea")
3. Clear search using X button
4. Test with non-existent term

**Expected Results:**
- [ ] Search is debounced (waits ~300ms after typing stops)
- [ ] Results filter as you type
- [ ] Shows only matching crops/fertilizers
- [ ] Search box has clear (X) button
- [ ] Clearing search restores full list
- [ ] No results shows "No Results Found" message

### 2.3 Date Range Filter

**Test Steps:**
1. Select "Today" from date range dropdown
2. Select "Last 7 Days"
3. Select "Last 30 Days"
4. Select "Custom Range" and pick dates
5. Clear filter

**Expected Results:**
- [ ] Each preset filters correctly
- [ ] Custom Range shows date pickers
- [ ] Date pickers allow selecting from/to dates
- [ ] Filters apply when dates selected
- [ ] Filter tag appears below controls
- [ ] Removing tag clears filter

### 2.4 Crop Type Filter

**Test Steps:**
1. Select a crop from dropdown (e.g., "Wheat")
2. Combine with other filters
3. Clear filter

**Expected Results:**
- [ ] Shows only predictions for selected crop
- [ ] Works with combined filters
- [ ] Filter tag appears
- [ ] Results count updates

### 2.5 Confidence Level Filter

**Test Steps:**
1. Select "High (≥80%)"
2. Select "Medium (60-79%)"
3. Select "Low (<60%)"
4. Clear filter

**Expected Results:**
- [ ] Each option filters correctly
- [ ] Shows only predictions in range
- [ ] Filter tag appears
- [ ] Results count updates

### 2.6 Active Filter Tags

**Test Steps:**
1. Apply multiple filters
2. Click X on individual tag
3. Click "Clear All"

**Expected Results:**
- [ ] Tags appear for each active filter
- [ ] Tags show filter name and value
- [ ] Clicking X on tag removes that filter
- [ ] "Clear All" link appears when filters active
- [ ] "Clear All" removes all filters at once

### 2.7 Sorting

**Test Steps:**
1. Change sort to "Date (Oldest First)"
2. Change to "Confidence (High to Low)"
3. Change to "Confidence (Low to High)"
4. Change to "Crop (A-Z)"

**Expected Results:**
- [ ] Table re-sorts immediately
- [ ] Date sorting works correctly
- [ ] Confidence sorting works correctly
- [ ] Crop sorting works alphabetically
- [ ] Pagination resets to page 1 on sort change

### 2.8 Pagination

**Test Steps:**
1. Navigate to page 2 using "Next" button
2. Use page number buttons
3. Use "First" and "Last" buttons
4. Test with different page counts

**Expected Results:**
- [ ] Shows 20 items per page
- [ ] Pagination controls at bottom
- [ ] Shows "Showing X-Y of Z" text
- [ ] First/Prev/Next/Last buttons work
- [ ] Page numbers clickable
- [ ] Ellipsis (...) for large page counts
- [ ] Current page highlighted
- [ ] Disabled buttons greyed out
- [ ] Smooth scroll to top on page change

### 2.9 Bulk Selection

**Test Steps:**
1. Click checkbox in table header
2. Click individual row checkboxes
3. Navigate to different page

**Expected Results:**
- [ ] Header checkbox selects all on current page
- [ ] Individual checkboxes work
- [ ] Selected rows highlighted
- [ ] Selection persists across operations
- [ ] Selection cleared on page change (or retained based on implementation)

### 2.10 View Details Modal

**Test Steps:**
1. Click "View" (eye icon) on a prediction
2. Click anywhere on a row
3. Review modal content
4. Close modal

**Expected Results:**
- [ ] Modal opens with prediction details
- [ ] Shows recommendation summary section
- [ ] Shows input parameters section
- [ ] All values display correctly
- [ ] Confidence badge color-coded
- [ ] Download PDF button present
- [ ] Delete button present
- [ ] Close button works

### 2.11 Delete Functionality

**Test Steps:**
1. Click delete (trash icon) on a row
2. Confirm deletion
3. Click delete from details modal
4. Cancel deletion

**Expected Results:**
- [ ] Delete confirmation modal appears
- [ ] Warning icon and message shown
- [ ] "This action cannot be undone" text
- [ ] Cancel button closes modal
- [ ] Delete button removes prediction
- [ ] Success toast notification
- [ ] Table updates with prediction removed
- [ ] Results count decreases

### 2.12 Bulk Actions

**Test Steps:**
1. Select multiple predictions
2. Click "Export" button
3. Select multiple predictions
4. Click "Delete" button

**Expected Results:**
- [ ] Warning toast if nothing selected
- [ ] Export downloads CSV with selected items only
- [ ] Delete shows confirmation: "Delete X predictions?"
- [ ] Bulk delete removes all selected
- [ ] Success message shows count deleted
- [ ] Selection cleared after action

---

## 3. Export Functionality Testing

### 3.1 CSV Export

**Test Steps:**
1. Navigate to history page
2. Select some predictions
3. Click "Export" button
4. Open downloaded CSV file

**Expected Results:**
- [ ] File downloads as `predictions_export_YYYY-MM-DD.csv`
- [ ] Contains all required columns
- [ ] Data properly formatted
- [ ] Special characters escaped correctly
- [ ] Commas in values handled (quoted)
- [ ] Opens correctly in Excel/Google Sheets

### 3.2 PDF Export

**Test Steps:**
1. View prediction details modal
2. Click "Download PDF"
3. Open downloaded PDF

**Expected Results:**
- [ ] File downloads as `prediction_report_YYYY-MM-DD.pdf`
- [ ] Professional header with "Kisan Smart" branding
- [ ] Shows generation timestamp
- [ ] Summary statistics included
- [ ] Table of predictions formatted well
- [ ] Green color theme for headers
- [ ] Page numbers in footer
- [ ] Readable and printable

---

## 4. Profile Management Testing

### 4.1 Profile Information

**Test Steps:**
1. Navigate to `/profile`
2. Review pre-filled information
3. Edit email, full name, phone, farm details
4. Click "Save Changes"
5. Test validation (invalid email, invalid phone)

**Expected Results:**
- [ ] Breadcrumb: Home > Profile
- [ ] Username field is read-only (greyed out)
- [ ] Current profile data loaded
- [ ] Email validation works
- [ ] Phone validation works (if provided)
- [ ] Save button shows loading state
- [ ] Success toast on save
- [ ] Error toast on failure
- [ ] Validation errors shown inline

### 4.2 Change Password

**Test Steps:**
1. Click "Change Password" button
2. Enter current password
3. Enter new password (try weak, then strong)
4. Observe password strength indicator
5. Toggle password visibility
6. Enter mismatched confirmation
7. Submit with correct data

**Expected Results:**
- [ ] Modal opens
- [ ] Current password field required
- [ ] New password shows strength indicator
- [ ] Indicator shows Weak (red), Medium (yellow), Strong (green)
- [ ] Progress bar fills based on strength
- [ ] Eye icon toggles password visibility
- [ ] Validation error if passwords don't match
- [ ] Validation error if current password wrong
- [ ] Success toast on successful change
- [ ] Modal closes on success
- [ ] Form cleared

### 4.3 Email Preferences

**Test Steps:**
1. Toggle each preference checkbox
2. Click "Save Preferences"

**Expected Results:**
- [ ] Checkboxes toggle correctly
- [ ] Current preferences pre-checked
- [ ] Save button works
- [ ] Success toast shown
- [ ] Preferences persisted (reload page to verify)

### 4.4 Delete Account

**Test Steps:**
1. Click "Delete Account" button in Danger Zone
2. Try to submit without typing "DELETE"
3. Try to submit without password
4. Type "DELETE" and enter password
5. Complete deletion

**Expected Results:**
- [ ] Modal has red header and warning styling
- [ ] Large warning icon shown
- [ ] Lists all data that will be deleted
- [ ] Must type exactly "DELETE" (case-sensitive)
- [ ] Must enter password
- [ ] Validation prevents submission if missing
- [ ] Successful deletion shows toast
- [ ] Redirects to home/login after 2 seconds
- [ ] localStorage cleared
- [ ] Account actually deleted from database

---

## 5. Responsive Design Testing

### 5.1 Dashboard Mobile

**Test Steps:**
1. Open `/home` on mobile (or resize browser to ~375px)
2. Scroll through page

**Expected Results:**
- [ ] Stat cards stack vertically
- [ ] Cards maintain readability
- [ ] Recent activity table responsive
- [ ] Quick action buttons full-width
- [ ] Charts responsive and scrollable if needed

### 5.2 History Mobile

**Test Steps:**
1. Open `/history` on mobile
2. Apply filters
3. View table/cards

**Expected Results:**
- [ ] Filters stack vertically
- [ ] Table converts to card view on mobile
- [ ] Each prediction in a card with all key info
- [ ] Cards tap-friendly
- [ ] Pagination controls work on mobile
- [ ] Modals full-screen or properly sized
- [ ] Action buttons accessible

### 5.3 Profile Mobile

**Test Steps:**
1. Open `/profile` on mobile
2. Fill form
3. Open modals

**Expected Results:**
- [ ] Form fields full-width
- [ ] Cards stack properly
- [ ] Modals display correctly
- [ ] Touch-friendly buttons
- [ ] Password toggle accessible

---

## 6. Integration Testing

### 6.1 Dashboard → History Flow

**Test Steps:**
1. Click on prediction in recent activity
2. Navigate back using breadcrumb

**Expected Results:**
- [ ] Clicking navigates to history page
- [ ] Filter/sort state persists or resets appropriately
- [ ] Back navigation works

### 6.2 History → Details → Delete Flow

**Test Steps:**
1. View prediction details
2. Delete from modal
3. Confirm deletion

**Expected Results:**
- [ ] Details modal shows
- [ ] Delete from modal opens confirmation
- [ ] Deletion works
- [ ] Both modals close
- [ ] Table updates

### 6.3 Profile → Change Password → Logout Flow

**Test Steps:**
1. Change password
2. Logout
3. Login with new password

**Expected Results:**
- [ ] Password change successful
- [ ] Can logout
- [ ] Old password doesn't work
- [ ] New password works

---

## 7. Error Handling Testing

### 7.1 Network Errors

**Test Steps:**
1. Stop backend server
2. Try to load dashboard
3. Try to load history
4. Try to save profile

**Expected Results:**
- [ ] Error messages displayed
- [ ] Loading states clear
- [ ] User notified of connection issue
- [ ] Graceful degradation

### 7.2 Empty States

**Test Steps:**
1. Test with brand new user (no predictions)
2. Test search with no results
3. Test filters with no matching data

**Expected Results:**
- [ ] Dashboard shows 0's in stat cards
- [ ] Recent activity shows empty state with CTA
- [ ] History shows "No Predictions Yet" message
- [ ] No results state for failed searches
- [ ] CTAs guide user to create prediction

---

## 8. Performance Testing

### 8.1 Large Dataset

**Test Steps:**
1. Test with 100+ predictions
2. Apply filters and sort
3. Navigate pages

**Expected Results:**
- [ ] Page loads quickly (<2 seconds)
- [ ] Filtering is instant (client-side)
- [ ] Sorting is instant
- [ ] Pagination smooth
- [ ] No browser lag

### 8.2 Export Large Dataset

**Test Steps:**
1. Export 100+ predictions to CSV
2. Export 100+ predictions to PDF

**Expected Results:**
- [ ] CSV exports quickly
- [ ] PDF generates without timeout
- [ ] Files are reasonable size
- [ ] All data included

---

## 9. Cross-Browser Testing

**Browsers to Test:**
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Safari (if available)

**Key Features to Verify:**
- [ ] Styling consistent
- [ ] Animations work
- [ ] Modals function
- [ ] Downloads work
- [ ] Forms submit correctly

---

## 10. Accessibility Testing

**Test Steps:**
1. Navigate using keyboard only (Tab, Enter, Escape)
2. Test with screen reader
3. Check color contrast

**Expected Results:**
- [ ] All interactive elements focusable
- [ ] Tab order logical
- [ ] Enter/Space activate buttons
- [ ] Escape closes modals
- [ ] ARIA labels present
- [ ] Color contrast meets WCAG standards 
- [ ] Form labels properly associated

---

## Summary Checklist

After completing all tests, verify:

- [ ] All dashboard stats display correctly
- [ ] Recent activity widget works
- [ ] All filters function properly
- [ ] Pagination works smoothly
- [ ] Sorting applies correctly
- [ ] Search is fast and accurate
- [ ] Bulk actions work
- [ ] CSV export succeeds
- [ ] PDF export succeeds
- [ ] Profile editing works
- [ ] Password change works
- [ ] Account deletion works
- [ ] Mobile responsive
- [ ] Modals function properly
- [ ] Error states handled
- [ ] Empty states shown
- [ ] Performance acceptable
- [ ] Cross-browser compatible
- [ ] Accessible

---

**Testing Complete!** If all items check out, Sprint 9 is ready for deployment.
