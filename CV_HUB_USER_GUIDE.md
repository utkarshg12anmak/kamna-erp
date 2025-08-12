# 🚀 CV Hub Access - Quick User Guide

## 📋 Simple Steps to Access CV Hub

### **Option 1: Simple Login (Easiest)**
1. **Open Browser** → Go to http://localhost:8000/login/
2. **Login:**
   - Username: `admin`
   - Password: `admin`
3. **Done!** → You'll be automatically redirected to CV Hub

### **Option 2: From Landing Page**
1. **Go to** → http://localhost:8000/
2. **Click** → "Simple Login" link at the bottom
3. **Login** → Enter admin credentials
4. **Navigate** → Go to CV Hub from the dashboard

### **Option 3: Admin Panel Route**
1. **Go to** → http://localhost:8000/admin/
2. **Login** → Use admin credentials
3. **Open new tab** → Go to http://localhost:8000/app/cv_hub/entries/

## 🔧 Troubleshooting

### **If You See "Access Denied":**
1. **Clear Browser Cache:** Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. **Check Console:** Press F12 → Look for authentication logs
3. **Try Debug Page:** http://localhost:8000/app/cv_hub/debug/
4. **Re-login:** Go to http://localhost:8000/logout/ then login again

### **If Login Doesn't Work:**
1. **Check Server:** Make sure Django server is running
2. **Verify Credentials:** Username: `admin`, Password: `admin`
3. **Clear Cookies:** Clear browser cookies and try again

## 🔗 Important URLs

| Page | URL |
|------|-----|
| **Login** | http://localhost:8000/login/ |
| **CV Hub** | http://localhost:8000/app/cv_hub/entries/ |
| **Dashboard** | http://localhost:8000/app/ |
| **Profile** | http://localhost:8000/profile/ |
| **Debug** | http://localhost:8000/app/cv_hub/debug/ |
| **Logout** | http://localhost:8000/logout/ |

## ✅ Success Indicators

**You know it's working when:**
- ✅ Login page loads without errors
- ✅ You see "Welcome back" message after login
- ✅ CV Hub entries page shows content (not "access denied")
- ✅ Debug page shows "Authenticated: True"
- ✅ Browser console shows "Access granted" messages

## 🆘 Getting Help

**Debug Page:** http://localhost:8000/app/cv_hub/debug/
- Shows your authentication status
- Lists your groups and permissions
- Provides detailed test results

**Browser Console (F12):**
- Look for authentication messages
- Check for any JavaScript errors
- See detailed access control logs

---

**🎉 Enjoy your fully functional CV Hub!**
