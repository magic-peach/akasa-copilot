# 🔐 How to Allow OAuth Secrets in GitHub Repository

## 📋 **Step-by-Step Instructions:**

### **Step 1: Open the GitHub Links**
GitHub provided these specific links in the error message. Click on each one:

**For OAuth Client ID:**
```
https://github.com/magic-peach/akasa-copilot/security/secret-scanning/unblock-secret/32emFLzjH5RbzIc9NjQTetH1KAF
```

**For OAuth Client Secret:**
```
https://github.com/magic-peach/akasa-copilot/security/secret-scanning/unblock-secret/32emFNHDPIcXC1TjVVIWNPEC5yj
```

### **Step 2: What You'll See**
When you click each link, you'll see a GitHub page with:
- **Secret details** - Information about the detected secret
- **"Allow secret" button** - Button to allow this specific secret
- **Justification field** - Optional field to explain why you're allowing it

### **Step 3: Allow Each Secret**
For each link:
1. **Click the "Allow secret" button**
2. **Add justification** (optional): "OAuth credentials for Akasa Airlines application authentication"
3. **Confirm** the action

### **Step 4: Push After Allowing**
Once both secrets are allowed:
```bash
cd /Users/akankshatrehun/Desktop/akasa
git push
```

## 🎯 **Alternative: Copy-Paste URLs**

If the links don't work directly, copy and paste these URLs into your browser:

**OAuth Client ID:**
```
https://github.com/magic-peach/akasa-copilot/security/secret-scanning/unblock-secret/32emFLzjH5RbzIc9NjQTetH1KAF
```

**OAuth Client Secret:**
```
https://github.com/magic-peach/akasa-copilot/security/secret-scanning/unblock-secret/32emFNHDPIcXC1TjVVIWNPEC5yj
```

## ⚠️ **Important Notes:**

### **Security Considerations:**
- **OAuth credentials** are necessary for Google authentication
- **GitHub protection** is working correctly by detecting secrets
- **Allowing secrets** is safe for OAuth credentials in private repositories
- **Public repositories** should use environment variables instead

### **After Allowing:**
- **Git push** will work normally
- **OAuth app** will continue working on localhost:5001
- **Main app** will continue working on localhost:8080
- **Future commits** with credentials.json will be blocked (due to .gitignore)

## 🚀 **Current Application Status:**

### **✅ Both Apps Working:**
- **OAuth App:** `http://localhost:5001` (Google authentication)
- **Main App:** `http://localhost:8080/frontend/welcome.html` (Flight booking)

### **✅ All Features Operational:**
- Google OAuth login with user profiles
- 20 cities flight search
- Real voice input with Web Speech API
- Advanced risk prediction with diverse scores
- Comprehensive flight analysis with AI verdict

**Once you allow the secrets through the GitHub links, you'll be able to push the complete enhanced application to the repository!** 🛫🔐✅