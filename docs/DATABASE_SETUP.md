# Navidrome Database Access Setup

This guide helps you configure Pyper to access your Navidrome database for play count features.

## 🎯 Overview

Pyper can access play count data in two ways:
1. **SSH Database Access** (recommended for remote servers)
2. **API Fallback** (limited data, but always works)

## 🔧 SSH Database Access Setup

### Step 1: Configure SSH Access

Ensure you can SSH to your Navidrome server:

```bash
# Test SSH connection
ssh user@your-server.com

# Test with specific key
ssh -i ~/.ssh/id_ed25519 user@your-server.com
```

### Step 2: Locate Navidrome Database

Find your Navidrome database file on the server:

```bash
# Common locations
find /home -name "navidrome.db" 2>/dev/null
find /var/lib -name "navidrome.db" 2>/dev/null
find /opt -name "navidrome.db" 2>/dev/null

# Check Navidrome config for DataFolder
cat /etc/navidrome/navidrome.toml | grep DataFolder
```

### Step 3: Update Pyper Configuration

Edit your `config/config.json`:

```json
{
    "navidrome": {
        "server_url": "http://your-server:4533",
        "username": "your_username",
        "password": "your_password",
        "database_path": "/home/kevin/.navidrome/navidrome.db",
        "ssh_host": "your-server.com",
        "ssh_user": "kevin",
        "ssh_key_path": "~/.ssh/id_ed25519"
    }
}
```

### Step 4: Test Database Access

```bash
# Test SCP access to database
scp -i ~/.ssh/id_ed25519 user@server:/path/to/navidrome.db /tmp/test.db

# Verify database content
sqlite3 /tmp/test.db "SELECT COUNT(*) FROM album;"
```

## 🚨 Troubleshooting

### SSH Connection Issues

**Problem**: "Permission denied (publickey)"
```bash
# Solution: Add your key to SSH agent
ssh-add ~/.ssh/id_ed25519

# Or specify key in SSH config
echo "Host your-server
    IdentityFile ~/.ssh/id_ed25519
    User kevin" >> ~/.ssh/config
```

**Problem**: "Host key verification failed"
```bash
# Solution: Add host to known_hosts
ssh-keyscan -H your-server >> ~/.ssh/known_hosts
```

### Database Access Issues

**Problem**: "Database is locked"
- Navidrome is using the database
- Solution: Pyper copies the database, so this shouldn't affect operation

**Problem**: "No such file or directory"
- Database path is incorrect
- Solution: Check the actual path on your server

**Problem**: "Permission denied"
- SSH user doesn't have read access to database
- Solution: Ensure your SSH user can read the database file

### Performance Considerations

**Database Size**: Large databases (>100MB) may take time to copy
```bash
# Check database size
ssh user@server "ls -lh /path/to/navidrome.db"
```

**Copy Frequency**: Database is copied once per session
- Restart Pyper to get latest play counts
- Consider automating with a refresh button

## 🔄 API Fallback Mode

If database access fails, Pyper automatically falls back to API mode:

### Available Data
- **Most Played**: Uses `getAlbumList2?type=frequent`
- **Recently Played**: Uses `getAlbumList2?type=recent`
- **Limitations**: No exact play counts, estimated based on order

### API Requirements
- Navidrome server must support these API endpoints
- Some older versions may not have all features

## 🎛️ Configuration Options

### SSH Configuration
```json
{
    "ssh_host": "server.example.com",    // Server hostname/IP
    "ssh_user": "username",              // SSH username  
    "ssh_key_path": "~/.ssh/id_rsa",    // Path to SSH private key
    "database_path": "/path/to/db"       // Database path on server
}
```

### Optional SSH Config
You can also use SSH config file (`~/.ssh/config`):
```
Host navidrome
    HostName your-server.com
    User kevin
    IdentityFile ~/.ssh/id_ed25519
    Port 22
```

Then use `"ssh_host": "navidrome"` in Pyper config.

## 🔒 Security Notes

1. **Read-Only Access**: Pyper only reads the database, never writes
2. **Temporary Files**: Database copies are stored in temp directory and cleaned up
3. **SSH Keys**: Use key-based authentication, not passwords
4. **Permissions**: Ensure minimal required permissions for SSH user

## 🚀 Advanced Setup

### Automated Database Sync
For frequently updated play counts, consider:

```bash
# Cron job to sync database hourly
0 * * * * scp user@server:/path/navidrome.db /local/cache/
```

### Multiple Servers
Configure different profiles for multiple Navidrome instances:

```json
{
    "profiles": {
        "home": {
            "navidrome": { "ssh_host": "home-server" }
        },
        "work": {
            "navidrome": { "ssh_host": "work-server" }
        }
    }
}
```

## 📊 Expected Results

When properly configured, you should see:
- Play counts in album listings: "Album Name (X plays)"
- Most Played tab populated with your top albums
- Recently Played tab with chronological listening history
- Status message: "Loaded play data from database"

If you see "Loaded play data from API", the fallback mode is active. 