#!/usr/bin/env python3
"""
iPhone Download Issues Analysis and Solutions
Comprehensive analysis of CSV download functionality for iPhone compatibility
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://scoreleader.preview.emergentagent.com/api"

class iPhoneDownloadAnalyzer:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_group_id = None
        self.issues_found = []
        self.solutions = []
        
    def log_issue(self, issue_type, description, severity="medium", solution=None):
        """Log an issue found during analysis"""
        issue = {
            "type": issue_type,
            "description": description,
            "severity": severity,
            "solution": solution
        }
        self.issues_found.append(issue)
        
        severity_icon = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
        print(f"{severity_icon} {issue_type}: {description}")
        if solution:
            print(f"   💡 Solution: {solution}")
    
    def log_solution(self, solution_type, description, implementation):
        """Log a solution for iPhone download issues"""
        solution = {
            "type": solution_type,
            "description": description,
            "implementation": implementation
        }
        self.solutions.append(solution)
        print(f"✅ {solution_type}: {description}")
    
    def setup_test_group(self):
        """Create a test group for analysis"""
        print("\n=== SETTING UP TEST GROUP FOR iPHONE ANALYSIS ===")
        
        try:
            # Create test group with sample data
            group_data = {"group_name": "iPhone Download Test"}
            response = requests.post(f"{self.base_url}/groups", json=group_data)
            
            if response.status_code == 200:
                group = response.json()
                self.test_group_id = group["id"]
                print(f"✅ Created test group: {group['group_name']} (ID: {group['id']})")
                
                # Add sample player and game data
                self.create_sample_data()
                return True
            else:
                print(f"❌ Failed to create group: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during setup: {str(e)}")
            return False
    
    def create_sample_data(self):
        """Create sample data for testing"""
        try:
            # Create sample players
            players = [
                {"player_name": "Alice Johnson", "group_id": self.test_group_id, "emoji": "🎭"},
                {"player_name": "Bob Smith", "group_id": self.test_group_id, "emoji": "🎯"}
            ]
            
            player_ids = []
            for player in players:
                response = requests.post(f"{self.base_url}/players", json=player)
                if response.status_code == 200:
                    player_ids.append(response.json()["id"])
            
            # Create sample game session
            if len(player_ids) >= 2:
                session_data = {
                    "group_id": self.test_group_id,
                    "game_name": "Test Game",
                    "game_date": "2024-01-15T19:00:00",
                    "player_scores": [
                        {"player_id": player_ids[0], "player_name": "Alice Johnson", "score": 15},
                        {"player_id": player_ids[1], "player_name": "Bob Smith", "score": 12}
                    ]
                }
                requests.post(f"{self.base_url}/game-sessions", json=session_data)
                
        except Exception as e:
            print(f"Warning: Could not create sample data: {str(e)}")
    
    def analyze_backend_compatibility(self):
        """Analyze backend CSV endpoint for iPhone compatibility"""
        print("\n=== ANALYZING BACKEND COMPATIBILITY ===")
        
        if not self.test_group_id:
            self.log_issue("Setup", "No test group available", "high")
            return
        
        try:
            # Test with iPhone user agent
            iphone_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/csv,application/csv,text/plain,*/*',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            response = requests.get(f"{self.base_url}/groups/{self.test_group_id}/download-csv", headers=iphone_headers)
            
            if response.status_code != 200:
                self.log_issue("Backend Response", f"CSV endpoint returns {response.status_code}", "high",
                             "Ensure backend CSV endpoint is accessible and returns 200 OK")
                return
            
            # Check headers for iPhone compatibility
            headers = response.headers
            
            # Content-Type analysis
            content_type = headers.get('Content-Type', '')
            if 'text/csv' not in content_type:
                self.log_issue("Content-Type", f"Content-Type is '{content_type}', should include 'text/csv'", "medium",
                             "Update backend to return 'text/csv; charset=utf-8'")
            
            # Content-Disposition analysis
            content_disposition = headers.get('Content-Disposition', '')
            if 'attachment' not in content_disposition:
                self.log_issue("Content-Disposition", "Missing 'attachment' in Content-Disposition", "medium",
                             "Add 'attachment; filename=...' to Content-Disposition header")
            
            # CORS analysis for web views
            cors_origin = headers.get('Access-Control-Allow-Origin')
            if not cors_origin:
                self.log_issue("CORS", "Missing CORS headers for web view compatibility", "medium",
                             "Add CORS middleware to allow cross-origin requests from mobile web views")
            
            # File size analysis
            content_length = headers.get('Content-Length')
            if content_length and int(content_length) > 50 * 1024 * 1024:  # 50MB
                self.log_issue("File Size", f"Large file size ({content_length} bytes) may cause iPhone issues", "low",
                             "Consider pagination or compression for large datasets")
            
            print("✅ Backend compatibility analysis completed")
            
        except Exception as e:
            self.log_issue("Backend Analysis", f"Exception during analysis: {str(e)}", "high")
    
    def analyze_frontend_implementation(self):
        """Analyze frontend implementation for iPhone issues"""
        print("\n=== ANALYZING FRONTEND IMPLEMENTATION ===")
        
        # Read the frontend implementation
        try:
            with open('/app/frontend/app/group/[id]/index.tsx', 'r') as f:
                frontend_code = f.read()
            
            # Check for proper Expo imports
            required_imports = [
                'expo-file-system',
                'expo-sharing',
                'expo-document-picker'
            ]
            
            missing_imports = []
            for import_name in required_imports:
                if import_name not in frontend_code:
                    missing_imports.append(import_name)
            
            if missing_imports:
                self.log_issue("Missing Imports", f"Missing imports: {', '.join(missing_imports)}", "high",
                             f"Add imports for {', '.join(missing_imports)}")
            
            # Check for iOS-specific handling
            if 'Platform.OS === \'ios\'' not in frontend_code:
                self.log_issue("iOS Detection", "No iOS-specific handling detected", "medium",
                             "Add Platform.OS === 'ios' checks for iOS-specific download behavior")
            
            # Check for proper error handling
            if 'catch' not in frontend_code or 'Alert.alert' not in frontend_code:
                self.log_issue("Error Handling", "Insufficient error handling for download failures", "medium",
                             "Add comprehensive try-catch blocks and user-friendly error messages")
            
            # Check for sharing availability check
            if 'Sharing.isAvailableAsync' not in frontend_code:
                self.log_issue("Sharing Check", "Missing sharing availability check", "low",
                             "Add Sharing.isAvailableAsync() check before attempting to share")
            
            print("✅ Frontend implementation analysis completed")
            
        except Exception as e:
            self.log_issue("Frontend Analysis", f"Could not analyze frontend: {str(e)}", "medium")
    
    def analyze_ios_specific_issues(self):
        """Analyze iOS-specific download issues"""
        print("\n=== ANALYZING iOS-SPECIFIC ISSUES ===")
        
        # Issue 1: iOS Safari download restrictions
        self.log_issue("Safari Restrictions", 
                      "iOS Safari has strict download restrictions and may not trigger downloads properly",
                      "high",
                      "Use expo-sharing with proper MIME types and UTI instead of direct downloads")
        
        # Issue 2: File system access
        self.log_issue("File System Access",
                      "iOS apps have sandboxed file system access",
                      "medium", 
                      "Use documentDirectory from expo-file-system for temporary file storage")
        
        # Issue 3: Sharing limitations
        self.log_issue("Sharing Limitations",
                      "iOS sharing requires proper UTI (Uniform Type Identifier) for CSV files",
                      "medium",
                      "Use UTI 'public.comma-separated-values-text' in sharing options")
        
        # Issue 4: Network security
        self.log_issue("Network Security",
                      "iOS requires HTTPS for network requests in production",
                      "low",
                      "Ensure all API calls use HTTPS (already implemented)")
        
        print("✅ iOS-specific issues analysis completed")
    
    def generate_solutions(self):
        """Generate comprehensive solutions for iPhone download issues"""
        print("\n=== GENERATING SOLUTIONS ===")
        
        # Solution 1: Enhanced backend CORS support
        self.log_solution("Backend CORS Enhancement",
                         "Add comprehensive CORS support for mobile web views",
                         """
Add CORS middleware to FastAPI backend:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```""")
        
        # Solution 2: Improved frontend download implementation
        self.log_solution("Frontend Download Enhancement",
                         "Implement iOS-optimized download strategy",
                         """
Enhanced handleDownloadHistory function:
```typescript
const handleDownloadHistory = async () => {
  if (!group) return;
  
  setExporting(true);
  try {
    const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/download-csv`);
    if (!response.ok) throw new Error('Failed to fetch CSV data');
    
    const csvData = await response.text();
    const filename = `${group.group_name.replace(/[^a-zA-Z0-9]/g, '_')}_history_${new Date().toISOString().split('T')[0]}.csv`;
    
    if (Platform.OS === 'ios') {
      // iOS-specific implementation
      const fileUri = documentDirectory + filename;
      await writeAsStringAsync(fileUri, csvData, { encoding: EncodingType.UTF8 });
      
      const isAvailable = await Sharing.isAvailableAsync();
      if (isAvailable) {
        await Sharing.shareAsync(fileUri, {
          mimeType: 'text/csv',
          dialogTitle: 'Save Board Game History',
          UTI: 'public.comma-separated-values-text'
        });
      } else {
        // Fallback: Copy to clipboard or show data
        Alert.alert('Download Complete', 'File saved to app documents');
      }
    } else {
      // Android/Web implementation
      // ... existing implementation
    }
  } catch (error) {
    Alert.alert('Download Failed', 'Please try again or contact support');
  } finally {
    setExporting(false);
  }
};
```""")
        
        # Solution 3: Alternative download methods
        self.log_solution("Alternative Download Methods",
                         "Implement fallback methods for iOS compatibility",
                         """
1. WebBrowser fallback:
```typescript
import * as WebBrowser from 'expo-web-browser';

const handleWebDownload = async () => {
  const downloadUrl = `${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/download-csv`;
  await WebBrowser.openBrowserAsync(downloadUrl);
};
```

2. Email sharing:
```typescript
import * as MailComposer from 'expo-mail-composer';

const handleEmailShare = async (csvData: string, filename: string) => {
  const isAvailable = await MailComposer.isAvailableAsync();
  if (isAvailable) {
    await MailComposer.composeAsync({
      subject: 'Board Game History',
      body: 'Please find attached your board game history.',
      attachments: [{
        filename,
        content: csvData,
        mimeType: 'text/csv'
      }]
    });
  }
};
```""")
        
        # Solution 4: User experience improvements
        self.log_solution("UX Improvements",
                         "Enhance user experience for iPhone users",
                         """
1. Clear instructions for iPhone users:
```typescript
const showDownloadInstructions = () => {
  Alert.alert(
    'Download Instructions',
    Platform.OS === 'ios' 
      ? 'On iPhone: Tap the share button and choose "Save to Files" or share via email/messages.'
      : 'Your file will be downloaded to your device.',
    [{ text: 'Got it!' }]
  );
};
```

2. Progress indicators:
```typescript
const [downloadProgress, setDownloadProgress] = useState(0);

// Show progress during download
<ActivityIndicator animating={exporting} />
{exporting && <Text>Preparing your download...</Text>}
```""")
        
        # Solution 5: Testing recommendations
        self.log_solution("Testing Strategy",
                         "Comprehensive testing approach for iPhone compatibility",
                         """
1. Test on actual iPhone devices with different iOS versions
2. Test in both Safari and in-app web views
3. Test with different file sizes and data volumes
4. Test network conditions (slow/fast connections)
5. Test sharing to different apps (Files, Mail, Messages, etc.)

Testing checklist:
- [ ] Download works in Safari
- [ ] Download works in app
- [ ] Sharing menu appears correctly
- [ ] File can be saved to Files app
- [ ] File can be shared via email
- [ ] Error handling works properly
- [ ] User gets clear feedback
""")
    
    def run_analysis(self):
        """Run complete iPhone download analysis"""
        print("📱 iPHONE DOWNLOAD ISSUES ANALYSIS STARTED")
        print("=" * 60)
        
        # Setup test environment
        if not self.setup_test_group():
            print("❌ Failed to setup test environment. Analysis may be incomplete.")
        
        # Run analysis
        self.analyze_backend_compatibility()
        self.analyze_frontend_implementation()
        self.analyze_ios_specific_issues()
        self.generate_solutions()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print analysis summary and recommendations"""
        print("\n" + "=" * 60)
        print("📊 iPHONE DOWNLOAD ANALYSIS SUMMARY")
        print("=" * 60)
        
        # Issues summary
        high_issues = [i for i in self.issues_found if i["severity"] == "high"]
        medium_issues = [i for i in self.issues_found if i["severity"] == "medium"]
        low_issues = [i for i in self.issues_found if i["severity"] == "low"]
        
        print(f"Issues Found:")
        print(f"  🔴 High Priority: {len(high_issues)}")
        print(f"  🟡 Medium Priority: {len(medium_issues)}")
        print(f"  🟢 Low Priority: {len(low_issues)}")
        print(f"  Total: {len(self.issues_found)}")
        
        if high_issues:
            print(f"\n🔴 HIGH PRIORITY ISSUES:")
            for issue in high_issues:
                print(f"   • {issue['type']}: {issue['description']}")
        
        print(f"\n✅ SOLUTIONS PROVIDED: {len(self.solutions)}")
        
        print(f"\n📋 IMMEDIATE ACTION ITEMS:")
        print("1. Add CORS middleware to backend for mobile web view support")
        print("2. Enhance frontend download implementation with iOS-specific handling")
        print("3. Test on actual iPhone devices with different iOS versions")
        print("4. Implement fallback methods (WebBrowser, email sharing)")
        print("5. Add clear user instructions for iPhone download process")
        
        print(f"\n🎯 EXPECTED OUTCOME:")
        print("After implementing these solutions, iPhone users should be able to:")
        print("• Download CSV files through the native sharing interface")
        print("• Save files to the Files app or share via email/messages")
        print("• Receive clear feedback and instructions throughout the process")
        print("• Have fallback options if primary download method fails")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    analyzer = iPhoneDownloadAnalyzer()
    analyzer.run_analysis()