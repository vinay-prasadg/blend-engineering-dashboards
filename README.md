# Blend Production Defect Tracker

A modern, web-based defect tracking system specifically designed for tracking production defects in the Blend production environment.

## Features

- ✅ **Add Defects**: Create new defect entries with comprehensive details
- ✅ **Edit Defects**: Update existing defect information
- ✅ **Delete Defects**: Remove defects from the tracker
- ✅ **Filter by Status**: Filter defects by Open, In Progress, Resolved, or Closed
- ✅ **Filter by Severity**: Filter by Critical, High, Medium, or Low severity
- ✅ **Search**: Search defects by title, description, assignee, or URL
- ✅ **Statistics Dashboard**: View total defects, critical count, open count, and resolved count
- ✅ **Local Storage**: All defects are saved locally in your browser
- ✅ **Responsive Design**: Works on desktop, tablet, and mobile devices

## Getting Started

1. **Open the Application**
   - Simply open `index.html` in any modern web browser (Chrome, Firefox, Safari, Edge)
   - No installation or server setup required!

2. **Add Your First Defect**
   - Click the "+ Add New Defect" button
   - Fill in the required fields:
     - **Defect Title**: Brief description of the issue
     - **Severity**: Critical, High, Medium, or Low
     - **Status**: Open, In Progress, Resolved, or Closed
     - **Description**: Detailed description of the defect
   - Optional fields:
     - **Assignee**: Person responsible for fixing the defect
     - **Environment**: Production (default), Staging, or Development
     - **Steps to Reproduce**: Step-by-step instructions
     - **Affected URL/Component**: The URL or component affected

3. **Manage Defects**
   - **Edit**: Click the "Edit" button on any defect card
   - **Delete**: Click the "Delete" button (with confirmation)
   - **Filter**: Use the dropdown filters to view specific defect types
   - **Search**: Type in the search box to find defects by keywords

## Defect Fields

### Required Fields
- **Defect Title**: A concise title describing the defect
- **Severity**: 
  - **Critical**: System down, data loss, security breach
  - **High**: Major functionality broken, significant impact
  - **Medium**: Moderate impact, workaround available
  - **Low**: Minor issue, cosmetic problem
- **Status**:
  - **Open**: Newly reported defect
  - **In Progress**: Currently being worked on
  - **Resolved**: Fixed but not yet verified
  - **Closed**: Verified and closed
- **Description**: Detailed information about the defect

### Optional Fields
- **Assignee**: Person or team responsible
- **Environment**: Production (default), Staging, Development
- **Steps to Reproduce**: Numbered steps to reproduce the issue
- **Affected URL/Component**: Specific URL or component path

## Data Storage

All defects are stored locally in your browser's localStorage. This means:
- ✅ No server required
- ✅ Data persists between sessions
- ✅ Fast and private
- ⚠️ Data is browser-specific (not synced across devices)
- ⚠️ Clearing browser data will remove all defects

## Statistics Dashboard

The dashboard shows:
- **Total Defects**: All defects in the system
- **Critical**: Count of critical severity defects
- **Open**: Count of open status defects
- **Resolved**: Count of resolved/closed defects

## Browser Compatibility

Works on all modern browsers:
- Chrome (recommended)
- Firefox
- Safari
- Edge
- Opera

## Tips

1. **Use Descriptive Titles**: Make defect titles clear and searchable
2. **Include Steps to Reproduce**: Helps developers fix issues faster
3. **Update Status Regularly**: Keep status current for accurate tracking
4. **Use Search**: Quickly find defects using keywords
5. **Filter by Severity**: Focus on critical issues first

## Export/Backup (Future Enhancement)

To backup your data:
1. Open browser Developer Tools (F12)
2. Go to Application/Storage tab
3. Find Local Storage → your domain
4. Copy the `blendDefects` value
5. Save it as a JSON file

To restore:
1. Open Developer Tools
2. Go to Local Storage
3. Paste the JSON value back into `blendDefects`

## Support

For issues or questions about this defect tracker, please contact your development team.

---

**Version**: 1.0.0  
**Last Updated**: February 2026
