# Sprint 8 Testing Guide - Core Application UI

## Quick Verification Checklist

### Prediction Input Form (`/dashboard`)
- [ ] Page loads with Bootstrap 5 styling
- [ ] Crop dropdown displays 7 options
- [ ] Farm area input accepts decimal values
- [ ] All 6 dual sliders work:
  - [ ] Nitrogen (N)
  - [ ] Phosphorus (P)
  - [ ] Potassium (K)
  - [ ] Soil pH
  - [ ] Moisture
  - [ ] Temperature
- [ ] Slider movement updates number input immediately
- [ ] Number input changes update slider immediately
- [ ] Status indicators update (Low/Medium/High)
- [ ] Status colors change based on value
- [ ] Tooltips appear on hover
- [ ] "Load Sample Data" button works
- [ ] "Clear All" button resets form
- [ ] Form validates before submission
- [ ] Loading overlay appears during prediction
- [ ] Mobile responsive (sliders stack vertically)

### Results Dashboard (`/results`)
- [ ] Hero section displays fertilizer type
- [ ] Quantity shows per hectare and total
- [ ] Confidence meter animates smoothly
- [ ] Confidence meter color matches level
- [ ] NPK donut chart renders correctly
- [ ] Application guidelines display
- [ ] Confidence detail bars show correctly
- [ ] Alternative recommendations table displays (if available)
- [ ] Input summary is collapsible
- [ ] "Save" button saves to history
- [ ] "Print" button opens print dialog
- [ ] "New Prediction" returns to dashboard
- [ ] Mobile responsive (sections stack)

### Dual Slider Component
- [ ] Slider has gradient background (red-yellow-green)
- [ ] Thumb is circular and green
- [ ] Number input shows unit label
- [ ] Synchronized in both directions
- [ ] Status badge shows correct color
- [ ] Touch-friendly on mobile

### Validation
- [ ] Empty crop shows error
- [ ] Empty farm area shows error
- [ ] NPK values > 200 show error
- [ ] pH < 3.0 or > 10.0 shows error
- [ ] Moisture > 100 shows error
- [ ] Temperature < -10 or > 50 shows error
- [ ] Validation messages clear on input
- [ ] Submit button disabled when invalid

## Detailed Testing Scenarios

### Scenario 1: Basic Prediction Flow
1. Navigate to `/dashboard`
2. Select "Wheat" from crop dropdown
3. Verify default values are loaded
4. Click "Get Recommendation"
5. Wait for loading overlay
6. Verify redirect to results page
7. Check all sections render correctly

**Expected Result**: Full prediction flow works end-to-end

### Scenario 2: Sample Data Loading
1. Go to `/dashboard`
2. Select "Rice" from dropdown
3. Click "Load Sample Data"
4. Verify all inputs populate with rice-specific values:
   - N: 50, P: 35, K: 30
   - pH: 6.5, Moisture: 75, Temp: 25
5. Check that statuses update automatically
6. Submit and verify results

**Expected Result**: Sample data loads correctly and prediction succeeds

### Scenario 3: Slider Synchronization
1. Go to `/dashboard`
2. Move Nitrogen slider to 100
3. Verify number input shows "100"
4. Verify status changes to "Medium" or "High"
5. Type "150" in number input
6. Verify slider moves to 150
7. Verify status updates
8. Repeat for all other sliders

**Expected Result**: Perfect synchronization in both directions

### Scenario 4: Validation Errors
1. Go to `/dashboard`
2. Leave crop empty
3. Click "Get Recommendation"
4. Verify error message appears
5. Select crop
6. Set Nitrogen to "250" (exceeds max)
7. Try to submit
8. Verify error message
9. Fix value to "100"
10. Verify error clears
11. Set pH to "2.0" (below min)
12. Try to submit
13. Verify error message

**Expected Result**: All validation errors caught and displayed clearly

### Scenario 5: Results Visualization
1. Complete a prediction
2. On results page:
   - Watch confidence meter animate from 0% to target
   - Verify meter color matches level (green/yellow/red)
   - Check NPK chart renders with 3 segments
   - Verify chart legend shows N, P, K
3. Scroll through all sections
4. Expand "View Input Parameters"
5. Verify all inputs are shown correctly

**Expected Result**: All visualizations render smoothly and accurately

### Scenario 6: Save and Print
1. Complete a prediction
2. Click "Save Recommendation"
3. Verify success toast appears
4. Click "Print"
5. Verify print preview shows:
   - No navigation/footer
   - All content visible
   - Proper formatting
6. Cancel print
7. Click "New Prediction"
8. Verify return to dashboard

**Expected Result**: Save and print functions work correctly

### Scenario 7: Mobile Responsiveness
1. Open dashboard on mobile (or use DevTools device mode)
2. Verify:
   - Hamburger menu visible
   - Sliders stack vertically
   - Number inputs full width
   - Touch interactions work
   - No horizontal scroll
3. Complete a prediction
4. On results page verify:
   - Hero section readable
   - Charts responsive
   - Action buttons stack
   - All content accessible

**Expected Result**: Fully functional on mobile devices

### Scenario 8: Error Handling
1. Disconnect internet
2. Try to submit prediction
3. Verify network error message
4. Reconnect internet
5. Stop Flask server
6. Try to submit
7. Verify appropriate error message
8. Restart server
9. Submit with invalid data
10. Verify validation error messages

**Expected Result**: All error scenarios handled gracefully

## Browser Compatibility Testing

Test on the following browsers:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Chrome Mobile (Android)
- [ ] Safari Mobile (iOS)

## Performance Testing

- [ ] Page load time < 2 seconds
- [ ] Slider interactions smooth (no lag)
- [ ] Chart rendering < 500ms
- [ ] Prediction submission < 5 seconds
- [ ] No memory leaks after multiple predictions

## Accessibility Testing

- [ ] All inputs have labels
- [ ] Tab navigation works
- [ ] Focus visible on all interactive elements
- [ ] ARIA labels present where needed
- [ ] Color contrast meets WCAG AA
- [ ] Screen reader can announce all content
- [ ] Tooltips accessible via keyboard

## Common Issues & Solutions

### Issue: Sliders not synchronizing
- **Check**: JavaScript console for errors
- **Solution**: Verify prediction.js is loaded

### Issue: Charts not rendering
- **Check**: Chart.js loaded successfully
- **Solution**: Check network tab, verify CDN link

### Issue: Prediction fails
- **Check**: Backend API running
- **Check**: JWT token valid
- **Solution**: Check browser console and network tab

### Issue: Mobile sliders hard to use
- **Check**: Touch event handling
- **Solution**: Use larger thumb size on mobile

### Issue: Print shows navigation
- **Check**: @media print styles
- **Solution**: Verify print CSS loaded

## Next Steps After Verification

After Sprint 8 verification, proceed to:
- Sprint 9: User Dashboard & History Management
- Implement history page with pagination
- Add filters and search
- Create user statistics dashboard
